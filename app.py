import os
import json
import uuid
import math
from datetime import datetime
from io import BytesIO
from pypdf import PdfReader
import docx
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configure the Gemini API with the provided key
API_KEY = "AIzaSyC4RcCu-C2jzLusZlua10wbpy3nemxaeRE"
genai.configure(api_key=API_KEY)

# Use the recommended Gemini model with a system instruction
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction="You are Bhoot AI, a friendly, modern, and helpful AI assistant with a slightly spooky but witty personality. Format your responses in Markdown for readability."
)

# Active chat sessions
chat_sessions = {}
pdf_knowledge = {} # stores { chat_id: [{"text": chunk, "embedding": vec}] }
HISTORY_FILE = "chat_history.json"

def compute_cosine_similarity(vec1, vec2):
    try:
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = math.sqrt(sum(a * a for a in vec1))
        norm_b = math.sqrt(sum(b * b for b in vec2))
        return dot_product / (norm_a * norm_b) if norm_a and norm_b else 0
    except Exception:
        return 0

def get_all_histories():
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_chat_history(chat_id):
    if chat_id not in chat_sessions:
        return
    chat = chat_sessions[chat_id]
    all_histories = get_all_histories()
    
    # Init new session dict if needed
    if str(chat_id) not in all_histories:
        title = "Chat " + datetime.now().strftime("%Y-%m-%d %H:%M")
        all_histories[str(chat_id)] = {"title": title, "messages": []}
            
    serialized = []
    # Chat history is a list of parts, we'll safely extract text to keep local storage lightweight
    for message in chat.history:
        text_parts = []
        for part in message.parts:
            try:
                # We save text. We don't save image blobs to disk.
                if part.text:
                    text_parts.append(part.text)
            except AttributeError:
                pass
        if text_parts:
            serialized.append({"role": message.role, "parts": text_parts})
            
    all_histories[str(chat_id)]["messages"] = serialized
    with open(HISTORY_FILE, 'w') as f:
        json.dump(all_histories, f)

def load_chat_history_messages(chat_id):
    all_histories = get_all_histories()
    data = all_histories.get(str(chat_id), {})
    return data.get("messages", [])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/history', methods=['GET'])
def get_histories_list():
    all_histories = get_all_histories()
    # Return a list of {chat_id, title}
    summaries = []
    # reverse to show newest first
    for k in reversed(list(all_histories.keys())):
        # Ensure it's not a legacy unformatted array
        if isinstance(all_histories[k], dict):
            summaries.append({"chat_id": k, "title": all_histories[k].get("title", "Unknown")})
    return jsonify({"histories": summaries})
    
@app.route('/api/chat/new', methods=['POST'])
def new_chat():
    chat_id = str(uuid.uuid4())
    chat_sessions[chat_id] = model.start_chat(history=[])
    return jsonify({"chat_id": chat_id})

@app.route('/api/history/<chat_id>', methods=['GET'])
def get_history(chat_id):
    messages = load_chat_history_messages(chat_id)
    return jsonify({"history": messages})

@app.route('/api/history/<chat_id>', methods=['DELETE'])
def delete_history(chat_id):
    # Remove from active sessions
    if chat_id in chat_sessions:
        del chat_sessions[chat_id]
        
    all_histories = get_all_histories()
    if str(chat_id) in all_histories:
        del all_histories[str(chat_id)]
        with open(HISTORY_FILE, 'w') as f:
            json.dump(all_histories, f)
            
    return jsonify({"success": True})

@app.route('/api/chat', methods=['POST'])
def chat():
    # Support both JSON (text only) and multipart/form-data (text + file)
    if request.is_json:
        user_message = request.json.get('message', '')
        chat_id = request.json.get('chat_id', '')
        file = None
    else:
        user_message = request.form.get('message', '')
        chat_id = request.form.get('chat_id', '')
        file = request.files.get('file')
        
    if not chat_id:
        return jsonify({'error': 'chat_id is required'}), 400
        
    if not user_message and not file:
        return jsonify({'error': 'Message or file is required'}), 400
        
    try:
        # Fallback if session doesn't exist yet
        if chat_id not in chat_sessions:
            messages = load_chat_history_messages(chat_id)
            chat_sessions[chat_id] = model.start_chat(history=messages)
            
        chat = chat_sessions[chat_id]
        
        # 1. Check if the file uploaded is a Document (PDF/DOCX) for RAG Processing
        is_document = False
        text = ""
        if file and file.filename:
            file_ext = file.filename.lower()
            if file_ext.endswith('.pdf'):
                is_document = True
                file.seek(0)
                reader = PdfReader(BytesIO(file.read()))
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            elif file_ext.endswith('.docx'):
                is_document = True
                file.seek(0)
                doc = docx.Document(BytesIO(file.read()))
                for para in doc.paragraphs:
                    if para.text:
                        text += para.text + "\n"
            
            # Chunking logic for knowledge extraction
            chunk_size = 1000
            overlap = 200
            chunks = []
            for i in range(0, len(text), chunk_size - overlap):
                chunk = text[i:i + chunk_size].strip()
                if len(chunk) > 50:
                    chunks.append(chunk)
                    
            if chunks:
                response_embed = genai.embed_content(
                    model="models/gemini-embedding-001",
                    content=chunks,
                    task_type="retrieval_document"
                )
                embeddings = response_embed['embedding']
                
                if chat_id not in pdf_knowledge:
                    pdf_knowledge[chat_id] = []
                    
                for chunk_text, emb in zip(chunks, embeddings):
                    pdf_knowledge[chat_id].append({"text": chunk_text, "embedding": emb})
                    
            if not user_message:
                # User just uploaded the PDF without a question
                return jsonify({'response': "I have read your PDF file and stored its contents in my temporary memory. What would you like to know about it?"})

        # 2. Augment the user's message using RAG if we have PDF memory for this chat
        augmented_message = user_message
        if user_message and chat_id in pdf_knowledge:
            query_embed = genai.embed_content(
                model="models/gemini-embedding-001",
                content=user_message,
                task_type="retrieval_query"
            )['embedding']
            
            # Calculate cosine similarity across all stored chunks
            scored_chunks = []
            for item in pdf_knowledge[chat_id]:
                sim = compute_cosine_similarity(query_embed, item["embedding"])
                scored_chunks.append((sim, item["text"]))
                
            # Select top 3 chunks
            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            top_chunks = [x[1] for x in scored_chunks[:3]]
            
            if top_chunks:
                context_block = "\n\n--- PDF DOCUMENT CONTEXT ---\n" + "\n---\n".join(top_chunks) + "\n----------------------------\n\nPlease answer the user's question drawing on the relevant context above."
                augmented_message = user_message + context_block

        # 3. Prepare content parts for Gemini
        parts = []
        if file and file.filename and not is_document:
            # If it's a multimodal image/audio, pass natively natively
            file.seek(0)
            parts.append({
                "mime_type": file.mimetype,
                "data": file.read()
            })
            
        if augmented_message:
            parts.append(augmented_message)
            
        # Send message with all parts
        response = chat.send_message(parts)
        
        # Save chat history to disk
        save_chat_history(chat_id)
        
        return jsonify({'response': response.text})
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "Exhausted" in error_msg:
            return jsonify({'error': 'You have exceeded your free tier limit of 100 messages per minute. Please wait 45 seconds and try again!'}), 500
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

import os
import json
import uuid
import math
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from io import BytesIO
from pypdf import PdfReader
import docx
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from duckduckgo_search import DDGS

app = Flask(__name__)
CORS(app)

# Configure the Gemini API with the provided key
API_KEY = "AIzaSyA7QB46Zktv5c77bFgS5EJA27JDmpJm50U"
genai.configure(api_key=API_KEY)

# Use the recommended Gemini model with a system instruction
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction="You are Ouro AI, a sophisticated, intelligent, and highly knowledgeable AI assistant. Provide direct, insightful, comprehensive, and clear answers formatted in clean Markdown. When citing web sources, use [Source Name](URL) format."
)

# Active chat sessions
chat_sessions = {}
pdf_knowledge = {} # stores { chat_id: [{"text": chunk, "embedding": vec, "source": URL_or_filename}] }
HISTORY_FILE = "chat_history.json"

def compute_cosine_similarity(vec1, vec2):
    try:
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = math.sqrt(sum(a * a for a in vec1))
        norm_b = math.sqrt(sum(b * b for b in vec2))
        return dot_product / (norm_a * norm_b) if norm_a and norm_b else 0
    except Exception:
        return 0

def fetch_and_extract_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        # Remove scripts and styles
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.extract()
        text = soup.get_text(separator=' ', strip=True)
        return text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def process_and_store_text(chat_id, text, source_name):
    chunk_size = 1000
    overlap = 200
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size].strip()
        if len(chunk) > 50:
            chunks.append(chunk)

    if not chunks:
        return

    try:
        # Generate embeddings
        response_embed = genai.embed_content(
            model="models/gemini-embedding-001",
            content=chunks,
            task_type="retrieval_document"
        )
        embeddings = response_embed['embedding']

        if chat_id not in pdf_knowledge:
            pdf_knowledge[chat_id] = []

        for chunk_text, emb in zip(chunks, embeddings):
            pdf_knowledge[chat_id].append({"text": chunk_text, "embedding": emb, "source": source_name})
    except Exception as e:
        print(f"Error generating embeddings for {source_name}: {e}")

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
    for message in chat.history:
        text_parts = []
        for part in message.parts:
            try:
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
    summaries = []
    for k in reversed(list(all_histories.keys())):
        if isinstance(all_histories[k], dict):
            summaries.append({"chat_id": k, "title": all_histories[k].get("title", "Unknown")})
    return jsonify({"histories": summaries})

@app.route('/api/chat/new', methods=['POST'])
def new_chat():
    chat_id = str(uuid.uuid4())
    chat_sessions[chat_id] = model.start_chat(history=[])
    if chat_id in pdf_knowledge:
        del pdf_knowledge[chat_id]
    return jsonify({"chat_id": chat_id})

@app.route('/api/history/<chat_id>', methods=['GET'])
def get_history(chat_id):
    messages = load_chat_history_messages(chat_id)
    return jsonify({"history": messages})

@app.route('/api/history/<chat_id>', methods=['DELETE'])
def delete_history(chat_id):
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
    if request.is_json:
        user_message = request.json.get('message', '')
        chat_id = request.json.get('chat_id', '')
        browse_web = request.json.get('browse_web', False)
        file = None
    else:
        user_message = request.form.get('message', '')
        chat_id = request.form.get('chat_id', '')
        browse_web = request.form.get('browse_web') == 'true'
        file = request.files.get('file')
        
    if not chat_id:
        return jsonify({'error': 'chat_id is required'}), 400
        
    if not user_message and not file:
        return jsonify({'error': 'Message or file is required'}), 400
        
    try:
        if chat_id not in chat_sessions:
            messages = load_chat_history_messages(chat_id)
            chat_sessions[chat_id] = model.start_chat(history=messages)
            
        chat = chat_sessions[chat_id]
        sources_used = []

        is_document = False
        if file and file.filename:
            file_ext = file.filename.lower()
            mime_type = file.mimetype
            text = ""
            if file_ext.endswith('.pdf') or 'pdf' in mime_type:
                is_document = True
                file.seek(0)
                reader = PdfReader(BytesIO(file.read()))
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            elif file_ext.endswith('.docx') or 'wordprocessingml.document' in mime_type or 'msword' in mime_type:
                is_document = True
                file.seek(0)
                doc = docx.Document(BytesIO(file.read()))
                for para in doc.paragraphs:
                    if para.text:
                        text += para.text + "\n"
            
            if is_document and text:
                process_and_store_text(chat_id, text, file.filename)
            
            if not user_message and is_document:
                return jsonify({'response': "I have read your document. What would you like to know about it?"})

        url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
        urls_in_message = url_pattern.findall(user_message)
        
        if browse_web and not urls_in_message and user_message:
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                resp = requests.post("https://html.duckduckgo.com/html/", data={"q": user_message}, headers=headers, timeout=5)
                soup = BeautifulSoup(resp.content, "html.parser")
                found_links = []
                for a in soup.find_all('a', class_='result__snippet')[:8]:
                    href = a.get('href')
                    if href and href.startswith('http') and not href.startswith('https://duckduckgo.com/y.js'):
                        found_links.append(href)
                urls_in_message.extend(found_links[:4])
            except Exception as e:
                print(f"Error searching DuckDuckGo: {e}")
                    
        if urls_in_message:
            urls_in_message = list(dict.fromkeys(urls_in_message))[:4]
            for url in urls_in_message:
                page_text = fetch_and_extract_url(url)
                if page_text:
                    process_and_store_text(chat_id, page_text, url)
                    sources_used.append(url)

        augmented_message = user_message
        if user_message and chat_id in pdf_knowledge:
            query_embed = genai.embed_content(
                model="models/gemini-embedding-001",
                content=user_message,
                task_type="retrieval_query"
            )['embedding']
            
            scored_chunks = []
            for item in pdf_knowledge[chat_id]:
                sim = compute_cosine_similarity(query_embed, item["embedding"])
                scored_chunks.append((sim, item["text"], item.get("source", "Unknown")))
                
            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            top_chunks = scored_chunks[:6]
            
            if top_chunks and any(x[0] > 0.5 for x in top_chunks):
                context_block = "\n\n--- RELEVANT KNOWLEDGE CONTEXT ---\n"
                used_sources = set()
                for _, chunk_text, src in top_chunks:
                    context_block += f"Source: {src}\n{chunk_text}\n---\n"
                    if src.startswith("http"):
                        used_sources.add(src)
                
                context_block += "----------------------------\n\nPlease answer the user's question accurately using the provided context. Cite sources when helpful."
                augmented_message = user_message + context_block
                
                for src in used_sources:
                    if src not in sources_used:
                        sources_used.append(src)

        parts = []
        if file and file.filename and not is_document:
            file.seek(0)
            parts.append({
                "mime_type": file.mimetype,
                "data": file.read()
            })
            
        if augmented_message:
            parts.append(augmented_message)
            
        response = chat.send_message(parts)
        save_chat_history(chat_id)
        
        return jsonify({
            'response': response.text,
            'sources': sources_used
        })
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "Exhausted" in error_msg:
            return jsonify({'error': 'You have exceeded your free tier limit of 100 messages per minute. Please wait 45 seconds and try again!'}), 500
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const welcomeScreen = document.getElementById('welcome-screen');
    const chatHistory = document.getElementById('chat-history');
    const chips = document.querySelectorAll('.chip');
    const menuToggle = document.getElementById('menu-toggle');
    const appContainer = document.querySelector('.app-container');

    // Auto-resize textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = userInput.scrollHeight + 'px';
    });

    // Session State
    let activeChatId = null;

    // Load persistent history logic
    async function createNewChat() {
        try {
            const res = await fetch('/api/chat/new', { method: 'POST' });
            const data = await res.json();
            activeChatId = data.chat_id;
            
            // UI Reset
            chatHistory.innerHTML = '';
            chatHistory.classList.add('hidden');
            welcomeScreen.classList.remove('hidden');
            const inputArea = document.querySelector('.input-area');
            welcomeScreen.appendChild(inputArea);
            inputArea.classList.remove('sticky-bottom');
        } catch (error) {
            console.error(error);
        }
    }

    async function loadChat(chatId) {
        try {
            const res = await fetch(`/api/history/${chatId}`);
            const data = await res.json();
            activeChatId = chatId;
            
            chatHistory.innerHTML = '';
            
            if (data.history && data.history.length > 0) {
                welcomeScreen.classList.add('hidden');
                chatHistory.classList.remove('hidden');
                const inputArea = document.querySelector('.input-area');
                chatHistory.after(inputArea);
                inputArea.classList.add('sticky-bottom');
                
                data.history.forEach(msg => {
                    const role = msg.role === 'user' ? 'user' : 'ai';
                    appendMessage(role, msg.parts.join('\n'));
                });
            } else {
                // If it's empty, act like a new chat
                chatHistory.classList.add('hidden');
                welcomeScreen.classList.remove('hidden');
            }
        } catch (error) {
            console.error(error);
        }
    }

    // Initialize
    createNewChat();

    // File upload elements
    const uploadBtn = document.getElementById('upload-btn');
    const fileUpload = document.getElementById('file-upload');
    const filePreviewContainer = document.getElementById('file-preview-container');
    const filePreviewImage = document.getElementById('file-preview-image');
    const filePreviewName = document.getElementById('file-preview-name');
    const removeFileBtn = document.getElementById('remove-file-btn');

    // Handle file selection UI
    uploadBtn.addEventListener('click', () => fileUpload.click());

    fileUpload.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            const file = this.files[0];
            filePreviewName.textContent = file.name;
            
            // If it's an image, show preview
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    filePreviewImage.src = e.target.result;
                    filePreviewImage.style.display = 'block';
                }
                reader.readAsDataURL(file);
            } else if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.docx') || file.name.toLowerCase().endsWith('.doc')) {
                // simple base64 placeholder for a document/pdf icon
                filePreviewImage.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512"><path fill="%23aaa" d="M0 64C0 28.7 28.7 0 64 0H224V128c0 17.7 14.3 32 32 32H384V448c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V64zm384 64H256V0L384 128z"/></svg>';
                filePreviewImage.style.display = 'block';
                filePreviewImage.style.padding = '5px';
                filePreviewImage.style.background = 'rgba(255,255,255,0.1)';
            } else {
                filePreviewImage.style.display = 'none';
            }
            
            filePreviewContainer.classList.remove('hidden');
        }
    });

    removeFileBtn.addEventListener('click', () => {
        fileUpload.value = '';
        filePreviewContainer.classList.add('hidden');
    });

    // Sidebar history interactions
    const btnNewChat = document.getElementById('btn-new-chat');
    const btnHistory = document.getElementById('btn-history');
    const historyList = document.getElementById('history-list');

    // Voice recording hook
    const micBtn = document.getElementById('mic-btn');
    let mediaRecorder = null;
    let audioChunks = [];
    let isRecording = false;

    micBtn.addEventListener('click', async () => {
        if (!isRecording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = event => {
                    if (event.data.size > 0) audioChunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    const audioFile = new File([audioBlob], "voice_message.webm", { type: 'audio/webm' });
                    
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(audioFile);
                    fileUpload.files = dataTransfer.files;
                    
                    // Dispatch change event to trigger the visual preview box
                    fileUpload.dispatchEvent(new Event('change'));
                    
                    // Flash the input area to show something was recorded
                    userInput.placeholder = "Voice loaded. Send or add text!";
                };

                mediaRecorder.start();
                isRecording = true;
                micBtn.style.color = '#ff4757';
                userInput.placeholder = "Listening...";
            } catch (err) {
                console.error("Microphone issue:", err);
                alert("Could not access microphone.");
            }
        } else {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
            isRecording = false;
            micBtn.style.color = '';
            userInput.placeholder = "Ask Bhoot AI...";
        }
    });

    btnNewChat.addEventListener('click', () => {
        createNewChat();
        historyList.classList.add('hidden');
    });

    btnHistory.addEventListener('click', async () => {
        historyList.classList.toggle('hidden');
        if (!historyList.classList.contains('hidden')) {
            try {
                historyList.innerHTML = 'Loading...';
                const res = await fetch('/api/history');
                const data = await res.json();
                historyList.innerHTML = '';
                if (data.histories && data.histories.length > 0) {
                    data.histories.forEach(h => {
                        const div = document.createElement('div');
                        div.style.display = 'flex';
                        div.style.justifyContent = 'space-between';
                        div.style.alignItems = 'center';
                        div.style.padding = '5px';
                        div.style.borderBottom = '1px solid rgba(255,255,255,0.1)';
                        
                        const titleSpan = document.createElement('span');
                        titleSpan.innerText = h.title;
                        titleSpan.style.cursor = 'pointer';
                        titleSpan.style.flexGrow = '1';
                        titleSpan.addEventListener('click', () => {
                            loadChat(h.chat_id);
                        });
                        
                        const deleteBtn = document.createElement('button');
                        deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
                        deleteBtn.style.background = 'none';
                        deleteBtn.style.border = 'none';
                        deleteBtn.style.color = '#ff6b6b';
                        deleteBtn.style.cursor = 'pointer';
                        deleteBtn.title = "Delete Chat";
                        deleteBtn.addEventListener('click', async (e) => {
                            e.stopPropagation();
                            if(confirm("Are you sure you want to delete this chat?")) {
                                await fetch(`/api/history/${h.chat_id}`, { method: 'DELETE' });
                                // trigger history reload
                                historyList.classList.add('hidden');
                                btnHistory.click();
                            }
                        });
                        
                        div.appendChild(titleSpan);
                        div.appendChild(deleteBtn);
                        historyList.appendChild(div);
                    });
                } else {
                    historyList.innerHTML = 'No history found.';
                }
            } catch (err) {
                historyList.innerHTML = 'Error loading history.';
            }
        }
    });

    // Handle menu toggle for mobile
    menuToggle.addEventListener('click', () => {
        appContainer.classList.toggle('sidebar-open');
    });

    // Send message on click
    sendBtn.addEventListener('click', () => handleUserInput());

    // Send message on Enter (but Shift+Enter for new line)
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleUserInput();
        }
    });

    // Handle suggestion chips
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            userInput.value = chip.innerText.trim();
            handleUserInput();
        });
    });

    async function handleUserInput() {
        const message = userInput.value.trim();
        const file = fileUpload.files[0];
        
        if (!message && !file) return;

        // Clear input and reset height
        userInput.value = '';
        userInput.style.height = 'auto';

        // Prepare UI
        if (!welcomeScreen.classList.contains('hidden')) {
            welcomeScreen.classList.add('hidden');
            chatHistory.classList.remove('hidden');
            // Move the input bar to the bottom of the chat history
            const inputArea = document.querySelector('.input-area');
            chatHistory.after(inputArea);
            inputArea.classList.add('sticky-bottom');
        }

        // Add user message to UI (if text exists or file exists)
        if (message) {
            appendMessage('user', message);
        } else if (file) {
            appendMessage('user', `[Uploaded file: ${file.name}]`);
        }

        // Fetch response from backend
        try {
            let requestBody;
            let headers = {};
            
            if (file) {
                // Use FormData if there is a file
                requestBody = new FormData();
                requestBody.append('message', message);
                requestBody.append('file', file);
                requestBody.append('chat_id', activeChatId);
                // Do not set Content-Type for FormData, fetch does it automatically with boundary
            } else {
                // Use JSON if there is no file
                headers['Content-Type'] = 'application/json';
                requestBody = JSON.stringify({ message: message, chat_id: activeChatId });
            }

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: headers,
                body: requestBody,
            });

            // Clear file input UI after sending
            if (file) {
                fileUpload.value = '';
                filePreviewContainer.classList.add('hidden');
            }

            const data = await response.json();
            if (data.response) {
                appendMessage('ai', data.response);
            } else if (data.error) {
                appendMessage('ai', "Error: " + data.error);
            }
        } catch (error) {
            console.error('Error fetching chat:', error);
            appendMessage('ai', "Sorry, I'm having trouble connecting to the server.");
        }
    }

    function appendMessage(role, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = `message-avatar ${role === 'ai' ? 'ai-avatar' : 'user-avatar'}`;
        avatar.innerHTML = role === 'ai' ? '<i class="fas fa-ghost"></i>' : 'A';

        const content = document.createElement('div');
        content.className = 'message-content';
        
        if (role === 'ai') {
            content.innerHTML = marked.parse(text);
        } else {
            content.innerText = text;
        }

        if (role === 'ai') {
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(content);
        } else {
            messageDiv.appendChild(content);
            messageDiv.appendChild(avatar);
        }

        chatHistory.appendChild(messageDiv);

        // Scroll to bottom
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
});

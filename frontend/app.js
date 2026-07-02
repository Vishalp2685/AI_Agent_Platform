// Configuration
const API_BASE_URL = 'http://localhost:8000';

// Application State
let activeSessionId = null;
let sessionsList = [];
let selectedModel = 'gemma-4-31b-it';
let isLoading = false;
let isUploading = false;

// DOM Elements
const sidebar = document.getElementById('sidebar');
const toggleSidebarBtn = document.getElementById('toggleSidebarBtn');
const closeSidebarBtn = document.getElementById('closeSidebarBtn');
const sessionsListEl = document.getElementById('sessionsList');
const newChatBtn = document.getElementById('newChatBtn');
const clearCacheBtn = document.getElementById('clearCacheBtn');
const activeSessionIdEl = document.getElementById('activeSessionId');
const modelSelect = document.getElementById('modelSelect');
const messagesContainer = document.getElementById('messagesContainer');
const welcomeScreen = document.getElementById('welcomeScreen');
const chatsWrapper = document.getElementById('chatsWrapper');
const typingIndicator = document.getElementById('typingIndicator');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const suggestionCards = document.querySelectorAll('.suggestion-card');

// Upload DOM Elements
const uploadBtn = document.getElementById('uploadBtn');
const fileInput = document.getElementById('fileInput');
const uploadPreviewContainer = document.getElementById('uploadPreviewContainer');
const uploadPreviewName = document.getElementById('uploadPreviewName');
const uploadPreviewStatus = document.getElementById('uploadPreviewStatus');
const removeUploadBtn = document.getElementById('removeUploadBtn');

// Setup Marked.js Markdown Parsing with Highlight.js code rendering
const renderer = new marked.Renderer();
renderer.code = function(code, lang) {
    let codeText = typeof code === 'object' ? code.text : code;
    let language = typeof code === 'object' ? code.lang : lang;
    language = language || 'plaintext';
    
    let highlighted;
    try {
        if (hljs.getLanguage(language)) {
            highlighted = hljs.highlight(codeText, { language }).value;
        } else {
            highlighted = hljs.highlightAuto(codeText).value;
        }
    } catch (e) {
        highlighted = codeText;
    }
    
    return `<pre><div class="code-header">
        <span>${language}</span>
        <button class="copy-btn" onclick="copyCode(this)">
            <i class="fa-regular fa-clipboard"></i> Copy
        </button>
    </div><code class="hljs language-${language}">${highlighted}</code></pre>`;
};
marked.setOptions({ renderer: renderer });

// Global function to copy code blocks to clipboard
window.copyCode = function(button) {
    const pre = button.closest('pre');
    const codeElement = pre.querySelector('code');
    const text = codeElement.innerText;
    
    navigator.clipboard.writeText(text).then(() => {
        button.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
        button.style.color = 'hsl(140, 80%, 65%)';
        setTimeout(() => {
            button.innerHTML = '<i class="fa-regular fa-clipboard"></i> Copy';
            button.style.color = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
};

// Event Listeners
document.addEventListener('DOMContentLoaded', init);

function init() {
    // Sidebar toggle (Mobile responsive design)
    toggleSidebarBtn.addEventListener('click', () => {
        sidebar.classList.toggle('open');
    });
    
    closeSidebarBtn.addEventListener('click', () => {
        sidebar.classList.remove('open');
    });

    // Close sidebar on main click if mobile and open
    messagesContainer.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
            sidebar.classList.remove('open');
        }
    });

    // Model Selector Change
    modelSelect.addEventListener('change', (e) => {
        selectedModel = e.target.value;
    });

    // New Chat Button Click
    newChatBtn.addEventListener('click', startNewChat);

    // Clear Cache Button Click
    clearCacheBtn.addEventListener('click', clearRedisCache);

    // Chat Input Textarea Listeners
    chatInput.addEventListener('input', () => {
        adjustTextareaHeight();
        toggleSendButtonState();
    });

    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitMessage();
        }
    });

    // Send Button Click
    sendBtn.addEventListener('click', submitMessage);

    // Welcome Suggestion Cards Click
    suggestionCards.forEach(card => {
        card.addEventListener('click', () => {
            const promptText = card.getAttribute('data-prompt');
            chatInput.value = promptText;
            adjustTextareaHeight();
            toggleSendButtonState();
            submitMessage();
        });
    });

    // Upload Button Click -> trigger hidden input
    uploadBtn.addEventListener('click', () => {
        if (isUploading) return;
        fileInput.click();
    });

    // File Input Selection Change
    fileInput.addEventListener('change', handleFileSelect);

    // Remove Upload Preview Button Click
    removeUploadBtn.addEventListener('click', removeAttachment);

    // Load initial data
    loadSessions(true);
}

// Adjust Textarea Height dynamically as user types
function adjustTextareaHeight() {
    chatInput.style.height = 'auto';
    chatInput.style.height = `${chatInput.scrollHeight}px`;
}

// Enable/Disable Send button based on text area contents
function toggleSendButtonState() {
    const value = chatInput.value.trim();
    sendBtn.disabled = value === '' || isLoading;
}

// Load session IDs from the backend API
async function loadSessions(selectFirst = false) {
    try {
        const response = await fetch(`${API_BASE_URL}/get_all_sessions/`);
        if (!response.ok) throw new Error('Failed to fetch sessions');
        
        sessionsList = await response.json();
        renderSessionsList();

        if (selectFirst) {
            if (sessionsList.length > 0) {
                // Select the first session (or last created)
                const targetSession = sessionsList[sessionsList.length - 1];
                setActiveSession(targetSession);
            } else {
                // If there are no sessions, create a new one automatically
                startNewChat();
            }
        }
    } catch (error) {
        console.error('Error fetching sessions:', error);
        // Show skeleton or failure indicator in sidebar
        sessionsListEl.innerHTML = `
            <div style="padding: 12px; color: var(--text-muted); font-size: 0.8rem; text-align: center;">
                <i class="fa-solid fa-triangle-exclamation" style="color: hsl(35, 80%, 60%); margin-bottom: 6px; font-size: 1.2rem;"></i><br>
                Unable to load session history. Ensure API is running at port 8000.
            </div>
        `;
    }
}

// Render the loaded session IDs inside the sidebar
function renderSessionsList() {
    sessionsListEl.innerHTML = '';
    
    if (sessionsList.length === 0) {
        sessionsListEl.innerHTML = `
            <div style="padding: 12px; color: var(--text-muted); font-size: 0.8rem; text-align: center;">
                No chats yet
            </div>
        `;
        return;
    }

    // Sort or reverse to show newest first
    const listCopy = [...sessionsList].reverse();
    
    listCopy.forEach(sessionId => {
        const li = document.createElement('li');
        li.className = `session-item ${sessionId === activeSessionId ? 'active' : ''}`;
        li.setAttribute('data-id', sessionId);
        li.innerHTML = `
            <i class="fa-regular fa-comment-dots"></i>
            <span>${sessionId}</span>
        `;
        
        li.addEventListener('click', () => {
            if (activeSessionId === sessionId) return;
            setActiveSession(sessionId);
            // On mobile, close the sidebar after selection
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('open');
            }
        });
        
        sessionsListEl.appendChild(li);
    });
}

// Request backend to create a new session ID
async function startNewChat() {
    if (isLoading) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat/create_new_session`);
        if (!response.ok) throw new Error('Failed to create new session');
        
        const newSessionId = await response.json();
        setActiveSession(newSessionId, true);
    } catch (error) {
        console.error('Error creating new session:', error);
        alert('Failed to start new chat session. Check if backend server is online.');
    }
}

// Set active session state, fetch chats, and update sidebar active item
function setActiveSession(sessionId, isNew = false) {
    activeSessionId = sessionId;
    activeSessionIdEl.textContent = sessionId || 'None';
    
    // Reset document upload preview on session switch
    if (uploadPreviewContainer) {
        uploadPreviewContainer.style.display = 'none';
    }
    if (fileInput) {
        fileInput.value = '';
    }
    isUploading = false;
    
    // Highlight active session item in sidebar
    document.querySelectorAll('.session-item').forEach(item => {
        if (item.getAttribute('data-id') === sessionId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    if (isNew) {
        // Clear message area and show welcome screen
        chatsWrapper.innerHTML = '';
        chatsWrapper.style.display = 'none';
        welcomeScreen.style.display = 'flex';
        // Add to list and render list without refetching
        if (!sessionsList.includes(sessionId)) {
            sessionsList.push(sessionId);
            renderSessionsList();
        }
    } else {
        // Load chats from API
        fetchChatsForSession(sessionId);
    }
}

// Fetch chat messages for a specific session
async function fetchChatsForSession(sessionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/get_chats/${sessionId}`);
        if (!response.ok) throw new Error('Failed to fetch chats');
        
        const chats = await response.json();
        
        chatsWrapper.innerHTML = '';
        
        if (chats.length === 0) {
            chatsWrapper.style.display = 'none';
            welcomeScreen.style.display = 'flex';
        } else {
            welcomeScreen.style.display = 'none';
            chatsWrapper.style.display = 'flex';
            
            chats.forEach(chat => {
                appendMessageToUI(chat.role, chat.message, chat.sent_on, chat.model_used);
            });
            
            scrollToBottom();
        }
    } catch (error) {
        console.error('Error loading chats:', error);
        chatsWrapper.innerHTML = `
            <div style="padding: 24px; text-align: center; color: hsl(0, 80%, 65%);">
                <i class="fa-solid fa-triangle-exclamation" style="font-size: 1.5rem; margin-bottom: 8px;"></i>
                <p>Failed to load chats. API might be offline.</p>
            </div>
        `;
        chatsWrapper.style.display = 'flex';
        welcomeScreen.style.display = 'none';
    }
}

// Render message structure into the messages area
function appendMessageToUI(role, messageText, timeString = null, modelName = null) {
    const isUser = role === 'user';
    const row = document.createElement('div');
    row.className = `message-row ${isUser ? 'user' : 'bot'}`;
    
    // Format timestamp
    let formattedTime = '';
    if (timeString) {
        try {
            const date = new Date(timeString);
            formattedTime = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            formattedTime = '';
        }
    } else {
        formattedTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    // Avatar HTML
    const avatarHTML = isUser 
        ? `<div class="user-avatar"><i class="fa-regular fa-user"></i></div>`
        : `<div class="bot-avatar"><i class="fa-solid fa-wand-magic-sparkles"></i></div>`;
        
    // Parse Markdown for assistant responses, plain text with escapes for user
    const contentHTML = isUser
        ? escapeHTML(messageText).replace(/\n/g, '<br>')
        : marked.parse(messageText);

    // Meta details (time + optionally model)
    const metaHTML = `
        <div class="message-meta">
            ${!isUser && modelName ? `<span>${modelName}</span> &bull;` : ''}
            <span>${formattedTime}</span>
        </div>
    `;

    row.innerHTML = `
        ${avatarHTML}
        <div class="message-bubble">
            ${contentHTML}
            ${metaHTML}
        </div>
    `;
    
    chatsWrapper.appendChild(row);
}

// Submit user message to backend
async function submitMessage() {
    const text = chatInput.value.trim();
    if (!text || isLoading || !activeSessionId) return;

    isLoading = true;
    chatInput.value = '';
    adjustTextareaHeight();
    toggleSendButtonState();
    
    // Hide welcome panel if visible
    if (welcomeScreen.style.display !== 'none') {
        welcomeScreen.style.display = 'none';
        chatsWrapper.style.display = 'flex';
    }
    
    // Display user message in UI immediately
    appendMessageToUI('user', text);
    scrollToBottom();
    
    // Display typing indicator
    typingIndicator.style.display = 'flex';
    scrollToBottom();

    try {
        const response = await fetch(`${API_BASE_URL}/chat/get_response`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model_name: selectedModel,
                chat_session_id: activeSessionId,
                user_message: text,
                role: 'user'
            })
        });

        if (!response.ok) throw new Error('API request failed');
        
        const payload = await response.json();
        
        // Hide typing indicator
        typingIndicator.style.display = 'none';
        
        if (payload.status && payload.model_answer) {
            appendMessageToUI('model', payload.model_answer, null, selectedModel);
            
            // Check if current session needs to be added to sessions list (if it was brand new)
            if (!sessionsList.includes(activeSessionId)) {
                await loadSessions(false);
            }
        } else {
            const comments = payload.comments || 'No response from model';
            appendMessageToUI('model', `*Failed to generate response: ${comments}*`);
        }
    } catch (error) {
        console.error('Error fetching chat response:', error);
        typingIndicator.style.display = 'none';
        appendMessageToUI('model', `*Connection error: Could not reach the AI Agent Platform backend. Check if the server is running.*`);
    } finally {
        isLoading = false;
        toggleSendButtonState();
        scrollToBottom();
    }
}

// Clear Redis cache and reset application state
async function clearRedisCache() {
    if (!confirm('Are you sure you want to clear the entire session cache? This will reset all stored chats.')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/clear_redis`);
        if (!response.ok) throw new Error('Failed to clear cache');
        
        const success = await response.json();
        if (success) {
            // Reset state
            activeSessionId = null;
            sessionsList = [];
            chatsWrapper.innerHTML = '';
            chatsWrapper.style.display = 'none';
            welcomeScreen.style.display = 'flex';
            
            // Reload (which will trigger a clean new chat session)
            await loadSessions(true);
        }
    } catch (error) {
        console.error('Error clearing redis cache:', error);
        alert('Failed to clear session cache. Is backend running?');
    }
}

// Auto-scroll the messages container to the bottom
function scrollToBottom() {
    messagesContainer.scrollTo({
        top: messagesContainer.scrollHeight,
        behavior: 'smooth'
    });
}

// Helper: Escape HTML strings to prevent XSS on user-injected text
function escapeHTML(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Handle file selection and upload
async function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    // Validate that it is a PDF file
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
        alert('Invalid file type. Only PDF files are allowed.');
        fileInput.value = '';
        return;
    }

    isUploading = true;
    
    // Disable inputs
    chatInput.disabled = true;
    sendBtn.disabled = true;
    uploadBtn.disabled = true;

    // Update upload preview UI
    uploadPreviewName.textContent = file.name;
    uploadPreviewStatus.textContent = 'Uploading...';
    uploadPreviewStatus.className = 'upload-preview-status uploading';
    removeUploadBtn.style.display = 'none';
    uploadPreviewContainer.style.display = 'block';

    try {
        // Ensure a session exists
        if (!activeSessionId) {
            const sessionResponse = await fetch(`${API_BASE_URL}/chat/create_new_session`);
            if (!sessionResponse.ok) throw new Error('Failed to create new chat session');
            const newSessionId = await sessionResponse.json();
            setActiveSession(newSessionId, true);
        }

        // Prepare request
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/documents/upload/?session_id=${activeSessionId}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Upload failed');
        }

        const data = await response.json();

        // Show success status
        uploadPreviewStatus.textContent = 'Ready';
        uploadPreviewStatus.className = 'upload-preview-status ready';
        
        // Add confirm message in chat
        if (welcomeScreen.style.display !== 'none') {
            welcomeScreen.style.display = 'none';
            chatsWrapper.style.display = 'flex';
        }
        
        appendMessageToUI('model', `📎 **Document Uploaded**: *"${file.name}"*\n\nParsed and embedded successfully. Gemma is now equipped with its content. You can ask questions based on it.`, null, selectedModel);
        scrollToBottom();

    } catch (error) {
        console.error('Error uploading file:', error);
        uploadPreviewStatus.textContent = 'Failed';
        uploadPreviewStatus.className = 'upload-preview-status failed';
        alert(`Failed to upload document: ${error.message}`);
    } finally {
        isUploading = false;
        removeUploadBtn.style.display = 'flex';
        
        // Re-enable inputs
        chatInput.disabled = false;
        uploadBtn.disabled = false;
        toggleSendButtonState();
        chatInput.focus();
        
        // Reset file input value
        fileInput.value = '';
    }
}

// Remove document preview visually
function removeAttachment() {
    if (isUploading) return;
    uploadPreviewContainer.style.display = 'none';
    fileInput.value = '';
    
    // Notify user how context behaves
    appendMessageToUI('model', `ℹ️ **Notice**: The document preview has been dismissed from the input panel. However, please note that any documents successfully parsed during this session remain embedded in the database context for this chat session until a **New Chat** is started or cache is cleared.`, null, selectedModel);
    scrollToBottom();
}

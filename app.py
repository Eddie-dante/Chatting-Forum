<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes">
  <title>ChatVerse • community forum</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 1rem;
      margin: 0;
    }

    .forum-container {
      width: 100%;
      max-width: 850px;
      height: 90vh;
      max-height: 800px;
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(18px);
      -webkit-backdrop-filter: blur(18px);
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 2.5rem;
      box-shadow: 0 30px 50px rgba(0, 0, 0, 0.6), inset 0 0 15px rgba(255, 255, 255, 0.05);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      color: #e2e8f0;
    }

    /* header */
    .forum-header {
      padding: 1.2rem 1.8rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: rgba(15, 23, 42, 0.4);
      backdrop-filter: blur(10px);
    }

    .logo {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .logo-icon {
      font-size: 2rem;
      filter: drop-shadow(0 0 8px #7c3aed);
    }

    .logo h1 {
      font-weight: 600;
      font-size: 1.6rem;
      letter-spacing: -0.3px;
      background: linear-gradient(to right, #c084fc, #a78bfa);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .online-badge {
      background: rgba(255, 255, 255, 0.08);
      padding: 0.4rem 1rem;
      border-radius: 2rem;
      font-size: 0.8rem;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 0.4rem;
      border: 1px solid rgba(255, 255, 255, 0.15);
    }

    .online-dot {
      width: 10px;
      height: 10px;
      background: #10b981;
      border-radius: 50%;
      box-shadow: 0 0 10px #10b981;
    }

    /* chat messages area */
    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 1.5rem 1.2rem;
      display: flex;
      flex-direction: column;
      gap: 1.2rem;
      scroll-behavior: smooth;
      background: rgba(0, 0, 0, 0.2);
    }

    .message-row {
      display: flex;
      align-items: flex-start;
      gap: 0.7rem;
      animation: fadeInUp 0.25s ease-out;
    }

    .message-row.own-message {
      flex-direction: row-reverse;
    }

    @keyframes fadeInUp {
      0% {
        opacity: 0;
        transform: translateY(10px);
      }
      100% {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: linear-gradient(135deg, #7c3aed, #a78bfa);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 600;
      font-size: 1rem;
      color: white;
      box-shadow: 0 8px 15px rgba(124, 58, 237, 0.4);
      flex-shrink: 0;
      text-transform: uppercase;
    }

    .own-message .avatar {
      background: linear-gradient(135deg, #3b82f6, #60a5fa);
      box-shadow: 0 8px 15px rgba(59, 130, 246, 0.5);
    }

    .message-bubble {
      background: rgba(255, 255, 255, 0.08);
      backdrop-filter: blur(5px);
      padding: 0.9rem 1.2rem;
      border-radius: 1.2rem 1.2rem 1.2rem 0.3rem;
      max-width: 75%;
      border: 1px solid rgba(255, 255, 255, 0.1);
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
      word-wrap: break-word;
    }

    .own-message .message-bubble {
      background: rgba(59, 130, 246, 0.2);
      border-radius: 1.2rem 1.2rem 0.3rem 1.2rem;
      border-color: rgba(59, 130, 246, 0.3);
    }

    .message-author {
      font-weight: 600;
      font-size: 0.8rem;
      margin-bottom: 0.25rem;
      color: #cbd5e1;
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }

    .own-message .message-author {
      color: #93c5fd;
      justify-content: flex-end;
    }

    .time-stamp {
      font-weight: 400;
      font-size: 0.7rem;
      color: #94a3b8;
      margin-left: 0.3rem;
    }

    .message-text {
      color: #f1f5f9;
      line-height: 1.45;
      font-size: 0.95rem;
    }

    .empty-chat {
      text-align: center;
      color: #64748b;
      margin-top: 3rem;
      font-style: italic;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.8rem;
      opacity: 0.8;
    }

    /* input area */
    .forum-input-area {
      padding: 1rem 1.5rem 1.3rem;
      background: rgba(15, 23, 42, 0.6);
      backdrop-filter: blur(15px);
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      display: flex;
      flex-direction: column;
      gap: 0.7rem;
    }

    .username-row {
      display: flex;
      align-items: center;
      gap: 0.8rem;
      flex-wrap: wrap;
    }

    .username-label {
      font-size: 0.8rem;
      color: #a5b4fc;
      display: flex;
      align-items: center;
      gap: 0.3rem;
    }

    #usernameInput {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 2rem;
      padding: 0.5rem 1rem;
      color: white;
      font-size: 0.9rem;
      outline: none;
      width: 160px;
      transition: all 0.2s;
    }

    #usernameInput:focus {
      border-color: #a78bfa;
      box-shadow: 0 0 10px rgba(167, 139, 250, 0.4);
    }

    .message-compose {
      display: flex;
      gap: 0.7rem;
      align-items: center;
    }

    #messageInput {
      flex: 1;
      background: rgba(255, 255, 255, 0.07);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 2.5rem;
      padding: 0.9rem 1.4rem;
      color: #f8fafc;
      font-size: 0.95rem;
      outline: none;
      transition: 0.2s;
      resize: none;
    }

    #messageInput:focus {
      border-color: #c084fc;
      box-shadow: 0 0 15px rgba(192, 132, 252, 0.3);
    }

    #messageInput::placeholder {
      color: #64748b;
    }

    .send-btn {
      background: linear-gradient(135deg, #7c3aed, #a855f7);
      border: none;
      border-radius: 50%;
      width: 48px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: white;
      font-size: 1.4rem;
      box-shadow: 0 8px 18px rgba(124, 58, 237, 0.5);
      transition: all 0.2s ease;
      border: 1px solid rgba(255, 255, 255, 0.2);
      flex-shrink: 0;
    }

    .send-btn:hover {
      background: linear-gradient(135deg, #8b5cf6, #c084fc);
      transform: scale(1.05);
      box-shadow: 0 10px 22px rgba(139, 92, 246, 0.7);
    }

    .send-btn:active {
      transform: scale(0.96);
    }

    .clear-chat-btn {
      background: transparent;
      border: 1px solid rgba(255, 255, 255, 0.2);
      color: #cbd5e1;
      padding: 0.3rem 1rem;
      border-radius: 2rem;
      font-size: 0.75rem;
      cursor: pointer;
      transition: 0.2s;
      margin-left: 0.5rem;
    }

    .clear-chat-btn:hover {
      background: rgba(255, 255, 255, 0.1);
      color: white;
    }

    @media (max-width: 500px) {
      .forum-container {
        height: 95vh;
        border-radius: 1.8rem;
      }
      .message-bubble {
        max-width: 85%;
      }
    }
  </style>
</head>
<body>
<div class="forum-container">
  <!-- Header -->
  <header class="forum-header">
    <div class="logo">
      <span class="logo-icon">💬</span>
      <h1>ChatVerse</h1>
    </div>
    <div class="online-badge">
      <span class="online-dot"></span>
      <span id="onlineCounter">1 online</span>
    </div>
  </header>

  <!-- Messages container -->
  <div class="chat-messages" id="chatMessages" aria-live="polite">
    <!-- welcome / empty state -->
    <div class="empty-chat" id="emptyState">
      <span style="font-size: 2.5rem;">🌌</span>
      <span>No messages yet. Start the conversation!</span>
      <span style="font-size: 0.8rem;">Be friendly ✨</span>
    </div>
  </div>

  <!-- Input section -->
  <div class="forum-input-area">
    <div class="username-row">
      <span class="username-label">👤 Your name</span>
      <input type="text" id="usernameInput" placeholder="e.g. Nova" maxlength="18" autocomplete="off" />
      <button class="clear-chat-btn" id="clearChatBtn" title="Clear all messages">🧹 Clear chat</button>
    </div>
    <div class="message-compose">
      <input type="text" id="messageInput" placeholder="Write your message..." maxlength="350" autocomplete="off" />
      <button class="send-btn" id="sendBtn" aria-label="Send message">▶</button>
    </div>
  </div>
</div>

<script>
  (function() {
    // ----- app state -----
    const STORAGE_KEY = 'chatverse_forum_messages';
    
    // Default welcome thread (only used if storage empty)
    const DEFAULT_MESSAGES = [
      {
        id: '1',
        username: 'Astra',
        text: 'Welcome to ChatVerse! 🌟 This is a live forum. Feel free to chat.',
        timestamp: Date.now() - 3600000
      },
      {
        id: '2',
        username: 'Nebula',
        text: 'Hey everyone! Love the vibe here.',
        timestamp: Date.now() - 1800000
      }
    ];

    // Current messages array
    let messages = [];

    // DOM elements
    const chatMessagesEl = document.getElementById('chatMessages');
    const usernameInput = document.getElementById('usernameInput');
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    const clearChatBtn = document.getElementById('clearChatBtn');
    const onlineCounterEl = document.getElementById('onlineCounter');
    const emptyStateEl = document.getElementById('emptyState');

    // ----- helper: load messages from localStorage -----
    function loadMessages() {
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          messages = JSON.parse(stored);
          // ensure messages is array
          if (!Array.isArray(messages)) messages = [];
        } else {
          // first visit: use default messages and save
          messages = DEFAULT_MESSAGES.map(m => ({...m}));
          saveMessagesToStorage();
        }
      } catch (e) {
        console.warn('Could not load messages, resetting', e);
        messages = DEFAULT_MESSAGES.map(m => ({...m}));
        saveMessagesToStorage();
      }
    }

    function saveMessagesToStorage() {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    }

    // ----- get or guess username -----
    function getCurrentUsername() {
      const raw = usernameInput.value.trim();
      if (raw !== '') return raw;
      // fallback random guest name
      return 'Guest_' + Math.floor(Math.random() * 1000);
    }

    // ----- format time -----
    function formatTime(timestamp) {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
    }

    // ----- render all messages -----
    function renderMessages() {
      if (!chatMessagesEl) return;
      
      // Remove all children except maybe we keep structure; we rebuild completely
      chatMessagesEl.innerHTML = '';
      
      if (messages.length === 0) {
        // show empty state
        const emptyDiv = document.createElement('div');
        emptyDiv.className = 'empty-chat';
        emptyDiv.id = 'emptyState';
        emptyDiv.innerHTML = `<span style="font-size:2.5rem;">🌌</span>
                              <span>No messages yet. Start the conversation!</span>
                              <span style="font-size:0.8rem;">Be friendly ✨</span>`;
        chatMessagesEl.appendChild(emptyDiv);
        return;
      }
      
      // If there was emptyState with id, it's removed.
      const currentUser = getCurrentUsername().toLowerCase();
      
      messages.forEach(msg => {
        const isOwn = msg.username.toLowerCase() === currentUser;
        const messageRow = document.createElement('div');
        messageRow.className = `message-row ${isOwn ? 'own-message' : ''}`;
        
        // avatar initial
        const initial = msg.username.charAt(0).toUpperCase();
        
        messageRow.innerHTML = `
          <div class="avatar">${initial}</div>
          <div class="message-bubble">
            <div class="message-author">
              ${escapeHTML(msg.username)}
              <span class="time-stamp">${formatTime(msg.timestamp)}</span>
            </div>
            <div class="message-text">${escapeHTML(msg.text)}</div>
          </div>
        `;
        chatMessagesEl.appendChild(messageRow);
      });
      
      // auto scroll to bottom
      chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
    }

    // simple escape to prevent XSS
    function escapeHTML(str) {
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    // ----- add new message -----
    function addMessage(text) {
      const trimmedText = text.trim();
      if (trimmedText === '') return false;
      
      const username = getCurrentUsername();
      // create message object
      const newMsg = {
        id: Date.now().toString() + Math.random().toString(36).substr(2, 6),
        username: username,
        text: trimmedText,
        timestamp: Date.now()
      };
      
      messages.push(newMsg);
      saveMessagesToStorage();
      renderMessages();
      return true;
    }

    // ----- clear all messages (with confirmation) -----
    function clearAllMessages() {
      if (messages.length === 0) {
        alert('Chat is already empty.');
        return;
      }
      if (confirm('Delete all forum messages? This cannot be undone.')) {
        messages = [];
        saveMessagesToStorage();
        renderMessages();
      }
    }

    // ----- update online counter (simulated) -----
    function updateOnlineCounter() {
      // Simulate 1-5 users based on something static; we can randomize mildly
      const base = 1;
      const extra = Math.floor(Math.random() * 4); // 0-3
      const online = base + extra;
      if (onlineCounterEl) {
        onlineCounterEl.textContent = `${online} online`;
      }
    }

    // ----- event handlers -----
    function handleSend() {
      const text = messageInput.value;
      const success = addMessage(text);
      if (success) {
        messageInput.value = '';
        // focus back
        messageInput.focus();
      } else {
        // maybe shake or alert? just gentle alert
        if (text.trim() === '') {
          alert('Please write a message.');
        }
      }
    }

    // ----- set default username if empty -----
    function setDefaultUsername() {
      if (!usernameInput.value.trim()) {
        // try to get from localStorage a saved username?
        const savedUser = localStorage.getItem('chatverse_username');
        if (savedUser) {
          usernameInput.value = savedUser;
        } else {
          // generate a cute random name
          const names = ['Nova', 'Orion', 'Lyra', 'Zen', 'Rune', 'Echo', 'Juno', 'Vega'];
          const randomName = names[Math.floor(Math.random() * names.length)];
          usernameInput.value = randomName;
          localStorage.setItem('chatverse_username', randomName);
        }
      }
    }

    // save username on change
    function saveUsernameToStorage() {
      const name = usernameInput.value.trim();
      if (name) {
        localStorage.setItem('chatverse_username', name);
      }
      // re-render to update own-message highlights
      renderMessages();
    }

    // ----- initial setup -----
    function init() {
      loadMessages();
      setDefaultUsername();
      renderMessages();
      updateOnlineCounter();
      
      // refresh online counter every 25 secs (visual flair)
      setInterval(updateOnlineCounter, 25000);
      
      // event listeners
      sendBtn.addEventListener('click', handleSend);
      
      messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          handleSend();
        }
      });
      
      clearChatBtn.addEventListener('click', clearAllMessages);
      
      usernameInput.addEventListener('input', () => {
        // save on typing with debounce feel; we just save and re-render
        saveUsernameToStorage();
      });
      
      // also re-render when username loses focus (blur)
      usernameInput.addEventListener('blur', () => {
        saveUsernameToStorage();
      });
      
      // additional: periodic re-render to keep times fresh? not necessary.
      // But we could listen for storage events from other tabs (simulate forum sync)
      window.addEventListener('storage', (e) => {
        if (e.key === STORAGE_KEY) {
          // another tab changed messages
          loadMessages();
          renderMessages();
        }
      });
    }

    // start everything
    init();
  })();
</script>
</body>
</html>

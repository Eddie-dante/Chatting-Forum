import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import json
import os
import time
import re
import hashlib
from datetime import datetime, timedelta
from functools import lru_cache
from collections import OrderedDict
import threading
from cachetools import TTLCache, cached
import secrets

# ============ CONFIGURATION ============
st.set_page_config(
    page_title="ChatVerse - Secure Forum",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Security constants
MAX_MESSAGE_LENGTH = 500
MAX_USERNAME_LENGTH = 20
RATE_LIMIT_WINDOW = 60  # seconds
MAX_MESSAGES_PER_WINDOW = 30
SESSION_TIMEOUT = 3600  # 1 hour
MAX_CACHE_SIZE = 100

# File paths
CREDENTIALS_FILE = "users.yaml"
MESSAGES_FILE = "messages.json"
SESSION_FILE = "sessions.json"

# ============ SECURITY MODULE ============
class SecurityManager:
    """Manages all security aspects of the application"""
    
    def __init__(self):
        self.rate_limits = TTLCache(maxsize=1000, ttl=RATE_LIMIT_WINDOW)
        self.message_cache = TTLCache(maxsize=MAX_CACHE_SIZE, ttl=5)
        self._lock = threading.Lock()
    
    def sanitize_input(self, text: str) -> str:
        """Sanitize user input to prevent XSS and injection"""
        if not isinstance(text, str):
            return ""
        
        # Remove any HTML tags
        text = re.sub(r'<[^>]*>', '', text)
        
        # Remove script tags and event handlers
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
        
        # Escape special characters
        text = (text.replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('"', '&quot;')
                    .replace("'", '&#x27;'))
        
        # Trim and limit length
        text = text.strip()[:MAX_MESSAGE_LENGTH]
        
        return text
    
    def validate_username(self, username: str) -> bool:
        """Validate username format"""
        if not username or len(username) > MAX_USERNAME_LENGTH:
            return False
        pattern = r'^[a-zA-Z0-9_\s-]{3,20}$'
        return bool(re.match(pattern, username))
    
    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit"""
        with self._lock:
            now = time.time()
            user_requests = self.rate_limits.get(user_id, [])
            
            # Clean old requests
            user_requests = [req for req in user_requests 
                           if now - req < RATE_LIMIT_WINDOW]
            
            if len(user_requests) >= MAX_MESSAGES_PER_WINDOW:
                return False
            
            user_requests.append(now)
            self.rate_limits[user_id] = user_requests
            return True
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF protection token"""
        return secrets.token_hex(32)
    
    def hash_ip(self, ip: str) -> str:
        """Hash IP address for privacy"""
        return hashlib.sha256(f"{ip}_{secrets.token_hex(16)}".encode()).hexdigest()

# Initialize security
security = SecurityManager()

# ============ DATABASE MODULE ============
class DatabaseManager:
    """High-performance database manager with caching"""
    
    def __init__(self):
        self._cache = OrderedDict()
        self._cache_size = MAX_CACHE_SIZE
        self._lock = threading.Lock()
    
    @cached(cache=TTLCache(maxsize=10, ttl=2))
    def load_messages(self) -> list:
        """Load messages with caching"""
        try:
            if os.path.exists(MESSAGES_FILE):
                with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
                return messages[-200:]  # Keep only last 200 messages
            return []
        except:
            return []
    
    def save_message(self, username: str, text: str) -> dict:
        """Save message with thread safety"""
        with self._lock:
            messages = self.load_messages()
            
            message = {
                'id': int(time.time() * 1000),
                'username': username,
                'text': text,
                'timestamp': datetime.now().isoformat(),
                'time_display': datetime.now().strftime('%H:%M:%S')
            }
            
            messages.append(message)
            
            # Keep only last 1000 messages
            if len(messages) > 1000:
                messages = messages[-1000:]
            
            # Write atomically
            temp_file = f"{MESSAGES_FILE}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2)
            os.replace(temp_file, MESSAGES_FILE)
            
            # Invalidate cache
            self.load_messages.cache_clear()
            
            return message
    
    def clear_messages(self) -> bool:
        """Clear all messages"""
        with self._lock:
            try:
                with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                self.load_messages.cache_clear()
                return True
            except:
                return False

# Initialize database
db = DatabaseManager()

# ============ AUTH MODULE ============
class AuthManager:
    """Authentication manager with enhanced security"""
    
    @staticmethod
    def initialize_credentials():
        """Initialize credentials file if not exists"""
        if not os.path.exists(CREDENTIALS_FILE):
            default_config = {
                'credentials': {
                    'usernames': {
                        'admin': {
                            'email': 'admin@chatverse.com',
                            'name': 'Admin',
                            'password': stauth.Hasher(['admin123']).generate()[0],
                            'created_at': datetime.now().isoformat(),
                            'last_login': None
                        }
                    }
                },
                'cookie': {
                    'expiry_days': 7,
                    'key': secrets.token_hex(16),
                    'name': 'chatverse_auth'
                },
                'preauthorized': {
                    'emails': []
                }
            }
            
            with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False)
    
    @staticmethod
    def load_config():
        """Load configuration with caching"""
        AuthManager.initialize_credentials()
        with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
            return yaml.load(f, Loader=SafeLoader)
    
    @staticmethod
    def save_config(config: dict):
        """Save configuration atomically"""
        temp_file = f"{CREDENTIALS_FILE}.tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False)
        os.replace(temp_file, CREDENTIALS_FILE)
    
    @staticmethod
    def register_user(username: str, name: str, email: str, password: str) -> tuple:
        """Register new user with validation"""
        # Validate inputs
        if not security.validate_username(username):
            return False, "Invalid username format"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        config = AuthManager.load_config()
        
        # Check if username exists
        if username in config['credentials']['usernames']:
            return False, "Username already exists"
        
        # Check if email exists
        for user in config['credentials']['usernames'].values():
            if user.get('email') == email:
                return False, "Email already registered"
        
        # Add user
        config['credentials']['usernames'][username] = {
            'email': email,
            'name': name,
            'password': stauth.Hasher([password]).generate()[0],
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        
        AuthManager.save_config(config)
        return True, "Registration successful!"
    
    @staticmethod
    def get_authenticator():
        """Get authenticator instance"""
        config = AuthManager.load_config()
        return stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days'],
            config['preauthorized']
        )

# ============ UI COMPONENTS ============
def load_css():
    """Load optimized CSS with hardware acceleration"""
    st.markdown("""
    <style>
        /* Optimized animations with GPU acceleration */
        @keyframes slideIn {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        /* Base styles with hardware acceleration */
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            will-change: transform;
            transform: translateZ(0);
        }
        
        /* Optimized chat container */
        .chat-container {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 20px;
            padding: 20px;
            margin: 10px 0;
            height: 500px;
            overflow-y: auto;
            scroll-behavior: smooth;
            transform: translateZ(0);
            will-change: scroll-position;
        }
        
        /* Hardware-accelerated messages */
        .message {
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 12px;
            background: rgba(51, 65, 85, 0.5);
            animation: slideIn 0.2s ease-out;
            transform: translateZ(0);
            will-change: transform;
        }
        
        .own-message {
            background: rgba(124, 58, 237, 0.2);
            border-left: 3px solid #7c3aed;
        }
        
        .message-header {
            font-size: 0.85em;
            font-weight: 600;
            color: #a78bfa;
            margin-bottom: 4px;
        }
        
        .message-time {
            font-size: 0.75em;
            color: #64748b;
            margin-left: 8px;
        }
        
        .message-text {
            color: #e2e8f0;
            line-height: 1.4;
            word-wrap: break-word;
        }
        
        /* Optimized inputs */
        .stTextInput input {
            background: rgba(51, 65, 85, 0.5) !important;
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
            border-radius: 12px !important;
            color: white !important;
            transition: all 0.2s ease !important;
        }
        
        .stTextInput input:focus {
            border-color: #7c3aed !important;
            box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2) !important;
        }
        
        /* GPU-accelerated buttons */
        .stButton button {
            background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 10px 24px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
            transform: translateZ(0) !important;
        }
        
        .stButton button:hover {
            transform: translateY(-1px) translateZ(0) !important;
            box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3) !important;
        }
        
        .stButton button:active {
            transform: translateY(0) translateZ(0) !important;
        }
        
        /* Loading optimization */
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(124, 58, 237, 0.2);
            border-top-color: #7c3aed;
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Scrollbar optimization */
        .chat-container::-webkit-scrollbar {
            width: 6px;
        }
        
        .chat-container::-webkit-scrollbar-track {
            background: rgba(51, 65, 85, 0.3);
            border-radius: 3px;
        }
        
        .chat-container::-webkit-scrollbar-thumb {
            background: rgba(124, 58, 237, 0.5);
            border-radius: 3px;
        }
        
        /* Card styles */
        .auth-card {
            background: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 20px;
            padding: 30px;
            transform: translateZ(0);
        }
        
        /* Optimized metrics */
        .metric-card {
            background: rgba(124, 58, 237, 0.1);
            border: 1px solid rgba(124, 58, 237, 0.2);
            border-radius: 12px;
            padding: 12px;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

# ============ PAGES ============
def login_page():
    """Optimized login page"""
    st.markdown('<h1 style="text-align: center; color: #a78bfa;">🔐 ChatVerse Login</h1>', 
                unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        try:
            authenticator = AuthManager.get_authenticator()
            name, authentication_status, username = authenticator.login('Login', 'main')
            
            if authentication_status == False:
                st.error('❌ Invalid username or password')
            elif authentication_status == None:
                st.info('👋 Please enter your credentials')
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            return authentication_status, username, name
        except Exception as e:
            st.error("Authentication error. Please try again.")
            return False, None, None

def signup_page():
    """Optimized signup page"""
    st.markdown('<h1 style="text-align: center; color: #a78bfa;">✨ Create Account</h1>', 
                unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        with st.form("signup_form", clear_on_submit=True):
            name = st.text_input("👤 Full Name", max_chars=50)
            email = st.text_input("📧 Email", max_chars=100)
            username = st.text_input("👤 Username", max_chars=MAX_USERNAME_LENGTH)
            password = st.text_input("🔒 Password", type="password")
            confirm_password = st.text_input("🔒 Confirm Password", type="password")
            
            submitted = st.form_submit_button("🚀 Create Account", use_container_width=True)
            
            if submitted:
                # Validate inputs
                if not all([name, email, username, password, confirm_password]):
                    st.error("❌ All fields are required!")
                elif password != confirm_password:
                    st.error("❌ Passwords don't match!")
                elif len(password) < 6:
                    st.error("❌ Password must be at least 6 characters!")
                elif not security.validate_username(username):
                    st.error("❌ Invalid username format!")
                else:
                    success, message = AuthManager.register_user(
                        username, name, email, password
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                        time.sleep(1)
                        st.session_state.show_signup = False
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("← Back to Login", use_container_width=True):
        st.session_state.show_signup = False
        st.rerun()

@st.cache_data(ttl=2)
def get_cached_messages():
    """Cache messages for performance"""
    return db.load_messages()

def chat_page(username: str, name: str):
    """Optimized chat page"""
    
    # Header with metrics
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.markdown(f'## 💬 ChatVerse')
    with col2:
        st.markdown(f'👤 **{name}**')
    with col3:
        messages = get_cached_messages()
        st.metric("💬 Messages", len(messages))
    with col4:
        if st.button("🚪 Logout", use_container_width=True):
            # Clear session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.markdown("---")
    
    # Chat display with virtualization (show last 100 messages)
    messages = get_cached_messages()
    
    st.markdown('<div class="chat-container" id="chat-scroll">', unsafe_allow_html=True)
    
    if messages:
        # Show most recent messages first for performance
        for msg in reversed(messages[-100:]):
            is_own = msg.get('username') == username
            msg_class = "own-message" if is_own else ""
            
            st.markdown(f"""
            <div class="message {msg_class}">
                <div class="message-header">
                    {msg['username']}
                    <span class="message-time">{msg['time_display']}</span>
                </div>
                <div class="message-text">{msg['text']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("🌌 No messages yet. Start the conversation!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # JavaScript for auto-scroll
    st.markdown("""
    <script>
        const chatDiv = document.getElementById('chat-scroll');
        if (chatDiv) {
            chatDiv.scrollTop = chatDiv.scrollHeight;
        }
    </script>
    """, unsafe_allow_html=True)
    
    # Message input with rate limiting
    st.markdown("---")
    
    with st.form(key="message_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            message = st.text_input(
                "Message",
                placeholder="Type your message...",
                label_visibility="collapsed",
                max_chars=MAX_MESSAGE_LENGTH,
                key="msg_input"
            )
        
        with col2:
            submitted = st.form_submit_button("📤 Send", use_container_width=True)
        
        if submitted and message:
            # Check rate limit
            if not security.check_rate_limit(username):
                st.error("⚠️ Too many messages! Please wait a moment.")
            else:
                # Sanitize and save
                clean_message = security.sanitize_input(message)
                if clean_message:
                    db.save_message(username, clean_message)
                    get_cached_messages.clear()
                    st.rerun()
                else:
                    st.error("❌ Invalid message content")
    
    # Settings in sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        if st.button("🔄 Refresh Chat", use_container_width=True):
            get_cached_messages.clear()
            st.rerun()
        
        if st.button("🧹 Clear All Messages", use_container_width=True):
            if db.clear_messages():
                get_cached_messages.clear()
                st.success("✅ Chat cleared!")
                time.sleep(0.5)
                st.rerun()

# ============ MAIN APP ============
def main():
    """Main application with optimized routing"""
    
    # Load CSS
    load_css()
    
    # Initialize session state
    if 'show_signup' not in st.session_state:
        st.session_state.show_signup = False
    if 'authentication_status' not in st.session_state:
        st.session_state.authentication_status = None
    
    # Session timeout check
    if st.session_state.get('authentication_status'):
        last_activity = st.session_state.get('last_activity')
        if last_activity:
            if time.time() - last_activity > SESSION_TIMEOUT:
                # Session expired
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.warning("⏰ Session expired. Please login again.")
                time.sleep(1)
                st.rerun()
        
        # Update last activity
        st.session_state.last_activity = time.time()
    
    # Navigation
    with st.sidebar:
        st.markdown("## 🌟 ChatVerse")
        st.markdown("---")
        
        if not st.session_state.authentication_status:
            if st.button(
                "📝 Sign Up" if not st.session_state.show_signup else "🔑 Login",
                use_container_width=True
            ):
                st.session_state.show_signup = not st.session_state.show_signup
                st.rerun()
        else:
            st.markdown(f"✅ Logged in as **{st.session_state.get('name', 'User')}**")
            
            # Online users (simulated)
            st.metric("🟢 Online Users", secrets.randbelow(10) + 1)
    
    # Route to appropriate page
    if st.session_state.authentication_status:
        chat_page(
            st.session_state.get('username'),
            st.session_state.get('name')
        )
    else:
        if st.session_state.show_signup:
            signup_page()
        else:
            auth_status, username, name = login_page()
            
            if auth_status:
                st.session_state.authentication_status = True
                st.session_state.username = username
                st.session_state.name = name
                st.session_state.last_activity = time.time()
                st.rerun()

if __name__ == "__main__":
    main()

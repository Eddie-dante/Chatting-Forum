import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import json
import os
import time
import re
import hashlib
from datetime import datetime
import threading
from functools import lru_cache

# ============ CONFIGURATION ============
st.set_page_config(
    page_title="ChatVerse - Secure Forum",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# File paths
CREDENTIALS_FILE = "users.yaml"
MESSAGES_FILE = "messages.json"

# ============ SECURITY ============
def sanitize_input(text):
    """Sanitize user input to prevent XSS"""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    # Remove script tags
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Escape HTML entities
    text = (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))
    return text.strip()[:500]

# ============ DATABASE ============
def initialize_files():
    """Initialize necessary files"""
    # Create credentials file if not exists
    if not os.path.exists(CREDENTIALS_FILE):
        default_config = {
            'credentials': {
                'usernames': {
                    'admin': {
                        'email': 'admin@chatverse.com',
                        'name': 'Admin User',
                        'password': stauth.Hasher(['admin123']).generate()[0]
                    }
                }
            },
            'cookie': {
                'expiry_days': 30,
                'key': 'chatverse_random_key_2024',
                'name': 'chatverse_cookie'
            },
            'preauthorized': {
                'emails': []
            }
        }
        with open(CREDENTIALS_FILE, 'w') as file:
            yaml.dump(default_config, file, default_flow_style=False)
    
    # Create messages file if not exists
    if not os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'w') as f:
            json.dump([], f)

def load_messages():
    """Load messages from file"""
    try:
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_message(username, text):
    """Save a new message"""
    messages = load_messages()
    
    message = {
        'id': len(messages) + 1,
        'username': username,
        'text': sanitize_input(text),
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'date': datetime.now().strftime("%Y-%m-%d")
    }
    
    messages.append(message)
    
    # Keep only last 500 messages
    if len(messages) > 500:
        messages = messages[-500:]
    
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages, f, indent=2)
    
    return message

def clear_all_messages():
    """Clear all messages"""
    with open(MESSAGES_FILE, 'w') as f:
        json.dump([], f)

# ============ AUTHENTICATION ============
def load_auth_config():
    """Load authentication configuration"""
    with open(CREDENTIALS_FILE) as file:
        config = yaml.load(file, Loader=SafeLoader)
    return config

def save_auth_config(config):
    """Save authentication configuration"""
    with open(CREDENTIALS_FILE, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

def register_user(username, name, email, password):
    """Register a new user"""
    config = load_auth_config()
    
    # Check if username exists
    if username in config['credentials']['usernames']:
        return False, "Username already exists!"
    
    # Check if email exists
    for user in config['credentials']['usernames'].values():
        if user.get('email') == email:
            return False, "Email already registered!"
    
    # Add new user
    config['credentials']['usernames'][username] = {
        'email': email,
        'name': name,
        'password': stauth.Hasher([password]).generate()[0]
    }
    
    save_auth_config(config)
    return True, "Registration successful!"

# ============ UI COMPONENTS ============
def load_css():
    """Load custom CSS"""
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        }
        
        .chat-container {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 20px;
            padding: 20px;
            margin: 10px 0;
            height: 500px;
            overflow-y: auto;
        }
        
        .message {
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 12px;
            background: rgba(51, 65, 85, 0.5);
            animation: slideIn 0.3s ease-out;
        }
        
        .own-message {
            background: rgba(124, 58, 237, 0.2);
            border-left: 3px solid #7c3aed;
        }
        
        @keyframes slideIn {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        .message-header {
            font-size: 0.85em;
            font-weight: 600;
            color: #a78bfa;
            margin-bottom: 5px;
        }
        
        .message-time {
            font-size: 0.75em;
            color: #64748b;
            margin-left: 10px;
        }
        
        .message-text {
            color: #e2e8f0;
            line-height: 1.5;
        }
        
        .stTextInput > div > div > input {
            background: rgba(51, 65, 85, 0.5) !important;
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
            border-radius: 12px !important;
            color: white !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #7c3aed !important;
            box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2) !important;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 10px 24px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3) !important;
        }
        
        .auth-card {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(10px);
        }
        
        .header-title {
            color: #a78bfa;
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 30px;
        }
    </style>
    """, unsafe_allow_html=True)

# ============ PAGES ============
def login_page():
    """Login page"""
    st.markdown('<h1 class="header-title">🔐 ChatVerse Login</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        config = load_auth_config()
        authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days'],
            config['preauthorized']
        )
        
        name, authentication_status, username = authenticator.login('Login', 'main')
        
        if authentication_status == False:
            st.error('❌ Username/password is incorrect')
        elif authentication_status == None:
            st.warning('👋 Please enter your username and password')
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        return authentication_status, username, name

def signup_page():
    """Signup page"""
    st.markdown('<h1 class="header-title">✨ Create Account</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        with st.form("signup_form", clear_on_submit=True):
            name = st.text_input("👤 Full Name", max_chars=50)
            email = st.text_input("📧 Email", max_chars=100)
            username = st.text_input("👤 Username", max_chars=20)
            password = st.text_input("🔒 Password", type="password")
            confirm_password = st.text_input("🔒 Confirm Password", type="password")
            
            submitted = st.form_submit_button("🚀 Create Account", use_container_width=True)
            
            if submitted:
                if not all([name, email, username, password, confirm_password]):
                    st.error("❌ All fields are required!")
                elif len(username) < 3:
                    st.error("❌ Username must be at least 3 characters!")
                elif len(password) < 6:
                    st.error("❌ Password must be at least 6 characters!")
                elif password != confirm_password:
                    st.error("❌ Passwords don't match!")
                elif not re.match(r'^[a-zA-Z0-9_]+$', username):
                    st.error("❌ Username can only contain letters, numbers, and underscores!")
                else:
                    success, message = register_user(username, name, email, password)
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

def chat_page(username, name):
    """Main chat page"""
    # Header
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.markdown(f'## 💬 ChatVerse Forum')
    with col2:
        st.markdown(f'👤 **{name}**')
    with col3:
        messages = load_messages()
        st.metric("💬 Messages", len(messages))
    with col4:
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.markdown("---")
    
    # Chat messages
    messages = load_messages()
    
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    if messages:
        for msg in reversed(messages[-100:]):  # Show last 100 messages
            is_own = msg.get('username') == username
            msg_class = "own-message" if is_own else ""
            
            st.markdown(f"""
            <div class="message {msg_class}">
                <div class="message-header">
                    {msg['username']}
                    <span class="message-time">{msg['timestamp']}</span>
                </div>
                <div class="message-text">{msg['text']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("🌌 No messages yet. Start the conversation!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Message input
    st.markdown("---")
    
    with st.form(key="message_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            message = st.text_input(
                "Message",
                placeholder="Type your message here...",
                label_visibility="collapsed",
                max_chars=500,
                key="msg_input"
            )
        
        with col2:
            submitted = st.form_submit_button("📤 Send", use_container_width=True)
        
        if submitted and message and message.strip():
            save_message(username, message)
            st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        if st.button("🔄 Refresh Chat", use_container_width=True):
            st.rerun()
        
        if st.button("🧹 Clear Chat", use_container_width=True):
            clear_all_messages()
            st.success("✅ Chat cleared!")
            time.sleep(0.5)
            st.rerun()

# ============ MAIN APP ============
def main():
    """Main application"""
    # Initialize files
    initialize_files()
    
    # Load CSS
    load_css()
    
    # Initialize session state
    if 'show_signup' not in st.session_state:
        st.session_state.show_signup = False
    if 'authentication_status' not in st.session_state:
        st.session_state.authentication_status = None
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## 🌟 ChatVerse")
        st.markdown("---")
        
        if not st.session_state.authentication_status:
            if st.button(
                "📝 Create Account" if not st.session_state.show_signup else "🔑 Login",
                use_container_width=True
            ):
                st.session_state.show_signup = not st.session_state.show_signup
                st.rerun()
    
    # Route to appropriate page
    if st.session_state.authentication_status:
        chat_page(st.session_state.username, st.session_state.name)
    else:
        if st.session_state.show_signup:
            signup_page()
        else:
            auth_status, username, name = login_page()
            if auth_status:
                st.session_state.authentication_status = True
                st.session_state.username = username
                st.session_state.name = name
                st.rerun()

if __name__ == "__main__":
    main()

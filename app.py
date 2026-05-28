import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import json
import os
import time
from datetime import datetime

# ============ CONFIGURATION ============
st.set_page_config(
    page_title="ChatVerse Forum",
    page_icon="💬",
    layout="wide"
)

# File paths
CREDENTIALS_FILE = "users.yaml"
MESSAGES_FILE = "messages.json"

# ============ INITIALIZE FILES ============
def init_files():
    # Create users.yaml if not exists
    if not os.path.exists(CREDENTIALS_FILE):
        hashed_passwords = stauth.Hasher(['admin123']).generate()
        
        config = {
            'credentials': {
                'usernames': {
                    'admin': {
                        'email': 'admin@chatverse.com',
                        'name': 'Admin',
                        'password': hashed_passwords[0]
                    }
                }
            },
            'cookie': {
                'expiry_days': 30,
                'key': 'random_signature_key_123',
                'name': 'chatverse_cookie'
            },
            'preauthorized': {
                'emails': []
            }
        }
        
        with open(CREDENTIALS_FILE, 'w') as file:
            yaml.dump(config, file)
    
    # Create messages.json if not exists
    if not os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'w') as f:
            json.dump([], f)

# ============ LOAD CONFIG ============
def load_config():
    with open(CREDENTIALS_FILE) as file:
        config = yaml.load(file, Loader=SafeLoader)
    return config

# ============ SAVE USER ============
def register_user(username, name, email, password):
    config = load_config()
    
    if username in config['credentials']['usernames']:
        return False, "Username already exists"
    
    for user in config['credentials']['usernames'].values():
        if user['email'] == email:
            return False, "Email already exists"
    
    hashed_passwords = stauth.Hasher([password]).generate()
    
    config['credentials']['usernames'][username] = {
        'email': email,
        'name': name,
        'password': hashed_passwords[0]
    }
    
    with open(CREDENTIALS_FILE, 'w') as file:
        yaml.dump(config, file)
    
    return True, "Registration successful"

# ============ MESSAGE HANDLING ============
def load_messages():
    try:
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_message(username, text):
    messages = load_messages()
    
    message = {
        'username': username,
        'text': text[:500],
        'time': datetime.now().strftime("%H:%M"),
        'date': datetime.now().strftime("%Y-%m-%d")
    }
    
    messages.append(message)
    
    if len(messages) > 200:
        messages = messages[-200:]
    
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages, f)
    
    return message

def clear_messages():
    with open(MESSAGES_FILE, 'w') as f:
        json.dump([], f)

# ============ CUSTOM CSS ============
def load_css():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
    .main-header {
        color: #a78bfa;
        text-align: center;
        font-size: 3em;
        font-weight: bold;
        margin-bottom: 20px;
    }
    
    .chat-box {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 15px;
        padding: 20px;
        height: 500px;
        overflow-y: auto;
        margin: 10px 0;
    }
    
    .message-bubble {
        background: rgba(51, 65, 85, 0.6);
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0;
    }
    
    .my-message {
        background: rgba(124, 58, 237, 0.3);
        border-left: 3px solid #7c3aed;
    }
    
    .msg-user {
        color: #a78bfa;
        font-weight: bold;
        font-size: 0.9em;
    }
    
    .msg-time {
        color: #64748b;
        font-size: 0.8em;
        margin-left: 10px;
    }
    
    .msg-text {
        color: #e2e8f0;
        margin-top: 5px;
    }
    
    div[data-testid="stTextInput"] input {
        background: rgba(51, 65, 85, 0.6) !important;
        border: 1px solid rgba(148, 163, 184, 0.3) !important;
        border-radius: 10px !important;
        color: white !important;
        padding: 12px !important;
    }
    
    div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 25px !important;
        font-weight: bold !important;
    }
    
    div[data-testid="stButton"] button:hover {
        background: linear-gradient(135deg, #8b5cf6, #7c3aed) !important;
        transform: translateY(-2px) !important;
    }
    
    .auth-container {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 20px;
        padding: 30px;
        max-width: 400px;
        margin: 0 auto;
    }
    </style>
    """, unsafe_allow_html=True)

# ============ LOGIN PAGE ============
def login_page():
    st.markdown('<h1 class="main-header">💬 ChatVerse</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        
        config = load_config()
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
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        return authentication_status, username, name

# ============ SIGNUP PAGE ============
def signup_page():
    st.markdown('<h1 class="main-header">✨ Create Account</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        
        with st.form("signup_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            submit = st.form_submit_button("Create Account", use_container_width=True)
            
            if submit:
                if not all([name, email, username, password]):
                    st.error("All fields are required")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                elif password != confirm_password:
                    st.error("Passwords don't match")
                else:
                    success, message = register_user(username, name, email, password)
                    if success:
                        st.success(message)
                        st.balloons()
                        time.sleep(1)
                        st.session_state.show_signup = False
                        st.rerun()
                    else:
                        st.error(message)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("← Back to Login"):
        st.session_state.show_signup = False
        st.rerun()

# ============ CHAT PAGE ============
def chat_page(username, name):
    st.markdown(f'<h1 class="main-header">💬 ChatVerse Forum</h1>', unsafe_allow_html=True)
    
    # Top bar
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"### Welcome, **{name}**! 👋")
    with col2:
        messages = load_messages()
        st.metric("Messages", len(messages))
    with col3:
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Chat messages
    st.markdown("---")
    messages = load_messages()
    
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    
    if messages:
        for msg in messages[-100:]:
            is_mine = msg['username'] == username
            msg_class = "my-message" if is_mine else ""
            
            st.markdown(f"""
            <div class="message-bubble {msg_class}">
                <span class="msg-user">{msg['username']}</span>
                <span class="msg-time">{msg['time']}</span>
                <div class="msg-text">{msg['text']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No messages yet. Start the conversation! 🌟")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Message input
    st.markdown("---")
    
    with st.form("message_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            msg = st.text_input("Message", placeholder="Type your message...", 
                               label_visibility="collapsed")
        with col2:
            send = st.form_submit_button("📤 Send", use_container_width=True)
        
        if send and msg:
            save_message(username, msg)
            st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Options")
        if st.button("🔄 Refresh"):
            st.rerun()
        if st.button("🧹 Clear Chat"):
            clear_messages()
            st.success("Chat cleared!")
            time.sleep(0.5)
            st.rerun()

# ============ MAIN ============
def main():
    init_files()
    load_css()
    
    if 'show_signup' not in st.session_state:
        st.session_state.show_signup = False
    if 'authentication_status' not in st.session_state:
        st.session_state.authentication_status = None
    
    if st.session_state.authentication_status:
        chat_page(st.session_state.username, st.session_state.name)
    else:
        if st.session_state.show_signup:
            signup_page()
        else:
            # Sidebar for switching between login/signup
            with st.sidebar:
                st.markdown("## 🌟 ChatVerse")
                st.markdown("---")
                if st.button("Create Account" if not st.session_state.show_signup else "Login"):
                    st.session_state.show_signup = not st.session_state.show_signup
                    st.rerun()
            
            auth_status, username, name = login_page()
            if auth_status:
                st.session_state.authentication_status = True
                st.session_state.username = username
                st.session_state.name = name
                st.rerun()

if __name__ == "__main__":
    main()

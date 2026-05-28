import streamlit as st
import yaml
from yaml.loader import SafeLoader
import json
import os
import time
from datetime import datetime
import hashlib
import secrets

# ============ CONFIGURATION ============
st.set_page_config(
    page_title="ChatVerse Forum",
    page_icon="💬",
    layout="wide"
)

# File paths
CREDENTIALS_FILE = "users.yaml"
MESSAGES_FILE = "messages.json"

# ============ SIMPLE PASSWORD HASHING ============
def hash_password(password):
    """Simple password hashing"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256(f"{password}{salt}".encode())
    return f"{salt}${hash_obj.hexdigest()}"

def check_password(password, hashed):
    """Check password against hash"""
    try:
        salt, hash_value = hashed.split('$')
        check_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        return check_hash == hash_value
    except:
        return False

# ============ INITIALIZE FILES ============
def init_files():
    if not os.path.exists(CREDENTIALS_FILE):
        default_config = {
            'users': {
                'admin': {
                    'email': 'admin@chatverse.com',
                    'name': 'Admin',
                    'password': hash_password('admin123')
                }
            }
        }
        with open(CREDENTIALS_FILE, 'w') as file:
            yaml.dump(default_config, file)
    
    if not os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'w') as f:
            json.dump([], f)

# ============ USER MANAGEMENT ============
def load_users():
    with open(CREDENTIALS_FILE) as file:
        config = yaml.load(file, Loader=SafeLoader)
    return config.get('users', {})

def save_users(users):
    config = {'users': users}
    with open(CREDENTIALS_FILE, 'w') as file:
        yaml.dump(config, file)

def register_user(username, name, email, password):
    users = load_users()
    
    if username in users:
        return False, "Username already exists"
    
    for user_data in users.values():
        if user_data.get('email') == email:
            return False, "Email already exists"
    
    users[username] = {
        'email': email,
        'name': name,
        'password': hash_password(password)
    }
    
    save_users(users)
    return True, "Registration successful"

def login_user(username, password):
    users = load_users()
    
    if username not in users:
        return False, None
    
    user_data = users[username]
    if check_password(password, user_data['password']):
        return True, user_data['name']
    
    return False, None

# ============ MESSAGE MANAGEMENT ============
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

def clear_messages():
    with open(MESSAGES_FILE, 'w') as f:
        json.dump([], f)

# ============ UI STYLING ============
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    .chat-box {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 15px;
        padding: 20px;
        height: 500px;
        overflow-y: auto;
        margin: 10px 0;
    }
    .message {
        background: rgba(51, 65, 85, 0.6);
        border-radius: 12px;
        padding: 12px;
        margin: 8px 0;
    }
    .my-msg {
        background: rgba(124, 58, 237, 0.3);
        border-left: 3px solid #7c3aed;
    }
    .msg-user {
        color: #a78bfa;
        font-weight: bold;
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
    .stButton button {
        background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: bold !important;
    }
    .stTextInput input {
        background: rgba(51, 65, 85, 0.6) !important;
        border-radius: 10px !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ============ SESSION STATE ============
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'name' not in st.session_state:
    st.session_state.name = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# ============ INITIALIZE ============
init_files()

# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("## 🌟 ChatVerse")
    st.markdown("---")
    
    if not st.session_state.logged_in:
        if st.button("Login" if st.session_state.page == 'signup' else "Sign Up", use_container_width=True):
            st.session_state.page = 'signup' if st.session_state.page == 'login' else 'login'
            st.rerun()

# ============ MAIN CONTENT ============
if st.session_state.logged_in:
    # ===== CHAT PAGE =====
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"## 💬 ChatVerse Forum")
    with col2:
        messages = load_messages()
        st.metric("Messages", len(messages))
    with col3:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.name = None
            st.rerun()
    
    st.markdown("---")
    
    # Display messages
    messages = load_messages()
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    
    if messages:
        for msg in messages[-100:]:
            is_mine = msg['username'] == st.session_state.username
            msg_class = "my-msg" if is_mine else ""
            
            st.markdown(f"""
            <div class="message {msg_class}">
                <span class="msg-user">{msg['username']}</span>
                <span class="msg-time">{msg['time']}</span>
                <div class="msg-text">{msg['text']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No messages yet. Start the conversation! 🌟")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Send message
    st.markdown("---")
    with st.form("send_msg", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            msg = st.text_input("Message", placeholder="Type your message...", label_visibility="collapsed")
        with col2:
            send = st.form_submit_button("📤 Send", use_container_width=True)
        
        if send and msg:
            save_message(st.session_state.username, msg)
            st.rerun()
    
    # Sidebar options
    with st.sidebar:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
        if st.button("🧹 Clear Chat", use_container_width=True):
            clear_messages()
            st.success("Chat cleared!")
            time.sleep(0.5)
            st.rerun()

else:
    if st.session_state.page == 'login':
        # ===== LOGIN PAGE =====
        st.markdown('<h1 style="text-align: center; color: #a78bfa;">🔐 ChatVerse Login</h1>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login", use_container_width=True)
                
                if submit:
                    if not username or not password:
                        st.error("Please enter username and password")
                    else:
                        success, name = login_user(username, password)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.name = name
                            st.success("Login successful!")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
    
    else:
        # ===== SIGNUP PAGE =====
        st.markdown('<h1 style="text-align: center; color: #a78bfa;">✨ Create Account</h1>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
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
                            st.session_state.page = 'login'
                            st.rerun()
                        else:
                            st.error(message)
        
        if st.button("← Back to Login", use_container_width=True):
            st.session_state.page = 'login'
            st.rerun()

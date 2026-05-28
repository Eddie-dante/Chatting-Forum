import streamlit as st
import json
import os
import time
from datetime import datetime
import hashlib
import secrets
import base64

# Page config
st.set_page_config(page_title="ChatVerse Forum", page_icon="💬", layout="wide")

# File paths
USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"

# ===== PASSWORD HASHING =====
def hash_password(password):
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${base64.b64encode(h).decode()}"

def check_password(password, hashed):
    try:
        salt, hv = hashed.split('$')
        return base64.b64encode(hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)).decode() == hv
    except:
        return False

# ===== FILE HELPERS =====
def load_json(filepath, default=None):
    if default is None:
        default = {}
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return default
    except:
        return default

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

# ===== USER MANAGEMENT =====
def load_users():
    return load_json(USERS_FILE, {})

def create_admin():
    users = load_users()
    if 'admin' not in users:
        users['admin'] = {
            'name': 'Admin User',
            'email': 'admin@chatverse.com',
            'password': hash_password('admin123')
        }
        save_json(USERS_FILE, users)

def register_user(username, name, email, password):
    users = load_users()
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if username.lower() in [k.lower() for k in users.keys()]:
        return False, "Username already exists"
    for v in users.values():
        if v.get('email', '').lower() == email.lower():
            return False, "Email already registered"
    
    users[username] = {
        'name': name,
        'email': email,
        'password': hash_password(password)
    }
    save_json(USERS_FILE, users)
    return True, "Registration successful! Please login."

def login_user(username, password):
    users = load_users()
    for key, data in users.items():
        if key.lower() == username.lower():
            if check_password(password, data['password']):
                return True, data['name']
    return False, None

# ===== MESSAGE MANAGEMENT =====
def load_messages():
    return load_json(MESSAGES_FILE, [])

def save_message(username, text):
    messages = load_messages()
    text = text.strip()[:500]
    if not text:
        return False
    messages.append({
        'username': username,
        'text': text,
        'time': datetime.now().strftime("%H:%M")
    })
    if len(messages) > 200:
        messages = messages[-200:]
    save_json(MESSAGES_FILE, messages)
    return True

def clear_all_messages():
    save_json(MESSAGES_FILE, [])

# ===== CUSTOM CSS =====
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    .chat-container {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(148, 163, 184, 0.2);
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
        animation: fadeIn 0.3s;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .own-message {
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
        word-wrap: break-word;
    }
    .stButton button {
        background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: bold !important;
    }
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 15px rgba(124, 58, 237, 0.4) !important;
    }
    .stTextInput input {
        background: rgba(51, 65, 85, 0.6) !important;
        border: 1px solid rgba(148, 163, 184, 0.3) !important;
        border-radius: 10px !important;
        color: white !important;
    }
    .auth-box {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 20px;
        padding: 30px;
    }
</style>
""", unsafe_allow_html=True)

# ===== INITIALIZE =====
create_admin()

# ===== SESSION STATE =====
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ''
if 'name' not in st.session_state:
    st.session_state.name = ''
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# ===== MAIN APP =====
if st.session_state.logged_in:
    # ===== CHAT PAGE =====
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"## 💬 ChatVerse Forum")
    with col2:
        messages = load_messages()
        st.metric("💬 Messages", len(messages))
    with col3:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ''
            st.session_state.name = ''
            st.rerun()
    
    st.markdown("---")
    
    # Messages display
    messages = load_messages()
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    if messages:
        for msg in messages[-100:]:
            is_own = msg['username'] == st.session_state.username
            st.markdown(f"""
            <div class="message {'own-message' if is_own else ''}">
                <span class="msg-user">{msg['username']}</span>
                <span class="msg-time">{msg['time']}</span>
                <div class="msg-text">{msg['text']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("🌌 No messages yet. Start the conversation!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Message input
    st.markdown("---")
    with st.form("send_message", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            text = st.text_input(
                "Message",
                placeholder="Type your message here...",
                label_visibility="collapsed"
            )
        with col2:
            send = st.form_submit_button("📤 Send", use_container_width=True)
        
        if send and text:
            save_message(st.session_state.username, text)
            st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Options")
        if st.button("🔄 Refresh Chat", use_container_width=True):
            st.rerun()
        if st.button("🧹 Clear All Messages", use_container_width=True):
            clear_all_messages()
            st.success("✅ Chat cleared!")
            time.sleep(0.5)
            st.rerun()
        st.markdown("---")
        st.markdown(f"👤 Logged in as: **{st.session_state.username}**")

else:
    # ===== AUTH PAGES =====
    if st.session_state.page == 'login':
        # ===== LOGIN PAGE =====
        st.markdown('<h1 style="text-align:center;color:#a78bfa;">🔐 ChatVerse Login</h1>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="auth-box">', unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("👤 Username", placeholder="Enter username")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter password")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    login_btn = st.form_submit_button("🚀 Login", use_container_width=True)
                with col_btn2:
                    signup_btn = st.form_submit_button("📝 Sign Up", use_container_width=True)
                
                if login_btn:
                    if not username or not password:
                        st.error("❌ Please fill in all fields")
                    else:
                        success, name = login_user(username, password)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.name = name
                            st.success("✅ Login successful!")
                            st.balloons()
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
                
                if signup_btn:
                    st.session_state.page = 'signup'
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            with st.expander("🔑 Default Login Credentials"):
                st.info("**Username:** admin\n\n**Password:** admin123")
    
    else:
        # ===== SIGNUP PAGE =====
        st.markdown('<h1 style="text-align:center;color:#a78bfa;">✨ Create Account</h1>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="auth-box">', unsafe_allow_html=True)
            
            with st.form("signup_form", clear_on_submit=True):
                name = st.text_input("👤 Full Name", placeholder="John Doe")
                email = st.text_input("📧 Email", placeholder="john@example.com")
                username = st.text_input("👤 Username", placeholder="Choose username")
                
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    password = st.text_input("🔒 Password", type="password", placeholder="Min 6 characters")
                with col_p2:
                    confirm_password = st.text_input("🔒 Confirm", type="password", placeholder="Repeat password")
                
                submit = st.form_submit_button("🚀 Create Account", use_container_width=True)
                
                if submit:
                    if not all([name, email, username, password, confirm_password]):
                        st.error("❌ All fields are required!")
                    elif password != confirm_password:
                        st.error("❌ Passwords don't match!")
                    else:
                        success, message = register_user(username, name, email, password)
                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                            time.sleep(1)
                            st.session_state.page = 'login'
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("← Back to Login", use_container_width=True):
                st.session_state.page = 'login'
                st.rerun()

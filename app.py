import streamlit as st
import json
import os
import time
from datetime import datetime
import hashlib
import secrets
import base64

st.set_page_config(page_title="ChatVerse Forum", page_icon="💬", layout="wide")

USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"

def hash_password(password):
    salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    hash_str = base64.b64encode(hash_obj).decode()
    return f"{salt}${hash_str}"

def check_password(password, hashed):
    try:
        salt, hash_value = hashed.split('$')
        check_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        check_str = base64.b64encode(check_hash).decode()
        return check_str == hash_value
    except:
        return False

def load_json(filename, default={}):
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return default
    except:
        return default

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def load_users():
    return load_json(USERS_FILE, {})

def save_users(users):
    save_json(USERS_FILE, users)

def create_admin():
    users = load_users()
    if not users:
        users = {
            'admin': {
                'email': 'admin@chatverse.com',
                'name': 'Admin User',
                'password': hash_password('admin123')
            }
        }
        save_users(users)

def register_user(username, name, email, password):
    users = load_users()
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if username.lower() in [u.lower() for u in users.keys()]:
        return False, "Username already exists"
    for u in users.values():
        if u.get('email','').lower() == email.lower():
            return False, "Email already registered"
    users[username] = {
        'email': email,
        'name': name,
        'password': hash_password(password)
    }
    save_users(users)
    return True, "Registration successful!"

def login_user(username, password):
    users = load_users()
    for key, data in users.items():
        if key.lower() == username.lower():
            if check_password(password, data['password']):
                return True, data['name']
    return False, None

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

def clear_messages():
    save_json(MESSAGES_FILE, [])

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
    .chat-box { background: rgba(30,41,59,0.8); border-radius: 15px; padding: 20px; height: 500px; overflow-y: auto; margin: 10px 0; }
    .message { background: rgba(51,65,85,0.6); border-radius: 12px; padding: 12px; margin: 8px 0; }
    .my-msg { background: rgba(124,58,237,0.3); border-left: 3px solid #7c3aed; }
    .msg-user { color: #a78bfa; font-weight: bold; }
    .msg-time { color: #64748b; font-size: 0.8em; margin-left: 10px; }
    .msg-text { color: #e2e8f0; margin-top: 5px; }
    .stButton button { background: linear-gradient(135deg, #7c3aed, #6d28d9) !important; color: white !important; border: none !important; border-radius: 10px !important; }
    .stTextInput input { background: rgba(51,65,85,0.6) !important; border-radius: 10px !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

create_admin()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'page' not in st.session_state:
    st.session_state.page = 'login'

if st.session_state.logged_in:
    col1, col2, col3 = st.columns([3,1,1])
    with col1:
        st.markdown(f"## 💬 ChatVerse Forum")
    with col2:
        st.metric("Messages", len(load_messages()))
    with col3:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    
    st.markdown("---")
    messages = load_messages()
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    if messages:
        for msg in messages[-100:]:
            is_mine = msg['username'] == st.session_state.username
            st.markdown(f"""
            <div class="message {'my-msg' if is_mine else ''}">
                <span class="msg-user">{msg['username']}</span>
                <span class="msg-time">{msg['time']}</span>
                <div class="msg-text">{msg['text']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No messages yet. Start the conversation! 🌟")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    with st.form("send_msg", clear_on_submit=True):
        col1, col2 = st.columns([5,1])
        with col1:
            msg = st.text_input("Message", placeholder="Type your message...", label_visibility="collapsed")
        with col2:
            send = st.form_submit_button("📤 Send", use_container_width=True)
        if send and msg:
            save_message(st.session_state.username, msg)
            st.rerun()

else:
    if st.session_state.page == 'login':
        st.markdown('<h1 style="text-align:center;color:#a78bfa;">🔐 ChatVerse Login</h1>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            with st.form("login"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                c1, c2 = st.columns(2)
                with c1:
                    login_btn = st.form_submit_button("🚀 Login", use_container_width=True)
                with c2:
                    signup_btn = st.form_submit_button("📝 Sign Up", use_container_width=True)
                if login_btn:
                    success, name = login_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.name = name
                        st.success("Login successful!")
                        st.balloons()
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                if signup_btn:
                    st.session_state.page = 'signup'
                    st.rerun()
            with st.expander("🔑 Default Credentials"):
                st.info("Username: **admin**\nPassword: **admin123**")
    else:
        st.markdown('<h1 style="text-align:center;color:#a78bfa;">✨ Create Account</h1>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            with st.form("signup"):
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                confirm = st.text_input("Confirm Password", type="password")
                submit = st.form_submit_button("Create Account", use_container_width=True)
                if submit:
                    if password != confirm:
                        st.error("Passwords don't match!")
                    else:
                        success, msg = register_user(username, name, email, password)
                        if success:
                            st.success(msg)
                            st.balloons()
                            time.sleep(1)
                            st.session_state.page = 'login'
                            st.rerun()
                        else:
                            st.error(msg)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button("← Back to Login", use_container_width=True):
                st.session_state.page = 'login'
                st.rerun()

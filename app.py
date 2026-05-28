import streamlit as st
import json
import os
import time
from datetime import datetime
import hashlib
import secrets
import base64

st.set_page_config(page_title="ChatVerse", page_icon="💬", layout="wide")

USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"

# Password functions
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

# File functions
def load_json(f, d={}):
    try:
        if os.path.exists(f):
            with open(f) as fh:
                return json.load(fh)
        return d
    except:
        return d

def save_json(f, d):
    with open(f, 'w') as fh:
        json.dump(d, fh)

# User functions
def load_users():
    return load_json(USERS_FILE, {})

def init_admin():
    u = load_users()
    if 'admin' not in u:
        u['admin'] = {'name': 'Admin', 'email': 'admin@chatverse.com', 'password': hash_password('admin123')}
        save_json(USERS_FILE, u)

def register(username, name, email, password):
    u = load_users()
    if len(username) < 3:
        return False, "Username too short"
    if len(password) < 6:
        return False, "Password too short"
    if username.lower() in [k.lower() for k in u]:
        return False, "Username exists"
    for v in u.values():
        if v.get('email', '').lower() == email.lower():
            return False, "Email exists"
    u[username] = {'name': name, 'email': email, 'password': hash_password(password)}
    save_json(USERS_FILE, u)
    return True, "Account created!"

def login(username, password):
    u = load_users()
    for k, v in u.items():
        if k.lower() == username.lower() and check_password(password, v['password']):
            return True, v['name']
    return False, None

# Message functions
def load_msgs():
    return load_json(MESSAGES_FILE, [])

def save_msg(username, text):
    msgs = load_msgs()
    text = text.strip()[:500]
    if not text:
        return False
    msgs.append({'user': username, 'text': text, 'time': datetime.now().strftime("%H:%M")})
    save_json(MESSAGES_FILE, msgs[-200:])
    return True

# CSS
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0f172a, #1e293b); }
.chat-box { background: rgba(30,41,59,0.8); border-radius: 15px; padding: 20px; height: 500px; overflow-y: auto; margin: 10px 0; border: 1px solid rgba(148,163,184,0.2); }
.msg { background: rgba(51,65,85,0.6); border-radius: 12px; padding: 12px; margin: 8px 0; }
.my { background: rgba(124,58,237,0.3); border-left: 3px solid #7c3aed; }
.uname { color: #a78bfa; font-weight: bold; }
.time { color: #64748b; font-size: 0.8em; margin-left: 10px; }
.txt { color: #e2e8f0; margin-top: 5px; }
.stButton button { background: linear-gradient(135deg, #7c3aed, #6d28d9) !important; color: white !important; border: none !important; border-radius: 10px !important; }
.stTextInput input { background: rgba(51,65,85,0.6) !important; color: white !important; border-radius: 10px !important; border: 1px solid rgba(148,163,184,0.3) !important; }
</style>
""", unsafe_allow_html=True)

# Init
init_admin()

# Session
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# Main app
if st.session_state.logged_in:
    c1, c2, c3 = st.columns([3, 1, 1])
    c1.markdown("## 💬 ChatVerse")
    c2.metric("Messages", len(load_msgs()))
    if c3.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
    
    st.markdown("---")
    msgs = load_msgs()
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    for m in msgs[-100:]:
        is_my = m['user'] == st.session_state.username
        st.markdown(f'<div class="msg {"my" if is_my else ""}"><span class="uname">{m["user"]}</span><span class="time">{m["time"]}</span><div class="txt">{m["text"]}</div></div>', unsafe_allow_html=True)
    if not msgs:
        st.info("No messages yet. Start chatting! 🌟")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    with st.form("send", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        txt = c1.text_input("Message", placeholder="Type here...", label_visibility="collapsed")
        if c2.form_submit_button("📤 Send", use_container_width=True) and txt:
            save_msg(st.session_state.username, txt)
            st.rerun()

elif st.session_state.page == 'login':
    st.markdown('<h1 style="text-align:center;color:#a78bfa;">🔐 Login</h1>', unsafe_allow_html=True)
    _, c, _ = st.columns([1, 2, 1])
    with c:
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            b1, b2 = st.columns(2)
            if b1.form_submit_button("🚀 Login", use_container_width=True):
                ok, name = login(u, p)
                if ok:
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.session_state.name = name
                    st.success("Logged in!")
                    st.balloons()
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            if b2.form_submit_button("📝 Sign Up", use_container_width=True):
                st.session_state.page = 'signup'
                st.rerun()
        with st.expander("🔑 Default Login"):
            st.info("**admin** / **admin123**")

else:
    st.markdown('<h1 style="text-align:center;color:#a78bfa;">✨ Sign Up</h1>', unsafe_allow_html=True)
    _, c, _ = st.columns([1, 2, 1])
    with c:
        with st.form("signup_form"):
            n = st.text_input("Name")
            e = st.text_input("Email")
            u = st.text_input("Username")
            p1 = st.text_input("Password", type="password")
            p2 = st.text_input("Confirm", type="password")
            if st.form_submit_button("Create Account", use_container_width=True):
                if p1 != p2:
                    st.error("Passwords don't match")
                else:
                    ok, msg = register(u, n, e, p1)
                    if ok:
                        st.success(msg)
                        st.balloons()
                        time.sleep(1)
                        st.session_state.page = 'login'
                        st.rerun()
                    else:
                        st.error(msg)
    _, c, _ = st.columns([1, 2, 1])
    if c.button("← Back to Login", use_container_width=True):
        st.session_state.page = 'login'
        st.rerun()
        

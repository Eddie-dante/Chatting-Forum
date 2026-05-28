import streamlit as st
import sqlite3
from datetime import datetime
from pathlib import Path
import bcrypt
import html
import uuid

# ============ CONFIGURATION ============
st.set_page_config(page_title="ChatVerse Forum", page_icon="💬", layout="wide")

# Database setup
DATA_DIR = Path("chatverse_data")
DATA_DIR.mkdir(exist_ok=True)

def init_db():
    conn = sqlite3.connect(str(DATA_DIR / "chatverse.db"))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            password TEXT,
            created_at TEXT
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            username TEXT,
            text TEXT,
            timestamp TEXT
        )
    ''')
    
    # Create admin if not exists
    admin = cursor.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()
    if not admin:
        hashed = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO users (username, name, email, password, created_at) VALUES (?, ?, ?, ?, ?)",
            ('admin', 'Admin', 'admin@chatverse.com', hashed, datetime.now().isoformat())
        )
    
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(str(DATA_DIR / "chatverse.db"))
    conn.row_factory = sqlite3.Row
    return conn

# ============ HELPER FUNCTIONS ============
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except:
        return False

def sanitize(text):
    return html.escape(str(text)) if text else ""

# ============ SESSION STATE ============
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'name' not in st.session_state:
    st.session_state.name = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# ============ CSS ============
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
    .chat-box { 
        background: rgba(30,41,59,0.8); 
        border: 1px solid rgba(148,163,184,0.2); 
        border-radius: 15px; 
        padding: 20px; 
        height: 450px; 
        overflow-y: auto; 
    }
    .msg { 
        background: rgba(51,65,85,0.6); 
        border-radius: 12px; 
        padding: 12px; 
        margin: 8px 0; 
    }
    .my { 
        background: rgba(124,58,237,0.3); 
        border-left: 3px solid #7c3aed; 
    }
    .uname { color: #a78bfa; font-weight: bold; }
    .time { color: #64748b; font-size: 0.8em; margin-left: 10px; }
    .txt { color: #e2e8f0; margin-top: 5px; }
    .stButton button { 
        background: linear-gradient(135deg, #7c3aed, #6d28d9) !important; 
        color: white !important; 
        border: none !important; 
        border-radius: 10px !important; 
        font-weight: bold !important; 
    }
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 15px rgba(124,58,237,0.4) !important;
    }
    .stTextInput input { 
        background: rgba(51,65,85,0.6) !important; 
        color: white !important; 
        border-radius: 10px !important; 
        border: 1px solid rgba(148,163,184,0.3) !important; 
    }
    .auth-card {
        background: rgba(30,41,59,0.9);
        border: 1px solid rgba(148,163,184,0.2);
        border-radius: 20px;
        padding: 30px;
    }
</style>
""", unsafe_allow_html=True)

# ============ PAGES ============
def login_page():
    st.markdown('<h1 style="text-align:center;color:#a78bfa;">🔐 ChatVerse Login</h1>', unsafe_allow_html=True)
    
    _, c, _ = st.columns([1, 2, 1])
    with c:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        with st.form("login"):
            username = st.text_input("👤 Username")
            password = st.text_input("🔒 Password", type="password")
            
            b1, b2 = st.columns(2)
            with b1:
                login_btn = st.form_submit_button("🚀 Login", use_container_width=True)
            with b2:
                signup_btn = st.form_submit_button("📝 Sign Up", use_container_width=True)
            
            if login_btn:
                if username and password:
                    conn = get_db()
                    user = conn.execute("SELECT * FROM users WHERE LOWER(username) = ?", 
                                      (username.lower(),)).fetchone()
                    conn.close()
                    
                    if user and verify_password(password, user['password']):
                        st.session_state.logged_in = True
                        st.session_state.username = user['username']
                        st.session_state.name = user['name']
                        st.success("✅ Login successful!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
            
            if signup_btn:
                st.session_state.page = 'signup'
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.expander("🔑 Default Login"):
            st.info("Username: **admin**\nPassword: **admin123**")

def signup_page():
    st.markdown('<h1 style="text-align:center;color:#a78bfa;">✨ Create Account</h1>', unsafe_allow_html=True)
    
    _, c, _ = st.columns([1, 2, 1])
    with c:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        with st.form("signup"):
            name = st.text_input("👤 Full Name")
            email = st.text_input("📧 Email")
            username = st.text_input("👤 Username")
            p1 = st.text_input("🔒 Password", type="password")
            p2 = st.text_input("🔒 Confirm Password", type="password")
            
            if st.form_submit_button("🚀 Create Account", use_container_width=True):
                if not all([name, email, username, p1, p2]):
                    st.error("All fields required!")
                elif len(username) < 3:
                    st.error("Username must be at least 3 characters!")
                elif len(p1) < 6:
                    st.error("Password must be at least 6 characters!")
                elif p1 != p2:
                    st.error("Passwords don't match!")
                else:
                    conn = get_db()
                    existing = conn.execute("SELECT * FROM users WHERE LOWER(username) = ?",
                                          (username.lower(),)).fetchone()
                    if existing:
                        st.error("Username already exists!")
                        conn.close()
                    else:
                        conn.execute(
                            "INSERT INTO users (username, name, email, password, created_at) VALUES (?, ?, ?, ?, ?)",
                            (username, name, email, hash_password(p1), datetime.now().isoformat())
                        )
                        conn.commit()
                        conn.close()
                        st.success("✅ Account created! Please login.")
                        st.balloons()
                        st.session_state.page = 'login'
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("← Back to Login"):
        st.session_state.page = 'login'
        st.rerun()

def chat_page():
    # Header
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        st.markdown(f"## 💬 ChatVerse Forum")
    with c2:
        conn = get_db()
        count = conn.execute("SELECT COUNT(*) as c FROM messages").fetchone()['c']
        conn.close()
        st.metric("Messages", count)
    with c3:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()
    
    st.markdown("---")
    
    # Messages
    conn = get_db()
    msgs = conn.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT 100").fetchall()
    conn.close()
    
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    for m in reversed(msgs):
        is_mine = m['username'] == st.session_state.username
        st.markdown(f"""
        <div class="msg {'my' if is_mine else ''}">
            <span class="uname">{sanitize(m['username'])}</span>
            <span class="time">{m['timestamp'][:16]}</span>
            <div class="txt">{sanitize(m['text'])}</div>
        </div>
        """, unsafe_allow_html=True)
    if not msgs:
        st.info("No messages yet. Start the conversation! 🌟")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input
    st.markdown("---")
    with st.form("send", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        txt = c1.text_input("Message", placeholder="Type your message...", label_visibility="collapsed")
        if c2.form_submit_button("📤 Send", use_container_width=True) and txt and txt.strip():
            conn = get_db()
            conn.execute(
                "INSERT INTO messages (id, username, text, timestamp) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), st.session_state.username, txt.strip()[:500], 
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
            conn.close()
            st.rerun()

# ============ MAIN ============
if st.session_state.logged_in:
    chat_page()
else:
    if st.session_state.page == 'signup':
        signup_page()
    else:
        login_page()

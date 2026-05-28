import streamlit as st
import json
import os
import time
from datetime import datetime
import hashlib
import secrets
import base64

# ============ CONFIGURATION ============
st.set_page_config(
    page_title="ChatVerse Forum",
    page_icon="💬",
    layout="wide"
)

# File paths
USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"

# ============ PASSWORD HASHING (Built-in only) ============
def hash_password(password):
    """Hash password using only built-in libraries"""
    salt = secrets.token_hex(16)
    # Use PBKDF2-like approach with hashlib
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    hash_str = base64.b64encode(hash_obj).decode()
    return f"{salt}${hash_str}"

def check_password(password, hashed):
    """Verify password"""
    try:
        salt, hash_value = hashed.split('$')
        check_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        check_str = base64.b64encode(check_hash).decode()
        return check_str == hash_value
    except:
        return False

# ============ FILE MANAGEMENT ============
def load_json(filename, default={}):
    """Safely load JSON file"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return default
    except:
        return default

def save_json(filename, data):
    """Safely save JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        st.error(f"Error saving data: {e}")

# ============ USER MANAGEMENT ============
def load_users():
    return load_json(USERS_FILE, {})

def save_users(users):
    save_json(USERS_FILE, users)

def create_default_admin():
    """Create admin user if no users exist"""
    users = load_users()
    if not users:
        users = {
            'admin': {
                'email': 'admin@chatverse.com',
                'name': 'Admin User',
                'password': hash_password('admin123'),
                'created_at': datetime.now().isoformat()
            }
        }
        save_users(users)

def register_user(username, name, email, password):
    """Register new user"""
    users = load_users()
    
    # Validation
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters"
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters"
    if not name:
        return False, "Name is required"
    if not email:
        return False, "Email is required"
    
    # Check existing
    if username.lower() in [u.lower() for u in users.keys()]:
        return False, "Username already exists"
    
    for user_data in users.values():
        if user_data.get('email', '').lower() == email.lower():
            return False, "Email already registered"
    
    # Add user
    users[username] = {
        'email': email,
        'name': name,
        'password': hash_password(password),
        'created_at': datetime.now().isoformat()
    }
    
    save_users(users)
    return True, "Registration successful! Please login."

def authenticate_user(username, password):
    """Authenticate user login"""
    users = load_users()
    
    if not username or not password:
        return False, None, "Please enter username and password"
    
    # Case-insensitive username lookup
    user_key = None
    for key in users.keys():
        if key.lower() == username.lower():
            user_key = key
            break
    
    if not user_key:
        return False, None, "Invalid username or password"
    
    user_data = users[user_key]
    if check_password(password, user_data['password']):
        return True, user_data['name'], None
    
    return False, None, "Invalid username or password"

# ============ MESSAGE MANAGEMENT ============
def load_messages():
    return load_json(MESSAGES_FILE, [])

def save_message(username, text):
    """Save a new message"""
    messages = load_messages()
    
    # Sanitize input
    text = text.strip()[:500]
    if not text:
        return False
    
    message = {
        'id': len(messages) + 1,
        'username': username,
        'text': text,
        'time': datetime.now().strftime("%H:%M"),
        'date': datetime.now().strftime("%Y-%m-%d"),
        'timestamp': datetime.now().isoformat()
    }
    
    messages.append(message)
    
    # Keep only last 200 messages
    if len(messages) > 200:
        messages = messages[-200:]
    
    save_json(MESSAGES_FILE, messages)
    return True

def clear_all_messages():
    """Clear chat history"""
    save_json(MESSAGES_FILE, [])
    return True

# ============ UI STYLING ============
def load_css():
    st.markdown("""
    <style>
        /* Main background */
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        }
        
        /* Header styling */
        .main-header {
            color: #a78bfa;
            text-align: center;
            font-size: 2.5em;
            font-weight: bold;
            margin: 20px 0;
            text-shadow: 0 0 20px rgba(124, 58, 237, 0.3);
        }
        
        /* Chat container */
        .chat-container {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 15px;
            padding: 20px;
            height: 500px;
            overflow-y: auto;
            margin: 10px 0;
        }
        
        /* Message bubbles */
        .message {
            background: rgba(51, 65, 85, 0.6);
            border-radius: 12px;
            padding: 12px 16px;
            margin: 8px 0;
            animation: fadeIn 0.3s ease-in;
        }
        
        .own-message {
            background: rgba(124, 58, 237, 0.3);
            border-left: 3px solid #7c3aed;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .msg-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }
        
        .msg-username {
            color: #a78bfa;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .msg-time {
            color: #64748b;
            font-size: 0.8em;
        }
        
        .msg-text {
            color: #e2e8f0;
            line-height: 1.5;
            word-wrap: break-word;
        }
        
        /* Input fields */
        div[data-testid="stTextInput"] input {
            background: rgba(51, 65, 85, 0.6) !important;
            border: 1px solid rgba(148, 163, 184, 0.3) !important;
            border-radius: 10px !important;
            color: white !important;
            padding: 12px 16px !important;
        }
        
        div[data-testid="stTextInput"] input:focus {
            border-color: #7c3aed !important;
            box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2) !important;
        }
        
        /* Buttons */
        div[data-testid="stButton"] button {
            background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 10px 25px !important;
            font-weight: bold !important;
            transition: all 0.3s ease !important;
        }
        
        div[data-testid="stButton"] button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 5px 15px rgba(124, 58, 237, 0.4) !important;
        }
        
        /* Cards */
        .auth-card {
            background: rgba(30, 41, 59, 0.9);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(10px);
        }
        
        /* Metrics */
        div[data-testid="stMetric"] {
            background: rgba(124, 58, 237, 0.1);
            border: 1px solid rgba(124, 58, 237, 0.2);
            border-radius: 10px;
            padding: 10px;
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.9);
        }
        
        /* Scrollbar */
        .chat-container::-webkit-scrollbar {
            width: 8px;
        }
        
        .chat-container::-webkit-scrollbar-track {
            background: rgba(51, 65, 85, 0.3);
            border-radius: 4px;
        }
        
        .chat-container::-webkit-scrollbar-thumb {
            background: rgba(124, 58, 237, 0.5);
            border-radius: 4px;
        }
        
        /* Info/Warning/Error boxes */
        div[data-testid="stAlert"] {
            border-radius: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

# ============ SESSION STATE INITIALIZATION ============
def init_session():
    """Initialize session state variables"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'name' not in st.session_state:
        st.session_state.name = None
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    if 'error' not in st.session_state:
        st.session_state.error = None

# ============ LOGIN PAGE ============
def login_page():
    st.markdown('<h1 class="main-header">🔐 ChatVerse Login</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                submit = st.form_submit_button("🚀 Login", use_container_width=True)
            with col_btn2:
                signup_btn = st.form_submit_button("📝 Sign Up", use_container_width=True)
            
            if submit:
                success, name, error = authenticate_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.name = name
                    st.success("✅ Login successful!")
                    st.balloons()
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"❌ {error}")
            
            if signup_btn:
                st.session_state.page = 'signup'
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Demo credentials
        with st.expander("🔑 Default Credentials"):
            st.info("Username: **admin**\nPassword: **admin123**")

# ============ SIGNUP PAGE ============
def signup_page():
    st.markdown('<h1 class="main-header">✨ Create Account</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        with st.form("signup_form", clear_on_submit=True):
            name = st.text_input("👤 Full Name", placeholder="John Doe")
            email = st.text_input("📧 Email", placeholder="john@example.com")
            username = st.text_input("👤 Username", placeholder="Choose a username")
            
            col_pass1, col_pass2 = st.columns(2)
            with col_pass1:
                password = st.text_input("🔒 Password", type="password", placeholder="Min 6 characters")
            with col_pass2:
                confirm_password = st.text_input("🔒 Confirm", type="password", placeholder="Repeat password")
            
            submit = st.form_submit_button("🚀 Create Account", use_container_width=True)
            
            if submit:
                if password != confirm_password:
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

# ============ CHAT PAGE ============
def chat_page():
    # Header
    st.markdown('<h1 class="main-header">💬 ChatVerse Forum</h1>', unsafe_allow_html=True)
    
    # Top bar
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.markdown(f"### 👋 Welcome, **{st.session_state.name}**!")
    with col2:
        messages = load_messages()
        st.metric("💬 Messages", len(messages))
    with col3:
        users = load_users()
        st.metric("👥 Users", len(users))
    with col4:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.name = None
            st.rerun()
    
    st.markdown("---")
    
    # Chat messages display
    messages = load_messages()
    
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    if messages:
        for msg in reversed(messages[-100:]):  # Last 100 messages, newest first
            is_own = msg['username'].lower() == st.session_state.username.lower()
            msg_class = "own-message" if is_own else ""
            
            st.markdown(f"""
            <div class="message {msg_class}">
                <div class="msg-header">
                    <span class="msg-username">{msg['username']}</span>
                    <span class="msg-time">{msg['time']}</span>
                </div>
                <div class="msg-text">{msg['text']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("🌌 No messages yet. Start the conversation! Be the first to say hello! 👋")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Message input
    st.markdown("---")
    
    with st.form("message_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            msg_text = st.text_input(
                "Message",
                placeholder="Type your message here...",
                label_visibility="collapsed",
                key="msg_input"
            )
        with col2:
            send_btn = st.form_submit_button("📤 Send", use_container_width=True)
        
        if send_btn and msg_text:
            if save_message(st.session_state.username, msg_text):
                st.rerun()
            else:
                st.warning("⚠️ Message cannot be empty!")
    
    # Sidebar options
    with st.sidebar:
        st.markdown("## ⚙️ Options")
        st.markdown("---")
        
        if st.button("🔄 Refresh Chat", use_container_width=True):
            st.rerun()
        
        if st.button("🧹 Clear All Messages", use_container_width=True):
            if clear_all_messages():
                st.success("✅ Chat cleared successfully!")
                time.sleep(0.5)
                st.rerun()
        
        st.markdown("---")
        st.markdown(f"👤 Logged in as: **{st.session_state.username}**")

# ============ MAIN APP ============
def main():
    """Main application entry point"""
    # Initialize
    create_default_admin()
    init_session()
    load_css()
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## 🌟 ChatVerse")
        st.markdown("Secure Community Forum")
        st.markdown("---")
    
    # Route to correct page
    if st.session_state.logged_in:
        chat_page()
    else:
        if st.session_state.page == 'signup':
            signup_page()
        else:
            login_page()

if __name__ == "__main__":
    main()

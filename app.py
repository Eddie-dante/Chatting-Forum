import streamlit as st
import json
import os
import html
import hashlib
import pathlib
import base64
from datetime import datetime
from io import BytesIO
from PIL import Image
import uuid
import threading
import time

# Page config MUST be the first Streamlit command
st.set_page_config(
    page_title="ChatVerse • Community Forum",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize paths and directories
DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)
MESSAGES_FILE = DATA_DIR / "chat_messages.json"
USERS_FILE = DATA_DIR / "users.json"
PROFILES_FILE = DATA_DIR / "profiles.json"
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# Thread lock for file operations
file_lock = threading.Lock()

# Custom CSS with wallpaper support
def get_custom_css(wallpaper_url=None):
    wallpaper_css = ""
    if wallpaper_url:
        wallpaper_css = f"""
        .stApp {{
            background-image: url("{wallpaper_url}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(15, 23, 42, 0.85);
            z-index: -1;
        }}
        """
    
    return f"""
    <style>
        /* Main container */
        .main {{
            background: transparent;
        }}
        
        {wallpaper_css}
        
        /* Chat message styling */
        .chat-message {{
            padding: 1rem;
            border-radius: 1rem;
            margin-bottom: 1rem;
            display: flex;
            animation: fadeIn 0.3s ease-in;
            backdrop-filter: blur(10px);
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .chat-message.user {{
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.3), rgba(96, 165, 250, 0.2));
            border: 1px solid rgba(59, 130, 246, 0.4);
            margin-left: 20%;
        }}
        
        .chat-message.other {{
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            margin-right: 20%;
        }}
        
        .chat-avatar {{
            width: 45px;
            height: 45px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.2rem;
            margin-right: 1rem;
            flex-shrink: 0;
            background-size: cover;
            background-position: center;
        }}
        
        .user-avatar {{
            background: linear-gradient(135deg, #3b82f6, #60a5fa);
        }}
        
        .other-avatar {{
            background: linear-gradient(135deg, #7c3aed, #a78bfa);
        }}
        
        .chat-content {{
            flex: 1;
        }}
        
        .chat-author {{
            font-weight: 600;
            font-size: 0.9rem;
            color: #cbd5e1;
            margin-bottom: 0.3rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .chat-time {{
            font-size: 0.7rem;
            color: #64748b;
        }}
        
        .chat-text {{
            color: #f1f5f9;
            line-height: 1.5;
        }}
        
        .chat-reactions {{
            margin-top: 0.5rem;
            display: flex;
            gap: 0.5rem;
        }}
        
        .reaction-btn {{
            background: rgba(255, 255, 255, 0.1);
            border: none;
            color: #cbd5e1;
            padding: 0.2rem 0.5rem;
            border-radius: 1rem;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.2s;
        }}
        
        .reaction-btn:hover {{
            background: rgba(255, 255, 255, 0.2);
            transform: scale(1.05);
        }}
        
        /* Header */
        .header-container {{
            text-align: center;
            padding: 1rem;
            margin-bottom: 2rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .online-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(255, 255, 255, 0.08);
            padding: 0.3rem 1rem;
            border-radius: 2rem;
            font-size: 0.8rem;
        }}
        
        .online-dot {{
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        /* Auth forms */
        .auth-container {{
            max-width: 400px;
            margin: 2rem auto;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 1rem;
            backdrop-filter: blur(10px);
        }}
        
        /* Profile card */
        .profile-card {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 1rem;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
            margin-bottom: 1rem;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .chat-message.user {{
                margin-left: 5%;
            }}
            .chat-message.other {{
                margin-right: 5%;
            }}
        }}
        
        /* Wallpaper gallery */
        .wallpaper-option {{
            border-radius: 0.5rem;
            cursor: pointer;
            transition: all 0.3s;
            border: 3px solid transparent;
        }}
        
        .wallpaper-option:hover {{
            transform: scale(1.05);
            border-color: #3b82f6;
        }}
        
        .wallpaper-option.selected {{
            border-color: #10b981;
        }}
    </style>
    """

# Default wallpapers
DEFAULT_WALLPAPERS = {
    "Cosmic Night": "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=1920",
    "Aurora Borealis": "https://images.unsplash.com/photo-1483347756197-71ef80e95f73?w=1920",
    "Starry Sky": "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=1920",
    "Ocean Waves": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1920",
    "Mountain Mist": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920",
    "Abstract Gradient": None  # Will use CSS gradient
}

# Helper functions
def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def sanitize_text(text):
    """Sanitize text to prevent XSS."""
    return html.escape(text)

def format_time(timestamp_str):
    """Format timestamp to human-readable time."""
    try:
        msg_time = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        diff = now - msg_time
        
        if diff.days == 0:
            if diff.seconds < 60:
                return "Just now"
            elif diff.seconds < 3600:
                return f"{diff.seconds // 60}m ago"
            else:
                return f"{diff.seconds // 3600}h ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days}d ago"
        else:
            return msg_time.strftime("%b %d, %Y")
    except:
        return "Unknown"

def load_json_file(file_path, default=None):
    """Safely load a JSON file."""
    try:
        if file_path.exists():
            with file_lock:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
    except json.JSONDecodeError as e:
        st.error(f"Corrupted file {file_path.name}: {e}")
    except PermissionError:
        st.error(f"Cannot access {file_path.name}")
    except Exception as e:
        st.error(f"Error loading {file_path.name}: {e}")
    
    return default if default is not None else []

def save_json_file(file_path, data):
    """Safely save data to a JSON file."""
    try:
        with file_lock:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Failed to save {file_path.name}: {e}")
        return False

# User management
def load_users():
    return load_json_file(USERS_FILE, {})

def save_users(users):
    return save_json_file(USERS_FILE, users)

def load_profiles():
    return load_json_file(PROFILES_FILE, {})

def save_profiles(profiles):
    return save_json_file(PROFILES_FILE, profiles)

def load_messages():
    messages = load_json_file(MESSAGES_FILE, [])
    return messages

def save_messages():
    return save_json_file(MESSAGES_FILE, st.session_state.messages)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = load_messages()
if 'username' not in st.session_state:
    st.session_state.username = "Guest_" + str(uuid.uuid4())[:6]
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'show_signin' not in st.session_state:
    st.session_state.show_signin = False
if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False
if 'show_profile' not in st.session_state:
    st.session_state.show_profile = False
if 'wallpaper' not in st.session_state:
    st.session_state.wallpaper = "Cosmic Night"
if 'show_wallpaper_gallery' not in st.session_state:
    st.session_state.show_wallpaper_gallery = False
if 'active_users' not in st.session_state:
    st.session_state.active_users = set()
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

# Load wallpaper from user profile if authenticated
if st.session_state.authenticated:
    profiles = load_profiles()
    user_profile = profiles.get(st.session_state.username, {})
    if 'wallpaper' in user_profile:
        st.session_state.wallpaper = user_profile['wallpaper']

# Apply custom CSS with wallpaper
wallpaper_url = DEFAULT_WALLPAPERS.get(st.session_state.wallpaper)
st.markdown(get_custom_css(wallpaper_url), unsafe_allow_html=True)

# Auth functions
def sign_up(email, username, password):
    users = load_users()
    profiles = load_profiles()
    
    if username in users:
        return False, "Username already exists"
    
    if any(u.get('email') == email for u in users.values()):
        return False, "Email already registered"
    
    users[username] = {
        "email": email,
        "password": hash_password(password),
        "created_at": datetime.now().isoformat()
    }
    
    profiles[username] = {
        "bio": "",
        "avatar_url": None,
        "wallpaper": "Cosmic Night",
        "joined_date": datetime.now().isoformat()
    }
    
    if save_users(users) and save_profiles(profiles):
        return True, "Account created successfully!"
    return False, "Failed to create account"

def sign_in(username, password):
    users = load_users()
    
    if username not in users:
        return False, "Username not found"
    
    if users[username]["password"] != hash_password(password):
        return False, "Incorrect password"
    
    return True, "Signed in successfully!"

def sign_out():
    st.session_state.authenticated = False
    st.session_state.username = "Guest_" + str(uuid.uuid4())[:6]
    st.session_state.user_email = ""
    st.session_state.show_profile = False
    st.session_state.wallpaper = "Cosmic Night"

def update_profile(username, bio, avatar_file, wallpaper):
    profiles = load_profiles()
    
    if username not in profiles:
        profiles[username] = {}
    
    profiles[username]['bio'] = sanitize_text(bio)
    profiles[username]['wallpaper'] = wallpaper
    
    if avatar_file is not None:
        try:
            # Save avatar image
            image = Image.open(avatar_file)
            image = image.resize((150, 150), Image.Resampling.LANCZOS)
            avatar_path = UPLOADS_DIR / f"{username}_avatar.png"
            image.save(avatar_path)
            profiles[username]['avatar_url'] = str(avatar_path)
        except Exception as e:
            st.error(f"Failed to process avatar: {e}")
    
    return save_profiles(profiles)

# Sidebar
with st.sidebar:
    st.markdown("## 🎨 ChatVerse")
    
    # Auth section
    if not st.session_state.authenticated:
        st.markdown("### 👋 Welcome, Guest!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔑 Sign In", use_container_width=True):
                st.session_state.show_signin = True
                st.session_state.show_signup = False
                st.rerun()
        with col2:
            if st.button("✨ Sign Up", use_container_width=True):
                st.session_state.show_signup = True
                st.session_state.show_signin = False
                st.rerun()
    else:
        profiles = load_profiles()
        user_profile = profiles.get(st.session_state.username, {})
        avatar_url = user_profile.get('avatar_url')
        
        if avatar_url and os.path.exists(avatar_url):
            st.image(avatar_url, width=80)
        else:
            st.markdown(f"### 🧑‍💻 {st.session_state.username}")
        
        st.markdown(f"**{st.session_state.username}**")
        if st.session_state.user_email:
            st.caption(f"📧 {st.session_state.user_email}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👤 Profile", use_container_width=True):
                st.session_state.show_profile = True
                st.rerun()
        with col2:
            if st.button("🚪 Sign Out", use_container_width=True):
                sign_out()
                st.rerun()
    
    st.markdown("---")
    
    # Search
    search_query = st.text_input("🔍 Search messages", placeholder="Search...", key="search_input")
    if search_query:
        st.session_state.search_query = search_query
    else:
        st.session_state.search_query = ""
    
    st.markdown("---")
    
    # Wallpaper selector
    st.markdown("### 🎨 Wallpaper")
    if st.button("Change Wallpaper", use_container_width=True):
        st.session_state.show_wallpaper_gallery = not st.session_state.show_wallpaper_gallery
        st.rerun()
    
    if st.session_state.show_wallpaper_gallery:
        st.markdown("**Choose your wallpaper:**")
        cols = st.columns(3)
        for i, (name, url) in enumerate(DEFAULT_WALLPAPERS.items()):
            col_idx = i % 3
            with cols[col_idx]:
                is_selected = st.session_state.wallpaper == name
                button_style = "🟢" if is_selected else "⬜"
                if st.button(f"{button_style} {name}", key=f"wall_{name}", use_container_width=True):
                    st.session_state.wallpaper = name
                    if st.session_state.authenticated:
                        profiles = load_profiles()
                        if st.session_state.username in profiles:
                            profiles[st.session_state.username]['wallpaper'] = name
                            save_profiles(profiles)
                    st.rerun()
    
    st.markdown("---")
    
    # Clear chat button
    if st.button("🗑️ Clear All Messages", use_container_width=True):
        if st.session_state.authenticated:
            st.session_state.messages = []
            save_messages()
            st.success("Chat cleared!")
            st.rerun()
        else:
            st.warning("Please sign in to clear messages")
    
    st.markdown("---")
    
    # Stats
    st.markdown("### 📊 Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Messages", len(st.session_state.messages))
    with col2:
        unique_users = len(set(msg['username'] for msg in st.session_state.messages[-100:]))
        st.metric("Active Users", unique_users)
    
    st.markdown("---")
    st.markdown("""
    ### ℹ️ About
    **ChatVerse** is a community forum where everyone can share ideas and connect.
    
    ✨ **Features:**
    - User accounts
    - Profile customization
    - Beautiful wallpapers
    - Message reactions
    - Persistent storage
    - Real-time feel
    """)

# Main content area
if st.session_state.show_signin:
    # Sign In Form
    st.markdown("""
    <div class="auth-container">
        <h2 style="text-align: center; color: white;">🔑 Sign In</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("signin_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("🔓 Sign In", use_container_width=True)
            with col2:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    st.session_state.show_signin = False
                    st.rerun()
            
            if submitted:
                if not username or not password:
                    st.error("Please fill in all fields")
                else:
                    success, message = sign_in(username, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        users = load_users()
                        st.session_state.user_email = users[username].get('email', '')
                        st.session_state.show_signin = False
                        st.success(message)
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(message)

elif st.session_state.show_signup:
    # Sign Up Form
    st.markdown("""
    <div class="auth-container">
        <h2 style="text-align: center; color: white;">✨ Create Account</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("signup_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            username = st.text_input("Username", placeholder="Choose a username")
            password = st.text_input("Password", type="password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("🚀 Sign Up", use_container_width=True)
            with col2:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    st.session_state.show_signup = False
                    st.rerun()
            
            if submitted:
                if not email or not username or not password:
                    st.error("Please fill in all fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                elif len(username) < 3:
                    st.error("Username must be at least 3 characters")
                else:
                    success, message = sign_up(email, username, password)
                    if success:
                        st.success(message)
                        time.sleep(0.5)
                        st.session_state.show_signup = False
                        st.rerun()
                    else:
                        st.error(message)

elif st.session_state.show_profile:
    # Profile Page
    st.markdown("## 👤 Edit Profile")
    
    profiles = load_profiles()
    user_profile = profiles.get(st.session_state.username, {})
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Profile Picture")
        current_avatar = user_profile.get('avatar_url')
        if current_avatar and os.path.exists(current_avatar):
            st.image(current_avatar, width=200)
        else:
            st.markdown(f"# {st.session_state.username[0].upper()}")
            st.caption("No profile picture")
        
        avatar_file = st.file_uploader("Upload new picture", type=['png', 'jpg', 'jpeg'])
    
    with col2:
        with st.form("profile_form"):
            bio = st.text_area("Bio", value=user_profile.get('bio', ''), max_chars=200, 
                              placeholder="Tell us about yourself...")
            
            wallpaper_choice = st.selectbox("Default Wallpaper", 
                                           list(DEFAULT_WALLPAPERS.keys()),
                                           index=list(DEFAULT_WALLPAPERS.keys()).index(
                                               user_profile.get('wallpaper', 'Cosmic Night'))
                                           if user_profile.get('wallpaper', 'Cosmic Night') in DEFAULT_WALLPAPERS else 0)
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("💾 Save Profile", use_container_width=True)
            with col2:
                if st.form_submit_button("↩️ Back to Chat", use_container_width=True):
                    st.session_state.show_profile = False
                    st.rerun()
            
            if submitted:
                if update_profile(st.session_state.username, bio, avatar_file, wallpaper_choice):
                    st.success("Profile updated successfully!")
                    st.session_state.wallpaper = wallpaper_choice
                    time.sleep(0.5)
                    st.session_state.show_profile = False
                    st.rerun()
                else:
                    st.error("Failed to update profile")

else:
    # Main Chat Interface
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="header-container">
            <h1 style="background: linear-gradient(to right, #c084fc, #a78bfa); 
                       -webkit-background-clip: text; 
                       -webkit-text-fill-color: transparent;
                       font-size: 2.5rem;
                       margin-bottom: 0.5rem;">
                💬 ChatVerse
            </h1>
            <div class="online-badge">
                <span class="online-dot"></span>
                <span>Community Forum</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Function to add message with rate limiting
    def add_message():
        if not st.session_state.authenticated:
            st.warning("Please sign in to send messages")
            return False
        
        message = st.session_state.message_input
        if not message or not message.strip():
            return False
        
        message_text = message.strip()
        
        # Validation
        if len(message_text) > 500:
            st.error("Message too long (max 500 characters)")
            return False
        
        # Check for spam (duplicate messages)
        if st.session_state.messages and st.session_state.messages[-1]['text'] == message_text and \
           st.session_state.messages[-1]['username'] == st.session_state.username:
            st.warning("Duplicate message detected")
            return False
        
        # Rate limiting (max 5 messages per minute)
        recent_messages = [msg for msg in st.session_state.messages[-10:]
                          if msg['username'] == st.session_state.username and
                          (datetime.now() - datetime.fromisoformat(msg['timestamp'])).seconds < 60]
        if len(recent_messages) >= 5:
            st.warning("Please slow down (max 5 messages per minute)")
            return False
        
        new_msg = {
            "id": str(uuid.uuid4()),
            "username": st.session_state.username,
            "text": sanitize_text(message_text),
            "timestamp": datetime.now().isoformat(),
            "reactions": {"👍": [], "❤️": [], "😂": [], "🔥": [], "👏": []}
        }
        st.session_state.messages.append(new_msg)
        save_messages()
        return True
    
    # Display messages
    if not st.session_state.messages:
        st.info("💫 No messages yet. Start the conversation!")
    else:
        # Filter messages if search is active
        displayed_messages = st.session_state.messages
        if st.session_state.search_query:
            query = st.session_state.search_query.lower()
            displayed_messages = [
                msg for msg in displayed_messages
                if query in msg['text'].lower() or query in msg['username'].lower()
            ]
            st.caption(f"Showing {len(displayed_messages)} results for '{st.session_state.search_query}'")
        
        if not displayed_messages:
            st.info("🔍 No messages found matching your search")
        else:
            # Display messages in reverse order (newest first)
            for msg in reversed(displayed_messages):
                is_user = msg['username'] == st.session_state.username
                
                # Get user profile for avatar
                profiles = load_profiles()
                user_profile = profiles.get(msg['username'], {})
                avatar_url = user_profile.get('avatar_url')
                
                if avatar_url and os.path.exists(avatar_url):
                    # Read and encode avatar image
                    with open(avatar_url, 'rb') as f:
                        avatar_data = base64.b64encode(f.read()).decode()
                    avatar_style = f"background-image: url(data:image/png;base64,{avatar_data}); background-size: cover;"
                else:
                    avatar_letter = msg['username'][0].upper() if msg['username'] else "?"
                    avatar_style = ""
                
                # Format time
                time_str = format_time(msg['timestamp'])
                
                # Get reactions
                reactions = msg.get('reactions', {"👍": [], "❤️": [], "😂": [], "🔥": [], "👏": []})
                
                # Create message HTML
                avatar_html = f"""
                <div class="chat-avatar {'user-avatar' if is_user else 'other-avatar'}" 
                     style="{avatar_style}">
                    {'' if avatar_style else avatar_letter}
                </div>
                """
                
                reactions_html = ""
                if any(reactions.values()):
                    reactions_html = '<div class="chat-reactions">'
                    for emoji, users in reactions.items():
                        if users:
                            reactions_html += f'<span class="reaction-btn">{emoji} {len(users)}</span>'
                    reactions_html += '</div>'
                
                message_html = f"""
                <div class="chat-message {'user' if is_user else 'other'}">
                    {avatar_html}
                    <div class="chat-content">
                        <div class="chat-author">
                            <span>{sanitize_text(msg['username'])}</span>
                            <span class="chat-time">{time_str}</span>
                        </div>
                        <div class="chat-text">
                            {msg['text']}
                        </div>
                        {reactions_html}
                    </div>
                </div>
                """
                st.markdown(message_html, unsafe_allow_html=True)
                
                # Reaction buttons (if authenticated)
                if st.session_state.authenticated:
                    cols = st.columns([0.1, 0.1, 0.1, 0.1, 0.1, 0.5])
                    reaction_emojis = ["👍", "❤️", "😂", "🔥", "👏"]
                    for i, emoji in enumerate(reaction_emojis):
                        with cols[i]:
                            reaction_key = f"reaction_{msg['id']}_{emoji}"
                            if st.button(emoji, key=reaction_key, help=f"React with {emoji}"):
                                # Toggle reaction
                                if st.session_state.username in reactions.get(emoji, []):
                                    msg['reactions'][emoji].remove(st.session_state.username)
                                else:
                                    if emoji not in msg['reactions']:
                                        msg['reactions'][emoji] = []
                                    msg['reactions'][emoji].append(st.session_state.username)
                                save_messages()
                                st.rerun()
    
    # Message input
    st.markdown("---")
    
    if st.session_state.authenticated:
        with st.form(key="message_form", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                message = st.text_input(
                    "Message",
                    placeholder=f"Type your message here, {st.session_state.username}...",
                    key="message_input",
                    label_visibility="collapsed"
                )
            with col2:
                submitted = st.form_submit_button("📤 Send", use_container_width=True)
            
            if submitted and message and message.strip():
                if add_message():
                    st.rerun()
    else:
        st.info("🔒 Please sign in to send messages and react to posts")

# Footer
st.markdown("""
<div style="text-align: center; padding: 1rem; color: #64748b; font-size: 0.8rem;">
    ✨ Be kind • Stay curious • Connect with others ✨
</div>
""", unsafe_allow_html=True)

# JavaScript for auto-scroll
st.markdown("""
<script>
    function scrollToBottom() {
        const mainContainer = window.parent.document.querySelector('.main');
        if (mainContainer) {
            mainContainer.scrollTop = mainContainer.scrollHeight;
        }
    }
    
    // Initial scroll
    setTimeout(scrollToBottom, 500);
    
    // Scroll on new messages
    const observer = new MutationObserver(scrollToBottom);
    const chatArea = window.parent.document.querySelector('.main');
    if (chatArea) {
        observer.observe(chatArea, { childList: true, subtree: true });
    }
</script>
""", unsafe_allow_html=True)

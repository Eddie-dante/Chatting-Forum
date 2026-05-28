import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import json
import os

# Page configuration
st.set_page_config(
    page_title="ChatVerse • Community Forum",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main container styling */
    .stApp {
        background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 1rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        display: flex;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .chat-message.user {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(96, 165, 250, 0.1));
        border: 1px solid rgba(59, 130, 246, 0.3);
        margin-left: 20%;
    }
    
    .chat-message.bot {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-right: 20%;
    }
    
    .chat-avatar {
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
    }
    
    .user-avatar {
        background: linear-gradient(135deg, #3b82f6, #60a5fa);
        box-shadow: 0 4px 10px rgba(59, 130, 246, 0.3);
    }
    
    .other-avatar {
        background: linear-gradient(135deg, #7c3aed, #a78bfa);
        box-shadow: 0 4px 10px rgba(124, 58, 237, 0.3);
    }
    
    .chat-content {
        flex: 1;
    }
    
    .chat-author {
        font-weight: 600;
        font-size: 0.9rem;
        color: #cbd5e1;
        margin-bottom: 0.3rem;
    }
    
    .chat-time {
        font-size: 0.7rem;
        color: #64748b;
        margin-left: 0.5rem;
    }
    
    .chat-text {
        color: #f1f5f9;
        line-height: 1.5;
        word-wrap: break-word;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(15, 23, 42, 0.95);
    }
    
    /* Input area styling */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.07);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 2rem;
        color: white;
        padding: 0.75rem 1.5rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #c084fc;
        box-shadow: 0 0 10px rgba(192, 132, 252, 0.3);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #a855f7);
        border: none;
        border-radius: 2rem;
        color: white;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 18px rgba(124, 58, 237, 0.4);
    }
    
    /* Header styling */
    .header-container {
        text-align: center;
        padding: 1rem;
        margin-bottom: 2rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .online-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(255, 255, 255, 0.08);
        padding: 0.3rem 1rem;
        border-radius: 2rem;
        font-size: 0.8rem;
    }
    
    .online-dot {
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Alert/info styling */
    .stAlert {
        background: rgba(124, 58, 237, 0.1);
        border: 1px solid rgba(124, 58, 237, 0.3);
        border-radius: 1rem;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .chat-message.user {
            margin-left: 5%;
        }
        .chat-message.bot {
            margin-right: 5%;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    if 'messages' not in st.session_state:
        # Load messages from file or create default
        st.session_state.messages = load_messages()
    
    if 'username' not in st.session_state:
        st.session_state.username = "Guest_" + str(uuid.uuid4())[:6]
    
    if 'user_avatar_color' not in st.session_state:
        st.session_state.user_avatar_color = "user-avatar"

def load_messages():
    """Load messages from JSON file"""
    try:
        if os.path.exists("chat_messages.json"):
            with open("chat_messages.json", "r", encoding="utf-8") as f:
                messages = json.load(f)
                return messages
    except Exception as e:
        print(f"Error loading messages: {e}")
    
    # Default messages
    return [
        {
            "id": "1",
            "username": "Astra",
            "text": "Welcome to ChatVerse! 🌟 This is a live community forum. Feel free to chat and connect!",
            "timestamp": datetime.now().isoformat(),
            "avatar": "A"
        },
        {
            "id": "2",
            "username": "Nebula",
            "text": "Hey everyone! Love the vibe here. What's everyone up to? ✨",
            "timestamp": datetime.now().isoformat(),
            "avatar": "N"
        }
    ]

def save_messages():
    """Save messages to JSON file"""
    try:
        with open("chat_messages.json", "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Error saving message: {e}")

def add_message(username, text):
    """Add a new message to the chat"""
    if text and text.strip():
        new_message = {
            "id": str(uuid.uuid4()),
            "username": username,
            "text": text.strip(),
            "timestamp": datetime.now().isoformat(),
            "avatar": username[0].upper() if username else "?"
        }
        st.session_state.messages.append(new_message)
        save_messages()
        return True
    return False

def clear_all_messages():
    """Clear all messages"""
    st.session_state.messages = []
    save_messages()

def format_time(timestamp_str):
    """Format timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%I:%M %p")
    except:
        return "Just now"

def get_online_count():
    """Simulate online users (for visual flair)"""
    import random
    return random.randint(2, 8)

# Initialize
init_session_state()

# Header Section
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
            <span>{}</span>
        </div>
    </div>
    """.format(f"{get_online_count()} online"), unsafe_allow_html=True)

# Sidebar for settings
with st.sidebar:
    st.markdown("## 🎨 Chat Settings")
    
    # Username input
    new_username = st.text_input(
        "Your Display Name",
        value=st.session_state.username,
        max_chars=20,
        help="Choose a name to show in chat"
    )
    if new_username != st.session_state.username and new_username:
        st.session_state.username = new_username
        st.rerun()
    
    st.markdown("---")
    
    # Chat actions
    st.markdown("### 🛠️ Actions")
    
    if st.button("🗑️ Clear All Messages", use_container_width=True):
        clear_all_messages()
        st.success("Chat cleared!")
        st.rerun()
    
    st.markdown("---")
    
    # Stats
    st.markdown("### 📊 Stats")
    st.metric("Total Messages", len(st.session_state.messages))
    st.metric("Active Users", "~" + str(get_online_count()))
    
    st.markdown("---")
    st.markdown("""
    ### ℹ️ About
    **ChatVerse** is a community forum where everyone can share ideas, ask questions, and connect.
    
    ✨ **Features:**
    - Real-time chat experience
    - Persistent messages
    - Custom usernames
    - Beautiful UI
    
    Be respectful and have fun! 🎉
    """)

# Main chat area
st.markdown("### 💬 Community Chat")

# Display messages
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        st.info("💫 No messages yet. Start the conversation!")
    else:
        # Display all messages
        for msg in reversed(st.session_state.messages):  # Show newest first
            is_current_user = msg['username'] == st.session_state.username
            avatar_class = "user-avatar" if is_current_user else "other-avatar"
            
            # Create message HTML
            message_html = f"""
            <div class="chat-message {'user' if is_current_user else 'bot'}">
                <div class="chat-avatar {avatar_class}">
                    {msg['avatar']}
                </div>
                <div class="chat-content">
                    <div class="chat-author">
                        {msg['username']}
                        <span class="chat-time">{format_time(msg['timestamp'])}</span>
                    </div>
                    <div class="chat-text">
                        {msg['text']}
                    </div>
                </div>
            </div>
            """
            st.markdown(message_html, unsafe_allow_html=True)

# Message input area
st.markdown("---")

col1, col2 = st.columns([4, 1])

with col1:
    message_input = st.text_input(
        "Message",
        placeholder="Type your message here...",
        key="message_input",
        label_visibility="collapsed"
    )

with col2:
    send_button = st.button("📤 Send", use_container_width=True)

# Handle sending messages
if send_button and message_input:
    if add_message(st.session_state.username, message_input):
        st.rerun()
    else:
        st.warning("Please enter a message")

# Handle Enter key
if message_input and message_input.endswith('\n'):
    if add_message(st.session_state.username, message_input.strip()):
        st.rerun()

# Auto-refresh (optional - for "real-time" feel)
# Uncomment the line below to enable auto-refresh every 3 seconds
# st.rerun()  # Note: This might cause performance issues

# Footer
st.markdown("""
<div style="text-align: center; padding: 1rem; color: #64748b; font-size: 0.8rem;">
    ✨ Be kind • Stay curious • Connect with others ✨
</div>
""", unsafe_allow_html=True)

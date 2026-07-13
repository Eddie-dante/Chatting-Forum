import streamlit as st
import json
import os
import html
import hashlib
import pathlib
from datetime import datetime
import uuid
import base64
from PIL import Image
import time
import requests

# Must be first
st.set_page_config(page_title="Chattier Pro", page_icon="💬", layout="wide", initial_sidebar_state="expanded")

# ========== CONFIG ==========
DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)
MESSAGES_FILE = DATA_DIR / "messages.json"
USERS_FILE = DATA_DIR / "users.json"
PROFILES_FILE = DATA_DIR / "profiles.json"
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Try cloud config
try:
    JSONBIN_KEY = st.secrets["jsonbin"]["api_key"]
    JSONBIN_ID = st.secrets["jsonbin"]["bin_id"]
    CLOUD = True
except:
    JSONBIN_KEY = os.environ.get("JSONBIN_KEY", "")
    JSONBIN_ID = os.environ.get("JSONBIN_ID", "")
    CLOUD = bool(JSONBIN_KEY and JSONBIN_ID)

# 30 wallpapers
WALLPAPERS = {
    "🌈 Gradient": "gradient",
    "✨ Purple": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=800&q=60",
    "🌌 Nebula": "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=800&q=60",
    "🌊 Ocean": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=800&q=60",
    "🏔️ Stars": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=60",
    "🌸 Cherry": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=800&q=60",
    "🌅 Sunset": "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?w=800&q=60",
    "🌿 Forest": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=800&q=60",
    "🏙️ City": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=800&q=60",
    "🔥 Lava": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800&q=60",
    "🎨 Cyber": "https://images.unsplash.com/photo-1515634928625-85bc09c9cbba?w=800&q=60",
    "🏝️ Beach": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&q=60",
    "❄️ Aurora": "https://images.unsplash.com/photo-1483921020237-2ff51e8e4b22?w=800&q=60",
    "🍁 Autumn": "https://images.unsplash.com/photo-1504208434309-cb69f4fe52b0?w=800&q=60",
    "💜 Lavender": "https://images.unsplash.com/photo-1505409859467-3a796fd5798e?w=800&q=60",
    "🏔️ Alpine": "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=800&q=60",
    "🌄 Desert": "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=800&q=60",
    "🌻 Sunflower": "https://images.unsplash.com/photo-1470506028280-a011fb34b6f7?w=800&q=60",
    "🎆 Fireworks": "https://images.unsplash.com/photo-1498931299472-f7a63a5a1cfa?w=800&q=60",
    "🌊 Storm": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=800&q=60",
    "🏖️ Crystal": "https://images.unsplash.com/photo-1505228395891-9a51e7e86bf6?w=800&q=60",
    "🏜️ Canyon": "https://images.unsplash.com/photo-1474044159687-1ee9f3a51722?w=800&q=60",
    "🏯 Temple": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800&q=60",
    "🌋 Volcano": "https://images.unsplash.com/photo-1468657988500-aca2e8a96ac1?w=800&q=60",
    "🏜️ Sahara": "https://images.unsplash.com/photo-1451337516015-6b6e9a44a8a3?w=800&q=60",
}

DEFAULT_WP = "🌈 Gradient"

EMOJIS = "😀😂🤣😍🥰😘😜🤪😎🤩🥳😇🤗🤔😴🥺😤😡💀👻👍👎👏🙌💪🤝❤️🧡💛💚💙💜🖤🔥⭐🌟✨🎉🎊🎂🍕🍔☕🏆💯".replace("", " ").split()

# ========== CLOUD FUNCTIONS ==========
def cloud_get(endpoint, timeout=3):
    """Get data from JSONBin"""
    if not CLOUD: return None
    try:
        r = requests.get(f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}/latest",
                        headers={"X-Master-Key": JSONBIN_KEY, "X-Bin-Meta": "false"}, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            return data if isinstance(data, list) else data.get("record", data)
        return None
    except: return None

def cloud_put(data, timeout=3):
    """Save data to JSONBin"""
    if not CLOUD: return False
    try:
        r = requests.put(f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}",
                        json=data, headers={"Content-Type": "application/json", "X-Master-Key": JSONBIN_KEY}, timeout=timeout)
        return r.status_code in [200, 201]
    except: return False

def load_all_data():
    """Load all shared data from cloud"""
    if CLOUD:
        data = cloud_get()
        if data and isinstance(data, dict):
            return data.get("messages", []), data.get("users", {}), data.get("profiles", {})
    
    # Fallback to local files
    return lj(MESSAGES_FILE, []), lj(USERS_FILE, {}), lj(PROFILES_FILE, {})

def save_all_data(messages, users, profiles):
    """Save all shared data to cloud and local"""
    if CLOUD:
        cloud_put({"messages": messages, "users": users, "profiles": profiles})
    
    # Always save local backup
    sj(MESSAGES_FILE, messages)
    sj(USERS_FILE, users)
    sj(PROFILES_FILE, profiles)

# ========== HELPERS ==========
def hp(pwd): return hashlib.sha256(pwd.encode()).hexdigest()
def sh(t): return html.escape(str(t)) if t else ""

def lj(p, d=None):
    try:
        if p.exists():
            with open(p, 'r', encoding='utf-8') as f: return json.load(f)
    except: pass
    return d if d is not None else {}

def sj(p, d):
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f: json.dump(d, f, indent=2)
    except: pass

def gup(u):
    """Get user profile from shared data"""
    _, _, profiles = load_all_data()
    if u not in profiles:
        profiles[u] = {"bio":"", "avatar":None, "wallpaper":DEFAULT_WP, "status":"", "last_seen":""}
    return profiles[u]

def up(u, bio, avatar, wallpaper, status=""):
    """Update user profile in shared data"""
    try:
        messages, users, profiles = load_all_data()
        if u not in profiles: profiles[u] = {}
        
        profiles[u]["bio"] = sh(bio) if bio else ""
        profiles[u]["status"] = sh(status) if status else ""
        profiles[u]["wallpaper"] = wallpaper if wallpaper in WALLPAPERS else DEFAULT_WP
        profiles[u]["last_seen"] = datetime.now().isoformat()
        
        if avatar:
            try:
                img = Image.open(avatar)
                if img.mode in ('RGBA','LA','P'):
                    bg = Image.new('RGB', img.size, (255,255,255))
                    if img.mode == 'P': img = img.convert('RGBA')
                    bg.paste(img, mask=img.split()[-1] if img.mode=='RGBA' else None)
                    img = bg
                else: img = img.convert("RGB")
                img.thumbnail((200,200))
                ap = UPLOADS_DIR / f"{u}_avatar.jpg"
                img.save(ap, "JPEG", quality=75)
                profiles[u]["avatar"] = str(ap)
            except: pass
        
        save_all_data(messages, users, profiles)
        return True
    except Exception as e:
        st.error(f"Profile update failed: {e}")
        return False

def gav(u, s=35):
    """Get avatar HTML"""
    try:
        _, _, profiles = load_all_data()
        p = profiles.get(u, {})
        if p.get("avatar") and os.path.exists(p["avatar"]):
            with open(p["avatar"],"rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f'<img src="data:image/jpeg;base64,{b64}" style="width:{s}px;height:{s}px;border-radius:50%;object-fit:cover;flex-shrink:0;">'
    except: pass
    c = ['#FF6B6B','#4ECDC4','#45B7D1','#96CEB4','#FFEAA7','#DDA0DD','#98D8C8','#F7B787','#FF8A80','#B388FF','#82B1FF','#B9F6CA','#FFE57F','#FF80AB','#EA80FC','#8C9EFF']
    return f'<div style="width:{s}px;height:{s}px;border-radius:50%;background:{c[hash(u)%len(c)]};display:flex;align-items:center;justify-content:center;font-weight:700;color:white;font-size:{s*0.4}px;flex-shrink:0;">{u[0].upper() if u else "?"}</div>'

def ft(ts):
    """Format timestamp"""
    try:
        t = datetime.fromisoformat(ts)
        d = (datetime.now()-t).seconds
        if d<60: return "now"
        if d<3600: return f"{d//60}m"
        if d<86400: return f"{d//3600}h"
        return t.strftime("%b %d")
    except: return ""

def send_msg(text, att=None, att_name=None):
    """Send a message to shared storage"""
    if not text and not att: return False
    
    text = sh(text.strip())[:1000] if text else ""
    messages, users, profiles = load_all_data()
    
    msg = {
        "id": str(uuid.uuid4()),
        "username": st.session_state.user,
        "text": text,
        "timestamp": datetime.now().isoformat(),
        "reactions": {}
    }
    
    if att:
        msg["attachment"] = att
        msg["attachment_name"] = att_name
        msg["attachment_type"] = "img" if att_name.lower().endswith(('.png','.jpg','.jpeg','.gif')) else "file"
    
    messages.append(msg)
    
    # Update last seen
    if st.session_state.user in profiles:
        profiles[st.session_state.user]["last_seen"] = datetime.now().isoformat()
    
    if len(messages) > 300:
        messages = messages[-300:]
    
    save_all_data(messages, users, profiles)
    st.session_state.messages = messages
    return True

def react(msg_id, emoji):
    """Toggle reaction on a message"""
    messages, users, profiles = load_all_data()
    for m in messages:
        if m.get("id") == msg_id:
            if "reactions" not in m: m["reactions"] = {}
            if emoji not in m["reactions"]: m["reactions"][emoji] = []
            
            u = st.session_state.user
            if u in m["reactions"][emoji]:
                m["reactions"][emoji].remove(u)
                if not m["reactions"][emoji]: del m["reactions"][emoji]
            else:
                m["reactions"][emoji].append(u)
            
            if not m.get("reactions"): del m["reactions"]
            break
    
    save_all_data(messages, users, profiles)
    st.session_state.messages = messages

def del_msg(msg_id):
    """Delete a message"""
    messages, users, profiles = load_all_data()
    messages = [m for m in messages if m.get("id") != msg_id]
    save_all_data(messages, users, profiles)
    st.session_state.messages = messages

def edit_msg(msg_id, txt):
    """Edit a message"""
    txt = sh(txt.strip())
    if not txt: return
    
    messages, users, profiles = load_all_data()
    for m in messages:
        if m.get("id") == msg_id:
            m["text"] = txt
            m["edited"] = True
            break
    
    save_all_data(messages, users, profiles)
    st.session_state.messages = messages

def sign_up(u, p, c):
    """Register new user - SHARED across all devices"""
    if not u or not p: return False, "Fill all fields"
    if p != c: return False, "Passwords don't match"
    if len(p) < 4: return False, "Password too short (min 4)"
    if len(u) < 2 or len(u) > 20: return False, "Username 2-20 characters"
    if not u.isalnum(): return False, "Only letters and numbers"
    
    messages, users, profiles = load_all_data()
    
    if u.lower() in [x.lower() for x in users]:
        return False, "Username already taken"
    
    users[u] = hp(p)
    profiles[u] = {"bio": "", "avatar": None, "wallpaper": DEFAULT_WP, "status": "", "last_seen": datetime.now().isoformat()}
    
    save_all_data(messages, users, profiles)
    return True, "Account created! Please sign in."

def sign_in(u, p):
    """Login - checks SHARED user database"""
    if not u or not p: return False, "Enter username and password"
    
    messages, users, profiles = load_all_data()
    
    for un, pw in users.items():
        if un.lower() == u.lower():
            if pw == hp(p):
                # Update last seen
                if un in profiles:
                    profiles[un]["last_seen"] = datetime.now().isoformat()
                    save_all_data(messages, users, profiles)
                return True, un
            else:
                return False, "Wrong password"
    
    return False, "Username not found. Create an account first."

# ========== SESSION ==========
if 'init' not in st.session_state:
    msgs, usrs, profs = load_all_data()
    st.session_state.messages = msgs
    st.session_state.auth = False
    st.session_state.user = ""
    st.session_state.wp = DEFAULT_WP
    st.session_state.view = "chat"
    st.session_state.edit_id = None
    st.session_state.reply_to = None
    st.session_state.vp = None
    st.session_state.init = True

# Reload messages and update last seen
if st.session_state.get('auth'):
    msgs, usrs, profs = load_all_data()
    st.session_state.messages = msgs
    st.session_state.wp = profs.get(st.session_state.user, {}).get("wallpaper", DEFAULT_WP)

wp_url = WALLPAPERS.get(st.session_state.wp, WALLPAPERS[DEFAULT_WP])

# ========== CSS ==========
if wp_url == "gradient":
    bg = "background: linear-gradient(135deg, #667eea, #764ba2, #f093fb, #f5576c, #4facfe); background-size: 400% 400%; animation: grad 15s ease infinite;"
    ov = "background: rgba(0,0,0,0.25);"
else:
    bg = f'background-image: url("{wp_url}"); background-size: cover; background-position: center; background-attachment: fixed;'
    ov = "background: rgba(0,0,0,0.5); backdrop-filter: blur(5px);"

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*{{font-family:'Inter',sans-serif}}#MainMenu,footer{{visibility:hidden}}
@keyframes grad{{0%{{background-position:0% 50%}}50%{{background-position:100% 50%}}100%{{background-position:0% 50%}}}}
@keyframes fade{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:translateY(0)}}}}
.stApp{{{bg}}}.stApp::before{{content:"";position:fixed;top:0;left:0;width:100%;height:100%;{ov};z-index:-1}}
section[data-testid="stSidebar"]{{background:linear-gradient(180deg,rgba(102,126,234,0.95),rgba(240,147,251,0.9),rgba(79,172,254,0.95))!important;backdrop-filter:blur(20px);border-right:2px solid rgba(255,255,255,0.2)!important}}
section[data-testid="stSidebar"] *{{color:white!important}}
section[data-testid="stSidebar"] .stButton>button{{background:rgba(255,255,255,0.2)!important;border:2px solid rgba(255,255,255,0.3)!important;font-weight:600!important}}
section[data-testid="stSidebar"] .stButton>button:hover{{background:rgba(255,255,255,0.4)!important;transform:translateY(-2px)}}
.msg{{display:flex;margin-bottom:0.4rem;animation:fade 0.2s ease}}
.msg.r{{justify-content:flex-start}}.msg.s{{justify-content:flex-end}}
.bub{{max-width:70%;padding:0.5rem 0.8rem;border-radius:0.8rem;word-wrap:break-word}}
.s .bub{{background:linear-gradient(135deg,rgba(102,126,234,0.4),rgba(118,75,162,0.4));border:1px solid rgba(102,126,234,0.5);margin-right:0.3rem}}
.r .bub{{background:rgba(255,255,255,0.1);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.1);margin-left:0.3rem}}
.un{{font-size:0.65rem;font-weight:600}}.s .un{{color:#c4b5fd}}.r .un{{color:#a5b4fc}}
.tm{{font-size:0.55rem;color:#94a3b8}}.tx{{color:#f8fafc;font-size:0.85rem;line-height:1.3}}
.stButton>button{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:0.6rem;padding:0.4rem 0.8rem;font-weight:600;transition:all 0.2s}}
.stButton>button:hover{{transform:translateY(-1px)}}
.stTextInput>div>div>input,.stTextArea>div>div>textarea{{background:rgba(255,255,255,0.9);border-radius:0.6rem;padding:0.5rem 0.8rem}}
.card{{background:rgba(255,255,255,0.08);border-radius:0.8rem;padding:1rem;text-align:center}}
.dot{{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:0.3rem}}
.on{{background:#10b981;box-shadow:0 0 8px rgba(16,185,129,0.5)}}.off{{background:#6b7280}}
.emoji{{font-size:1.3rem;cursor:pointer;padding:0.3rem;border-radius:0.3rem;transition:all 0.2s;display:inline-block}}
.emoji:hover{{background:rgba(255,255,255,0.2);transform:scale(1.2)}}
.att{{max-width:150px;border-radius:0.5rem;margin-top:0.3rem}}
::-webkit-scrollbar{{width:4px}}::-webkit-scrollbar-thumb{{background:linear-gradient(#667eea,#764ba2);border-radius:2px}}
</style>""", unsafe_allow_html=True)

# ========== AUTH PAGE ==========
if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("""
        <div style="text-align:center;padding:2rem">
            <div style="font-size:4rem">💬</div>
            <h1 style="color:white;background:linear-gradient(135deg,#667eea,#764ba2,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent">Chattier Pro</h1>
            <p style="color:#94a3b8">Chat across all your devices!</p>
        </div>
        """, unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["🔑 Sign In", "✨ Sign Up"])
        
        with t1:
            with st.form("login_form"):
                u = st.text_input("Username", placeholder="Your username")
                p = st.text_input("Password", type="password", placeholder="Your password")
                submitted = st.form_submit_button("Sign In", use_container_width=True)
                
                if submitted:
                    success, result = sign_in(u, p)
                    if success:
                        st.session_state.auth = True
                        st.session_state.user = result
                        msgs, _, _ = load_all_data()
                        st.session_state.messages = msgs
                        st.success(f"Welcome back, {result}! 🎉")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(result)
        
        with t2:
            with st.form("signup_form"):
                u = st.text_input("Choose Username", placeholder="2-20 characters, letters & numbers")
                p = st.text_input("Create Password", type="password", placeholder="Minimum 4 characters")
                c = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
                submitted = st.form_submit_button("Create Account", use_container_width=True)
                
                if submitted:
                    success, msg = sign_up(u, p, c)
                    if success:
                        st.success(msg)
                        st.balloons()
                    else:
                        st.error(msg)
        
        # Show cloud status
        if CLOUD:
            st.success("✅ Cloud sync active - chat across devices!")
        else:
            st.warning("⚠️ Add JSONBin keys for cross-device chat")

# ========== MAIN APP ==========
else:
    # Update last seen on every interaction
    msgs, usrs, profs = load_all_data()
    if st.session_state.user in profs:
        profs[st.session_state.user]["last_seen"] = datetime.now().isoformat()
        save_all_data(msgs, usrs, profs)
    
    # ========== SIDEBAR ==========
    with st.sidebar:
        st.markdown('<div style="text-align:center"><div style="font-size:2.5rem">💬</div><h3>Chattier Pro</h3></div>', unsafe_allow_html=True)
        
        pd = profs.get(st.session_state.user, {})
        st.markdown(f"""
        <div style="text-align:center">
            {gav(st.session_state.user, 60)}
            <h4>@{st.session_state.user}</h4>
            <p style="font-size:0.7rem;opacity:0.9">{sh(pd.get("status", "No status"))[:50]}</p>
            <span class="dot on"></span> Online
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Refresh button
        if st.button("🔄 Refresh", use_container_width=True):
            msgs, _, _ = load_all_data()
            st.session_state.messages = msgs
            st.rerun()
        
        if st.button("💬 Chat", use_container_width=True):
            st.session_state.view = "chat"
            st.rerun()
        
        if st.button("👤 My Profile", use_container_width=True):
            st.session_state.view = "profile"
            st.rerun()
        
        if st.button("👥 Members", use_container_width=True):
            st.session_state.view = "members"
            st.rerun()
        
        if st.button("🎨 Themes", use_container_width=True):
            st.session_state.view = "themes"
            st.rerun()
        
        st.divider()
        
        # Stats
        total_msgs = len(st.session_state.messages)
        total_users = len(set(m["username"] for m in st.session_state.messages)) if st.session_state.messages else 0
        st.caption(f"📝 Messages: {total_msgs}")
        st.caption(f"👥 Members: {total_users}")
        
        # Online users
        online_users = []
        for un, pr in profs.items():
            try:
                ls = pr.get("last_seen", "")
                if ls and (datetime.now() - datetime.fromisoformat(ls)).seconds < 300:
                    if un != st.session_state.user:
                        online_users.append(un)
            except: pass
        
        if online_users:
            st.caption(f"🟢 Online: {len(online_users)}")
        
        st.divider()
        
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.auth = False
            st.session_state.user = ""
            st.rerun()
    
    # ========== CHAT VIEW ==========
    if st.session_state.view == "chat":
        st.markdown(f'<h3 style="color:white">💬 Community Chat <small style="font-size:0.6rem;color:#94a3b8">({len(st.session_state.messages)} messages)</small></h3>', unsafe_allow_html=True)
        
        if not st.session_state.messages:
            st.markdown('<div style="text-align:center;padding:3rem;color:#94a3b8"><div style="font-size:3rem">✨</div><p>No messages yet</p><p>Be the first to say hello!</p></div>', unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages[-20:]:
                own = msg["username"] == st.session_state.user
                mid = msg.get("id", "")
                cls = "s" if own else "r"
                
                if st.session_state.get("edit_id") == mid:
                    with st.form(key=f"e_{mid}"):
                        nt = st.text_input("Edit", value=msg['text'], label_visibility="collapsed")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.form_submit_button("💾 Save"):
                                edit_msg(mid, nt)
                                st.session_state.edit_id = None
                                st.rerun()
                        with c2:
                            if st.form_submit_button("❌ Cancel"):
                                st.session_state.edit_id = None
                                st.rerun()
                else:
                    ed = ' <small style="color:#94a3b8">(edited)</small>' if msg.get("edited") else ""
                    
                    st.markdown(f"""
                    <div class="msg {cls}">
                        <div style="flex-shrink:0;align-self:flex-end;margin:{'0 0 0 0.3rem' if own else '0 0.3rem 0 0'}">
                            {gav(msg["username"], 25)}
                        </div>
                        <div style="max-width:70%">
                            <div class="bub">
                                <span class="un">{sh(msg["username"])}</span>
                                <span class="tm"> • {ft(msg.get("timestamp", ""))}{ed}</span>
                                {f'<div class="tx">{msg["text"]}</div>' if msg.get("text") else ""}
                                {f'<a href="{msg["attachment"]}" target="_blank"><img src="{msg["attachment"]}" class="att" /></a>' if msg.get("attachment", "") and msg.get("attachment_type") == "img" else ""}
                                {f'<div><a href="{msg["attachment"]}" target="_blank" style="color:#a5b4fc;text-decoration:none">📎 {msg.get("attachment_name", "File")}</a></div>' if msg.get("attachment", "") and msg.get("attachment_type") != "img" else ""}
                            </div>
                    """, unsafe_allow_html=True)
                    
                    # Action buttons
                    cols = st.columns([1, 1, 1, 1, 8])
                    with cols[0]:
                        if st.button("👍", key=f"l_{mid}"): react(mid, "👍"); st.rerun()
                    with cols[1]:
                        if st.button("❤️", key=f"h_{mid}"): react(mid, "❤️"); st.rerun()
                    with cols[2]:
                        if st.button("↩️", key=f"r_{mid}"): st.session_state.reply_to = mid; st.rerun()
                    if own:
                        with cols[3]:
                            if st.button("✏️", key=f"ed_{mid}"): st.session_state.edit_id = mid; st.rerun()
                    
                    # Reactions display
                    if msg.get("reactions"):
                        rh = '<div style="margin-top:0.2rem;display:flex;gap:0.2rem;flex-wrap:wrap">'
                        for em, users in msg["reactions"].items():
                            active = st.session_state.user in users
                            rh += f'<span style="background:rgba(255,255,255,{0.3 if active else 0.1});padding:0.1rem 0.4rem;border-radius:0.8rem;font-size:0.7rem;cursor:pointer" onclick="this.click()">{em} {len(users)}</span>'
                        rh += '</div>'
                        st.markdown(rh, unsafe_allow_html=True)
                    
                    if own:
                        if st.button("🗑️ Delete", key=f"d_{mid}"):
                            del_msg(mid)
                            st.rerun()
                    
                    st.markdown('</div></div>', unsafe_allow_html=True)
        
        # Reply indicator
        if st.session_state.get("reply_to"):
            rm = next((m for m in st.session_state.messages if m.get("id") == st.session_state.reply_to), None)
            if rm:
                col1, col2 = st.columns([10, 1])
                with col1:
                    st.info(f"↩️ Replying to {rm['username']}: {rm.get('text', '')[:50]}...")
                with col2:
                    if st.button("✕", key="cancel_reply"):
                        st.session_state.reply_to = None
                        st.rerun()
        
        # Emoji picker
        with st.expander("😊 Emoji Picker"):
            ec = st.columns(15)
            for i, emo in enumerate(EMOJIS):
                with ec[i % 15]:
                    if st.button(emo, key=f"em_{i}"):
                        st.session_state.emoji_pick = emo
                        st.rerun()
        
        # Message input
        st.divider()
        with st.form("msg_form", clear_on_submit=True):
            default_val = st.session_state.get('emoji_pick', '')
            if default_val:
                st.session_state.emoji_pick = ''
            
            c1, c2, c3 = st.columns([5, 1, 1])
            with c1:
                txt = st.text_input(
                    "Message",
                    placeholder=f"Type as @{st.session_state.user}...",
                    label_visibility="collapsed",
                    value=default_val,
                    key="msg_input"
                )
            with c2:
                fl = st.file_uploader(
                    "📎",
                    type=['png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'zip'],
                    label_visibility="collapsed",
                    key="file_upload"
                )
            with c3:
                sb = st.form_submit_button("📤 Send", use_container_width=True)
            
            if sb:
                ad, an = None, None
                if fl:
                    try:
                        fb = fl.read()
                        if len(fb) < 5_000_000:  # 5MB limit
                            ad = base64.b64encode(fb).decode()
                            an = fl.name
                        else:
                            st.error("File too large (max 5MB)")
                    except:
                        st.error("Failed to read file")
                
                if txt.strip() or ad:
                    if send_msg(txt, ad, an):
                        st.rerun()
    
    # ========== PROFILE VIEW ==========
    elif st.session_state.view == "profile":
        st.markdown('<h3 style="color:white">👤 My Profile</h3>', unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            pd = profs.get(st.session_state.user, {})
            st.markdown(f'<div class="card">{gav(st.session_state.user, 100)}<h4>@{st.session_state.user}</h4><span class="dot on"></span> Online</div>', unsafe_allow_html=True)
            av = st.file_uploader("Change Avatar", type=['png', 'jpg', 'jpeg'])
        
        with c2:
            with st.form("profile_form"):
                pd = profs.get(st.session_state.user, {})
                bio = st.text_area("Bio", value=pd.get("bio", ""), max_chars=200, height=80, placeholder="Tell us about yourself...")
                status = st.text_input("Status", value=pd.get("status", ""), max_chars=60, placeholder="What's on your mind?")
                
                c_a, c_b = st.columns(2)
                with c_a:
                    if st.form_submit_button("💾 Save Profile", use_container_width=True):
                        if up(st.session_state.user, bio, av, st.session_state.wp, status):
                            st.success("Profile updated! ✅")
                            time.sleep(0.5)
                            st.rerun()
                with c_b:
                    if st.form_submit_button("↩️ Back to Chat", use_container_width=True):
                        st.session_state.view = "chat"
                        st.rerun()
    
    # ========== MEMBERS VIEW ==========
    elif st.session_state.view == "members":
        if st.session_state.get("vp"):
            v = st.session_state.vp
            p = profs.get(v, {})
            
            st.markdown(f'<h3 style="color:white">👤 {sh(v)}\'s Profile</h3>', unsafe_allow_html=True)
            if st.button("↩️ Back to Members"):
                st.session_state.vp = None
                st.rerun()
            
            c1, c2 = st.columns([1, 2])
            with c1:
                ls = p.get("last_seen", "")
                on = False
                if ls:
                    try: on = (datetime.now() - datetime.fromisoformat(ls)).seconds < 300
                    except: pass
                
                st.markdown(f"""
                <div class="card">
                    {gav(v, 80)}
                    <h4>@{sh(v)}</h4>
                    <span class="dot {'on' if on else 'off'}"></span>
                    {'Online now' if on else 'Offline'}
                    <p style="color:#94a3b8;font-size:0.8rem;margin-top:0.5rem">{sh(p.get('status', 'No status'))}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with c2:
                st.markdown("### About")
                st.markdown(f'<div style="background:rgba(255,255,255,0.05);padding:1rem;border-radius:0.5rem"><p style="color:#f8fafc">{sh(p.get("bio", "No bio yet"))}</p></div>', unsafe_allow_html=True)
                
                ums = [m for m in st.session_state.messages if m["username"] == v][-5:]
                if ums:
                    st.markdown("### Recent Messages")
                    for m in reversed(ums):
                        st.markdown(f'<div style="background:rgba(255,255,255,0.05);padding:0.5rem;border-radius:0.5rem;margin:0.2rem 0"><small style="color:#94a3b8">{ft(m.get("timestamp",""))}</small><p style="color:#f8fafc;margin:0.2rem 0">{m.get("text","")}</p></div>', unsafe_allow_html=True)
        else:
            st.markdown('<h3 style="color:white">👥 Community Members</h3>', unsafe_allow_html=True)
            
            all_users = list(set([m["username"] for m in st.session_state.messages])) if st.session_state.messages else []
            
            if not all_users:
                st.info("No members yet. Send a message to be the first!")
            else:
                q = st.text_input("🔍 Search members", placeholder="Type username...")
                fu = [u for u in all_users if q.lower() in u.lower()] if q else all_users
                
                for i, u in enumerate(fu[:30]):
                    if i % 3 == 0:
                        cols = st.columns(3)
                    
                    p = profs.get(u, {})
                    ls = p.get("last_seen", "")
                    on = False
                    if ls:
                        try: on = (datetime.now() - datetime.fromisoformat(ls)).seconds < 300
                        except: pass
                    
                    with cols[i % 3]:
                        st.markdown(f"""
                        <div class="card" style="margin-bottom:0.5rem">
                            {gav(u, 50)}
                            <h4>@{sh(u)}</h4>
                            <span class="dot {'on' if on else 'off'}"></span>
                            {'Online' if on else 'Offline'}
                            <p style="font-size:0.7rem;color:#94a3b8;margin-top:0.3rem">{sh(p.get('status',''))[:30]}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("👁️ View Profile", key=f"vp_{u}", use_container_width=True):
                            st.session_state.vp = u
                            st.rerun()
    
    # ========== THEMES VIEW ==========
    elif st.session_state.view == "themes":
        st.markdown(f'<h3 style="color:white">🎨 Themes ({len(WALLPAPERS)})</h3>', unsafe_allow_html=True)
        
        items = list(WALLPAPERS.items())
        for i, (name, url) in enumerate(items):
            if i % 5 == 0:
                cols = st.columns(5)
            
            sel = name == st.session_state.wp
            with cols[i % 5]:
                if url == "gradient":
                    st.markdown(f'<div style="background:linear-gradient(135deg,#667eea,#764ba2,#f093fb,#f5576c,#4facfe);height:80px;border-radius:0.5rem;border:2px solid {"#667eea" if sel else "rgba(255,255,255,0.1)"};margin-bottom:0.3rem;display:flex;align-items:center;justify-content:center;font-size:2rem">🌈</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div style="background-image:url({url});background-size:cover;height:80px;border-radius:0.5rem;border:2px solid {"#667eea" if sel else "rgba(255,255,255,0.1)"};margin-bottom:0.3rem"></div>', unsafe_allow_html=True)
                
                if st.button(f"{'✅' if sel else ''} {name}", key=f"th_{i}", use_container_width=True):
                    st.session_state.wp = name
                    msgs, usrs, profs = load_all_data()
                    if st.session_state.user in profs:
                        profs[st.session_state.user]["wallpaper"] = name
                    save_all_data(msgs, usrs, profs)
                    st.rerun()

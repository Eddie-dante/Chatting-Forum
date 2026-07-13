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

# 30 wallpapers (reduced for performance)
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
    "🏰 Northern": "https://images.unsplash.com/photo-1483347756197-71ef80e95f73?w=800&q=60",
    "🎆 Fireworks": "https://images.unsplash.com/photo-1498931299472-f7a63a5a1cfa?w=800&q=60",
    "🌊 Storm": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=800&q=60",
    "🏖️ Crystal": "https://images.unsplash.com/photo-1505228395891-9a51e7e86bf6?w=800&q=60",
    "🏜️ Canyon": "https://images.unsplash.com/photo-1474044159687-1ee9f3a51722?w=800&q=60",
    "🌊 Turquoise": "https://images.unsplash.com/photo-1505144808419-1957a94ca61e?w=800&q=60",
    "🌸 Meadow": "https://images.unsplash.com/photo-1444021465936-c6ca6d1cb1e6?w=800&q=60",
    "🎭 Abstract": "https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=800&q=60",
    "🏯 Temple": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800&q=60",
    "🏛️ Greece": "https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&q=60",
    "🌋 Volcano": "https://images.unsplash.com/photo-1468657988500-aca2e8a96ac1?w=800&q=60",
    "🏜️ Sahara": "https://images.unsplash.com/photo-1451337516015-6b6e9a44a8a3?w=800&q=60",
}

DEFAULT_WP = "🌈 Gradient"

EMOJIS = "😀😂🤣😍🥰😘😜🤪😎🤩🥳😇🤗🤔😴🥺😤😡💀👻👍👎👏🙌💪🤝❤️🧡💛💚💙💜🖤🔥⭐🌟✨🎉🎊🎂🍕🍔☕🏆💯".replace("", " ").split()

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
        with open(p, 'w', encoding='utf-8') as f: json.dump(d, f)
    except: pass

def lu(): return lj(USERS_FILE, {})
def su(u): sj(USERS_FILE, u)
def lp(): return lj(PROFILES_FILE, {})
def sp(p): sj(PROFILES_FILE, p)

def gup(u):
    p = lp()
    if u not in p: p[u] = {"bio":"", "avatar":None, "wallpaper":DEFAULT_WP, "status":"", "last_seen":""}
    return p[u]

def up(u, bio, avatar, wallpaper, status=""):
    try:
        p = lp()
        if u not in p: p[u] = {}
        p[u]["bio"] = sh(bio) if bio else ""
        p[u]["status"] = sh(status) if status else ""
        p[u]["wallpaper"] = wallpaper if wallpaper in WALLPAPERS else DEFAULT_WP
        p[u]["last_seen"] = datetime.now().isoformat()
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
                p[u]["avatar"] = str(ap)
            except: pass
        sp(p)
        return True
    except: return False

def gav(u, s=35):
    try:
        p = lp().get(u,{})
        if p.get("avatar") and os.path.exists(p["avatar"]):
            with open(p["avatar"],"rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f'<img src="data:image/jpeg;base64,{b64}" style="width:{s}px;height:{s}px;border-radius:50%;object-fit:cover;flex-shrink:0;">'
    except: pass
    c = ['#FF6B6B','#4ECDC4','#45B7D1','#96CEB4','#FFEAA7','#DDA0DD','#98D8C8','#F7B787','#FF8A80','#B388FF','#82B1FF','#B9F6CA','#FFE57F','#FF80AB','#EA80FC','#8C9EFF']
    return f'<div style="width:{s}px;height:{s}px;border-radius:50%;background:{c[hash(u)%len(c)]};display:flex;align-items:center;justify-content:center;font-weight:700;color:white;font-size:{s*0.4}px;flex-shrink:0;">{u[0].upper() if u else "?"}</div>'

def lm():
    if CLOUD:
        try:
            r = requests.get(f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}/latest", 
                           headers={"X-Master-Key": JSONBIN_KEY, "X-Bin-Meta": "false"}, timeout=3)
            if r.status_code==200:
                d = r.json()
                return d if isinstance(d,list) else d.get("messages",[])
        except: pass
    return lj(MESSAGES_FILE, [])

def sm(msgs):
    if len(msgs)>300: msgs = msgs[-300:]
    if CLOUD:
        try:
            requests.put(f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}",
                        json={"messages":msgs},
                        headers={"Content-Type":"application/json","X-Master-Key":JSONBIN_KEY}, timeout=3)
        except: pass
    sj(MESSAGES_FILE, msgs)

def ft(ts):
    try:
        t = datetime.fromisoformat(ts)
        d = (datetime.now()-t).seconds
        if d<60: return "now"
        if d<3600: return f"{d//60}m"
        if d<86400: return f"{d//3600}h"
        return t.strftime("%b %d")
    except: return ""

def send_msg(text, att=None, att_name=None):
    if not text and not att: return
    text = sh(text.strip())[:1000] if text else ""
    msgs = lm()
    msg = {"id":str(uuid.uuid4()), "username":st.session_state.username, "text":text,
           "timestamp":datetime.now().isoformat(), "reactions":{}}
    if att:
        msg["attachment"] = att
        msg["attachment_name"] = att_name
        msg["attachment_type"] = "img" if att_name.lower().endswith(('.png','.jpg','.jpeg','.gif')) else "file"
    msgs.append(msg)
    sm(msgs)
    st.session_state.messages = msgs

def react(msg_id, emoji):
    msgs = lm()
    for m in msgs:
        if m.get("id")==msg_id:
            if "reactions" not in m: m["reactions"]={}
            if emoji not in m["reactions"]: m["reactions"][emoji]=[]
            u = st.session_state.username
            if u in m["reactions"][emoji]: m["reactions"][emoji].remove(u)
            else: m["reactions"][emoji].append(u)
            if not m["reactions"][emoji]: del m["reactions"][emoji]
            if not m["reactions"]: del m["reactions"]
            break
    sm(msgs)
    st.session_state.messages = msgs

def del_msg(msg_id):
    msgs = [m for m in lm() if m.get("id")!=msg_id]
    sm(msgs)
    st.session_state.messages = msgs

def edit_msg(msg_id, txt):
    txt = sh(txt.strip())
    if not txt: return
    msgs = lm()
    for m in msgs:
        if m.get("id")==msg_id: m["text"]=txt; m["edited"]=True; break
    sm(msgs)
    st.session_state.messages = msgs

def sign_up(u, p, c):
    if not u or not p: return False, "Fill all fields"
    if p!=c: return False, "Passwords don't match"
    if len(p)<4: return False, "Password too short"
    if len(u)<2 or len(u)>20: return False, "Username 2-20 chars"
    if not u.isalnum(): return False, "Only letters/numbers"
    users = lu()
    if u.lower() in [x.lower() for x in users]: return False, "Username exists"
    users[u] = hp(p)
    su(users)
    prof = lp()
    prof[u] = {"bio":"","avatar":None,"wallpaper":DEFAULT_WP,"status":"","last_seen":datetime.now().isoformat()}
    sp(prof)
    return True, "Created! Sign in."

def sign_in(u, p):
    users = lu()
    for un, pw in users.items():
        if un.lower()==u.lower():
            return (True, un) if pw==hp(p) else (False, "Wrong password")
    return False, "User not found"

# ========== SESSION ==========
if 'init' not in st.session_state:
    st.session_state.messages = lm()
    st.session_state.auth = False
    st.session_state.user = ""
    st.session_state.wp = DEFAULT_WP
    st.session_state.view = "chat"
    st.session_state.edit_id = None
    st.session_state.reply_to = None
    st.session_state.vp = None
    st.session_state.init = True

if st.session_state.get('auth'):
    st.session_state.messages = lm()
    st.session_state.wp = gup(st.session_state.user).get("wallpaper", DEFAULT_WP)
    # Update last seen
    p = lp()
    if st.session_state.user in p:
        p[st.session_state.user]["last_seen"] = datetime.now().isoformat()
        sp(p)

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

# ========== AUTH ==========
if not st.session_state.auth:
    c1,c2,c3 = st.columns([1,2,1])
    with c2:
        st.markdown('<div style="text-align:center;padding:2rem"><div style="font-size:4rem">💬</div><h1 style="color:white;background:linear-gradient(135deg,#667eea,#764ba2,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent">Chattier Pro</h1></div>', unsafe_allow_html=True)
        t1,t2 = st.tabs(["Sign In","Sign Up"])
        with t1:
            with st.form("li"):
                u=st.text_input("Username"); p=st.text_input("Password",type="password")
                if st.form_submit_button("Sign In",use_container_width=True):
                    ok,r=sign_in(u,p)
                    if ok: st.session_state.auth=True; st.session_state.user=r; st.rerun()
                    else: st.error(r)
        with t2:
            with st.form("su"):
                u=st.text_input("Username"); p=st.text_input("Password",type="password"); c=st.text_input("Confirm",type="password")
                if st.form_submit_button("Create Account",use_container_width=True):
                    ok,r=sign_up(u,p,c)
                    if ok: st.success(r)
                    else: st.error(r)
else:
    # ========== SIDEBAR ==========
    with st.sidebar:
        st.markdown(f'<div style="text-align:center"><div style="font-size:2.5rem">💬</div><h3>Chattier Pro</h3></div>', unsafe_allow_html=True)
        pd = gup(st.session_state.user)
        st.markdown(f'<div style="text-align:center">{gav(st.session_state.user,60)}<h4>@{st.session_state.user}</h4><p style="font-size:0.7rem;opacity:0.9">{sh(pd.get("status","No status"))[:50]}</p></div>', unsafe_allow_html=True)
        st.divider()
        
        if st.button("💬 Chat", use_container_width=True): st.session_state.view="chat"; st.rerun()
        if st.button("👤 Profile", use_container_width=True): st.session_state.view="profile"; st.rerun()
        if st.button("👥 Members", use_container_width=True): st.session_state.view="members"; st.rerun()
        if st.button("🎨 Themes", use_container_width=True): st.session_state.view="themes"; st.rerun()
        st.divider()
        st.caption(f"Messages: {len(st.session_state.messages)}")
        st.caption(f"Members: {len(set(m['username'] for m in st.session_state.messages)) if st.session_state.messages else 0}")
        st.divider()
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.auth=False; st.session_state.user=""; st.rerun()
    
    # ========== CHAT ==========
    if st.session_state.view == "chat":
        st.markdown('<h3 style="color:white">💬 Community Chat</h3>', unsafe_allow_html=True)
        
        if not st.session_state.messages:
            st.markdown('<div style="text-align:center;padding:3rem;color:#94a3b8"><div style="font-size:3rem">✨</div><p>No messages yet</p></div>', unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages[-20:]:
                own = msg["username"]==st.session_state.user
                mid = msg.get("id","")
                cls = "s" if own else "r"
                
                if st.session_state.get("edit_id")==mid:
                    with st.form(key=f"e_{mid}"):
                        nt=st.text_input("Edit",value=msg['text'],label_visibility="collapsed")
                        if st.form_submit_button("Save"): edit_msg(mid,nt); st.session_state.edit_id=None; st.rerun()
                else:
                    ed = ' <small style="color:#94a3b8">(edited)</small>' if msg.get("edited") else ""
                    st.markdown(f'<div class="msg {cls}"><div style="flex-shrink:0;align-self:flex-end;margin:{0 if own else "0 0.3rem 0 0" if not own else "0 0 0 0.3rem"}">{gav(msg["username"],25)}</div><div style="max-width:70%"><div class="bub"><span class="un">{sh(msg["username"])}</span> <span class="tm">• {ft(msg.get("timestamp",""))}{ed}</span>{f"<div class='tx'>{msg['text']}</div>" if msg.get("text") else ""}{f"<img src='{msg['attachment']}' class='att' />" if msg.get("attachment","") and msg.get("attachment_type")=="img" else ""}{f"<a href='{msg['attachment']}' target='_blank'>📎 {msg.get('attachment_name','')}</a>" if msg.get("attachment","") and msg.get("attachment_type")!="img" else ""}</div>', unsafe_allow_html=True)
                    
                    # Actions
                    c1,c2,c3,c4,c5 = st.columns([1,1,1,1,8])
                    with c1:
                        if st.button("👍",key=f"l_{mid}"): react(mid,"👍"); st.rerun()
                    with c2:
                        if st.button("❤️",key=f"h_{mid}"): react(mid,"❤️"); st.rerun()
                    with c3:
                        if st.button("↩️",key=f"r_{mid}"): st.session_state.reply_to=mid; st.rerun()
                    if own:
                        with c4:
                            if st.button("✏️",key=f"ed_{mid}"): st.session_state.edit_id=mid; st.rerun()
                    
                    # Reactions
                    if msg.get("reactions"):
                        rh = '<div style="margin-top:0.2rem">'
                        for em,users in msg["reactions"].items():
                            rh += f'<span style="background:rgba(255,255,255,{0.3 if st.session_state.user in users else 0.1});padding:0.1rem 0.3rem;border-radius:0.5rem;font-size:0.7rem;margin:0.1rem">{em} {len(users)}</span>'
                        rh += '</div>'
                        st.markdown(rh, unsafe_allow_html=True)
                    
                    if own:
                        if st.button("🗑️",key=f"d_{mid}"): del_msg(mid); st.rerun()
                    st.markdown('</div></div>', unsafe_allow_html=True)
        
        # Reply
        if st.session_state.get("reply_to"):
            rm = next((m for m in st.session_state.messages if m.get("id")==st.session_state.reply_to), None)
            if rm:
                st.info(f"↩️ Replying to {rm['username']}")
                if st.button("Cancel"): st.session_state.reply_to=None; st.rerun()
        
        # Emoji picker
        with st.expander("😊 Emojis"):
            ec = st.columns(15)
            for i,emo in enumerate(EMOJIS):
                with ec[i%15]:
                    if st.button(emo, key=f"em_{i}"):
                        st.session_state.emoji_pick = emo
                        st.rerun()
        
        # Input
        st.divider()
        with st.form("mf", clear_on_submit=True):
            dv = st.session_state.get('emoji_pick','')
            if dv: st.session_state.emoji_pick=''
            c1,c2,c3 = st.columns([5,1,1])
            with c1:
                txt = st.text_input("Message", placeholder=f"Type as @{st.session_state.user}...", label_visibility="collapsed", value=dv)
            with c2:
                fl = st.file_uploader("📎", type=['png','jpg','jpeg','gif','pdf','txt'], label_visibility="collapsed")
            with c3:
                sb = st.form_submit_button("📤", use_container_width=True)
            if sb:
                ad,an = None,None
                if fl:
                    try:
                        fb = fl.read()
                        ad = base64.b64encode(fb).decode()
                        an = fl.name
                    except: pass
                if txt.strip() or ad:
                    send_msg(txt, ad, an)
                    st.rerun()
    
    # ========== PROFILE ==========
    elif st.session_state.view == "profile":
        st.markdown('<h3 style="color:white">👤 My Profile</h3>', unsafe_allow_html=True)
        c1,c2 = st.columns([1,2])
        with c1:
            st.markdown(f'<div class="card">{gav(st.session_state.user,100)}<h4>@{st.session_state.user}</h4></div>', unsafe_allow_html=True)
            av = st.file_uploader("Avatar", type=['png','jpg','jpeg'], label_visibility="collapsed")
        with c2:
            with st.form("pf"):
                pd = gup(st.session_state.user)
                bio = st.text_area("Bio", value=pd.get("bio",""), max_chars=200, height=80)
                status = st.text_input("Status", value=pd.get("status",""), max_chars=60, placeholder="What's on your mind?")
                if st.form_submit_button("💾 Save", use_container_width=True):
                    up(st.session_state.user, bio, av, st.session_state.wp, status)
                    st.success("Saved!")
                    time.sleep(0.5)
                    st.rerun()
    
    # ========== MEMBERS ==========
    elif st.session_state.view == "members":
        if st.session_state.get("vp"):
            v = st.session_state.vp
            p = gup(v)
            st.markdown(f'<h3 style="color:white">👤 {sh(v)}</h3>', unsafe_allow_html=True)
            if st.button("↩️ Back"): st.session_state.vp=None; st.rerun()
            c1,c2 = st.columns([1,2])
            with c1:
                ls = p.get("last_seen","")
                on = False
                if ls:
                    try: on = (datetime.now()-datetime.fromisoformat(ls)).seconds<300
                    except: pass
                st.markdown(f'<div class="card">{gav(v,80)}<h4>@{sh(v)}</h4><span class="dot {"on" if on else "off"}"></span>{"Online" if on else "Offline"}<p style="color:#94a3b8;font-size:0.8rem">{sh(p.get("status","No status"))}</p></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div style="background:rgba(255,255,255,0.05);padding:1rem;border-radius:0.5rem"><p style="color:#f8fafc">{sh(p.get("bio","No bio"))}</p></div>', unsafe_allow_html=True)
                ums = [m for m in st.session_state.messages if m["username"]==v][-5:]
                if ums:
                    st.markdown("**Recent messages:**")
                    for m in reversed(ums):
                        st.markdown(f'<div style="background:rgba(255,255,255,0.05);padding:0.5rem;border-radius:0.5rem;margin:0.2rem 0"><small style="color:#94a3b8">{ft(m.get("timestamp",""))}</small><p style="color:#f8fafc;margin:0.2rem 0">{m.get("text","")}</p></div>', unsafe_allow_html=True)
        else:
            st.markdown('<h3 style="color:white">👥 Members</h3>', unsafe_allow_html=True)
            users = list(set([m["username"] for m in st.session_state.messages])) if st.session_state.messages else []
            if not users: st.info("No members yet")
            else:
                q = st.text_input("🔍 Search")
                fu = [u for u in users if q.lower() in u.lower()] if q else users
                for i,u in enumerate(fu[:30]):
                    if i%3==0: cols=st.columns(3)
                    p = gup(u)
                    ls = p.get("last_seen","")
                    on = False
                    if ls:
                        try: on = (datetime.now()-datetime.fromisoformat(ls)).seconds<300
                        except: pass
                    with cols[i%3]:
                        st.markdown(f'<div class="card">{gav(u,50)}<h4>@{sh(u)}</h4><span class="dot {"on" if on else "off"}"></span>{"Online" if on else "Offline"}<p style="font-size:0.7rem;color:#94a3b8">{sh(p.get("status",""))[:30]}</p></div>', unsafe_allow_html=True)
                        if st.button("View", key=f"v_{u}", use_container_width=True):
                            st.session_state.vp = u
                            st.rerun()
    
    # ========== THEMES ==========
    elif st.session_state.view == "themes":
        st.markdown(f'<h3 style="color:white">🎨 Themes ({len(WALLPAPERS)})</h3>', unsafe_allow_html=True)
        items = list(WALLPAPERS.items())
        for i,(n,u) in enumerate(items):
            if i%5==0: cols=st.columns(5)
            sel = n==st.session_state.wp
            with cols[i%5]:
                if u=="gradient":
                    st.markdown(f'<div style="background:linear-gradient(135deg,#667eea,#764ba2,#f093fb,#f5576c,#4facfe);height:80px;border-radius:0.5rem;border:2px solid {"#667eea" if sel else "rgba(255,255,255,0.1)"};margin-bottom:0.3rem;display:flex;align-items:center;justify-content:center;font-size:2rem">🌈</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div style="background-image:url({u});background-size:cover;height:80px;border-radius:0.5rem;border:2px solid {"#667eea" if sel else "rgba(255,255,255,0.1)"};margin-bottom:0.3rem"></div>', unsafe_allow_html=True)
                if st.button(f"{'✅' if sel else ''} {n}", key=f"th_{i}", use_container_width=True):
                    st.session_state.wp = n
                    p = lp()
                    if st.session_state.user in p: p[st.session_state.user]["wallpaper"]=n
                    sp(p)
                    st.rerun()

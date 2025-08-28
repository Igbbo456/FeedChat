import streamlit as st
import sqlite3, io, datetime
from PIL import Image
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

DB_FILE = "feedchat.db"

# ==============================
# DATABASE HELPERS (per-query connection)
# ==============================
def run_query(query, params=(), fetch=False, fetchone=False):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        if fetch:
            return c.fetchall()
        if fetchone:
            return c.fetchone()

# ==============================
# INITIALIZE TABLES
# ==============================
TABLES = [
    """CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        profile_pic BLOB
    )""",
    """CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT,
        media BLOB,
        media_type TEXT,
        timestamp TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS likes (
        post_id INTEGER,
        username TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        username TEXT,
        comment TEXT,
        timestamp TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS follows (
        follower TEXT,
        following TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        message TEXT,
        timestamp TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT,
        timestamp TEXT,
        seen INTEGER
    )"""
]

for t in TABLES:
    run_query(t)

# ==============================
# USER MANAGEMENT
# ==============================
def add_user(username, password, profile_pic=None):
    try:
        run_query("INSERT INTO users (username, password, profile_pic) VALUES (?, ?, ?)",
                  (username, password, profile_pic))
    except sqlite3.IntegrityError:
        pass

def verify_user(username, password):
    r = run_query("SELECT 1 FROM users WHERE username=? AND password=?",
                  (username, password), fetchone=True)
    return r is not None

def get_user(username):
    return run_query("SELECT username, profile_pic FROM users WHERE username=?",
                     (username,), fetchone=True)

# ==============================
# POSTS
# ==============================
def add_post(username, message, media=None, media_type=None):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_query("INSERT INTO posts (username,message,media,media_type,timestamp) VALUES (?,?,?,?,?)",
              (username, message, media, media_type, ts))
    # Notify followers
    followers = run_query("SELECT follower FROM follows WHERE following=?", (username,), fetch=True)
    for (f,) in followers:
        add_notification(f, f"{username} posted: {(message or '')[:80]}")

def get_posts():
    return run_query("SELECT id, username, message, media, media_type, timestamp FROM posts ORDER BY id DESC",
                     fetch=True)

# ==============================
# LIKES
# ==============================
def like_post_db(post_id, username):
    if not has_liked(post_id, username):
        run_query("INSERT INTO likes (post_id, username) VALUES (?,?)", (post_id, username))

def unlike_post_db(post_id, username):
    run_query("DELETE FROM likes WHERE post_id=? AND username=?", (post_id, username))

def has_liked(post_id, username):
    r = run_query("SELECT 1 FROM likes WHERE post_id=? AND username=?", (post_id, username), fetchone=True)
    return r is not None

def count_likes(post_id):
    r = run_query("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,), fetchone=True)
    return r[0] if r else 0

# ==============================
# COMMENTS
# ==============================
def add_comment(post_id, username, comment):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_query("INSERT INTO comments (post_id, username, comment, timestamp) VALUES (?,?,?,?)",
              (post_id, username, comment, ts))

def get_comments(post_id):
    return run_query("SELECT username, comment, timestamp FROM comments WHERE post_id=? ORDER BY id ASC",
                     (post_id,), fetch=True)

# ==============================
# FOLLOWS
# ==============================
def follow_user(follower, following):
    if follower==following:
        return
    if not is_following(follower, following):
        run_query("INSERT INTO follows (follower, following) VALUES (?,?)", (follower, following))

def unfollow_user(follower, following):
    run_query("DELETE FROM follows WHERE follower=? AND following=?", (follower, following))

def is_following(follower, following):
    r = run_query("SELECT 1 FROM follows WHERE follower=? AND following=?", (follower, following), fetchone=True)
    return r is not None

def get_followers(username):
    return [r[0] for r in run_query("SELECT follower FROM follows WHERE following=?", (username,), fetch=True)]

def get_following(username):
    return [r[0] for r in run_query("SELECT following FROM follows WHERE follower=?", (username,), fetch=True)]

# ==============================
# MESSAGES
# ==============================
def send_message(sender, receiver, message):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_query("INSERT INTO messages (sender,receiver,message,timestamp) VALUES (?,?,?,?)",
              (sender, receiver, message, ts))
    add_notification(receiver, f"New message from {sender}")

def get_messages(user1, user2):
    return run_query("""SELECT sender,message,timestamp FROM messages
                        WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
                        ORDER BY id ASC""",
                     (user1,user2,user2,user1), fetch=True)

# ==============================
# NOTIFICATIONS
# ==============================
def add_notification(username, message):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_query("INSERT INTO notifications (username,message,timestamp,seen) VALUES (?,?,?,0)",
              (username, message, ts))

def get_notifications(username):
    return run_query("SELECT id,message,timestamp,seen FROM notifications WHERE username=? ORDER BY id DESC",
                     (username,), fetch=True)

def mark_notifications_seen(username):
    run_query("UPDATE notifications SET seen=1 WHERE username=?", (username,))

def count_unseen(username):
    r = run_query("SELECT COUNT(*) FROM notifications WHERE username=? AND seen=0",
                  (username,), fetchone=True)
    return r[0] if r else 0

# ==============================
# VIDEO CALL (WebRTC)
# ==============================
class VideoCall(VideoTransformerBase):
    def transform(self, frame):
        return frame.to_ndarray(format="bgr24")

def start_video_call():
    st.header("📹 Video Call")
    webrtc_streamer(key="video_call", video_transformer_factory=VideoCall)

# ==============================
# STREAMLIT UI
# ==============================
st.set_page_config(page_title="FeedChat", layout="wide")
st.title("📘 FeedChat")

# SESSION DEFAULTS
if "username" not in st.session_state:
    st.session_state.username = None
if "view_profile" not in st.session_state:
    st.session_state.view_profile = None

# ------------------------------
# AUTHENTICATION
# ------------------------------
if not st.session_state.username:
    st.sidebar.header("Login / Register")
    choice = st.sidebar.selectbox("I want to:", ["Login","Register"])
    if choice=="Register":
        new_user = st.sidebar.text_input("Username", key="reg_user")
        new_pass = st.sidebar.text_input("Password", type="password", key="reg_pass")
        new_pic = st.sidebar.file_uploader("Profile picture (optional)", type=["png","jpg","jpeg"], key="reg_pic")
        if st.sidebar.button("Register"):
            if not new_user.strip() or not new_pass.strip():
                st.sidebar.error("Provide username and password.")
            else:
                pic_bytes = new_pic.read() if new_pic else None
                add_user(new_user.strip(), new_pass.strip(), pic_bytes)
                st.sidebar.success("Account created — now log in.")
    else:
        user = st.sidebar.text_input("Username", key="login_user")
        pw = st.sidebar.text_input("Password", type="password", key="login_pw")
        if st.sidebar.button("Login"):
            if verify_user(user, pw):
                st.session_state.username = user
                st.experimental_rerun()
            else:
                st.sidebar.error("Invalid credentials.")
    st.stop()

# ------------------------------
# TOP BAR
# ------------------------------
col_left, col_right = st.columns([8,1])
with col_left:
    st.write(f"Logged in as **{st.session_state.username}**")
with col_right:
    if st.button("Logout"):
        st.session_state.username = None
        st.session_state.view_profile = None
        st.experimental_rerun()

# ------------------------------
# HOME / FEED
# ------------------------------
st.header("📰 Home / Feed")
with st.expander("✍️ Create Post"):
    post_text = st.text_area("What's on your mind?", key="home_post_text")
    media_file = st.file_uploader("Upload image/video (optional)", type=["png","jpg","jpeg","mp4","mov","avi"], key="home_media")
    media_bytes, media_type = None, None
    if media_file:
        if media_file.type.startswith("image") or media_file.name.lower().endswith((".png",".jpg",".jpeg")):
            img = Image.open(media_file)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            media_bytes = buf.getvalue()
            media_type = "image"
        else:
            media_bytes = media_file.read()
            media_type = "video"
    if st.button("Post", key="home_post_btn"):
        if not (post_text.strip() or media_bytes):
            st.warning("Write something or upload media.")
        else:
            add_post(st.session_state.username, post_text.strip(), media_bytes, media_type)
            st.success("Posted!")
            st.experimental_rerun()

# Display feed
posts = get_posts()
for pid, user, msg, media, mtype, ts in posts:
    st.markdown(f"**{user}** · _{ts}_")
    if msg: st.write(msg)
    if media and mtype=="image": st.image(media, use_container_width=True)
    elif media and mtype=="video": st.video(media)
    st.write(f"👍 {count_likes(pid)} · 💬 {len(get_comments(pid))}")

# ------------------------------
# VIDEO CALL BUTTON
# ------------------------------
if st.sidebar.button("Start Video Call"):
    start_video_call()

import streamlit as st
import sqlite3, io
from PIL import Image
import datetime

# ==============================
# DATABASE SETUP
# ==============================
conn = sqlite3.connect("feedchat.db", check_same_thread=False)
c = conn.cursor()

# Users
c.execute("""CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    profile_pic BLOB
)""")

# Posts (media can be image or video)
c.execute("""CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    message TEXT,
    media BLOB,
    media_type TEXT,
    timestamp TEXT
)""")

# Likes
c.execute("""CREATE TABLE IF NOT EXISTS likes (
    post_id INTEGER,
    username TEXT
)""")

# Comments
c.execute("""CREATE TABLE IF NOT EXISTS comments (
    post_id INTEGER,
    username TEXT,
    comment TEXT,
    timestamp TEXT
)""")

# Follows
c.execute("""CREATE TABLE IF NOT EXISTS follows (
    follower TEXT,
    following TEXT
)""")

# Messages
c.execute("""CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    message TEXT,
    timestamp TEXT
)""")

# Notifications
c.execute("""CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    message TEXT,
    timestamp TEXT,
    seen INTEGER
)""")

conn.commit()

# ==============================
# HELPER FUNCTIONS
# ==============================

# User management
def add_user(username, password, profile_pic=None):
    try:
        c.execute(
            "INSERT INTO users (username, password, profile_pic) VALUES (?, ?, ?)",
            (username, password, profile_pic)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        st.sidebar.error("Username already exists!")

def get_user(username):
    c.execute("SELECT username, profile_pic FROM users WHERE username=?", (username,))
    return c.fetchone()

def verify_user(username, password):
    c.execute("SELECT 1 FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone() is not None

# Posts
def add_post(username, message, media=None, media_type=None):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT INTO posts (username, message, media, media_type, timestamp) VALUES (?, ?, ?, ?, ?)",
        (username, message, media, media_type, ts)
    )
    conn.commit()
    # notify followers
    c.execute("SELECT follower FROM follows WHERE following=?", (username,))
    followers = c.fetchall()
    for (f,) in followers:
        add_notification(f, f"{username} posted: { (message or '')[:80] }")

def get_posts():
    c.execute("SELECT id, username, message, media, media_type, timestamp FROM posts ORDER BY id DESC")
    return c.fetchall()

# Likes
def like_post_db(post_id, username):
    if not has_liked(post_id, username):
        c.execute("INSERT INTO likes (post_id, username) VALUES (?, ?)", (post_id, username))
        conn.commit()

def unlike_post_db(post_id, username):
    c.execute("DELETE FROM likes WHERE post_id=? AND username=?", (post_id, username))
    conn.commit()

def has_liked(post_id, username):
    c.execute("SELECT 1 FROM likes WHERE post_id=? AND username=?", (post_id, username))
    return c.fetchone() is not None

def count_likes(post_id):
    c.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,))
    r = c.fetchone()
    return r[0] if r else 0

# Comments
def add_comment(post_id, username, comment):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO comments (post_id, username, comment, timestamp) VALUES (?, ?, ?, ?)",
              (post_id, username, comment, ts))
    conn.commit()

def get_comments(post_id):
    c.execute("SELECT username, comment, timestamp FROM comments WHERE post_id=? ORDER BY rowid ASC", (post_id,))
    return c.fetchall()

# Follows
def follow_user(follower, following):
    if follower == following: 
        return
    if not is_following(follower, following):
        c.execute("INSERT INTO follows (follower, following) VALUES (?, ?)", (follower, following))
        conn.commit()

def unfollow_user(follower, following):
    c.execute("DELETE FROM follows WHERE follower=? AND following=?", (follower, following))
    conn.commit()

def is_following(follower, following):
    c.execute("SELECT 1 FROM follows WHERE follower=? AND following=?", (follower, following))
    return c.fetchone() is not None

def get_followers(username):
    c.execute("SELECT follower FROM follows WHERE following=?", (username,))
    return [r[0] for r in c.fetchall()]

def get_following(username):
    c.execute("SELECT following FROM follows WHERE follower=?", (username,))
    return [r[0] for r in c.fetchall()]

# Messages
def send_message(sender, receiver, message):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO messages (sender, receiver, message, timestamp) VALUES (?, ?, ?, ?)",
              (sender, receiver, message, ts))
    conn.commit()
    add_notification(receiver, f"New message from {sender}")

def get_messages(user1, user2):
    c.execute("""SELECT sender, message, timestamp FROM messages
                 WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
                 ORDER BY id ASC""", (user1, user2, user2, user1))
    return c.fetchall()

# Notifications
def add_notification(username, message):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO notifications (username, message, timestamp, seen) VALUES (?, ?, ?, 0)",
              (username, message, ts))
    conn.commit()

def get_notifications(username):
    c.execute("SELECT id, message, timestamp, seen FROM notifications WHERE username=? ORDER BY id DESC", (username,))
    return c.fetchall()

def mark_notifications_seen(username):
    c.execute("UPDATE notifications SET seen=1 WHERE username=?", (username,))
    conn.commit()

def count_total_likes(username):
    c.execute("""SELECT COUNT(*) FROM likes JOIN posts ON likes.post_id = posts.id WHERE posts.username=?""", (username,))
    r = c.fetchone()
    return r[0] if r else 0

# Sound
def play_sound(sound_url):
    st.markdown(f"""
    <audio autoplay="true">
        <source src="{sound_url}" type="audio/mp3">
    </audio>
    """, unsafe_allow_html=True)

# ==============================
# STREAMLIT UI
# ==============================
st.set_page_config(page_title="FeedChat", layout="wide")
st.title("📘 FeedChat")

# Session defaults
if "username" not in st.session_state:
    st.session_state.username = None
if "view_profile" not in st.session_state:
    st.session_state.view_profile = None
if "notified" not in st.session_state:
    st.session_state.notified = False

# -----------------------------
# AUTHENTICATION
# -----------------------------
if not st.session_state.username:
    st.sidebar.header("Login / Register")
    choice = st.sidebar.selectbox("I want to:", ["Login", "Register"])
    
    if choice == "Register":
        st.sidebar.subheader("Create account")
        new_user = st.sidebar.text_input("Username", key="reg_user")
        new_pass = st.sidebar.text_input("Password", type="password", key="reg_pass")
        new_pic = st.sidebar.file_uploader("Profile picture (optional)", type=["png","jpg","jpeg"], key="reg_pic")
        if st.sidebar.button("Register"):
            if not new_user.strip() or not new_pass:
                st.sidebar.error("Provide username and password.")
            else:
                # SAFE PROFILE PICTURE HANDLING
                pic_bytes = None
                if new_pic is not None:
                    try:
                        pic_bytes = new_pic.read()
                    except Exception:
                        st.sidebar.warning("Failed to read profile picture.")
                add_user(new_user.strip(), new_pass, pic_bytes)
                st.sidebar.success("Account created — now log in.")
    else:
        st.sidebar.subheader("Log in")
        user = st.sidebar.text_input("Username", key="login_user")
        pw = st.sidebar.text_input("Password", type="password", key="login_pw")
        if st.sidebar.button("Login"):
            if verify_user(user, pw):
                st.session_state.username = user
                st.experimental_rerun()
            else:
                st.sidebar.error("Invalid credentials.")
    st.stop()

# -----------------------------
# TOP BAR + LOGOUT
# -----------------------------
col_left, col_right = st.columns([8,1])
with col_left:
    st.write(f"Logged in as **{st.session_state.username}**")
with col_right:
    if st.button("Logout"):
        st.session_state.username = None
        st.session_state.view_profile = None
        st.session_state.notified = False
        st.experimental_rerun()

# -----------------------------
# NOTIFICATIONS SOUND
# -----------------------------
notes = get_notifications(st.session_state.username)
unseen_notes = [n for n in notes if n[3]==0]
if unseen_notes and not st.session_state.notified:
    play_sound("https://www.soundjay.com/buttons/sounds/button-3.mp3")
    st.session_state.notified = True

# -----------------------------
# HOME / FEED
# -----------------------------
st.header("📰 Home / News Feed")
with st.expander("✍️ Create a post"):
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

# -----------------------------
# DISPLAY FEED
# -----------------------------
posts = get_posts()
if not posts:
    st.info("No posts yet.")
else:
    for pid, user, msg, media, mtype, ts in posts:
        card = st.container()
        with card:
            col1, col2 = st.columns([1,9])
            with col1:
                u = get_user(user)
                if u and u[1]:
                    st.image(io.BytesIO(u[1]), width=60)
                else:
                    st.write("👤")
            with col2:
                st.markdown(f"**{user}**  ·  _{ts}_")
                if msg:
                    st.write(msg)
                if media and mtype=="image":
                    st.image(io.BytesIO(media), use_container_width=True)
                elif media and mtype=="video":
                    st.video(io.BytesIO(media))

                # Like / Unlike
                like_col, info_col = st.columns([1,4])
                with like_col:
                    if has_liked(pid, st.session_state.username):
                        if st.button(f"Unlike ({count_likes(pid)})", key=f"unlike_{pid}"):
                            unlike_post_db(pid, st.session_state.username)
                            st.experimental_rerun()
                    else:
                        if st.button(f"Like ({count_likes(pid)})", key=f"like_{pid}"):
                            like_post_db(pid, st.session_state.username)
                            st.experimental_rerun()
                with info_col:
                    st.write(f"👍 {count_likes(pid)}  ·  💬 {len(get_comments(pid))}")

                # Comments
                st.markdown("**Comments**")
                for cu, cm, ct in get_comments(pid):
                    cu_user = get_user(cu)
                    cols = st.columns([1,9])
                    if cu_user and cu_user[1]:
                        cols[0].image(io.BytesIO(cu_user[1]), width=30)
                    cols[1].markdown(f"**{cu}**: {cm}  _({ct})_")

                comment_text = st.text_input("Add a comment", key=f"comment_input_{pid}")
                if st.button("Post comment", key=f"comment_btn_{pid}"):
                    if comment_text.strip():
                        add_comment(pid, st.session_state.username, comment_text.strip())
                        st.experimental_rerun()

        st.markdown("---")

# -----------------------------
# PROFILE, MESSAGES, NOTIFICATIONS
# -----------------------------
# (Rest of your previous code stays the same, but make sure to wrap BLOBs in io.BytesIO)

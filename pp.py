import streamlit as st
import sqlite3
import datetime
# import av   # ❌ Disabled for now (causing crash)
# from streamlit_webrtc import webrtc_streamer, VideoTransformerBase  # ❌ Disabled

# ==============================
# 📦 Database Setup
# ==============================
conn = sqlite3.connect("feedchat.db", check_same_thread=False)
c = conn.cursor()

# --- Users table ---
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    profile_pic BLOB
)
""")

# --- Posts table ---
c.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    message TEXT,
    media BLOB,
    media_type TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# --- Comments table ---
c.execute("""
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    username TEXT,
    comment TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts (id)
)
""")

# --- Likes table ---
c.execute("""
CREATE TABLE IF NOT EXISTS likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    username TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts (id)
)
""")

# --- Notifications table ---
c.execute("""
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    seen INTEGER DEFAULT 0
)
""")

conn.commit()

# ==============================
# 👤 User Functions
# ==============================
def add_user(username, password, profile_pic=None):
    c.execute("INSERT OR REPLACE INTO users (username, password, profile_pic) VALUES (?, ?, ?)",
              (username, password, profile_pic))
    conn.commit()

def verify_user(username, password):
    c.execute("SELECT 1 FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone() is not None

# ==============================
# 📬 Posts, Comments & Likes
# ==============================
def add_post(username, message, media=None, media_type=None):
    c.execute("INSERT INTO posts (username, message, media, media_type) VALUES (?, ?, ?, ?)",
              (username, message, media, media_type))
    conn.commit()

def get_posts():
    c.execute("SELECT id, username, message, timestamp FROM posts ORDER BY id DESC")
    return c.fetchall()

def add_comment(post_id, username, comment):
    c.execute("INSERT INTO comments (post_id, username, comment) VALUES (?, ?, ?)",
              (post_id, username, comment))
    conn.commit()

def get_comments(post_id):
    c.execute("SELECT username, comment, timestamp FROM comments WHERE post_id=? ORDER BY id ASC", (post_id,))
    return c.fetchall()

def add_like(post_id, username):
    c.execute("INSERT INTO likes (post_id, username) VALUES (?, ?)", (post_id, username))
    conn.commit()

def count_likes(post_id):
    c.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,))
    return c.fetchone()[0]

# ==============================
# 🎥 Video Call (DISABLED for Presentation)
# ==============================
# class VideoTransformer(VideoTransformerBase):
#     def transform(self, frame):
#         img = frame.to_ndarray(format="bgr24")
#         return av.VideoFrame.from_ndarray(img, format="bgr24")

# ==============================
# 🌐 Streamlit App
# ==============================
st.set_page_config(page_title="📱 FeedChat", layout="wide")

menu = ["Login", "Signup", "Feed"]  # Removed "Video Call"
choice = st.sidebar.selectbox("Menu", menu)

# --- Signup ---
if choice == "Signup":
    st.subheader("Create a New Account")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")
    pic = st.file_uploader("Upload Profile Picture", type=["jpg", "png"])

    if st.button("Signup"):
        pic_bytes = pic.read() if pic else None
        add_user(new_user.strip(), new_pass, pic_bytes)
        st.success("✅ Account created! Go to Login.")

# --- Login ---
elif choice == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if verify_user(username, password):
            st.session_state["user"] = username
            st.success(f"Welcome {username} 👋")
        else:
            st.error("❌ Invalid username or password")

# --- Feed ---
elif choice == "Feed":
    if "user" not in st.session_state:
        st.warning("⚠️ Please login first.")
    else:
        st.subheader("📢 Feed")
        post_msg = st.text_area("What's happening?")
        if st.button("Post"):
            add_post(st.session_state["user"], post_msg)
            st.success("✅ Post added!")

        st.write("### Recent Posts")
        posts = get_posts()
        for pid, uname, msg, ts in posts:
            st.markdown(f"**{uname}** 🕒 {ts}")
            st.write(msg)

            st.write(f"👍 {count_likes(pid)}  ·  💬 {len(get_comments(pid))}")
            if st.button(f"Like {pid}"):
                add_like(pid, st.session_state["user"])
            comment = st.text_input(f"Comment on {pid}", key=f"c{pid}")
            if st.button(f"Add Comment {pid}"):
                add_comment(pid, st.session_state["user"], comment)
            with st.expander("View Comments"):
                for cu, cm, ct in get_comments(pid):
                    st.markdown(f"- **{cu}**: {cm} 🕒 {ct}")

# --- Video Call ---
# Disabled to prevent errors during presentation
# elif choice == "Video Call":
#     st.subheader("🎥 Video Chat Room")
#     webrtc_streamer(key="video", video_transformer_factory=VideoTransformer)

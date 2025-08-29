import streamlit as st
import sqlite3
import time
from datetime import datetime
from PIL import Image

# ======================
# Database Setup
# ======================
conn = sqlite3.connect("feedchat.db", check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute("""CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, profile_pic BLOB)""")
    c.execute("""CREATE TABLE IF NOT EXISTS posts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, content TEXT, timestamp TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS comments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER, username TEXT, comment TEXT, timestamp TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS likes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER, username TEXT)""")
    conn.commit()

init_db()

# ======================
# User Management
# ======================
def add_user(username, password, profile_pic):
    try:
        c.execute("INSERT INTO users (username, password, profile_pic) VALUES (?, ?, ?)",
                  (username, password, profile_pic))
        conn.commit()
    except sqlite3.IntegrityError:
        pass

def verify_user(username, password):
    c.execute("SELECT 1 FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone() is not None

# ======================
# Posts
# ======================
def add_post(username, content):
    c.execute("INSERT INTO posts (username, content, timestamp) VALUES (?, ?, ?)",
              (username, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_posts():
    c.execute("SELECT id, username, content, timestamp FROM posts ORDER BY id DESC")
    return c.fetchall()

def add_comment(post_id, username, comment):
    c.execute("INSERT INTO comments (post_id, username, comment, timestamp) VALUES (?, ?, ?, ?)",
              (post_id, username, comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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

# ======================
# Streamlit UI
# ======================
st.title("📱 FeedChat")

menu = ["Login", "Sign Up", "Feed"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Sign Up":
    st.subheader("Create New Account")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")
    profile_pic = st.file_uploader("Upload Profile Picture", type=["png", "jpg", "jpeg"])
    pic_bytes = profile_pic.read() if profile_pic else None
    if st.button("Sign Up"):
        add_user(new_user, new_pass, pic_bytes)
        st.success("Account created! Please login.")

elif choice == "Login":
    st.subheader("Login to FeedChat")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if verify_user(user, pw):
            st.session_state.username = user
            st.success(f"Welcome back {user}!")
        else:
            st.error("Invalid username or password")

elif choice == "Feed":
    if "username" not in st.session_state:
        st.warning("Please login first.")
    else:
        st.subheader("Your Feed")
        post_content = st.text_area("What's on your mind?")
        if st.button("Post"):
            if post_content.strip():
                add_post(st.session_state.username, post_content)
                st.success("Posted successfully!")
                time.sleep(1)
                st.experimental_rerun()

        posts = get_posts()
        for pid, uname, content, timestamp in posts:
            st.markdown(f"**{uname}** at {timestamp}")
            st.write(content)
            if st.button(f"👍 Like {pid}", key=f"like_{pid}"):
                add_like(pid, st.session_state.username)
                st.experimental_rerun()
            st.write(f"👍 {count_likes(pid)}  ·  💬 {len(get_comments(pid))}")

            with st.expander("Comments"):
                for cuser, comment, ctime in get_comments(pid):
                    st.markdown(f"**{cuser}** at {ctime}")
                    st.write(comment)
                new_comment = st.text_input("Add a comment:", key=f"comment_{pid}")
                if st.button("Submit", key=f"submit_{pid}"):
                    if new_comment.strip():
                        add_comment(pid, st.session_state.username, new_comment)
                        st.experimental_rerun()

# ======================
# NOTE: Video Call Disabled
# ======================
# The video call feature is disabled to prevent av/streamlit-webrtc errors
# Uncomment later if av is installed
# from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
# webrtc_streamer(key="video_call")

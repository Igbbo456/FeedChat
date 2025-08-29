import streamlit as st
import sqlite3
import base64
from datetime import datetime
from io import BytesIO
from PIL import Image

# ==============================
# ✅ Initialize Database
# ==============================
def init_db():
    conn = sqlite3.connect("feedchat.db")
    c = conn.cursor()

    # Users table (with profile_pic support)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            profile_pic BLOB
        )
    """)

    # Posts table
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            message TEXT,
            media BLOB,
            media_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Likes table
    c.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            username TEXT
        )
    """)

    # Comments table
    c.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            username TEXT,
            comment TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Follows table
    c.execute("""
        CREATE TABLE IF NOT EXISTS follows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            follower TEXT,
            following TEXT
        )
    """)

    # Notifications table
    c.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            message TEXT,
            seen INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# ✅ Run database setup
init_db()

# ==============================
# Database Functions
# ==============================
def add_user(username, password, profile_pic=None):
    conn = sqlite3.connect("feedchat.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, profile_pic) VALUES (?, ?, ?)",
                  (username, password, profile_pic))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def verify_user(username, password):
    conn = sqlite3.connect("feedchat.db")
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE username=? AND password=?", (username, password))
    valid = c.fetchone()
    conn.close()
    return valid is not None

def add_post(username, message, media=None, media_type=None):
    conn = sqlite3.connect("feedchat.db")
    c = conn.cursor()
    c.execute("INSERT INTO posts (username, message, media, media_type) VALUES (?, ?, ?, ?)",
              (username, message, media, media_type))
    conn.commit()
    conn.close()

def get_posts():
    conn = sqlite3.connect("feedchat.db")
    c = conn.cursor()
    c.execute("SELECT id, username, message, media, media_type, timestamp FROM posts ORDER BY id DESC")
    posts = c.fetchall()
    conn.close()
    return posts

def add_like(post_id, username):
    conn = sqlite3.connect("feedchat.db")
    c = conn.cursor()
    c.execute("INSERT INTO likes (post_id, username) VALUES (?, ?)", (post_id, username))
    conn.commit()
    conn.close()

def count_likes(post_id):
    conn = sqlite3.connect("feedchat.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def add_comment(post_id, username, comment):
    conn = sqlite3.connect("feedchat.db")
    c = conn.cursor()
    c.execute("INSERT INTO comments (post_id, username, comment) VALUES (?, ?, ?)",
              (post_id, username, comment))
    conn.commit()
    conn.close()

def get_comments(post_id):
    conn = sqlite3.connect("feedchat.db")
    c = conn.cursor()
    c.execute("SELECT username, comment, timestamp FROM comments WHERE post_id=? ORDER BY id ASC", (post_id,))
    comments = c.fetchall()
    conn.close()
    return comments

def add_follow(follower, following):
    conn = sqlite3.connect("feedchat.db")
    c = conn.cursor()
    c.execute("INSERT INTO follows (follower, following) VALUES (?, ?)", (follower, following))
    conn.commit()
    conn.close()

def add_notification(username, message):
    conn = sqlite3.connect("feedchat.db")
    c = conn.cursor()
    c.execute("INSERT INTO notifications (username, message) VALUES (?, ?)", (username, message))
    conn.commit()
    conn.close()

def get_notifications(username):
    conn = sqlite3.connect("feedchat.db")
    c = conn.cursor()
    c.execute("SELECT id, message, timestamp, seen FROM notifications WHERE username=? ORDER BY id DESC", (username,))
    notifs = c.fetchall()
    conn.close()
    return notifs

def count_unseen(username):
    conn = sqlite3.connect("feedchat.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM notifications WHERE username=? AND seen=0", (username,))
    count = c.fetchone()[0]
    conn.close()
    return count

# ==============================
# Streamlit UI
# ==============================
st.set_page_config(page_title="📱 FeedChat", layout="wide")

st.title("📱 FeedChat - Mini Social Network")

# Sidebar login/signup
menu = ["Login", "Sign Up"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Sign Up":
    st.subheader("Create a New Account")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")
    pic = st.file_uploader("Upload Profile Picture", type=["jpg", "png"])
    pic_bytes = pic.read() if pic else None

    if st.button("Sign Up"):
        add_user(new_user.strip(), new_pass, pic_bytes)
        st.success("✅ Account created! Please login.")

elif choice == "Login":
    st.subheader("Login to Your Account")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")

    if st.button("Login"):
        if verify_user(user, pw):
            st.session_state.username = user
            st.success(f"✅ Welcome {user}!")
        else:
            st.error("❌ Invalid username or password")

# Main app if logged in
if "username" in st.session_state:
    st.sidebar.subheader(f"👤 Logged in as {st.session_state.username}")

    tab1, tab2, tab3 = st.tabs(["🏠 Feed", "🔔 Notifications", "➕ New Post"])

    # Feed
    with tab1:
        posts = get_posts()
        for pid, uname, msg, media, media_type, ts in posts:
            st.markdown(f"**{uname}** · {ts}")
            if msg:
                st.write(msg)
            if media:
                if media_type == "image":
                    st.image(media)
                elif media_type == "video":
                    st.video(media)

            if st.button(f"👍 Like {pid}", key=f"like{pid}"):
                add_like(pid, st.session_state.username)
            with st.expander("💬 Comments"):
                comments = get_comments(pid)
                for cu, ct, cts in comments:
                    st.markdown(f"**{cu}**: {ct} ({cts})")
                comment_text = st.text_input("Add a comment:", key=f"c{pid}")
                if st.button("Post Comment", key=f"pc{pid}"):
                    add_comment(pid, st.session_state.username, comment_text)

            st.write(f"👍 {count_likes(pid)} · 💬 {len(get_comments(pid))}")
            st.divider()

    # Notifications
    with tab2:
        notifs = get_notifications(st.session_state.username)
        unseen = count_unseen(st.session_state.username)
        st.write(f"🔔 You have {unseen} unseen notifications")
        for nid, msg, nts, seen in notifs:
            st.markdown(f"- {msg} ({nts}) {'✅' if seen else '🆕'}")

    # New Post
    with tab3:
        msg = st.text_area("What's on your mind?")
        media_file = st.file_uploader("Upload media", type=["jpg", "png", "mp4", "mov"])
        media_bytes, media_type = None, None
        if media_file:
            media_bytes = media_file.read()
            if media_file.type.startswith("image"):
                media_type = "image"
            elif media_file.type.startswith("video"):
                media_type = "video"

        if st.button("Post"):
            add_post(st.session_state.username, msg, media_bytes, media_type)
            st.success("✅ Posted successfully!")

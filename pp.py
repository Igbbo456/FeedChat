import streamlit as st
import sqlite3
import datetime

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
# 🌐 Streamlit App
# ==============================
st.set_page_config(page_title="📱 FeedChat", layout="wide")

menu = ["Login", "Signup", "Feed"]
choice = st.sidebar.selectbox("Menu", menu)

# --- Signup ---
if choice == "Signup":
    st.subheader("Create a New Account")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")
    pic = st.file_uploader("Upload Profile Picture", type=["jpg", "png"])

    if st.button("Signup"):
        if new_user.strip() == "" or new_pass.strip() == "":
            st.error("❌ Username and password are required")
        else:
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
            st.session_state["menu"] = "Feed"
            st.success(f"Welcome {username} 👋")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

# --- Feed ---
elif choice == "Feed" or st.session_state.get("menu") == "Feed":
    if "user" not in st.session_state:
        st.warning("⚠️ Please login first.")
    else:
        st.subheader("📢 Feed")

        # 🔴 Logout button
        if st.button("Logout"):
            st.session_state.pop("user")
            st.session_state["menu"] = "Login"
            st.rerun()

        post_msg = st.text_area("What's happening?")
        if st.button("Post"):
            if post_msg.strip():
                add_post(st.session_state["user"], post_msg)
                st.success("✅ Post added!")
                st.rerun()
            else:
                st.warning("⚠️ Post cannot be empty")

        st.write("### Recent Posts")
        posts = get_posts()
        if not posts:
            st.info("No posts yet. Be the first to post!")
        for pid, uname, msg, ts in posts:
            st.markdown(f"**{uname}** 🕒 {ts}")
            st.write(msg)

            st.write(f"👍 {count_likes(pid)}  ·  💬 {len(get_comments(pid))}")
            if st.button(f"Like {pid}"):
                add_like(pid, st.session_state["user"])
                st.rerun()

            comment = st.text_input(f"Comment on {pid}", key=f"c{pid}")
            if st.button(f"Add Comment {pid}"):
                if comment.strip():
                    add_comment(pid, st.session_state["user"], comment)
                    st.rerun()
                else:
                    st.warning("⚠️ Comment cannot be empty")

            with st.expander("View Comments"):
                for cu, cm, ct in get_comments(pid):
                    st.markdown(f"- **{cu}**: {cm} 🕒 {ct}")

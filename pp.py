import streamlit as st
import sqlite3
from datetime import datetime

# ======================
# Database Setup
# ======================
conn = sqlite3.connect("feedchat.db", check_same_thread=False)
c = conn.cursor()

# Create USERS table (username + password + profile_pic)
c.execute('''CREATE TABLE IF NOT EXISTS users
             (username TEXT PRIMARY KEY,
              password TEXT,
              profile_pic BLOB)''')

# Create POSTS table
c.execute('''CREATE TABLE IF NOT EXISTS posts
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT,
              content TEXT,
              timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

# Create COMMENTS table
c.execute('''CREATE TABLE IF NOT EXISTS comments
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              post_id INTEGER,
              username TEXT,
              comment TEXT,
              timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

# Create LIKES table
c.execute('''CREATE TABLE IF NOT EXISTS likes
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              post_id INTEGER,
              username TEXT)''')

# Create NOTIFICATIONS table
c.execute('''CREATE TABLE IF NOT EXISTS notifications
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT,
              message TEXT,
              seen INTEGER DEFAULT 0,
              timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

conn.commit()

# ======================
# User Management
# ======================
def add_user(username, password, profile_pic):
    c.execute("INSERT OR REPLACE INTO users (username, password, profile_pic) VALUES (?, ?, ?)",
              (username, password, profile_pic))
    conn.commit()

def verify_user(username, password):
    c.execute("SELECT 1 FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone() is not None

def get_user_profile_pic(username):
    c.execute("SELECT profile_pic FROM users WHERE username=?", (username,))
    result = c.fetchone()
    return result[0] if result else None

# ======================
# Post Management
# ======================
def add_post(username, content):
    c.execute("INSERT INTO posts (username, content) VALUES (?, ?)", (username, content))
    conn.commit()

def get_posts():
    c.execute("SELECT id, username, content, timestamp FROM posts ORDER BY id DESC")
    return c.fetchall()

def add_comment(post_id, username, comment):
    c.execute("INSERT INTO comments (post_id, username, comment) VALUES (?, ?, ?)", (post_id, username, comment))
    conn.commit()

def get_comments(post_id):
    c.execute("SELECT username, comment, timestamp FROM comments WHERE post_id=? ORDER BY id ASC", (post_id,))
    return c.fetchall()

def add_like(post_id, username):
    c.execute("SELECT 1 FROM likes WHERE post_id=? AND username=?", (post_id, username))
    if not c.fetchone():
        c.execute("INSERT INTO likes (post_id, username) VALUES (?, ?)", (post_id, username))
        conn.commit()

def count_likes(post_id):
    c.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,))
    return c.fetchone()[0]

# ======================
# Streamlit UI
# ======================
st.set_page_config(page_title="FeedChat", page_icon="💬", layout="wide")

st.title("💬 FeedChat")

# -------------------
# Sidebar - Sign Up
# -------------------
st.sidebar.subheader("Sign Up")
new_user = st.sidebar.text_input("Choose a username")
new_pass = st.sidebar.text_input("Choose a password", type="password")
new_pic = st.sidebar.file_uploader("Upload profile picture", type=["jpg", "png", "jpeg"])

if st.sidebar.button("Create Account"):
    if new_user and new_pass:
        pic_bytes = new_pic.read() if new_pic else None
        add_user(new_user.strip(), new_pass, pic_bytes)
        st.sidebar.success("✅ Account created! Please log in.")

# -------------------
# Sidebar - Login
# -------------------
st.sidebar.subheader("Login")
user = st.sidebar.text_input("Username")
pw = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    if verify_user(user, pw):
        st.session_state.username = user
        st.sidebar.success(f"Welcome {user} 🎉")
    else:
        st.sidebar.error("❌ Invalid username or password")

# -------------------
# Main Feed
# -------------------
if "username" in st.session_state:
    st.success(f"Logged in as {st.session_state.username}")

    # Show profile picture
    pic = get_user_profile_pic(st.session_state.username)
    if pic:
        st.image(pic, width=100, caption="Profile Picture")

    # New Post
    st.subheader("Create a Post")
    post_content = st.text_area("What's on your mind?")
    if st.button("Post"):
        if post_content.strip():
            add_post(st.session_state.username, post_content.strip())
            st.success("✅ Post added!")

    # Display Feed
    st.subheader("📢 Feed")
    posts = get_posts()
    for pid, uname, content, ts in posts:
        st.markdown(f"**{uname}** 🕒 {ts}")
        st.write(content)

        # Likes
        if st.button(f"👍 Like ({count_likes(pid)})", key=f"like_{pid}"):
            add_like(pid, st.session_state.username)

        # Comments
        st.markdown("💬 Comments:")
        for cuser, ctext, ctime in get_comments(pid):
            st.markdown(f"- **{cuser}**: {ctext} ({ctime})")

        comment_text = st.text_input(f"Add comment to post {pid}", key=f"comment_{pid}")
        if st.button(f"Comment on {pid}", key=f"cbtn_{pid}"):
            if comment_text.strip():
                add_comment(pid, st.session_state.username, comment_text.strip())
                st.success("💬 Comment added!")

        st.markdown("---")

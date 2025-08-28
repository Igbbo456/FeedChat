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
# Posts
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
def add_user(username, password, profile_pic=None):
    try:
        c.execute("INSERT INTO users (username, password, profile_pic) VALUES (?, ?, ?)",
                  (username, password, profile_pic))
        conn.commit()
    except sqlite3.IntegrityError:
        pass

def get_user(username):
    c.execute("SELECT username, profile_pic FROM users WHERE username=?", (username,))
    return c.fetchone()

def verify_user(username, password):
    c.execute("SELECT 1 FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone() is not None

def add_post(username, message, media=None, media_type=None):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO posts (username, message, media, media_type, timestamp) VALUES (?, ?, ?, ?, ?)",
              (username, message, media, media_type, ts))
    conn.commit()
    # Notify followers
    c.execute("SELECT follower FROM follows WHERE following=?", (username,))
    followers = c.fetchall()
    for (f,) in followers:
        add_notification(f, f"{username} posted: {(message or '')[:80]}")

def get_posts():
    c.execute("SELECT id, username, message, media, media_type, timestamp FROM posts ORDER BY id DESC")
    return c.fetchall()

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

def add_comment(post_id, username, comment):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO comments (post_id, username, comment, timestamp) VALUES (?, ?, ?, ?)",
              (post_id, username, comment, ts))
    conn.commit()

def get_comments(post_id):
    c.execute("SELECT username, comment, timestamp FROM comments WHERE post_id=? ORDER BY id ASC", (post_id,))
    return c.fetchall()

def follow_user(follower, following):
    if follower == following: return
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

def count_unseen(username):
    c.execute("SELECT COUNT(*) FROM notifications WHERE username=? AND seen=0", (username,))
    r = c.fetchone()
    return r[0] if r else 0

# -----------------------------
# STREAMLIT UI
# -----------------------------
st.set_page_config(page_title="FeedChat", layout="wide")
st.title("📘 FeedChat")

# --- Session defaults ---
if "username" not in st.session_state:
    st.session_state.username = None
if "view_profile" not in st.session_state:
    st.session_state.view_profile = None

# --- Authentication ---
if not st.session_state.username:
    st.sidebar.header("Login / Register")
    choice = st.sidebar.selectbox("I want to:", ["Login", "Register"])
    if choice == "Register":
        st.sidebar.subheader("Create account")
        new_user = st.sidebar.text_input("Username", key="reg_user")
        new_pass = st.sidebar.text_input("Password", type="password", key="reg_pass")
        new_pic = st.sidebar.file_uploader("Profile picture (optional)", type=["png","jpg","jpeg"], key="reg_pic")
        if st.sidebar.button("Register"):
            if new_user.strip() and new_pass.strip():
                pic_bytes = new_pic.read() if new_pic else None
                add_user(new_user.strip(), new_pass, pic_bytes)
                st.sidebar.success("Account created — now log in.")
            else:
                st.sidebar.error("Provide username and password.")
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
# The rest of your FeedChat UI
# (posts, likes, comments, profile, messages, notifications)
# -----------------------------

# ✅ All reruns should be handled outside loops or after UI blocks to prevent experimental_rerun() errors.

import streamlit as st
import sqlite3

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

# Show profile pic if logged in
if "username" in st.session_state:
    st.success(f"Logged in as {st.session_state.username}")
    pic = get_user_profile_pic(st.session_state.username)
    if pic:
        st.image(pic, width=100, caption="Profile Picture")

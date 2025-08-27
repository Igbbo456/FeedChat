import streamlit as st
import sqlite3
from PIL import Image
import io

# ================================
# 📘 Mini Facebook Clone + Messaging
# ================================
st.set_page_config(page_title="FeedChat", page_icon="📘", layout="centered")
st.title("FeedChat")

# -------------------------------
# Database Setup
# -------------------------------
def init_db():
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    # Posts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            message TEXT,
            image BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Messages table
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_post(user, message, image_bytes):
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    c.execute("INSERT INTO posts (user, message, image) VALUES (?, ?, ?)", (user, message, image_bytes))
    conn.commit()
    conn.close()

def get_posts():
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    c.execute("SELECT user, message, image, created_at FROM posts ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def add_message(sender, receiver, message):
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)", (sender, receiver, message))
    conn.commit()
    conn.close()

def get_messages(user1, user2):
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    c.execute("""
        SELECT sender, message, created_at 
        FROM messages 
        WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
        ORDER BY created_at ASC
    """, (user1, user2, user2, user1))
    rows = c.fetchall()
    conn.close()
    return rows

# Initialize DB
init_db()

# -------------------------------
# Sidebar Navigation
# -------------------------------
page = st.sidebar.radio("📌 Navigate", ["News Feed", "Messaging"])

# -------------------------------
# News Feed Page
# -------------------------------
if page == "News Feed":
    st.sidebar.header("✍️ Create a Post")

    username = st.sidebar.text_input("Your Name")
    message = st.sidebar.text_area("What's on your mind?")
    uploaded_image = st.sidebar.file_uploader("Upload a photo", type=["png", "jpg", "jpeg"])

    if st.sidebar.button("Post"):
        if username.strip() and (message.strip() or uploaded_image):
            img_data = None
            if uploaded_image is not None:
                img = Image.open(uploaded_image)
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="PNG")
                img_data = img_bytes.getvalue()
            
            add_post(username, message, img_data)
            st.sidebar.success("✅ Post created! Refresh to see it.")
        else:
            st.sidebar.warning("You need to write something or upload an image.")

    st.subheader("📰 News Feed")

    posts = get_posts()

    if len(posts) == 0:
        st.info("No posts yet. Be the first to post something!")
    else:
        for user, msg, img_data, created_at in posts:
            st.markdown(f"**{user}** · *{created_at}*")
            if msg:
                st.write(msg)
            if img_data:
                st.image(img_data, use_container_width=True)
            st.markdown("---")

# -------------------------------
# Messaging Page
# -------------------------------
elif page == "Messaging":
    st.subheader("💬 Private Messaging")

    sender = st.text_input("Your Name")
    receiver = st.text_input("Send message to (receiver's name)")
    chat_message = st.text_area("Type your message")

    if st.button("Send Message"):
        if sender.strip() and receiver.strip() and chat_message.strip():
            add_message(sender, receiver, chat_message)
            st.success("✅ Message sent!")
        else:
            st.warning("Please fill in all fields to send a message.")

    # Display chat history
    if sender.strip() and receiver.strip():
        st.markdown(f"### Chat between **{sender}** and **{receiver}**")
        msgs = get_messages(sender, receiver)
        if len(msgs) == 0:
            st.info("No messages yet. Start the conversation!")
        else:
            for s, m, t in msgs:
                st.markdown(f"**{s}** [{t}]: {m}")

import streamlit as st
import sqlite3
from PIL import Image
import io

# ================================
# 📘 Mini Facebook Clone + Profile Pics
# ================================
st.set_page_config(page_title="Mini Facebook", page_icon="📘", layout="centered")
st.title("📘 Mini Facebook Clone")

# -------------------------------
# Database Setup
# -------------------------------
def init_db():
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    # Users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            profile_pic BLOB
        )
    ''')
    # Posts
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            message TEXT,
            image BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Messages
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Follows
    c.execute('''
        CREATE TABLE IF NOT EXISTS follows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            follower TEXT,
            following TEXT
        )
    ''')
  # Likes
col1, col2 = st.columns([1, 5])
with col1:
    if has_liked(post_id, st.session_state.username):
        if st.button("Unlike", key=f"unlike_{post_id}_{user}"):
            unlike_post(post_id, st.session_state.username)
            st.experimental_rerun()
    else:
        if st.button("Like", key=f"like_{post_id}_{user}"):
            like_post(post_id, st.session_state.username)
            st.experimental_rerun()
with col2:
    st.write(f"👍 {count_likes(post_id)} likes")

# Comments
st.markdown("💬 Comments:")
comments = get_comments(post_id)
for cu, cm, ct in comments:
    st.markdown(f"**{cu}**: {cm}  ⏱ {ct}")

comment_input = st.text_input(
    f"Add comment to post {post_id}", 
    key=f"comment_input_{post_id}"
)
if st.button("Comment", key=f"comment_btn_{post_id}"):
    if comment_input.strip():
        add_comment(post_id, st.session_state.username, comment_input)
        st.experimental_rerun()
st.markdown("---")


# -------------------------------
# User Functions
# -------------------------------
def register_user(username, password, profile_pic):
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, profile_pic) VALUES (?, ?, ?)", 
                  (username, password, profile_pic))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

def get_user(username):
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    c.execute("SELECT username, profile_pic FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    if user:
        return user  # (username, profile_pic)
    else:
        return (username, None)  # fallback so unpacking never fails

def get_all_users():
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    c.execute("SELECT username FROM users")
    users = [u[0] for u in c.fetchall()]
    conn.close()
    return users

# -------------------------------
# Posts
# -------------------------------
def add_post(user, message, image_bytes):
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    c.execute("INSERT INTO posts (user, message, image) VALUES (?, ?, ?)", (user, message, image_bytes))
    conn.commit()
    conn.close()

def get_all_posts():
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    c.execute("SELECT id, user, message, image, created_at FROM posts ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return rows

# -------------------------------
# Messaging
# -------------------------------
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

# -------------------------------
# Likes & Comments
# -------------------------------
def like_post(post_id, username):
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    c.execute("SELECT * FROM likes WHERE post_id=? AND username=?", (post_id, username))
    if not c.fetchone():
        c.execute("INSERT INTO likes (post_id, username) VALUES (?, ?)", (post_id, username))
        conn.commit()
    conn.close()

def unlike_post(post_id, username):
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    c.execute("DELETE FROM likes WHERE post_id=? AND username=?", (post_id, username))
    conn.commit()
    conn.close()

def count_likes(post_id):
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def has_liked(post_id, username):
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    c.execute("SELECT 1 FROM likes WHERE post_id=? AND username=?", (post_id, username))
    liked = c.fetchone() is not None
    conn.close()
    return liked

def add_comment(post_id, username, comment):
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    c.execute("INSERT INTO comments (post_id, username, comment) VALUES (?, ?, ?)", 
              (post_id, username, comment))
    conn.commit()
    conn.close()

def get_comments(post_id):
    conn = sqlite3.connect("facebook_clone.db")
    c = conn.cursor()
    c.execute("SELECT username, comment, created_at FROM comments WHERE post_id=? ORDER BY created_at ASC", (post_id,))
    rows = c.fetchall()
    conn.close()
    return rows

# -------------------------------
# Init DB
# -------------------------------
init_db()

# -------------------------------
# Authentication State
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None

menu = ["Login", "Register"] if not st.session_state.logged_in else ["News Feed", "Messaging", "Logout"]
choice = st.sidebar.radio("📌 Menu", menu)

# -------------------------------
# Register
# -------------------------------
if choice == "Register" and not st.session_state.logged_in:
    st.subheader("📝 Create Account")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")
    new_pic = st.file_uploader("Upload Profile Picture", type=["png", "jpg", "jpeg"])
    
    profile_pic_data = None
    if new_pic:
        img = Image.open(new_pic)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        profile_pic_data = img_bytes.getvalue()

    if st.button("Register"):
        if register_user(new_user, new_pass, profile_pic_data):
            st.success("✅ Account created! You can now log in.")
        else:
            st.error("❌ Username already exists.")

# -------------------------------
# Login
# -------------------------------
elif choice == "Login" and not st.session_state.logged_in:
    st.subheader("🔑 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"✅ Welcome {username}!")
        else:
            st.error("❌ Invalid credentials")

# -------------------------------
# Logout
# -------------------------------
elif choice == "Logout" and st.session_state.logged_in:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.success("👋 Logged out successfully.")

# -------------------------------
# Logged-in Features
# -------------------------------
if st.session_state.logged_in:

    if choice == "News Feed":
        st.sidebar.header("✍️ Create a Post")

        message = st.sidebar.text_area("What's on your mind?")
        uploaded_image = st.sidebar.file_uploader("Upload a photo", type=["png", "jpg", "jpeg"])

        if st.sidebar.button("Post"):
            if message.strip() or uploaded_image:
                img_data = None
                if uploaded_image is not None:
                    img = Image.open(uploaded_image)
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="PNG")
                    img_data = img_bytes.getvalue()
                
                add_post(st.session_state.username, message, img_data)
                st.sidebar.success("✅ Post created! Refresh to see it.")
            else:
                st.sidebar.warning("You need to write something or upload an image.")

        st.subheader("📰 News Feed (All Posts)")

        posts = get_all_posts()

        if len(posts) == 0:
            st.info("No posts yet.")
        else:
            for post_id, user, msg, img_data, created_at in posts:
                u, pic = get_user(user)

                # Show profile picture beside username
                col1, col2 = st.columns([1, 8])
                with col1:
                    if pic:
                        st.image(pic, width=50)
                with col2:
                    st.markdown(f"**{u}**")
                    st.caption(created_at)

                if msg:
                    st.write(msg)
                if img_data:
                    st.image(img_data, use_container_width=True)

                # Likes
                col1, col2 = st.columns([1,5])
                with col1:
                    if has_liked(post_id, st.session_state.username):
                        if st.button(f"Unlike {post_id}"):
                            unlike_post(post_id, st.session_state.username)
                            st.experimental_rerun()
                    else:
                        if st.button(f"Like {post_id}"):
                            like_post(post_id, st.session_state.username)
                            st.experimental_rerun()
                with col2:
                    st.write(f"👍 {count_likes(post_id)} likes")

                # Comments
                st.markdown("💬 Comments:")
                comments = get_comments(post_id)
                for cu, cm, ct in comments:
                    cu_name, cu_pic = get_user(cu)
                    colc1, colc2 = st.columns([1, 8])
                    with colc1:
                        if cu_pic:
                            st.image(cu_pic, width=35)
                    with colc2:
                        st.markdown(f"**{cu_name}**: {cm} ⏱ {ct}")

                comment_input = st.text_input(f"Add comment to post {post_id}", key=f"comment_{post_id}")
                if st.button(f"Comment {post_id}"):
                    if comment_input.strip():
                        add_comment(post_id, st.session_state.username, comment_input)
                        st.experimental_rerun()
                st.markdown("---")

    elif choice == "Messaging":
        st.subheader("💬 Private Messaging")

        receiver = st.text_input("Send message to (username)")
        chat_message = st.text_area("Type your message")

        if st.button("Send Message"):
            if receiver.strip() and chat_message.strip():
                add_message(st.session_state.username, receiver, chat_message)
                st.success("✅ Message sent!")
            else:
                st.warning("Please fill in all fields to send a message.")

        if receiver.strip():
            st.markdown(f"### Chat between **{st.session_state.username}** and **{receiver}**")
            msgs = get_messages(st.session_state.username, receiver)
            if len(msgs) == 0:
                st.info("No messages yet. Start the conversation!")
            else:
                for s, m, t in msgs:
                    su, spic = get_user(s)
                    colm1, colm2 = st.columns([1, 8])
                    with colm1:
                        if spic:
                            st.image(spic, width=35)
                    with colm2:
                        st.markdown(f"**{su}** ({t}): {m}")
                    st.markdown("---")


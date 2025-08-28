import streamlit as st
import sqlite3
from datetime import datetime
from PIL import Image
import io
import base64

# ================================
# 📘 Mini Facebook Clone with Notifications
# ================================

st.set_page_config(page_title="Mini Facebook Clone", page_icon="📘", layout="wide")

# ----------------------
# Database Setup
# ----------------------
conn = sqlite3.connect("feedchat.db", check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users
             (username TEXT PRIMARY KEY, profile_pic BLOB)''')

c.execute('''CREATE TABLE IF NOT EXISTS posts
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT,
              message TEXT,
              media BLOB,
              media_type TEXT,
              timestamp TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS likes
             (post_id INTEGER, username TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS comments
             (post_id INTEGER, username TEXT, comment TEXT, timestamp TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS messages
             (sender TEXT, receiver TEXT, message TEXT, timestamp TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS follows
             (follower TEXT, following TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS notifications
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT,
              message TEXT,
              timestamp TEXT,
              seen INTEGER DEFAULT 0)''')

conn.commit()

# ----------------------
# Helper Functions
# ----------------------
def add_user(username, profile_pic=None):
    c.execute("INSERT OR IGNORE INTO users (username, profile_pic) VALUES (?,?)", (username, profile_pic))
    conn.commit()

def get_user(username):
    c.execute("SELECT username, profile_pic FROM users WHERE username=?", (username,))
    return c.fetchone()

def add_post(username, message, media, media_type):
    c.execute("INSERT INTO posts (username, message, media, media_type, timestamp) VALUES (?,?,?,?,?)",
              (username, message, media, media_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_posts():
    c.execute("SELECT id, username, message, media, media_type, timestamp FROM posts ORDER BY id DESC")
    return c.fetchall()

def add_like(post_id, username):
    c.execute("INSERT INTO likes (post_id, username) VALUES (?,?)", (post_id, username))
    conn.commit()

def count_likes(post_id):
    c.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,))
    return c.fetchone()[0]

def has_liked(post_id, username):
    c.execute("SELECT 1 FROM likes WHERE post_id=? AND username=?", (post_id, username))
    return c.fetchone() is not None

def add_comment(post_id, username, comment):
    c.execute("INSERT INTO comments (post_id, username, comment, timestamp) VALUES (?,?,?,?)",
              (post_id, username, comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_comments(post_id):
    c.execute("SELECT username, comment, timestamp FROM comments WHERE post_id=?", (post_id,))
    return c.fetchall()

def follow(follower, following):
    c.execute("INSERT INTO follows (follower, following) VALUES (?,?)", (follower, following))
    conn.commit()

def unfollow(follower, following):
    c.execute("DELETE FROM follows WHERE follower=? AND following=?", (follower, following))
    conn.commit()

def get_following(username):
    c.execute("SELECT following FROM follows WHERE follower=?", (username,))
    return [row[0] for row in c.fetchall()]

def send_message(sender, receiver, message):
    c.execute("INSERT INTO messages (sender, receiver, message, timestamp) VALUES (?,?,?,?)",
              (sender, receiver, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_messages(user1, user2):
    c.execute("""SELECT sender, message, timestamp FROM messages 
                 WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
                 ORDER BY timestamp ASC""", (user1, user2, user2, user1))
    return c.fetchall()

# ----------------------
# Notifications
# ----------------------
def add_notification(username, message):
    c.execute("INSERT INTO notifications (username, message, timestamp, seen) VALUES (?,?,?,0)",
              (username, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_notifications(username):
    c.execute("SELECT id, message, timestamp, seen FROM notifications WHERE username=? ORDER BY id DESC", (username,))
    return c.fetchall()

def mark_seen(notif_id):
    c.execute("UPDATE notifications SET seen=1 WHERE id=?", (notif_id,))
    conn.commit()

def count_unseen(username):
    c.execute("SELECT COUNT(*) FROM notifications WHERE username=? AND seen=0", (username,))
    return c.fetchone()[0]

def notify_followers(username, post_msg):
    c.execute("SELECT follower FROM follows WHERE following=?", (username,))
    followers = c.fetchall()
    for f in followers:
        add_notification(f[0], f"{username} posted: {post_msg[:50]}")

# ----------------------
# User Login / Profile
# ----------------------
st.sidebar.title("👤 Login / Profile")
username = st.sidebar.text_input("Enter your username:")

if username:
    st.session_state.username = username
    user = get_user(username)
    if not user:
        add_user(username)
    st.sidebar.success(f"Logged in as {username}")

    # Profile Picture
    uploaded_pic = st.sidebar.file_uploader("Upload Profile Picture", type=["png", "jpg", "jpeg"])
    if uploaded_pic:
        img = Image.open(uploaded_pic)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        add_user(username, img_bytes.getvalue())
        st.sidebar.success("Profile picture updated!")

    # Show Notifications
    unseen = count_unseen(username)
    if st.sidebar.button(f"🔔 Notifications ({unseen} new)"):
        notifs = get_notifications(username)
        for nid, msg, ts, seen in notifs:
            st.sidebar.write(f"{msg} ⏱ {ts}")
            if seen == 0:
                mark_seen(nid)

    # Create Post
    st.sidebar.header("✍️ Create a Post")
    msg = st.sidebar.text_area("What's on your mind?")
    uploaded_media = st.sidebar.file_uploader("Upload image/video", type=["png", "jpg", "jpeg", "mp4"])
    if st.sidebar.button("Post"):
        media_bytes, media_type = None, None
        if uploaded_media:
            media_bytes = uploaded_media.read()
            media_type = "video" if uploaded_media.type == "video/mp4" else "image"
        add_post(username, msg, media_bytes, media_type)
        notify_followers(username, msg)
        st.sidebar.success("✅ Post created!")

# ----------------------
# News Feed
# ----------------------
st.title("📰 News Feed")

for post_id, user, msg, media, media_type, ts in get_posts():
    st.markdown(f"### {user} — ⏱ {ts}")
    st.write(msg)

    if media:
        if media_type == "image":
            st.image(media, use_container_width=True)
        elif media_type == "video":
            st.video(io.BytesIO(media))

    likes = count_likes(post_id)
    if "username" in st.session_state:
        if has_liked(post_id, st.session_state.username):
            st.button(f"❤️ {likes} Likes", key=f"like_{post_id}")
        else:
            if st.button(f"🤍 {likes} Likes", key=f"like_{post_id}"):
                add_like(post_id, st.session_state.username)

        comment = st.text_input(f"💬 Comment on post {post_id}", key=f"cmt_{post_id}")
        if st.button("Add Comment", key=f"btn_cmt_{post_id}"):
            add_comment(post_id, st.session_state.username, comment)

    for cuser, cmt, cts in get_comments(post_id):
        st.markdown(f"- **{cuser}**: {cmt} ({cts})")

    st.markdown("---")

# ----------------------
# Messaging
# ----------------------
if "username" in st.session_state:
    st.sidebar.header("💬 Messages")
    other_user = st.sidebar.text_input("Chat with:")
    if other_user:
        chat = get_messages(st.session_state.username, other_user)
        st.sidebar.subheader(f"Chat with {other_user}")
        for sender, msg, ts in chat:
            st.sidebar.write(f"**{sender}**: {msg} ({ts})")

        new_msg = st.sidebar.text_input("Type a message")
        if st.sidebar.button("Send"):
            send_message(st.session_state.username, other_user, new_msg)
            add_notification(other_user, f"📩 New message from {st.session_state.username}")

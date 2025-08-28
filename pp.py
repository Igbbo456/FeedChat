import streamlit as st
import sqlite3
from datetime import datetime
from PIL import Image
import io
import base64

# ==============================
# DATABASE SETUP
# ==============================
conn = sqlite3.connect("feedchat.db", check_same_thread=False)
c = conn.cursor()

# Users
c.execute("""CREATE TABLE IF NOT EXISTS users
             (username TEXT PRIMARY KEY, profile_pic BLOB)""")

# Posts
c.execute("""CREATE TABLE IF NOT EXISTS posts
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT,
              message TEXT,
              image BLOB,
              timestamp TEXT)""")

# Followers
c.execute("""CREATE TABLE IF NOT EXISTS followers
             (follower TEXT, following TEXT)""")

# Likes
c.execute("""CREATE TABLE IF NOT EXISTS likes
             (post_id INTEGER, username TEXT)""")

# Messages
c.execute("""CREATE TABLE IF NOT EXISTS messages
             (sender TEXT, receiver TEXT, message TEXT, timestamp TEXT)""")

# Notifications
c.execute("""CREATE TABLE IF NOT EXISTS notifications
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT,
              type TEXT,
              message TEXT,
              is_read INTEGER DEFAULT 0,
              timestamp TEXT)""")

conn.commit()

# ==============================
# UTILS
# ==============================
def add_user(username, profile_pic=None):
    if not get_user(username):
        c.execute("INSERT INTO users VALUES (?, ?)", (username, profile_pic))
        conn.commit()

def get_user(username):
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    return c.fetchone()

def add_post(username, message, image):
    c.execute("INSERT INTO posts (username, message, image, timestamp) VALUES (?,?,?,?)",
              (username, message, image, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

    # Notify followers
    c.execute("SELECT follower FROM followers WHERE following=?", (username,))
    followers = c.fetchall()
    for (f,) in followers:
        add_notification(f, "post", f"{username} just posted: {message[:30]}...")

def get_posts():
    c.execute("SELECT * FROM posts ORDER BY id DESC")
    return c.fetchall()

def follow_user(follower, following):
    c.execute("INSERT INTO followers VALUES (?, ?)", (follower, following))
    conn.commit()

def unfollow_user(follower, following):
    c.execute("DELETE FROM followers WHERE follower=? AND following=?", (follower, following))
    conn.commit()

def is_following(follower, following):
    c.execute("SELECT * FROM followers WHERE follower=? AND following=?", (follower, following))
    return c.fetchone() is not None

def like_post(post_id, username):
    if not has_liked(post_id, username):
        c.execute("INSERT INTO likes VALUES (?, ?)", (post_id, username))
        conn.commit()

def unlike_post(post_id, username):
    c.execute("DELETE FROM likes WHERE post_id=? AND username=?", (post_id, username))
    conn.commit()

def has_liked(post_id, username):
    c.execute("SELECT * FROM likes WHERE post_id=? AND username=?", (post_id, username))
    return c.fetchone() is not None

def count_likes(post_id):
    c.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,))
    return c.fetchone()[0]

def send_message(sender, receiver, message):
    c.execute("INSERT INTO messages VALUES (?,?,?,?)",
              (sender, receiver, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    add_notification(receiver, "message", f"New message from {sender}: {message[:30]}...")

def get_messages(user1, user2):
    c.execute("SELECT * FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY timestamp",
              (user1, user2, user2, user1))
    return c.fetchall()

# ---------------- Notifications ----------------
def add_notification(username, ntype, message):
    c.execute("INSERT INTO notifications (username, type, message, timestamp) VALUES (?,?,?,?)",
              (username, ntype, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_notifications(username):
    c.execute("SELECT id, type, message, is_read, timestamp FROM notifications WHERE username=? ORDER BY id DESC", (username,))
    return c.fetchall()

def mark_notifications_read(username):
    c.execute("UPDATE notifications SET is_read=1 WHERE username=?", (username,))
    conn.commit()

def count_unread_notifications(username):
    c.execute("SELECT COUNT(*) FROM notifications WHERE username=? AND is_read=0", (username,))
    return c.fetchone()[0]

# ==============================
# STREAMLIT APP
# ==============================
st.set_page_config(page_title="📘 FeedChat", page_icon="📘", layout="centered")

st.title("📘 FeedChat")

# ---------------- LOGIN ----------------
if "username" not in st.session_state:
    st.subheader("👤 Login / Signup")
    username = st.text_input("Enter your username:")
    profile_pic = st.file_uploader("Upload profile picture", type=["jpg", "png", "jpeg"])

    if st.button("Enter"):
        pic_data = None
        if profile_pic:
            img = Image.open(profile_pic)
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            pic_data = img_bytes.getvalue()
        add_user(username, pic_data)
        st.session_state.username = username
        st.rerun()
    st.stop()

# ---------------- MAIN TABS ----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📰 News Feed",
    "✍️ Create Post",
    "💬 Messages",
    "👤 Profile",
    f"🔔 Notifications ({count_unread_notifications(st.session_state.username)})"
])

# ---------------- NEWS FEED ----------------
with tab1:
    st.subheader("📰 News Feed")
    posts = get_posts()
    if not posts:
        st.info("No posts yet. Be the first to post something!")
    else:
        for pid, user, msg, img, ts in posts:
            u = get_user(user)
            if u and u[1]:
                st.image(u[1], width=40, caption=user)
            else:
                st.write(f"**{user}**")

            st.write(msg)
            if img:
                st.image(img, use_container_width=True)
            st.caption(f"🕒 {ts}")

            col1, col2 = st.columns([1, 5])
            with col1:
                if has_liked(pid, st.session_state.username):
                    if st.button(f"💔 Unlike ({count_likes(pid)})", key=f"unlike_{pid}"):
                        unlike_post(pid, st.session_state.username)
                        st.rerun()
                else:
                    if st.button(f"❤️ Like ({count_likes(pid)})", key=f"like_{pid}"):
                        like_post(pid, st.session_state.username)
                        st.rerun()
            st.markdown("---")

# ---------------- CREATE POST ----------------
with tab2:
    st.subheader("✍️ Create a Post")
    msg = st.text_area("What's on your mind?")
    img_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    img_data = None
    if img_file:
        img = Image.open(img_file)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_data = img_bytes.getvalue()

    if st.button("Post"):
        if msg.strip() or img_data:
            add_post(st.session_state.username, msg, img_data)
            st.success("✅ Post created!")
            st.rerun()

# ---------------- MESSAGES ----------------
with tab3:
    st.subheader("💬 Messages")
    receiver = st.text_input("Send message to (username):")
    message = st.text_area("Your message:")
    if st.button("Send"):
        if get_user(receiver):
            send_message(st.session_state.username, receiver, message)
            st.success("✅ Message sent!")
        else:
            st.error("❌ User does not exist.")

    if receiver:
        st.write(f"📨 Chat with {receiver}")
        msgs = get_messages(st.session_state.username, receiver)
        for s, r, m, ts in msgs:
            st.write(f"**{s}**: {m} ({ts})")

# ---------------- PROFILE ----------------
with tab4:
    st.subheader(f"👤 {st.session_state.username}'s Profile")
    u = get_user(st.session_state.username)
    if u and u[1]:
        st.image(u[1], width=100, caption="Profile Picture")

    st.write("### Your Posts")
    c.execute("SELECT * FROM posts WHERE username=? ORDER BY id DESC", (st.session_state.username,))
    my_posts = c.fetchall()
    for pid, user, msg, img, ts in my_posts:
        st.write(msg)
        if img:
            st.image(img, use_container_width=True)
        st.caption(f"🕒 {ts} | ❤️ {count_likes(pid)} likes")

# ---------------- NOTIFICATIONS ----------------
with tab5:
    st.subheader("🔔 Notifications")
    notes = get_notifications(st.session_state.username)
    if not notes:
        st.info("No notifications yet.")
    else:
        for nid, ntype, msg, is_read, ts in notes:
            st.markdown(f"- {'✅' if is_read else '🆕'} **[{ntype.upper()}]** {msg} _(at {ts})_")

        if st.button("Mark all as read"):
            mark_notifications_read(st.session_state.username)
            st.rerun()


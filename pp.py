import streamlit as st
import sqlite3
import datetime
import io

# ================================
# 📘 FeedChat (Facebook-like App)
# ================================
st.set_page_config(page_title="FeedChat", page_icon="📘", layout="wide")

# ----------------------
# Database Setup
# ----------------------
conn = sqlite3.connect("feedchat.db", check_same_thread=False)
c = conn.cursor()

# Users table
c.execute('''CREATE TABLE IF NOT EXISTS users
             (username TEXT PRIMARY KEY, profile_pic BLOB)''')

# Posts table (new schema with media + media_type)
c.execute('''CREATE TABLE IF NOT EXISTS posts
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT,
              message TEXT,
              media BLOB,
              media_type TEXT,
              timestamp TEXT)''')

# Likes table
c.execute('''CREATE TABLE IF NOT EXISTS likes
             (post_id INTEGER, username TEXT)''')

# Comments table
c.execute('''CREATE TABLE IF NOT EXISTS comments
             (post_id INTEGER, username TEXT, comment TEXT, timestamp TEXT)''')

# Messages table
c.execute('''CREATE TABLE IF NOT EXISTS messages
             (sender TEXT, receiver TEXT, message TEXT, timestamp TEXT)''')

# Follows table
c.execute('''CREATE TABLE IF NOT EXISTS follows
             (follower TEXT, following TEXT)''')

# Notifications table
c.execute('''CREATE TABLE IF NOT EXISTS notifications
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT,
              message TEXT,
              timestamp TEXT,
              seen INTEGER DEFAULT 0)''')

conn.commit()

# ----------------------
# Migration Script
# ----------------------
def migrate_posts_table():
    c.execute("PRAGMA table_info(posts)")
    cols = [col[1] for col in c.fetchall()]

    # If old schema has "image" column instead of "media"
    if "image" in cols and "media" not in cols:
        st.warning("⚠️ Detected old database schema. Upgrading posts table...")

        # Rename old table
        c.execute("ALTER TABLE posts RENAME TO posts_old")

        # Create new posts table
        c.execute('''CREATE TABLE posts
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT,
                      message TEXT,
                      media BLOB,
                      media_type TEXT,
                      timestamp TEXT)''')

        # Migrate data (image -> media, media_type = 'image')
        c.execute('''INSERT INTO posts (id, username, message, media, media_type, timestamp)
                     SELECT id, username, message, image, 'image', timestamp FROM posts_old''')

        # Drop old table
        c.execute("DROP TABLE posts_old")
        conn.commit()
        st.success("✅ Database upgraded successfully!")

migrate_posts_table()

# ----------------------
# Helpers
# ----------------------
def add_user(username, profile_pic=None):
    c.execute("INSERT OR REPLACE INTO users (username, profile_pic) VALUES (?, ?)", (username, profile_pic))
    conn.commit()

def get_user(username):
    c.execute("SELECT username, profile_pic FROM users WHERE username=?", (username,))
    return c.fetchone()

def add_post(username, message, media=None, media_type=None):
    c.execute("INSERT INTO posts (username, message, media, media_type, timestamp) VALUES (?, ?, ?, ?, ?)",
              (username, message, media, media_type, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_posts():
    c.execute("SELECT id, username, message, media, media_type, timestamp FROM posts ORDER BY id DESC")
    return c.fetchall()

def like_post(post_id, username):
    c.execute("INSERT INTO likes (post_id, username) VALUES (?, ?)", (post_id, username))
    conn.commit()

def unlike_post(post_id, username):
    c.execute("DELETE FROM likes WHERE post_id=? AND username=?", (post_id, username))
    conn.commit()

def has_liked(post_id, username):
    c.execute("SELECT 1 FROM likes WHERE post_id=? AND username=?", (post_id, username))
    return c.fetchone() is not None

def count_likes(post_id):
    c.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,))
    return c.fetchone()[0]

def add_comment(post_id, username, comment):
    c.execute("INSERT INTO comments (post_id, username, comment, timestamp) VALUES (?, ?, ?, ?)",
              (post_id, username, comment, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_comments(post_id):
    c.execute("SELECT username, comment, timestamp FROM comments WHERE post_id=?", (post_id,))
    return c.fetchall()

def follow(follower, following):
    c.execute("INSERT INTO follows (follower, following) VALUES (?, ?)", (follower, following))
    conn.commit()

def unfollow(follower, following):
    c.execute("DELETE FROM follows WHERE follower=? AND following=?", (follower, following))
    conn.commit()

def is_following(follower, following):
    c.execute("SELECT 1 FROM follows WHERE follower=? AND following=?", (follower, following))
    return c.fetchone() is not None

def get_following(username):
    c.execute("SELECT following FROM follows WHERE follower=?", (username,))
    return [x[0] for x in c.fetchall()]

def send_message(sender, receiver, message):
    c.execute("INSERT INTO messages (sender, receiver, message, timestamp) VALUES (?, ?, ?, ?)",
              (sender, receiver, message, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_messages(user1, user2):
    c.execute("""SELECT sender, receiver, message, timestamp FROM messages
                 WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
                 ORDER BY timestamp ASC""", (user1, user2, user2, user1))
    return c.fetchall()

def add_notification(username, msg):
    c.execute("INSERT INTO notifications (username, message, timestamp) VALUES (?, ?, ?)",
              (username, msg, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_notifications(username):
    c.execute("SELECT id, message, timestamp, seen FROM notifications WHERE username=? ORDER BY id DESC", (username,))
    return c.fetchall()

# ----------------------
# Login
# ----------------------
st.sidebar.header("👤 Login")
username = st.sidebar.text_input("Enter your username")
profile_pic = st.sidebar.file_uploader("Upload Profile Picture", type=["png", "jpg", "jpeg"])

if st.sidebar.button("Login / Register"):
    pic_data = profile_pic.read() if profile_pic else None
    add_user(username, pic_data)
    st.session_state.username = username
    st.sidebar.success(f"✅ Logged in as {username}")

# ----------------------
# Main App
# ----------------------
if "username" in st.session_state:
    tab1, tab2, tab3, tab4 = st.tabs(["📰 Feed", "💬 Messages", "👥 Profile", "🔔 Notifications"])

    # Feed
    with tab1:
        st.subheader("📰 News Feed")

        message = st.text_area("What's on your mind?")
        uploaded_file = st.file_uploader("Upload image/video", type=["png", "jpg", "jpeg", "mp4", "mov", "avi"])

        if st.button("Post"):
            if message.strip() or uploaded_file:
                media_data = None
                media_type = None
                if uploaded_file:
                    media_data = uploaded_file.read()
                    if uploaded_file.type.startswith("image"):
                        media_type = "image"
                    elif uploaded_file.type.startswith("video"):
                        media_type = "video"

                add_post(st.session_state.username, message, media_data, media_type)
                add_notification(st.session_state.username, "📝 You created a new post.")
                st.success("✅ Post created!")
                st.rerun()

        posts = get_posts()
        if not posts:
            st.info("No posts yet.")
        else:
            for post_id, user, msg, media, media_type, ts in posts:
                st.markdown(f"**{user}** • _{ts}_")
                st.write(msg)
                if media:
                    if media_type == "image":
                        st.image(media, use_container_width=True)
                    elif media_type == "video":
                        st.video(io.BytesIO(media))
                if has_liked(post_id, st.session_state.username):
                    if st.button(f"💔 Unlike ({count_likes(post_id)})", key=f"unlike{post_id}"):
                        unlike_post(post_id, st.session_state.username)
                        st.rerun()
                else:
                    if st.button(f"❤️ Like ({count_likes(post_id)})", key=f"like{post_id}"):
                        like_post(post_id, st.session_state.username)
                        st.rerun()

                with st.expander("💬 Comments"):
                    for cu, cm, cts in get_comments(post_id):
                        st.markdown(f"**{cu}** ({cts}): {cm}")
                    new_comment = st.text_input("Write a comment:", key=f"comment{post_id}")
                    if st.button("Post Comment", key=f"btncomment{post_id}"):
                        add_comment(post_id, st.session_state.username, new_comment)
                        st.rerun()
                st.markdown("---")

    # Messages
    with tab2:
        st.subheader("💬 Messages")
        receiver = st.text_input("Send message to:")
        msg_text = st.text_input("Message")
        if st.button("Send"):
            if receiver and msg_text:
                send_message(st.session_state.username, receiver, msg_text)
                add_notification(receiver, f"💌 New message from {st.session_state.username}")
                st.success("✅ Message sent!")
        st.markdown("### Your Messages")
        for following in get_following(st.session_state.username):
            with st.expander(f"Chat with {following}"):
                msgs = get_messages(st.session_state.username, following)
                for s, r, m, t in msgs:
                    st.write(f"**{s}** ({t}): {m}")

    # Profile
    with tab3:
        st.subheader("👥 Profile")
        u, pic = get_user(st.session_state.username)
        if pic:
            st.image(pic, width=100)
        st.write(f"**Username:** {u}")

        st.write("### Your Posts")
        user_posts = [p for p in get_posts() if p[1] == u]
        for post_id, user, msg, media, media_type, ts in user_posts:
            st.write(f"**{msg}** • {ts}")
            if media:
                if media_type == "image":
                    st.image(media, use_container_width=True)
                elif media_type == "video":
                    st.video(io.BytesIO(media))

    # Notifications
    with tab4:
        st.subheader("🔔 Notifications")
        notifs = get_notifications(st.session_state.username)
        if not notifs:
            st.info("No notifications.")
        else:
            for _, msg, ts, seen in notifs:
                st.write(f"{msg} • _{ts}_")

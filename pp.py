import streamlit as st
import sqlite3, io
from PIL import Image
from datetime import datetime

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

# 🔧 Ensure "seen" column exists in notifications
c.execute("PRAGMA table_info(notifications)")
columns = [col[1] for col in c.fetchall()]
if "seen" not in columns:
    c.execute("ALTER TABLE notifications ADD COLUMN seen INTEGER DEFAULT 0")
    conn.commit()

conn.commit()

# ----------------------
# Helper Functions
# ----------------------
def save_user(username, profile_pic):
    c.execute("INSERT OR REPLACE INTO users VALUES (?, ?)", (username, profile_pic))
    conn.commit()

def get_user(username):
    c.execute("SELECT username, profile_pic FROM users WHERE username=?", (username,))
    return c.fetchone()

def add_post(username, message, media, media_type):
    c.execute("INSERT INTO posts (username, message, media, media_type, timestamp) VALUES (?,?,?,?,?)",
              (username, message, media, media_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    notify_followers(username, f"{username} added a new post!")

def get_posts():
    c.execute("SELECT id, username, message, media, media_type, timestamp FROM posts ORDER BY id DESC")
    return c.fetchall()

def like_post(post_id, username):
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

def add_comment(post_id, username, comment):
    c.execute("INSERT INTO comments VALUES (?,?,?,?)",
              (post_id, username, comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_comments(post_id):
    c.execute("SELECT username, comment, timestamp FROM comments WHERE post_id=?", (post_id,))
    return c.fetchall()

def send_message(sender, receiver, message):
    c.execute("INSERT INTO messages VALUES (?,?,?,?)",
              (sender, receiver, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    add_notification(receiver, f"📩 New message from {sender}")

def get_messages(user1, user2):
    c.execute("""SELECT sender, message, timestamp FROM messages
                 WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
                 ORDER BY timestamp ASC""", (user1, user2, user2, user1))
    return c.fetchall()

def follow_user(follower, following):
    c.execute("INSERT INTO follows VALUES (?, ?)", (follower, following))
    conn.commit()

def unfollow_user(follower, following):
    c.execute("DELETE FROM follows WHERE follower=? AND following=?", (follower, following))
    conn.commit()

def is_following(follower, following):
    c.execute("SELECT * FROM follows WHERE follower=? AND following=?", (follower, following))
    return c.fetchone() is not None

def get_followers(username):
    c.execute("SELECT follower FROM follows WHERE following=?", (username,))
    return [f[0] for f in c.fetchall()]

def get_following(username):
    c.execute("SELECT following FROM follows WHERE follower=?", (username,))
    return [f[0] for f in c.fetchall()]

def add_notification(username, message):
    c.execute("INSERT INTO notifications (username, message, timestamp, seen) VALUES (?,?,?,0)",
              (username, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_notifications(username):
    c.execute("SELECT id, message, timestamp, seen FROM notifications WHERE username=? ORDER BY id DESC", (username,))
    return c.fetchall()

def mark_notification_seen(notif_id):
    c.execute("UPDATE notifications SET seen=1 WHERE id=?", (notif_id,))
    conn.commit()

def count_unseen(username):
    c.execute("SELECT COUNT(*) FROM notifications WHERE username=? AND seen=0", (username,))
    return c.fetchone()[0]

def notify_followers(user, message):
    followers = get_followers(user)
    for f in followers:
        add_notification(f, message)

# ----------------------
# Streamlit App
# ----------------------
st.set_page_config(page_title="FeedChat", page_icon="💬", layout="wide")
st.title("💬 FeedChat")

# Sidebar - Login / Register
st.sidebar.header("👤 User Login / Register")
if "username" not in st.session_state:
    st.session_state.username = None

if st.session_state.username:
    st.sidebar.success(f"✅ Logged in as {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.username = None
        st.rerun()
else:
    username = st.sidebar.text_input("Enter your username")
    profile_pic_file = st.sidebar.file_uploader("Upload profile picture", type=["png","jpg","jpeg"])
    if st.sidebar.button("Save Profile"):
        if username.strip():
            pic_bytes = None
            if profile_pic_file:
                img = Image.open(profile_pic_file)
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="PNG")
                pic_bytes = img_bytes.getvalue()
            save_user(username, pic_bytes)
            st.session_state.username = username
            st.sidebar.success("✅ Profile saved!")
            st.rerun()

# ----------------------
# Main Tabs
# ----------------------
if st.session_state.username:
    unseen = count_unseen(st.session_state.username)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📰 News Feed",
        "✍️ Create Post",
        "💬 Messages",
        "👤 Profile",
        f"🔔 Notifications ({unseen})"
    ])

    # News Feed
    with tab1:
        posts = get_posts()
        if not posts:
            st.info("No posts yet. Be the first to post something!")
        else:
            for post in posts:
                post_id, user, message, media, media_type, timestamp = post
                u, pic = get_user(user)

                col1, col2 = st.columns([1, 8])
                with col1:
                    if pic:
                        st.image(pic, width=50)
                with col2:
                    st.markdown(f"**{u}** · ⏱ {timestamp}")
                    if message:
                        st.write(message)
                    if media:
                        if media_type == "image":
                            st.image(media, use_container_width=True)
                        elif media_type == "video":
                            st.video(media)

                # Likes
                col1, col2 = st.columns([1, 5])
                with col1:
                    if has_liked(post_id, st.session_state.username):
                        if st.button("Unlike", key=f"unlike_{post_id}"):
                            unlike_post(post_id, st.session_state.username)
                            st.rerun()
                    else:
                        if st.button("Like", key=f"like_{post_id}"):
                            like_post(post_id, st.session_state.username)
                            st.rerun()
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

                comment_input = st.text_input(f"Add comment to post {post_id}", key=f"comment_input_{post_id}")
                if st.button("Comment", key=f"comment_btn_{post_id}"):
                    if comment_input.strip():
                        add_comment(post_id, st.session_state.username, comment_input)
                        st.rerun()
                st.markdown("---")

    # Create Post
    with tab2:
        st.subheader("✍️ Create a Post")
        msg = st.text_area("What's on your mind?")
        uploaded_file = st.file_uploader("Upload media (photo or video)", type=["png","jpg","jpeg","mp4","mov","avi"])
        if st.button("Post Now"):
            if msg.strip() or uploaded_file:
                media_bytes, media_type = None, None
                if uploaded_file:
                    ext = uploaded_file.name.split(".")[-1].lower()
                    if ext in ["png","jpg","jpeg"]:
                        img = Image.open(uploaded_file)
                        img_bytes = io.BytesIO()
                        img.save(img_bytes, format="PNG")
                        media_bytes = img_bytes.getvalue()
                        media_type = "image"
                    elif ext in ["mp4","mov","avi"]:
                        media_bytes = uploaded_file.read()
                        media_type = "video"
                add_post(st.session_state.username, msg, media_bytes, media_type)
                st.success("✅ Post created!")
                st.rerun()
            else:
                st.warning("Please write something or upload an image/video.")

    # Messages
    with tab3:
        st.subheader("💬 Private Messages")
        other_user = st.text_input("Enter the username you want to chat with")
        if other_user:
            chat = get_messages(st.session_state.username, other_user)
            st.write(f"📨 Chat between **{st.session_state.username}** and **{other_user}**:")
            for sender, msg, ts in chat:
                st.markdown(f"**{sender}** ({ts}): {msg}")

            new_msg = st.text_input("Type your message")
            if st.button("Send"):
                if new_msg.strip():
                    send_message(st.session_state.username, other_user, new_msg)
                    st.rerun()

    # Profile
    with tab4:
        st.subheader(f"👤 Profile: {st.session_state.username}")
        user, pic = get_user(st.session_state.username)
        if pic:
            st.image(pic, width=100)

        st.write(f"Following: {len(get_following(st.session_state.username))}")
        st.write(f"Followers: {len(get_followers(st.session_state.username))}")

        st.markdown("### Your Posts")
        user_posts = [p for p in get_posts() if p[1] == st.session_state.username]
        for post in user_posts:
            post_id, user, message, media, media_type, timestamp = post
            st.markdown(f"**{user}** · ⏱ {timestamp}")
            if message:
                st.write(message)
            if media:
                if media_type == "image":
                    st.image(media, use_container_width=True)
                elif media_type == "video":
                    st.video(media)
            st.write(f"👍 {count_likes(post_id)} likes")
            st.markdown("---")

    # Notifications
    with tab5:
        st.subheader("🔔 Notifications")
        notifs = get_notifications(st.session_state.username)
        if not notifs:
            st.info("No notifications yet.")
        else:
            for notif_id, msg, ts, seen in notifs:
                st.markdown(f"{'🆕' if not seen else '✔️'} {msg} ⏱ {ts}")
                if not seen:
                    mark_notification_seen(notif_id)

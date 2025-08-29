# pp.py
import streamlit as st
import sqlite3
import io
from datetime import datetime
from PIL import Image

# Optional: streamlit-webrtc for video calls
try:
    from streamlit_webrtc import webrtc_streamer, RTCConfiguration
    WEbrtc_AVAILABLE = True
    RTC_CONFIGURATION = RTCConfiguration(
        {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    )
except Exception:
    WEbrtc_AVAILABLE = False

# -------------------------
# DB Setup & Migration
# -------------------------
DB_PATH = "feedchat.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

def init_db():
    # Users (username, password, profile_pic)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            profile_pic BLOB
        )
    """)
    # Posts (media supports image or video stored as BLOB)
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            message TEXT,
            media BLOB,
            media_type TEXT,
            timestamp TEXT
        )
    """)
    # Likes
    c.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            username TEXT
        )
    """)
    # Comments
    c.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            username TEXT,
            comment TEXT,
            timestamp TEXT
        )
    """)
    # Follows
    c.execute("""
        CREATE TABLE IF NOT EXISTS follows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            follower TEXT,
            following TEXT
        )
    """)
    # Messages
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)
    # Notifications
    c.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            message TEXT,
            timestamp TEXT,
            seen INTEGER DEFAULT 0
        )
    """)
    conn.commit()

init_db()

# -------------------------
# Helpers (DB operations)
# -------------------------
def safe_rerun():
    try:
        st.experimental_rerun()
    except Exception:
        try:
            st.rerun()
        except Exception:
            pass

# --- Users
def add_user(username, password, profile_pic):
    if not username:
        return
    username = username.strip()
    try:
        c.execute("INSERT INTO users (username, password, profile_pic) VALUES (?, ?, ?)",
                  (username, password, profile_pic))
        conn.commit()
    except sqlite3.IntegrityError:
        # Replace existing (update) - keep semantics simple
        c.execute("UPDATE users SET password=?, profile_pic=? WHERE username=?",
                  (password, profile_pic, username))
        conn.commit()

def verify_user(username, password):
    c.execute("SELECT 1 FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone() is not None

def get_user(username):
    if not username:
        return None
    c.execute("SELECT username, profile_pic FROM users WHERE username=?", (username,))
    row = c.fetchone()
    return row  # (username, profile_pic) or None

def get_user_profile_pic(username):
    row = get_user(username)
    return row[1] if row and row[1] else None

# --- Posts
def add_post(username, message, media=None, media_type=None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO posts (username, message, media, media_type, timestamp) VALUES (?, ?, ?, ?, ?)",
              (username, message, media, media_type, ts))
    conn.commit()
    # notify followers
    c.execute("SELECT follower FROM follows WHERE following=?", (username,))
    followers = c.fetchall()
    for (f,) in followers:
        add_notification(f, f"{username} posted: {(message or '')[:120]}")

def get_posts():
    c.execute("SELECT id, username, message, media, media_type, timestamp FROM posts ORDER BY id DESC")
    return c.fetchall()

# --- Likes
def add_like(post_id, username):
    c.execute("SELECT 1 FROM likes WHERE post_id=? AND username=?", (post_id, username))
    if not c.fetchone():
        c.execute("INSERT INTO likes (post_id, username) VALUES (?, ?)", (post_id, username))
        conn.commit()

def remove_like(post_id, username):
    c.execute("DELETE FROM likes WHERE post_id=? AND username=?", (post_id, username))
    conn.commit()

def has_liked(post_id, username):
    c.execute("SELECT 1 FROM likes WHERE post_id=? AND username=?", (post_id, username))
    return c.fetchone() is not None

def count_likes(post_id):
    c.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,))
    r = c.fetchone()
    return r[0] if r else 0

def count_total_likes_for_user(username):
    c.execute("""
        SELECT COUNT(*) FROM likes
        JOIN posts ON likes.post_id = posts.id
        WHERE posts.username=?
    """, (username,))
    r = c.fetchone()
    return r[0] if r else 0

# --- Comments
def add_comment(post_id, username, comment):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO comments (post_id, username, comment, timestamp) VALUES (?, ?, ?, ?)",
              (post_id, username, comment, ts))
    conn.commit()

def get_comments(post_id):
    c.execute("SELECT username, comment, timestamp FROM comments WHERE post_id=? ORDER BY id ASC", (post_id,))
    return c.fetchall()

# --- Follows
def follow_user(follower, following):
    if follower == following:
        return
    c.execute("SELECT 1 FROM follows WHERE follower=? AND following=?", (follower, following))
    if not c.fetchone():
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

def count_followers(username):
    return len(get_followers(username))

def count_following(username):
    return len(get_following(username))

# --- Messages
def send_message(sender, receiver, message):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO messages (sender, receiver, message, timestamp) VALUES (?, ?, ?, ?)",
              (sender, receiver, message, ts))
    conn.commit()
    add_notification(receiver, f"New message from {sender}")

def get_messages(user1, user2):
    c.execute("""SELECT sender, message, timestamp FROM messages
                 WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
                 ORDER BY id ASC""", (user1, user2, user2, user1))
    return c.fetchall()

# --- Notifications
def add_notification(username, message):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

# -------------------------
# UI (Streamlit)
# -------------------------
st.set_page_config(page_title="FeedChat", page_icon="💬", layout="wide")
st.title("💬 FeedChat")

# Session defaults
if "username" not in st.session_state:
    st.session_state.username = None
if "view_profile" not in st.session_state:
    st.session_state.view_profile = None

# --- Authentication area in sidebar ---
st.sidebar.header("Account")

auth_choice = st.sidebar.selectbox("I want to:", ["Login", "Register", "Logout"] if st.session_state.username else ["Login", "Register"])
if auth_choice == "Register":
    st.sidebar.subheader("Create account")
    reg_user = st.sidebar.text_input("Username", key="reg_user")
    reg_pass = st.sidebar.text_input("Password", type="password", key="reg_pass")
    reg_pic = st.sidebar.file_uploader("Profile picture (optional)", type=["png","jpg","jpeg"], key="reg_pic")
    if st.sidebar.button("Register account", key="reg_btn"):
        if not reg_user or not reg_user.strip() or not reg_pass:
            st.sidebar.error("Provide username and password.")
        else:
            pic_bytes = reg_pic.read() if reg_pic else None
            add_user(reg_user.strip(), reg_pass, pic_bytes)
            st.sidebar.success("Account created — now login.")
elif auth_choice == "Login":
    st.sidebar.subheader("Log in")
    login_user = st.sidebar.text_input("Username", key="login_user")
    login_pw = st.sidebar.text_input("Password", type="password", key="login_pw")
    if st.sidebar.button("Login", key="login_btn"):
        if verify_user(login_user, login_pw):
            st.session_state.username = login_user
            safe_rerun()
        else:
            st.sidebar.error("Invalid credentials.")
elif auth_choice == "Logout":
    if st.sidebar.button("Logout"):
        st.session_state.username = None
        st.session_state.view_profile = None
        safe_rerun()

# If not logged in, stop UI (so they must login/register)
if not st.session_state.username:
    st.info("Please register or login in the sidebar to use FeedChat.")
    st.stop()

# Top bar: show logged in user and unseen notifications count
col1, col2 = st.columns([8,1])
with col1:
    st.write(f"Logged in as **{st.session_state.username}**")
with col2:
    unseen = count_unseen(st.session_state.username)
    if unseen:
        st.button(f"🔔 {unseen}", key="notifs_btn")
    else:
        st.button("🔔 0", key="notifs_btn_zero")

# Play a small sound if there are unseen notifications (browser may autoplay block)
notes = get_notifications(st.session_state.username)
if any(n[3] == 0 for n in notes):
    st.markdown(
        """
        <audio autoplay>
          <source src="https://www.soundjay.com/buttons/sounds/button-3.mp3" type="audio/mp3">
        </audio>
        """,
        unsafe_allow_html=True,
    )

# Tabs
tabs = st.tabs(["Home", "Create Post", "Messages", "Notifications", "Profile", "Video Call"])
home_tab, create_tab, messages_tab, notifications_tab, profile_tab, videocall_tab = tabs

# --- Home (Feed)
with home_tab:
    st.header("📰 Home / Feed")
    posts = get_posts()
    if not posts:
        st.info("No posts yet — be the first to share!")
    else:
        for pid, user, msg, media, mtype, ts in posts:
            card = st.container()
            with card:
                c1, c2 = st.columns([1, 9])
                with c1:
                    user_row = get_user(user)
                    if user_row and user_row[1]:
                        try:
                            img = Image.open(io.BytesIO(user_row[1]))
                            st.image(img, width=60)
                        except Exception:
                            st.write("👤")
                    else:
                        st.write("👤")
                with c2:
                    st.markdown(f"**{user}**  ·  _{ts}_")
                    if msg:
                        st.write(msg)
                    if media and mtype == "image":
                        try:
                            st.image(Image.open(io.BytesIO(media)), use_container_width=True)
                        except Exception:
                            st.write("Unable to display image.")
                    elif media and mtype == "video":
                        try:
                            st.video(media)
                        except Exception:
                            st.write("Unable to play video.")

                    like_col, info_col = st.columns([1,4])
                    with like_col:
                        if has_liked(pid, st.session_state.username):
                            if st.button(f"Unlike ({count_likes(pid)})", key=f"unlike_{pid}"):
                                remove_like(pid, st.session_state.username)
                                safe_rerun()
                        else:
                            if st.button(f"Like ({count_likes(pid)})", key=f"like_{pid}"):
                                add_like(pid, st.session_state.username)
                                safe_rerun()
                    with info_col:
                        st.write(f"👍 {count_likes(pid)}  ·  💬 {len(get_comments(pid))}")

                    st.markdown("**Comments**")
                    for cu, cm, ct in get_comments(pid):
                        cu_row = get_user(cu)
                        cols = st.columns([1, 9])
                        if cu_row and cu_row[1]:
                            try:
                                cols[0].image(Image.open(io.BytesIO(cu_row[1])), width=30)
                            except Exception:
                                cols[0].write("👤")
                        else:
                            cols[0].write("👤")
                        cols[1].markdown(f"**{cu}**: {cm}  _({ct})_")

                    new_comment = st.text_input("Add a comment", key=f"comment_input_{pid}")
                    if st.button("Post comment", key=f"comment_btn_{pid}"):
                        if new_comment and new_comment.strip():
                            add_comment(pid, st.session_state.username, new_comment.strip())
                            safe_rerun()
            st.markdown("---")

# --- Create Post
with create_tab:
    st.header("✍️ Create a Post")
    post_text = st.text_area("What's on your mind?", key="create_text")
    media_file = st.file_uploader("Upload image/video (optional)", type=["png","jpg","jpeg","mp4","mov","avi"], key="create_media")
    media_bytes = None
    media_type = None
    if media_file:
        try:
            if media_file.type.startswith("image") or media_file.name.lower().endswith((".png", ".jpg", ".jpeg")):
                img = Image.open(media_file)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                media_bytes = buf.getvalue()
                media_type = "image"
            else:
                media_bytes = media_file.read()
                media_type = "video"
        except Exception:
            st.error("Could not process uploaded media.")
    if st.button("Post", key="create_post_btn"):
        if not (post_text and post_text.strip()) and not media_bytes:
            st.warning("Write something or upload media.")
        else:
            add_post(st.session_state.username, post_text.strip() if post_text else None, media_bytes, media_type)
            st.success("Posted!")
            safe_rerun()

# --- Messages
with messages_tab:
    st.header("💬 Messages")
    other = st.text_input("Open chat with (username)", key="msg_other")
    if other:
        conv = get_messages(st.session_state.username, other)
        if not conv:
            st.info("No messages yet.")
        else:
            for s, m, ts in conv:
                st.markdown(f"**{s}** ({ts}): {m}")
    new_msg = st.text_area("Type message", key="msg_text")
    if st.button("Send message", key="send_msg_btn"):
        if other and new_msg and new_msg.strip():
            send_message(st.session_state.username, other, new_msg.strip())
            st.success("Message sent.")
            safe_rerun()

# --- Notifications
with notifications_tab:
    st.header("🔔 Notifications")
    notes = get_notifications(st.session_state.username)
    if not notes:
        st.info("No notifications.")
    else:
        for nid, msg, ts, seen in notes:
            st.markdown(f"- {'✅' if seen else '🆕'} {msg}  _({ts})_")
    if st.button("Mark all notifications as read"):
        mark_notifications_seen(st.session_state.username)
        safe_rerun()

# --- Profile
with profile_tab:
    st.header("👤 Profile")
    target = st.session_state.view_profile or st.session_state.username
    row = get_user(target)
    if row:
        uname, pic = row
        if pic:
            try:
                st.image(Image.open(io.BytesIO(pic)), width=140)
            except Exception:
                st.write("👤")
        st.markdown(f"**Username:** {uname}")
        colA, colB, colC = st.columns(3)
        with colA:
            st.metric("Followers", count_followers(uname))
        with colB:
            st.metric("Following", count_following(uname))
        with colC:
            st.metric("Likes received", count_total_likes_for_user(uname))
    else:
        st.error("User not found.")

    st.markdown("---")
    view_user = st.text_input("Enter username to view profile", key="profile_view_input")
    if view_user:
        user_row = get_user(view_user)
        if user_row:
            ou, opic = user_row
            st.markdown(f"### {ou}'s Profile")
            if opic:
                try:
                    st.image(Image.open(io.BytesIO(opic)), width=100)
                except Exception:
                    st.write("👤")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Followers", count_followers(ou))
            with col2:
                st.metric("Following", count_following(ou))
            with col3:
                st.metric("Likes received", count_total_likes_for_user(ou))

            if is_following(st.session_state.username, ou):
                if st.button("Unfollow", key=f"unfollow_{ou}"):
                    unfollow_user(st.session_state.username, ou)
                    safe_rerun()
            else:
                if st.button("Follow", key=f"follow_{ou}"):
                    follow_user(st.session_state.username, ou)
                    safe_rerun()

            st.markdown("**Their posts**")
            their_posts = [p for p in get_posts() if p[1] == ou]
            if not their_posts:
                st.info("No posts by this user.")
            else:
                for pid, usr, msg, media, mtype, ts in their_posts:
                    st.markdown(f"**{usr}** · _{ts}_")
                    if msg:
                        st.write(msg)
                    if media and mtype == "image":
                        try:
                            st.image(Image.open(io.BytesIO(media)), use_container_width=True)
                        except Exception:
                            st.write("Unable to display image.")
                    elif media and mtype == "video":
                        try:
                            st.video(media)
                        except Exception:
                            st.write("Unable to play video.")
                    st.caption(f"❤️ {count_likes(pid)} likes")
                    st.markdown("---")
        else:
            st.error("User not found.")

# --- Video Call Tab
with videocall_tab:
    st.header("📹 Video Call")
    st.write("Start a small peer-to-peer video call (uses your camera & mic).")
    if not WEbrtc_AVAILABLE:
        st.warning("Video call requires the `streamlit-webrtc` package. Install with: pip install streamlit-webrtc")
    else:
        # A simple webrtc streamer that shows local camera + audio
        try:
            webrtc_streamer(
                key="feedchat-video-call",
                rtc_configuration=RTC_CONFIGURATION,
                media_stream_constraints={"video": True, "audio": True},
            )
        except Exception as e:
            st.error(f"Could not start video call: {e}")

# End of file

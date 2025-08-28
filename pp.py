import streamlit as st
import sqlite3
from datetime import datetime
from PIL import Image
import io

# ---------------------------
# Database
# ---------------------------
conn = sqlite3.connect("feedchat.db", check_same_thread=False)
c = conn.cursor()

# Users
c.execute("""CREATE TABLE IF NOT EXISTS users
             (username TEXT PRIMARY KEY, profile_pic BLOB)""")

# Posts: media (image or video) + media_type tells how to render
c.execute("""CREATE TABLE IF NOT EXISTS posts
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT,
              message TEXT,
              media BLOB,
              media_type TEXT,
              timestamp TEXT)""")

# Followers
c.execute("""CREATE TABLE IF NOT EXISTS followers
             (follower TEXT, following TEXT)""")

# Likes
c.execute("""CREATE TABLE IF NOT EXISTS likes
             (post_id INTEGER, username TEXT)""")

# Comments
c.execute("""CREATE TABLE IF NOT EXISTS comments
             (post_id INTEGER, username TEXT, comment TEXT, timestamp TEXT)""")

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

# ---------------------------
# Helper functions
# ---------------------------
def add_user(username, profile_pic=None):
    if not get_user(username):
        c.execute("INSERT INTO users VALUES (?, ?)", (username, profile_pic))
        conn.commit()

def get_user(username):
    c.execute("SELECT username, profile_pic FROM users WHERE username=?", (username,))
    return c.fetchone()  # returns (username, profile_pic) or None

def add_post(username, message, media_bytes, media_type):
    c.execute(
        "INSERT INTO posts (username, message, media, media_type, timestamp) VALUES (?,?,?,?,?)",
        (username, message, media_bytes, media_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()

    # notify followers
    c.execute("SELECT follower FROM followers WHERE following=?", (username,))
    followers = c.fetchall()
    for (f,) in followers:
        add_notification(f, "post", f"{username} just posted: { (message or '')[:40] }...")

def get_posts(all_posts=True, user=None):
    if user:
        c.execute("SELECT id, username, message, media, media_type, timestamp FROM posts WHERE username=? ORDER BY id DESC", (user,))
    else:
        c.execute("SELECT id, username, message, media, media_type, timestamp FROM posts ORDER BY id DESC")
    return c.fetchall()

def follow_user(follower, following):
    if follower == following:
        return
    if not is_following(follower, following):
        c.execute("INSERT INTO followers VALUES (?, ?)", (follower, following))
        conn.commit()

def unfollow_user(follower, following):
    c.execute("DELETE FROM followers WHERE follower=? AND following=?", (follower, following))
    conn.commit()

def is_following(follower, following):
    c.execute("SELECT 1 FROM followers WHERE follower=? AND following=?", (follower, following))
    return c.fetchone() is not None

def like_post_db(post_id, username):
    if not has_liked(post_id, username):
        c.execute("INSERT INTO likes VALUES (?, ?)", (post_id, username))
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

def count_total_likes(user):
    c.execute("""SELECT COUNT(*) FROM likes
                 JOIN posts ON likes.post_id = posts.id
                 WHERE posts.username=?""", (user,))
    r = c.fetchone()
    return r[0] if r else 0

def add_comment(post_id, username, comment):
    c.execute("INSERT INTO comments VALUES (?,?,?,?)", (
        post_id, username, comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()

def get_comments(post_id):
    c.execute("SELECT username, comment, timestamp FROM comments WHERE post_id=? ORDER BY timestamp", (post_id,))
    return c.fetchall()

def send_message(sender, receiver, message):
    if not get_user(receiver):
        return False
    c.execute("INSERT INTO messages VALUES (?,?,?,?)", (
        sender, receiver, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    add_notification(receiver, "message", f"New message from {sender}: { (message or '')[:40] }...")
    return True

def get_messages(user1, user2):
    c.execute("""SELECT sender, receiver, message, timestamp FROM messages
                 WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
                 ORDER BY timestamp""", (user1, user2, user2, user1))
    return c.fetchall()

# Notifications
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
    r = c.fetchone()
    return r[0] if r else 0

def get_user_liked_posts(username):
    c.execute("""SELECT p.id, p.username, p.message, p.media, p.media_type, p.timestamp
                 FROM posts p JOIN likes l ON l.post_id = p.id
                 WHERE l.username=? ORDER BY p.id DESC""", (username,))
    return c.fetchall()

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="FeedChat", page_icon="💬", layout="wide")
st.title("💬 FeedChat")

# ---------------------------
# Login / Signup (simple)
# ---------------------------
if "username" not in st.session_state:
    st.session_state.username = None

if not st.session_state.username:
    st.sidebar.header("👤 Login / Signup")
    entered_username = st.sidebar.text_input("Username")
    profile_pic_file = st.sidebar.file_uploader("Upload profile picture (optional)", type=["png","jpg","jpeg"])
    if st.sidebar.button("Enter / Create"):
        if not entered_username or not entered_username.strip():
            st.sidebar.error("Enter a username.")
        else:
            pic_bytes = None
            if profile_pic_file:
                img = Image.open(profile_pic_file)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                pic_bytes = buf.getvalue()
            add_user(entered_username, pic_bytes)
            st.session_state.username = entered_username
            st.experimental_rerun()
    st.stop()

# Top bar: show user and logout
col_a, col_b = st.columns([8,2])
with col_a:
    st.write(f"Logged in as **{st.session_state.username}**")
with col_b:
    if st.button("Logout"):
        st.session_state.username = None
        st.experimental_rerun()

# Main tabs (include notifications count)
unread = count_unread_notifications(st.session_state.username)
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📰 News Feed",
    "✍️ Create Post",
    "💬 Messages",
    "👤 Profile",
    f"🔔 Notifications ({unread})"
])

# ---------------------------
# News Feed
# ---------------------------
with tab1:
    st.subheader("📰 News Feed")
    posts = get_posts()
    if not posts:
        st.info("No posts yet.")
    else:
        for pid, user, msg, media, media_type, ts in posts:
            # user profile pic (if any)
            u = get_user(user)
            row = st.container()
            with row:
                col1, col2 = st.columns([1, 8])
                with col1:
                    if u and u[1]:
                        st.image(u[1], width=50)
                    else:
                        st.write("👤")
                with col2:
                    st.markdown(f"**{user}** · ⏱ {ts}")
                    if msg:
                        st.write(msg)
                    # media rendering
                    if media and media_type == "image":
                        st.image(media, use_container_width=True)
                    elif media and media_type == "video":
                        st.video(media)

                    # Likes / Comments UI
                    lcol1, lcol2 = st.columns([1,4])
                    with lcol1:
                        if has_liked(pid, st.session_state.username):
                            if st.button("💔 Unlike", key=f"unlike_{pid}"):
                                unlike_post_db(pid, st.session_state.username)
                                st.experimental_rerun()
                        else:
                            if st.button("❤️ Like", key=f"like_{pid}"):
                                like_post_db(pid, st.session_state.username)
                                st.experimental_rerun()
                    with lcol2:
                        st.write(f"👍 {count_likes(pid)} likes")

                    # Comments
                    st.markdown("💬 Comments:")
                    comments = get_comments(pid)
                    for cu, cm, ct in comments:
                        cu_user = get_user(cu)
                        rowc = st.columns([1, 9])
                        if cu_user and cu_user[1]:
                            rowc[0].image(cu_user[1], width=30)
                        rowc[1].markdown(f"**{cu}**: {cm}  ⏱ {ct}")

                    comment_input = st.text_input("Add comment", key=f"comment_input_{pid}")
                    if st.button("Comment", key=f"comment_btn_{pid}"):
                        if comment_input.strip():
                            add_comment(pid, st.session_state.username, comment_input)
                            st.experimental_rerun()
            st.markdown("---")

# ---------------------------
# Create Post (supports image & video)
# ---------------------------
with tab2:
    st.subheader("✍️ Create a Post (image or video allowed)")
    post_text = st.text_area("What's on your mind?")
    media_file = st.file_uploader("Upload image or video (optional)", type=["png","jpg","jpeg","mp4","mov","avi","mkv"])
    media_bytes = None
    media_type = None

    if media_file:
        # streamlit file uploader object gives .type for MIME
        try:
            mime = media_file.type
        except:
            mime = ""
        if mime.startswith("image") or media_file.name.lower().endswith((".png", ".jpg", ".jpeg")):
            img = Image.open(media_file)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            media_bytes = buf.getvalue()
            media_type = "image"
        else:
            # treat as video (read raw bytes)
            media_bytes = media_file.read()
            media_type = "video"

    if st.button("Post"):
        if (not post_text or not post_text.strip()) and not media_bytes:
            st.warning("Please write something or upload an image/video.")
        else:
            add_post(st.session_state.username, post_text, media_bytes, media_type)
            st.success("✅ Post created!")
            st.experimental_rerun()

# ---------------------------
# Messages
# ---------------------------
with tab3:
    st.subheader("💬 Messages")
    with st.expander("Send a message"):
        to_user = st.text_input("Send to (username):", key="msg_to")
        msg_body = st.text_area("Message:", key="msg_body")
        if st.button("Send Message"):
            if not to_user.strip() or not msg_body.strip():
                st.warning("Fill recipient and message.")
            elif not get_user(to_user):
                st.error("User does not exist.")
            else:
                send_message(st.session_state.username, to_user, msg_body)
                st.success("✅ Message sent.")
                st.experimental_rerun()

    st.markdown("---")
    st.write("Open a chat to view conversation:")
    chat_with = st.text_input("Chat with (username):", key="chat_with")
    if chat_with:
        conv = get_messages(st.session_state.username, chat_with)
        if not conv:
            st.info("No messages yet.")
        else:
            for s, r, m, ts in conv:
                st.markdown(f"**{s}** ({ts}): {m}")

# ---------------------------
# Profile
# ---------------------------
with tab4:
    st.subheader(f"👤 {st.session_state.username}'s Profile")
    me = get_user(st.session_state.username)
    if me and me[1]:
        st.image(me[1], width=120)

    # show metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Followers", count_followers(st.session_state.username))
    with col2:
        st.metric("Following", count_following(st.session_state.username))
    with col3:
        st.metric("Total Likes Received", count_total_likes(st.session_state.username))

    st.markdown("### Your Posts")
    my_posts = get_posts(user=st.session_state.username)
    if not my_posts:
        st.info("You haven't posted yet.")
    else:
        for pid, user, msg, media, mtype, ts in my_posts:
            st.markdown(f"**{ts}**")
            if msg:
                st.write(msg)
            if media and mtype == "image":
                st.image(media, use_container_width=True)
            elif media and mtype == "video":
                st.video(media)
            st.caption(f"❤️ {count_likes(pid)} likes")
            st.markdown("---")

    # liked posts
    st.markdown("### Posts You Liked")
    liked_posts = get_user_liked_posts(st.session_state.username)
    if not liked_posts:
        st.info("You haven't liked any posts yet.")
    else:
        for pid, user, msg, media, mtype, ts in liked_posts:
            st.markdown(f"**{user}** · {ts}")
            if msg:
                st.write(msg)
            if media and mtype == "image":
                st.image(media, use_container_width=True)
            elif media and mtype == "video":
                st.video(media)
            st.markdown("---")

    # View other user's profile + follow/unfollow
    st.markdown("### View another user's profile")
    other = st.text_input("Enter username to view:", key="profile_view")
    if other:
        ou = get_user(other)
        if not ou:
            st.error("User not found.")
        else:
            st.markdown(f"### 👤 {other}")
            if ou[1]:
                st.image(ou[1], width=100)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Followers", count_followers(other))
            with c2:
                st.metric("Following", count_following(other))
            with c3:
                st.metric("Total Likes", count_total_likes(other))

            if is_following(st.session_state.username, other):
                if st.button("Unfollow", key=f"unfollow_{other}"):
                    unfollow_user(st.session_state.username, other)
                    st.experimental_rerun()
            else:
                if st.button("Follow", key=f"follow_{other}"):
                    follow_user(st.session_state.username, other)
                    st.experimental_rerun()

            st.markdown("#### Their Posts")
            their_posts = get_posts(user=other)
            if not their_posts:
                st.info("No posts yet.")
            else:
                for pid, user, msg, media, mtype, ts in their_posts:
                    st.markdown(f"**{user}** · {ts}")
                    if msg:
                        st.write(msg)
                    if media and mtype == "image":
                        st.image(media, use_container_width=True)
                    elif media and mtype == "video":
                        st.video(media)
                    st.caption(f"❤️ {count_likes(pid)} likes")
                    st.markdown("---")

# ---------------------------
# Notifications
# ---------------------------
with tab5:
    st.subheader("🔔 Notifications")
    notes = get_notifications(st.session_state.username)
    if not notes:
        st.info("No notifications")
    else:
        for nid, ntype, msg, is_read, ts in notes:
            st.markdown(f"- {'✅' if is_read else '🆕'} **[{ntype.upper()}]** {msg} _(at {ts})_")
    if st.button("Mark all as read"):
        mark_notifications_read(st.session_state.username)
        st.experimental_rerun()

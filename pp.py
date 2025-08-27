import streamlit as st
import sqlite3, io
from PIL import Image
from datetime import datetime

# ----------------------
# Database Setup
# ----------------------
conn = sqlite3.connect("feedchat.db", check_same_thread=False)  # renamed DB file
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users
             (username TEXT PRIMARY KEY, profile_pic BLOB)''')

c.execute('''CREATE TABLE IF NOT EXISTS posts
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT,
              message TEXT,
              image BLOB,
              timestamp TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS likes
             (post_id INTEGER, username TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS comments
             (post_id INTEGER, username TEXT, comment TEXT, timestamp TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS messages
             (sender TEXT, receiver TEXT, message TEXT, timestamp TEXT)''')

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

def add_post(username, message, image):
    c.execute("INSERT INTO posts (username, message, image, timestamp) VALUES (?,?,?,?)",
              (username, message, image, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_posts():
    c.execute("SELECT * FROM posts ORDER BY id DESC")
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

def get_messages(user1, user2):
    c.execute("""SELECT sender, message, timestamp FROM messages
                 WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
                 ORDER BY timestamp ASC""", (user1, user2, user2, user1))
    return c.fetchall()

# ----------------------
# Streamlit App
# ----------------------
st.set_page_config(page_title="FeedChat", page_icon="💬", layout="wide")
st.title("💬 FeedChat")

# Sidebar - Login / Register
st.sidebar.header("👤 User Login / Register")
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
        st.sidebar.success("✅ Profile saved!")

if username:
    st.session_state.username = username
else:
    st.warning("Please enter your username in the sidebar to continue.")

# ----------------------
# Main Tabs
# ----------------------
if "username" in st.session_state:
    tab1, tab2, tab3 = st.tabs(["📰 News Feed", "✍️ Create Post", "💬 Messages"])

    # News Feed
    with tab1:
        posts = get_posts()
        if not posts:
            st.info("No posts yet. Be the first to post something!")
        else:
            for post in posts:
                post_id, user, message, image, timestamp = post
                u, pic = get_user(user)

                col1, col2 = st.columns([1, 8])
                with col1:
                    if pic:
                        st.image(pic, width=50)
                with col2:
                    st.markdown(f"**{u}** · ⏱ {timestamp}")
                    if message:
                        st.write(message)
                    if image:
                        st.image(image, use_container_width=True)

                # Likes
                col1, col2 = st.columns([1, 5])
                with col1:
                    if has_liked(post_id, st.session_state.username):
                        if st.button("Unlike", key=f"unlike_{post_id}"):
                            unlike_post(post_id, st.session_state.username)
                            st.experimental_rerun()
                    else:
                        if st.button("Like", key=f"like_{post_id}"):
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

                comment_input = st.text_input(f"Add comment to post {post_id}", key=f"comment_input_{post_id}")
                if st.button("Comment", key=f"comment_btn_{post_id}"):
                    if comment_input.strip():
                        add_comment(post_id, st.session_state.username, comment_input)
                        st.experimental_rerun()
                st.markdown("---")

    # Create Post
    with tab2:
        st.subheader("✍️ Create a Post")
        msg = st.text_area("What's on your mind?")
        uploaded_img = st.file_uploader("Upload a photo", type=["png","jpg","jpeg"])
        if st.button("Post Now"):
            if msg.strip() or uploaded_img:
                img_bytes = None
                if uploaded_img:
                    img = Image.open(uploaded_img)
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="PNG")
                    img_bytes = img_bytes.getvalue()
                add_post(st.session_state.username, msg, img_bytes)
                st.success("✅ Post created!")
                st.experimental_rerun()
            else:
                st.warning("Please write something or upload an image.")

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



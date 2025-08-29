import streamlit as st
import sqlite3

# ===================================
# Database setup (same as before)
# ===================================
conn = sqlite3.connect("feedchat.db", check_same_thread=False)
c = conn.cursor()

# --- Users table ---
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    profile_pic BLOB
)
""")

# --- Posts table ---
c.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# --- Comments table ---
c.execute("""
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    username TEXT,
    comment TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# --- Likes table ---
c.execute("""
CREATE TABLE IF NOT EXISTS likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    username TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# --- Messages table ---
c.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# ===================================
# Helper functions
# ===================================
def add_user(username, password, profile_pic=None):
    c.execute("INSERT OR REPLACE INTO users (username, password, profile_pic) VALUES (?, ?, ?)",
              (username, password, profile_pic))
    conn.commit()

def verify_user(username, password):
    c.execute("SELECT 1 FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone() is not None

def get_all_users():
    c.execute("SELECT username FROM users")
    return [u[0] for u in c.fetchall()]

def add_post(username, message):
    c.execute("INSERT INTO posts (username, message) VALUES (?, ?)", (username, message))
    conn.commit()

def get_posts():
    c.execute("SELECT id, username, message, timestamp FROM posts ORDER BY id DESC")
    return c.fetchall()

def add_comment(post_id, username, comment):
    c.execute("INSERT INTO comments (post_id, username, comment) VALUES (?, ?, ?)",
              (post_id, username, comment))
    conn.commit()

def get_comments(post_id):
    c.execute("SELECT username, comment, timestamp FROM comments WHERE post_id=? ORDER BY id ASC", (post_id,))
    return c.fetchall()

def add_like(post_id, username):
    c.execute("SELECT 1 FROM likes WHERE post_id=? AND username=?", (post_id, username))
    if not c.fetchone():
        c.execute("INSERT INTO likes (post_id, username) VALUES (?, ?)", (post_id, username))
        conn.commit()

def count_likes(post_id):
    c.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,))
    return c.fetchone()[0]

def send_message(sender, receiver, message):
    c.execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)",
              (sender, receiver, message))
    conn.commit()

def get_messages(user1, user2):
    c.execute("""
        SELECT sender, message, timestamp 
        FROM messages
        WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
        ORDER BY id ASC
    """, (user1, user2, user2, user1))
    return c.fetchall()

# ===================================
# Streamlit UI
# ===================================
st.set_page_config(page_title="📱 FeedChat", layout="wide")

if "user" not in st.session_state:
    st.session_state["user"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Feed"

# Sidebar navigation
with st.sidebar:
    st.title("📱 FeedChat")
    if st.session_state["user"]:
        st.success(f"👋 {st.session_state['user']}")
        if st.button("Feed"): st.session_state["page"] = "Feed"
        if st.button("Messages"): st.session_state["page"] = "Messages"
        if st.button("Logout"):
            st.session_state["user"] = None
            st.rerun()
    else:
        menu = st.radio("Navigation", ["Login", "Signup"])

# ===================================
# Login / Signup Pages
# ===================================
if not st.session_state["user"]:
    if menu == "Signup":
        st.subheader("📝 Create Account")
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        pic = st.file_uploader("Upload Profile Picture", type=["jpg", "png"])
        if st.button("Signup"):
            if new_user and new_pass:
                pic_bytes = pic.read() if pic else None
                add_user(new_user, new_pass, pic_bytes)
                st.success("✅ Account created! Go to Login.")
            else:
                st.error("❌ Username and password required")

    elif menu == "Login":
        st.subheader("🔐 Login")
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if verify_user(user, pw):
                st.session_state["user"] = user
                st.session_state["page"] = "Feed"
                st.rerun()
            else:
                st.error("❌ Invalid login")

# ===================================
# Main Layout (when logged in)
# ===================================
else:
    left, center, right = st.columns([1.2, 3, 1.2])

    # Left column (profile & users)
    with left:
        st.subheader("👥 Users")
        users = get_all_users()
        for u in users:
            if u != st.session_state["user"]:
                st.write(f"🔹 {u}")

    # Center column (Feed / Messages)
    with center:
        if st.session_state["page"] == "Feed":
            st.subheader("📢 Feed")

            post_msg = st.text_area("What's happening?")
            if st.button("Post"):
                if post_msg.strip():
                    add_post(st.session_state["user"], post_msg)
                    st.success("✅ Posted!")
                    st.rerun()

            posts = get_posts()
            for pid, uname, msg, ts in posts:
                st.markdown(f"**{uname}** 🕒 {ts}")
                st.write(msg)
                st.write(f"👍 {count_likes(pid)} · 💬 {len(get_comments(pid))}")

                c1, c2 = st.columns([1, 2])
                if c1.button(f"👍 Like {pid}"):
                    add_like(pid, st.session_state["user"])
                    st.rerun()
                comment = c2.text_input(f"Comment on {pid}", key=f"c{pid}")
                if c2.button(f"Add {pid}"):
                    if comment.strip():
                        add_comment(pid, st.session_state["user"], comment)
                        st.rerun()

                with st.expander("💬 View Comments"):
                    for cu, cm, ct in get_comments(pid):
                        st.markdown(f"- **{cu}**: {cm} 🕒 {ct}")
                st.divider()

        elif st.session_state["page"] == "Messages":
            st.subheader("💬 Messages")
            all_users = [u for u in get_all_users() if u != st.session_state["user"]]
            receiver = st.selectbox("Chat with:", all_users)

            msg = st.text_input("Type a message")
            if st.button("Send"):
                if msg.strip():
                    send_message(st.session_state["user"], receiver, msg)
                    st.rerun()

            if receiver:
                chat = get_messages(st.session_state["user"], receiver)
                for sender, message, ts in chat:
                    if sender == st.session_state["user"]:
                        st.markdown(f"<p style='text-align:right; color:blue;'>You: {message} 🕒 {ts}</p>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<p style='text-align:left; color:green;'>{sender}: {message} 🕒 {ts}</p>", unsafe_allow_html=True)

    # Right column (extra info)
    with right:
        st.subheader("📊 Stats")
        st.write(f"Total Users: {len(get_all_users())}")
        st.write(f"Total Posts: {len(get_posts())}")

import streamlit as st
import sqlite3
import datetime
import random
import time
from PIL import Image
import io
import base64
import json

# ===================================
# Database Initialization - SIMPLIFIED
# ===================================
def init_db():
    conn = sqlite3.connect("feedchat.db", check_same_thread=False)
    c = conn.cursor()

    # Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT,
        profile_pic BLOB,
        bio TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Posts table
    c.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        media_type TEXT,
        media_data BLOB,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Likes table
    c.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        post_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Comments table
    c.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_id INTEGER,
        content TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Follows table
    c.execute("""
    CREATE TABLE IF NOT EXISTS follows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        follower_id INTEGER,
        following_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Messages table
    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        content TEXT,
        is_read BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    return conn

# Initialize database
conn = init_db()

# ===================================
# CORE FUNCTIONS
# ===================================
def is_valid_image(image_data):
    """Check if the image data is valid"""
    try:
        if image_data is None:
            return False
        image = Image.open(io.BytesIO(image_data))
        image.verify()
        return True
    except:
        return False

def display_image_safely(image_data, caption="", width=None):
    """Safely display an image"""
    try:
        if image_data and is_valid_image(image_data):
            if width:
                st.image(io.BytesIO(image_data), caption=caption, width=width)
            else:
                st.image(io.BytesIO(image_data), caption=caption, use_container_width=True)
        else:
            st.warning("Unable to display image")
    except Exception as e:
        st.warning(f"Error displaying image: {str(e)}")

def create_user(username, password, email, profile_pic=None, bio=""):
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=?", (username,))
        if c.fetchone():
            return False
        if profile_pic and not is_valid_image(profile_pic):
            st.error("Invalid profile picture format.")
            return False
        c.execute("INSERT INTO users (username, password, email, profile_pic, bio) VALUES (?, ?, ?, ?, ?)",
                 (username, password, email, profile_pic, bio))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except:
            pass

def verify_user(username, password):
    try:
        c = conn.cursor()
        c.execute("SELECT id, username FROM users WHERE username=? AND password=?", (username, password))
        return c.fetchone()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except:
            pass

def get_user(user_id):
    try:
        c = conn.cursor()
        c.execute("SELECT id, username, email, profile_pic, bio FROM users WHERE id=?", (user_id,))
        return c.fetchone()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except:
            pass

def get_all_users():
    try:
        c = conn.cursor()
        c.execute("SELECT id, username FROM users")
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except:
            pass

def create_post(user_id, content, media_type=None, media_data=None):
    try:
        c = conn.cursor()
        if media_data and media_type == "image" and not is_valid_image(media_data):
            st.error("Invalid image format.")
            return None
        c.execute("INSERT INTO posts (user_id, content, media_type, media_data) VALUES (?, ?, ?, ?)",
                 (user_id, content, media_type, media_data))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except:
            pass

def get_posts(user_id=None):
    try:
        c = conn.cursor()
        if user_id:
            c.execute("""
                SELECT p.id, p.user_id, u.username, p.content, p.media_type, p.media_data, p.created_at,
                       COUNT(l.id) as like_count,
                       SUM(CASE WHEN l.user_id = ? THEN 1 ELSE 0 END) as user_liked
                FROM posts p
                JOIN users u ON p.user_id = u.id
                LEFT JOIN likes l ON p.id = l.post_id
                WHERE p.user_id IN (SELECT following_id FROM follows WHERE follower_id=?) OR p.user_id=?
                GROUP BY p.id
                ORDER BY p.created_at DESC
            """, (user_id, user_id, user_id))
        else:
            c.execute("""
                SELECT p.id, p.user_id, u.username, p.content, p.media_type, p.media_data, p.created_at,
                       COUNT(l.id) as like_count,
                       0 as user_liked
                FROM posts p
                JOIN users u ON p.user_id = u.id
                LEFT JOIN likes l ON p.id = l.post_id
                GROUP BY p.id
                ORDER BY p.created_at DESC
            """)
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except:
            pass

def like_post(user_id, post_id):
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM likes WHERE user_id=? AND post_id=?", (user_id, post_id))
        if not c.fetchone():
            c.execute("INSERT INTO likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
            conn.commit()
            return True
        return False
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except:
            pass

def follow_user(follower_id, following_id):
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM follows WHERE follower_id=? AND following_id=?", (follower_id, following_id))
        if not c.fetchone():
            c.execute("INSERT INTO follows (follower_id, following_id) VALUES (?, ?)", (follower_id, following_id))
            conn.commit()
            return True
        return False
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except:
            pass

def unfollow_user(follower_id, following_id):
    try:
        c = conn.cursor()
        c.execute("DELETE FROM follows WHERE follower_id=? AND following_id=?", (follower_id, following_id))
        conn.commit()
        return c.rowcount > 0
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except:
            pass

def is_following(follower_id, following_id):
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM follows WHERE follower_id=? AND following_id=?", (follower_id, following_id))
        return c.fetchone() is not None
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except:
            pass

def add_comment(post_id, user_id, content):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
                 (post_id, user_id, content))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except:
            pass

def get_comments(post_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT c.id, c.user_id, u.username, c.content, c.created_at
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id=?
            ORDER BY c.created_at ASC
        """, (post_id,))
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except:
            pass

def get_comment_count(post_id):
    try:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM comments WHERE post_id=?", (post_id,))
        return c.fetchone()[0]
    except sqlite3.Error as e:
        return 0
    finally:
        try:
            c.close()
        except:
            pass

def send_message(sender_id, receiver_id, content):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)",
                 (sender_id, receiver_id, content))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except:
            pass

def get_messages(user1_id, user2_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT m.id, m.sender_id, u1.username as sender, m.receiver_id, u2.username as receiver, 
                   m.content, m.is_read, m.created_at
            FROM messages m
            JOIN users u1 ON m.sender_id = u1.id
            JOIN users u2 ON m.receiver_id = u2.id
            WHERE (m.sender_id=? AND m.receiver_id=?) OR (m.sender_id=? AND m.receiver_id=?)
            ORDER BY m.created_at ASC
        """, (user1_id, user2_id, user2_id, user1_id))
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except:
            pass

def get_conversations(user_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT DISTINCT 
                CASE WHEN m.sender_id = ? THEN m.receiver_id ELSE m.sender_id END as other_user_id,
                u.username,
                (SELECT content FROM messages 
                 WHERE (sender_id = ? AND receiver_id = other_user_id) 
                    OR (sender_id = other_user_id AND receiver_id = ?)
                 ORDER BY created_at DESC LIMIT 1) as last_message
            FROM messages m
            JOIN users u ON u.id = CASE WHEN m.sender_id = ? THEN m.receiver_id ELSE m.sender_id END
            WHERE (m.sender_id = ? OR m.receiver_id = ?)
            GROUP BY other_user_id
            ORDER BY last_message DESC
        """, (user_id, user_id, user_id, user_id, user_id, user_id))
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except:
            pass

def get_suggested_users(user_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT id, username 
            FROM users 
            WHERE id != ? 
            AND id NOT IN (SELECT following_id FROM follows WHERE follower_id=?)
            ORDER BY RANDOM() 
            LIMIT 5
        """, (user_id, user_id))
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except:
            pass

# ===================================
# Streamlit UI
# ===================================
st.set_page_config(page_title="FeedChat", page_icon="💬", layout="wide")

# Initialize session state
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Feed"
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None
if "show_comments" not in st.session_state:
    st.session_state.show_comments = {}

# Sidebar
with st.sidebar:
    st.title("💬 FeedChat")
    
    if st.session_state.user:
        user_info = get_user(st.session_state.user[0])
        if user_info:
            if user_info[3]:
                display_image_safely(user_info[3], width=80)
            st.success(f"**Welcome, {user_info[1]}!**")
        
        st.markdown("---")
        
        if st.button("🏠 Feed", use_container_width=True):
            st.session_state.page = "Feed"
        if st.button("💬 Messages", use_container_width=True):
            st.session_state.page = "Messages"
        if st.button("👥 Discover", use_container_width=True):
            st.session_state.page = "Discover"
        if st.button("👤 Profile", use_container_width=True):
            st.session_state.page = "Profile"
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = "Feed"
            st.rerun()
    else:
        st.info("Please login to use FeedChat")

# Main content
if not st.session_state.user:
    # Login/Signup page
    st.title("Welcome to FeedChat")
    
    auth_tab1, auth_tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with auth_tab1:
        with st.form("Login"):
            st.subheader("Welcome Back!")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login", use_container_width=True):
                if username and password:
                    user = verify_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter both username and password")
    
    with auth_tab2:
        with st.form("Sign Up"):
            st.subheader("Join FeedChat!")
            new_username = st.text_input("Choose a username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Choose a password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            profile_pic = st.file_uploader("Profile picture (optional)", type=["jpg", "png", "jpeg"])
            bio = st.text_area("Bio (optional)")
            
            if st.form_submit_button("Create Account", use_container_width=True):
                if new_password != confirm_password:
                    st.error("Passwords don't match")
                elif not new_username or not new_email or not new_password:
                    st.error("Please fill in all required fields")
                else:
                    profile_pic_data = profile_pic.read() if profile_pic else None
                    if create_user(new_username, new_password, new_email, profile_pic_data, bio):
                        st.success("Account created! Please login.")
                    else:
                        st.error("Username already exists")

else:
    user_id = st.session_state.user[0]
    
    # Feed Page
    if st.session_state.page == "Feed":
        st.header("📱 Your Feed")
        
        # Create post
        with st.expander("➕ Create New Post", expanded=False):
            post_content = st.text_area("What's on your mind?", height=100)
            media_file = st.file_uploader("Upload image", type=["jpg", "png", "jpeg"])
            
            if st.button("Post", use_container_width=True):
                if post_content or media_file:
                    media_data = media_file.read() if media_file else None
                    media_type = "image" if media_file else None
                    if create_post(user_id, post_content, media_type, media_data):
                        st.success("Posted successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to create post")
                else:
                    st.warning("Please add some content or media to your post")
        
        # Display posts
        posts = get_posts(user_id)
        if not posts:
            st.info("✨ No posts yet. Follow some users to see their posts here!")
        else:
            for post in posts:
                with st.container():
                    st.markdown("---")
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        user_info = get_user(post[1])
                        if user_info and user_info[3]:
                            display_image_safely(user_info[3], width=50)
                    with col2:
                        st.write(f"**{post[2]}** · {post[6]}")
                    
                    st.write(post[3])
                    
                    if post[4] and post[5]:
                        if post[4] == "image":
                            display_image_safely(post[5], use_container_width=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        like_text = "❤️ Unlike" if post[8] else "🤍 Like"
                        if st.button(like_text, key=f"like_{post[0]}"):
                            like_post(user_id, post[0])
                            st.rerun()
                        st.write(f"**{post[7]}** likes")
                    
                    with col2:
                        comment_count = get_comment_count(post[0])
                        if st.button(f"💬 {comment_count}", key=f"comment_btn_{post[0]}"):
                            if post[0] in st.session_state.show_comments:
                                st.session_state.show_comments[post[0]] = not st.session_state.show_comments[post[0]]
                            else:
                                st.session_state.show_comments[post[0]] = True
                            st.rerun()
                    
                    # Comments section
                    if st.session_state.show_comments.get(post[0], False):
                        st.markdown("---")
                        st.subheader("💬 Comments")
                        
                        # Display existing comments
                        comments = get_comments(post[0])
                        if comments:
                            for comment in comments:
                                with st.container():
                                    st.write(f"**{comment[2]}**: {comment[3]}")
                                    st.caption(f"{comment[4]}")
                        
                        # Add new comment
                        with st.form(key=f"comment_form_{post[0]}", clear_on_submit=True):
                            new_comment = st.text_input("Add a comment...", key=f"comment_input_{post[0]}")
                            if st.form_submit_button("Post Comment"):
                                if new_comment:
                                    if add_comment(post[0], user_id, new_comment):
                                        st.success("Comment added!")
                                        st.rerun()
    
    # Messages Page
    elif st.session_state.page == "Messages":
        st.header("💬 Messages")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Conversations")
            conversations = get_conversations(user_id)
            
            for conv in conversations:
                if st.button(f"{conv[1]}", key=f"conv_{conv[0]}", use_container_width=True):
                    st.session_state.current_chat = conv[0]
                    st.rerun()
            
            st.subheader("Start New Chat")
            all_users = get_all_users()
            for user in all_users:
                if user[0] != user_id:
                    if st.button(f"💬 {user[1]}", key=f"new_{user[0]}", use_container_width=True):
                        st.session_state.current_chat = user[0]
                        st.rerun()
        
        with col2:
            if st.session_state.current_chat:
                other_user = get_user(st.session_state.current_chat)
                if other_user:
                    st.subheader(f"Chat with {other_user[1]}")
                    
                    messages = get_messages(user_id, st.session_state.current_chat)
                    
                    # Display messages
                    for msg in messages:
                        if msg[1] == user_id:
                            st.markdown(f"<div style='background-color: #dcf8c6; padding: 10px; border-radius: 10px; margin: 5px 0;'><b>You:</b> {msg[5]}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='background-color: #ffffff; padding: 10px; border-radius: 10px; margin: 5px 0;'><b>{msg[2]}:</b> {msg[5]}</div>", unsafe_allow_html=True)
                    
                    # Send message
                    with st.form(key="message_form", clear_on_submit=True):
                        new_message = st.text_input("Type a message...", key="msg_input")
                        if st.form_submit_button("Send"):
                            if new_message:
                                if send_message(user_id, st.session_state.current_chat, new_message):
                                    st.rerun()
                else:
                    st.error("User not found")
            else:
                st.info("👆 Select a conversation or start a new chat")
    
    # Discover Page
    elif st.session_state.page == "Discover":
        st.header("👥 Discover People")
        
        suggested_users = get_suggested_users(user_id)
        if not suggested_users:
            st.info("No suggested users found.")
        else:
            for user in suggested_users:
                with st.container():
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col1:
                        user_info = get_user(user[0])
                        if user_info and user_info[3]:
                            display_image_safely(user_info[3], width=50)
                    with col2:
                        st.write(f"**{user[1]}**")
                    with col3:
                        if not is_following(user_id, user[0]):
                            if st.button("Follow", key=f"follow_{user[0]}"):
                                follow_user(user_id, user[0])
                                st.rerun()
                        else:
                            if st.button("Unfollow", key=f"unfollow_{user[0]}"):
                                unfollow_user(user_id, user[0])
                                st.rerun()
    
    # Profile Page
    elif st.session_state.page == "Profile":
        user_info = get_user(user_id)
        
        if user_info:
            st.header(f"👤 {user_info[1]}'s Profile")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if user_info[3]:
                    display_image_safely(user_info[3], width=150)
                else:
                    st.info("No profile picture")
                
                st.write(f"**Username:** {user_info[1]}")
                st.write(f"**Email:** {user_info[2]}")
                st.write(f"**Bio:** {user_info[4] if user_info[4] else 'No bio yet'}")
            
            with col2:
                st.subheader("Your Posts")
                # Get user's posts
                posts = get_posts(user_id)
                user_posts = [p for p in posts if p[1] == user_id]
                
                if not user_posts:
                    st.info("📝 You haven't posted anything yet. Share your first post!")
                else:
                    for post in user_posts:
                        with st.container():
                            st.write(f"**{post[2]}** · {post[6]}")
                            st.write(post[3])
                            if post[4] and post[5]:
                                if post[4] == "image":
                                    display_image_safely(post[5], use_container_width=True)
                            st.write(f"❤️ {post[7]} likes")
                            st.markdown("---")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>💬 FeedChat - Connect with friends and share your moments</div>", unsafe_allow_html=True)

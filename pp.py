import streamlit as st
import sqlite3
import datetime
import random
import time
from PIL import Image
import io
import base64

# ===================================
# Database Initialization
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

    # Posts table (with media support)
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

    # Calls table
    c.execute("""
    CREATE TABLE IF NOT EXISTS calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caller_id INTEGER,
        receiver_id INTEGER,
        status TEXT,
        started_at DATETIME,
        ended_at DATETIME
    )
    """)

    # Notifications table
    c.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
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
# Helper Functions (same as before)
# ===================================
def create_user(username, password, email, profile_pic=None, bio=""):
    try:
        c = conn.cursor()
        # Check if the user already exists
        c.execute("SELECT id FROM users WHERE username=?", (username,))
        if c.fetchone():
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
        result = c.fetchone()
        return result
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
            # Get posts from users that the current user follows, plus their own posts
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
            # Get all posts for non-logged in users
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
        # Check if already liked
        c.execute("SELECT id FROM likes WHERE user_id=? AND post_id=?", (user_id, post_id))
        if not c.fetchone():
            c.execute("INSERT INTO likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
            conn.commit()
            
            # Get post owner
            c.execute("SELECT user_id FROM posts WHERE id=?", (post_id,))
            post_owner_result = c.fetchone()
            if post_owner_result:
                post_owner = post_owner_result[0]
                
                # Create notification for like
                user = get_user(user_id)
                if user:
                    c.execute("INSERT INTO notifications (user_id, content) VALUES (?, ?)",
                             (post_owner, f"{user[1]} liked your post"))
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
        # Check if already following
        c.execute("SELECT id FROM follows WHERE follower_id=? AND following_id=?", (follower_id, following_id))
        if not c.fetchone():
            c.execute("INSERT INTO follows (follower_id, following_id) VALUES (?, ?)", (follower_id, following_id))
            conn.commit()
            
            # Create notification for follow
            follower = get_user(follower_id)
            if follower:
                c.execute("INSERT INTO notifications (user_id, content) VALUES (?, ?)",
                         (following_id, f"{follower[1]} started following you"))
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

def send_message(sender_id, receiver_id, content):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)",
                 (sender_id, receiver_id, content))
        conn.commit()
        
        # Create notification for message
        sender = get_user(sender_id)
        if sender:
            c.execute("INSERT INTO notifications (user_id, content) VALUES (?, ?)",
                     (receiver_id, f"New message from {sender[1]}"))
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
                 ORDER BY created_at DESC LIMIT 1) as last_message,
                (SELECT created_at FROM messages 
                 WHERE (sender_id = ? AND receiver_id = other_user_id) 
                    OR (sender_id = other_user_id AND receiver_id = ?)
                 ORDER BY created_at DESC LIMIT 1) as last_message_time,
                SUM(CASE WHEN m.receiver_id = ? AND m.is_read = 0 THEN 1 ELSE 0 END) as unread_count
            FROM messages m
            JOIN users u ON u.id = CASE WHEN m.sender_id = ? THEN m.receiver_id ELSE m.sender_id END
            WHERE m.sender_id = ? OR m.receiver_id = ?
            GROUP BY other_user_id
            ORDER BY last_message_time DESC
        """, (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id))
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except:
            pass

def mark_messages_as_read(sender_id, receiver_id):
    try:
        c = conn.cursor()
        c.execute("UPDATE messages SET is_read=1 WHERE sender_id=? AND receiver_id=?", (sender_id, receiver_id))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
    finally:
        try:
            c.close()
        except:
            pass

def get_notifications(user_id):
    try:
        c = conn.cursor()
        c.execute("SELECT id, content, is_read, created_at FROM notifications WHERE user_id=? ORDER BY created_at DESC", (user_id,))
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except:
            pass

def mark_notification_as_read(notification_id):
    try:
        c = conn.cursor()
        c.execute("UPDATE notifications SET is_read=1 WHERE id=?", (notification_id,))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
    finally:
        try:
            c.close()
        except:
            pass

def get_followers(user_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT u.id, u.username 
            FROM follows f 
            JOIN users u ON f.follower_id = u.id 
            WHERE f.following_id=?
        """, (user_id,))
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except:
            pass

def get_following(user_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT u.id, u.username 
            FROM follows f 
            JOIN users u ON f.following_id = u.id 
            WHERE f.follower_id=?
        """, (user_id,))
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
        # Get users that the current user is not following
        c.execute("""
            SELECT id, username 
            FROM users 
            WHERE id != ? AND id NOT IN (
                SELECT following_id FROM follows WHERE follower_id=?
            )
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

def start_call(caller_id, receiver_id):
    try:
        c = conn.cursor()
        call_id = random.randint(100000, 999999)  # Simulate call ID
        # In a real app, you would integrate with a WebRTC service here
        c.execute("INSERT INTO calls (caller_id, receiver_id, status, started_at) VALUES (?, ?, ?, ?)",
                 (caller_id, receiver_id, "initiated", datetime.datetime.now()))
        conn.commit()
        
        # Create notification for call
        caller = get_user(caller_id)
        if caller:
            c.execute("INSERT INTO notifications (user_id, content) VALUES (?, ?)",
                     (receiver_id, f"📞 Incoming call from {caller[1]}"))
            conn.commit()
        return call_id
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except:
            pass

# ===================================
# Streamlit UI with NEW MODERN DESIGN
# ===================================
st.set_page_config(page_title="FeedChat", page_icon="💬", layout="wide", initial_sidebar_state="expanded")

# Modern CSS with gradient background and glassmorphism effect
st.markdown("""
    <style>
    /* Main background gradient */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Main content area */
    .main .block-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 30px;
        margin: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Cards and containers */
    .post {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.3);
        transition: transform 0.2s ease;
    }
    
    .post:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
    }
    
    .user-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    /* Message styling */
    .message-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 20px;
        background: rgba(248, 249, 250, 0.8);
        border-radius: 15px;
        margin-bottom: 20px;
    }
    
    .message {
        padding: 15px;
        border-radius: 18px;
        margin-bottom: 15px;
        max-width: 70%;
        word-wrap: break-word;
    }
    
    .sent {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: auto;
        margin-right: 0;
        border-bottom-right-radius: 5px;
    }
    
    .received {
        background: linear-gradient(135deg, #e6e9f0 0%, #eef1f5 100%);
        color: #333;
        margin-right: auto;
        margin-left: 0;
        border-bottom-left-radius: 5px;
    }
    
    /* Notification styling */
    .notification {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        border-left: 4px solid #ffc107;
    }
    
    .unread {
        background: linear-gradient(135deg, #cce5ff 0%, #b8daff 100%);
        border-left: 4px solid #007bff;
        font-weight: 600;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Input fields */
    .stTextInput>div>div>input {
        border-radius: 25px;
        border: 2px solid #e9ecef;
        padding: 12px 20px;
    }
    
    .stTextArea>div>div>textarea {
        border-radius: 15px;
        border: 2px solid #e9ecef;
        padding: 15px;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: #2c3e50;
        font-weight: 700;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.8);
        border-radius: 15px 15px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    /* Profile image styling */
    .profile-img {
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Feed"
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

# Sidebar with modern design
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h1 style='color: white; margin-bottom: 30px;'>💬 FeedChat</h1>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.user:
        user_info = get_user(st.session_state.user[0])
        if user_info and user_info[3]:  # Profile picture
            st.image(io.BytesIO(user_info[3]), width=80, output_format="PNG", use_column_width=True)
        st.success(f"**Welcome, {user_info[1]}!**" if user_info else "**Welcome!**")
        
        st.markdown("---")
        
        # Navigation buttons with icons
        nav_col1, nav_col2 = st.columns(2)
        with nav_col1:
            if st.button("🏠", help="Feed"):
                st.session_state.page = "Feed"
            if st.button("💬", help="Messages"):
                st.session_state.page = "Messages"
        with nav_col2:
            if st.button("🔔", help="Notifications"):
                st.session_state.page = "Notifications"
            if st.button("👤", help="Profile"):
                st.session_state.page = "Profile"
        
        if st.button("🌐 Discover People", use_container_width=True):
            st.session_state.page = "Discover"
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = "Feed"
            st.rerun()
    else:
        st.info("Please login or sign up to use FeedChat")

# Main content area with modern background
if not st.session_state.user:
    # Auth pages with modern design
    st.markdown("""
        <div style='text-align: center; margin-bottom: 30px;'>
            <h1 style='color: white;'>Welcome to FeedChat</h1>
            <p style='color: rgba(255, 255, 255, 0.8);'>Connect with friends and share your moments</p>
        </div>
    """, unsafe_allow_html=True)
    
    auth_tab1, auth_tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with auth_tab1:
        with st.form("Login"):
            st.subheader("Welcome Back!")
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
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
            st.subheader("Join FeedChat Today!")
            new_username = st.text_input("Choose a username", placeholder="Enter a unique username")
            new_email = st.text_input("Email", placeholder="Enter your email")
            new_password = st.text_input("Choose a password", type="password", placeholder="Create a strong password")
            confirm_password = st.text_input("Confirm password", type="password", placeholder="Confirm your password")
            profile_pic = st.file_uploader("Profile picture (optional)", type=["jpg", "png", "jpeg"])
            bio = st.text_area("Bio (optional)", placeholder="Tell us about yourself...")
            
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

# Main App (after login)
else:
    user_id = st.session_state.user[0]
    
    # Feed Page
    if st.session_state.page == "Feed":
        st.header("📱 Your Feed")
        
        # Create post card
        with st.expander("➕ Create New Post", expanded=False):
            post_content = st.text_area("What's on your mind?", placeholder="Share your thoughts...", height=100)
            media_type = st.selectbox("Media type", ["None", "Image", "Video"])
            media_file = st.file_uploader("Upload media", type=["jpg", "png", "jpeg", "mp4", "mov"])
            
            if st.button("Post", use_container_width=True):
                if post_content or media_file:
                    media_data = media_file.read() if media_file else None
                    media_type_val = media_type.lower() if media_file else None
                    create_post(user_id, post_content, media_type_val, media_data)
                    st.success("Posted successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Please add some content or media to your post")
        
        # Display posts
        posts = get_posts(user_id)
        if not posts:
            st.info("✨ No posts yet. Follow some users to see their posts here!")
        else:
            for post in posts:
                with st.container():
                    st.markdown(f"<div class='post'>", unsafe_allow_html=True)
                    
                    # User info with profile picture
                    col1, col2 = st.columns([1, 20])
                    with col1:
                        user_info = get_user(post[1])
                        if user_info and user_info[3]:  # Profile picture
                            st.image(io.BytesIO(user_info[3]), width=50, output_format="PNG")
                    with col2:
                        st.write(f"**{post[2]}** · 🕒 {post[6]}")
                    
                    # Post content
                    st.write(post[3])
                    
                    # Media
                    if post[4] and post[5]:
                        if post[4] == "image":
                            st.image(io.BytesIO(post[5]), use_column_width=True)
                        elif post[4] == "video":
                            st.video(io.BytesIO(post[5]))
                    
                    # Like button and stats
                    col1, col2 = st.columns([2, 3])
                    with col1:
                        like_text = "❤️ Unlike" if post[8] else "🤍 Like"
                        if st.button(like_text, key=f"like_{post[0]}"):
                            like_post(user_id, post[0])
                            st.rerun()
                        st.write(f"**{post[7]}** likes")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
    
    # Messages Page
    elif st.session_state.page == "Messages":
        st.header("💬 Messages")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Conversations")
            conversations = get_conversations(user_id)
            
            for conv in conversations:
                unread_indicator = f" 🔵 {conv[4]}" if conv[4] > 0 else ""
                if st.button(f"{conv[1]}{unread_indicator}", key=f"conv_{conv[0]}", use_container_width=True):
                    st.session_state.current_chat = conv[0]
                    mark_messages_as_read(conv[0], user_id)
                    st.rerun()
            
            st.subheader("Start New Chat")
            all_users = get_all_users()
            for user in all_users:
                if user[0] != user_id:  # Don't show current user
                    if st.button(f"💬 {user[1]}", key=f"new_{user[0]}", use_container_width=True):
                        st.session_state.current_chat = user[0]
                        st.rerun()
        
        with col2:
            if st.session_state.current_chat:
                other_user = get_user(st.session_state.current_chat)
                if other_user:
                    # Chat header with call button
                    chat_header = st.columns([4, 1])
                    with chat_header[0]:
                        st.subheader(f"Chat with {other_user[1]}")
                    with chat_header[1]:
                        if st.button("📞", help="Start Video Call"):
                            call_id = start_call(user_id, st.session_state.current_chat)
                            st.info(f"Calling {other_user[1]}... Call ID: {call_id}")
                    
                    # Messages
                    messages = get_messages(user_id, st.session_state.current_chat)
                    st.markdown("<div class='message-container'>", unsafe_allow_html=True)
                    
                    for msg in messages:
                        if msg[1] == user_id:
                            st.markdown(f"<div class='message sent'><b>You:</b> {msg[5]}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='message received'><b>{msg[2]}:</b> {msg[5]}</div>", unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Send message
                    message_col1, message_col2 = st.columns([4, 1])
                    with message_col1:
                        new_message = st.text_input("Type a message...", key="msg_input", label_visibility="collapsed")
                    with message_col2:
                        if st.button("Send", key="send_msg", use_container_width=True):
                            if new_message:
                                send_message(user_id, st.session_state.current_chat, new_message)
                                st.rerun()
                else:
                    st.error("User not found")
            else:
                st.info("👆 Select a conversation or start a new chat from the sidebar")
    
    # Notifications Page
    elif st.session_state.page == "Notifications":
        st.header("🔔 Notifications")
        
        notifications = get_notifications(user_id)
        if not notifications:
            st.info("🎉 You're all caught up! No new notifications.")
        else:
            for notif in notifications:
                css_class = "notification unread" if not notif[2] else "notification"
                st.markdown(f"<div class='{css_class}'>{notif[1]}<br><small>🕒 {notif[3]}</small></div>", 
                           unsafe_allow_html=True)
                if not notif[2]:
                    if st.button("Mark as read", key=f"read_{notif[0]}"):
                        mark_notification_as_read(notif[0])
                        st.rerun()
    
    # Discover Page
    elif st.session_state.page == "Discover":
        st.header("👥 Discover People")
        
        st.subheader("Suggested Users")
        suggested_users = get_suggested_users(user_id)
        
        if not suggested_users:
            st.info("🌟 You're following everyone! Great job being social!")
        else:
            for user in suggested_users:
                user_info = get_user(user[0])
                if user_info:
                    with st.container():
                        st.markdown("<div class='user-card'>", unsafe_allow_html=True)
                        
                        col1, col2, col3 = st.columns([1, 3, 2])
                        with col1:
                            if user_info[3]:  # Profile picture
                                st.image(io.BytesIO(user_info[3]), width=60, output_format="PNG")
                        with col2:
                            st.write(f"**{user_info[1]}**")
                            if user_info[4]:  # Bio
                                st.caption(user_info[4])
                        with col3:
                            if is_following(user_id, user[0]):
                                if st.button("Unfollow", key=f"unfollow_{user[0]}"):
                                    unfollow_user(user_id, user[0])
                                    st.rerun()
                            else:
                                if st.button("Follow", key=f"follow_{user[0]}"):
                                    follow_user(user_id, user[0])
                                    st.rerun()
                        
                        st.markdown("</div>", unsafe_allow_html=True)
    
    # Profile Page
    elif st.session_state.page == "Profile":
        user_info = get_user(user_id)
        
        if user_info:
            st.header(f"👤 {user_info[1]}'s Profile")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if user_info[3]:  # Profile picture
                    st.image(io.BytesIO(user_info[3]), width=150, output_format="PNG")
                else:
                    st.info("No profile picture")
                
                # Profile stats
                followers = get_followers(user_id)
                following = get_following(user_id)
                
                st.subheader("Stats")
                st.metric("Followers", len(followers))
                st.metric("Following", len(following))
                
                # Edit profile
                if st.button("✏️ Edit Profile", use_container_width=True):
                    st.session_state.page = "EditProfile"
                    st.rerun()
            
            with col2:
                st.write(f"**Bio:** {user_info[4] if user_info[4] else 'No bio yet'}")
                
                # User's posts
                st.subheader("Your Posts")
                user_posts = get_posts()  # Get all posts
                user_posts = [p for p in user_posts if p[1] == user_id]
                
                if not user_posts:
                    st.info("📝 You haven't posted anything yet. Share your first post!")
                else:
                    for post in user_posts:
                        with st.container():
                            st.markdown(f"<div class='post'>", unsafe_allow_html=True)
                            st.write(f"**{post[2]}** · 🕒 {post[6]}")
                            st.write(post[3])
                            
                            if post[4] and post[5]:
                                if post[4] == "image":
                                    st.image(io.BytesIO(post[5]), use_column_width=True)
                                elif post[4] == "video":
                                    st.video(io.BytesIO(post[5]))
                            
                            st.write(f"❤️ {post[7]} likes")
                            st.markdown("</div>", unsafe_allow_html=True)
    
    # Edit Profile Page
    elif st.session_state.page == "EditProfile":
        st.header("✏️ Edit Profile")
        
        user_info = get_user(user_id)
        
        if user_info:
            with st.form("EditProfileForm"):
                new_username = st.text_input("Username", value=user_info[1])
                new_email = st.text_input("Email", value=user_info[2])
                new_bio = st.text_area("Bio", value=user_info[4] if user_info[4] else "", height=100)
                new_profile_pic = st.file_uploader("Profile Picture", type=["jpg", "png", "jpeg"])
                
                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                    # Update user in database
                    try:
                        c = conn.cursor()
                        profile_pic_data = new_profile_pic.read() if new_profile_pic else user_info[3]
                        c.execute("UPDATE users SET username=?, email=?, bio=?, profile_pic=? WHERE id=?",
                                 (new_username, new_email, new_bio, profile_pic_data, user_id))
                        conn.commit()
                        st.success("Profile updated successfully!")
                        time.sleep(1)
                        st.session_state.page = "Profile"
                        st.rerun()
                    except sqlite3.Error as e:
                        st.error(f"Error updating profile: {e}")
                    finally:
                        try:
                            c.close()
                        except:
                            pass

import streamlit as st
import sqlite3
import datetime
import random
import time
from PIL import Image
import io
import base64
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av
import threading
import queue

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

    # Calls table - Updated for WebRTC
    c.execute("""
    CREATE TABLE IF NOT EXISTS calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caller_id INTEGER,
        receiver_id INTEGER,
        room_id TEXT UNIQUE,
        status TEXT DEFAULT 'ringing',
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
# WebRTC Configuration
# ===================================
RTC_CONFIG = RTCConfiguration({
    "iceServers": [
        {"urls": ["stun:stun.l.google.com:19302"]},
        {"urls": ["stun:stun1.l.google.com:19302"]}
    ]
})

# Global state for active calls
if "active_calls" not in st.session_state:
    st.session_state.active_calls = {}
if "current_call" not in st.session_state:
    st.session_state.current_call = None
if "call_status" not in st.session_state:
    st.session_state.call_status = "idle"

# ===================================
# Helper Functions
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
            
            c.execute("SELECT user_id FROM posts WHERE id=?", (post_id,))
            post_owner_result = c.fetchone()
            if post_owner_result:
                post_owner = post_owner_result[0]
                
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
        c.execute("SELECT id FROM follows WHERE follower_id=? AND following_id=?", (follower_id, following_id))
        if not c.fetchone():
            c.execute("INSERT INTO follows (follower_id, following_id) VALUES (?, ?)", (follower_id, following_id))
            conn.commit()
            
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

# ===================================
# WebRTC Video Call Functions
# ===================================
def generate_room_id():
    return f"room_{random.randint(100000, 999999)}_{int(time.time())}"

def start_video_call(caller_id, receiver_id):
    try:
        c = conn.cursor()
        room_id = generate_room_id()
        
        # Create call record
        c.execute("INSERT INTO calls (caller_id, receiver_id, room_id, status, started_at) VALUES (?, ?, ?, ?, ?)",
                 (caller_id, receiver_id, room_id, "ringing", datetime.datetime.now()))
        conn.commit()
        
        # Create notification
        caller = get_user(caller_id)
        if caller:
            c.execute("INSERT INTO notifications (user_id, content) VALUES (?, ?)",
                     (receiver_id, f"📞 Incoming video call from {caller[1]}"))
            conn.commit()
        
        # Store active call
        st.session_state.active_calls[room_id] = {
            "caller_id": caller_id,
            "receiver_id": receiver_id,
            "status": "ringing",
            "started_at": datetime.datetime.now()
        }
        
        return room_id
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except:
            pass

def get_active_call(user_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT room_id, caller_id, receiver_id, status 
            FROM calls 
            WHERE (caller_id=? OR receiver_id=?) AND status IN ('ringing', 'active')
            ORDER BY started_at DESC LIMIT 1
        """, (user_id, user_id))
        return c.fetchone()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except:
            pass

def update_call_status(room_id, status):
    try:
        c = conn.cursor()
        c.execute("UPDATE calls SET status=?, ended_at=CASE WHEN ?='ended' THEN CURRENT_TIMESTAMP ELSE NULL END WHERE room_id=?",
                 (status, status, room_id))
        conn.commit()
        
        if room_id in st.session_state.active_calls:
            st.session_state.active_calls[room_id]["status"] = status
            if status == "ended":
                del st.session_state.active_calls[room_id]
        
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
    finally:
        try:
            c.close()
        except:
            pass

def answer_call(room_id):
    update_call_status(room_id, "active")
    st.session_state.current_call = room_id
    st.session_state.call_status = "active"
    st.rerun()

def end_call(room_id):
    update_call_status(room_id, "ended")
    st.session_state.current_call = None
    st.session_state.call_status = "idle"
    st.rerun()

# Video processor for WebRTC
class VideoProcessor:
    def __init__(self):
        self.frames_queue = queue.Queue()
    
    def recv(self, frame):
        self.frames_queue.put(frame)
        return frame

# ===================================
# Streamlit UI with WebRTC Video Calls
# ===================================
st.set_page_config(page_title="FeedChat", page_icon="💬", layout="wide", initial_sidebar_state="expanded")

# Modern CSS with gradient background
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .main .block-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 30px;
        margin: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .video-call-container {
        background: linear-gradient(135deg, #000000 0%, #2d3436 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        text-align: center;
        color: white;
    }
    
    .call-buttons {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin: 20px 0;
    }
    
    .call-button {
        padding: 15px 30px;
        border-radius: 50px;
        border: none;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .answer-btn {
        background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
        color: white;
    }
    
    .decline-btn {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        color: white;
    }
    
    .end-call-btn {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        color: white;
        padding: 15px 30px;
        border-radius: 50px;
        border: none;
        font-size: 16px;
        font-weight: bold;
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
if "message_input" not in st.session_state:
    st.session_state.message_input = ""
if "last_message_id" not in st.session_state:
    st.session_state.last_message_id = 0

# Check for incoming calls
def check_incoming_calls():
    if st.session_state.user:
        user_id = st.session_state.user[0]
        active_call = get_active_call(user_id)
        if active_call and active_call[3] == "ringing":
            st.session_state.current_call = active_call[0]
            st.session_state.call_status = "ringing"

# Sidebar
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h1 style='color: white; margin-bottom: 30px;'>💬 FeedChat</h1>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.user:
        user_info = get_user(st.session_state.user[0])
        if user_info and user_info[3]:
            st.image(io.BytesIO(user_info[3]), width=80, output_format="PNG")
        st.success(f"**Welcome, {user_info[1]}!**" if user_info else "**Welcome!**")
        
        st.markdown("---")
        
        # Check for incoming calls
        check_incoming_calls()
        
        # Show call status
        if st.session_state.call_status == "ringing":
            st.warning("📞 Incoming call!")
        elif st.session_state.call_status == "active":
            st.success("📞 Call in progress")
        
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
            st.session_state.current_call = None
            st.session_state.call_status = "idle"
            st.rerun()
    else:
        st.info("Please login or sign up to use FeedChat")

# Main content
if not st.session_state.user:
    # Auth pages
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
    
    # Handle incoming calls
    if st.session_state.call_status == "ringing":
        active_call = get_active_call(user_id)
        if active_call:
            caller_id = active_call[1]
            caller_info = get_user(caller_id)
            
            st.markdown(f"""
                <div class='video-call-container'>
                    <h2>📞 Incoming Video Call</h2>
                    <h3>From: {caller_info[1] if caller_info else 'Unknown'}</h3>
                    <div class='call-buttons'>
                        <button class='call-button answer-btn' onclick='window.answerCall()'>Answer</button>
                        <button class='call-button decline-btn' onclick='window.declineCall()'>Decline</button>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # JavaScript for call handling
            st.markdown("""
                <script>
                function answerCall() {
                    window.parent.postMessage({type: 'answerCall'}, '*');
                }
                function declineCall() {
                    window.parent.postMessage({type: 'declineCall'}, '*');
                }
                </script>
            """, unsafe_allow_html=True)
            
            # Handle JavaScript messages
            if st.button("Answer Call (Fallback)", key="answer_fallback"):
                answer_call(st.session_state.current_call)
            if st.button("Decline Call (Fallback)", key="decline_fallback"):
                end_call(st.session_state.current_call)
    
    # Active call interface
    elif st.session_state.call_status == "active":
        st.markdown(f"""
            <div class='video-call-container'>
                <h2>📞 Video Call in Progress</h2>
                <p>Room ID: {st.session_state.current_call}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # WebRTC Video Stream
        webrtc_ctx = webrtc_streamer(
            key="video-call",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTC_CONFIG,
            media_stream_constraints={
                "video": True,
                "audio": True
            },
            video_processor_factory=VideoProcessor
        )
        
        if st.button("End Call", use_container_width=True, key="end_call"):
            end_call(st.session_state.current_call)
    
    # Normal app pages when not in a call
    if st.session_state.call_status == "idle":
        # Feed Page
        if st.session_state.page == "Feed":
            st.header("📱 Your Feed")
            
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
            
            posts = get_posts(user_id)
            if not posts:
                st.info("✨ No posts yet. Follow some users to see their posts here!")
            else:
                for post in posts:
                    with st.container():
                        st.markdown(f"<div class='post'>", unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([1, 20])
                        with col1:
                            user_info = get_user(post[1])
                            if user_info and user_info[3]:
                                st.image(io.BytesIO(user_info[3]), width=50, output_format="PNG")
                        with col2:
                            st.write(f"**{post[2]}** · 🕒 {post[6]}")
                        
                        st.write(post[3])
                        
                        if post[4] and post[5]:
                            if post[4] == "image":
                                st.image(io.BytesIO(post[5]), use_column_width=True)
                            elif post[4] == "video":
                                st.video(io.BytesIO(post[5]))
                        
                        col1, col2 = st.columns([2, 3])
                        with col1:
                            like_text = "❤️ Unlike" if post[8] else "🤍 Like"
                            if st.button(like_text, key=f"like_{post[0]}"):
                                like_post(user_id, post[0])
                                st.rerun()
                            st.write(f"**{post[7]}** likes")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
        
        # Messages Page with Video Call
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
                        st.session_state.last_message_id = 0
                        st.rerun()
                
                st.subheader("Start New Chat")
                all_users = get_all_users()
                for user in all_users:
                    if user[0] != user_id:
                        if st.button(f"💬 {user[1]}", key=f"new_{user[0]}", use_container_width=True):
                            st.session_state.current_chat = user[0]
                            st.session_state.last_message_id = 0
                            st.rerun()
            
            with col2:
                if st.session_state.current_chat:
                    other_user = get_user(st.session_state.current_chat)
                    if other_user:
                        chat_header = st.columns([4, 1])
                        with chat_header[0]:
                            st.subheader(f"Chat with {other_user[1]}")
                        with chat_header[1]:
                            if st.button("📞", help="Start Video Call"):
                                room_id = start_video_call(user_id, st.session_state.current_chat)
                                if room_id:
                                    st.success(f"Calling {other_user[1]}...")
                                    st.info("They will receive a notification to answer the call.")
                        
                        messages = get_messages(user_id, st.session_state.current_chat)
                        
                        if messages:
                            current_last_id = messages[-1][0] if messages else 0
                            if current_last_id > st.session_state.last_message_id:
                                st.session_state.last_message_id = current_last_id
                        
                        st.markdown("<div class='message-container'>", unsafe_allow_html=True)
                        
                        for msg in messages:
                            if msg[1] == user_id:
                                st.markdown(f"<div class='message sent'><b>You:</b> {msg[5]}</div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div class='message received'><b>{msg[2]}:</b> {msg[5]}</div>", unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        with st.form(key="message_form", clear_on_submit=True):
                            message_col1, message_col2 = st.columns([4, 1])
                            with message_col1:
                                new_message = st.text_input("Type a message...", key="msg_input", label_visibility="collapsed")
                            with message_col2:
                                submitted = st.form_submit_button("➤", use_container_width=True, help="Send message")
                            
                            if submitted and new_message:
                                if send_message(user_id, st.session_state.current_chat, new_message):
                                    st.session_state.last_message_id = 0
                                    st.rerun()
                    else:
                        st.error("User not found")
                else:
                    st.info("👆 Select a conversation or start a new chat from the sidebar")
        
        # Other pages (Notifications, Discover, Profile) remain the same
        # ... [rest of the pages code remains unchanged]

# JavaScript message handling
components.html("""
<script>
window.addEventListener('message', function(event) {
    if (event.data.type === 'answerCall') {
        window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'answer'}, '*');
    } else if (event.data.type === 'declineCall') {
        window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'decline'}, '*');
    }
});
</script>
""", height=0)

# Handle call responses
if st.session_state.call_status == "ringing":
    if st.button("Answer Call", key="answer_call_btn"):
        answer_call(st.session_state.current_call)
    if st.button("Decline Call", key="decline_call_btn"):
        end_call(st.session_state.current_call)


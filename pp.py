import streamlit as st
import sqlite3
import datetime
import random
import time
from PIL import Image
import io
import base64
import threading
import queue

# ===================================
# Database Initialization - UPDATED with blocking
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
        is_active BOOLEAN DEFAULT TRUE,
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
        is_deleted BOOLEAN DEFAULT FALSE,
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
        created_at DAT极IME DEFAULT CURRENT_TIMESTAMP
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
        id INTEGER PRIMARY极 KEY AUTOINCREMENT,
        caller_id INTEGER,
        receiver_id INTEGER,
        meeting_url TEXT,
        status TEXT DEFAULT 'scheduled',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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

    # Blocked users table - NEW
    c.execute("""
    CREATE TABLE IF NOT EXISTS blocked_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        blocker_id INTEGER,
        blocked_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(blocker_id, blocked_id)
    )
    """)

    conn.commit()
    return conn

# Initialize database
conn = init_db()

# ===================================
# NEW: Blocking Functions
# ===================================
def block_user(blocker_id, blocked_id):
    try:
        c = conn.cursor()
        # Check if already blocked
        c.execute("SELECT id FROM blocked_users WHERE blocker_id=? AND blocked_id=?", (blocker_id, blocked_id))
        if not c.fetchone():
            c.execute("INSERT INTO blocked_users (blocker_id, blocked_id) VALUES (?, ?)", (blocker_id, blocked_id))
            conn.commit()
            
            # Also unfollow if following
            c.execute("DELETE FROM follows WHERE follower_id=? AND following_id=?", (blocker_id, blocked_id))
            c.execute("DELETE FROM follows WHERE follower_id=? AND following_id=?", (blocked_id, blocker_id))
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

def unblock_user(blocker_id, blocked_id):
    try:
        c = conn.cursor()
        c.execute("DELETE FROM blocked_users WHERE blocker_id=? AND blocked_id=?", (blocker_id, blocked_id))
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

def is_blocked(blocker_id, blocked_id):
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM blocked_users WHERE blocker_id=? AND blocked_id=?", (blocker_id, blocked_id))
        return c.fetchone() is not None
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except:
            pass

def get_blocked_users(user_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT u.id, u.username 
            FROM blocked_users b 
            JOIN users u ON b.blocked_id = u.id 
            WHERE b.blocker_id=?
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

# ===================================
# NEW: Post Deletion Function
# ===================================
def delete_post(post_id, user_id):
    try:
        c = conn.cursor()
        # Verify user owns the post
        c.execute("SELECT user_id FROM posts WHERE id=?", (post_id,))
        post = c.fetchone()
        if post and post[0] == user_id:
            c.execute("UPDATE posts SET is_deleted=1 WHERE id=?", (post_id,))
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

# ===================================
# UPDATED Helper Functions with Blocking
# ===================================
def create_user(username, password, email, profile_pic=None, bio=""):
    try:
        c = conn.cursor()
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
        c.execute("SELECT id, username FROM users WHERE username=? AND password=? AND is_active=1", (username, password))
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
        c.execute("SELECT id, username, email, profile_pic, bio FROM users WHERE id=? AND is_active=1", (user_id,))
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
        c.execute("SELECT id, username FROM users WHERE is_active=1")
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
                 (user_id极, content, media_type, media_data))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error as e:
        st.error(f极"Database error: {e}")
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
            # Exclude posts from blocked users and deleted posts
            c.execute("""
                SELECT p.id, p.user_id, u.username, p.content, p.media_type, p.media_data, p.created_at,
                       COUNT(l.id) as like_count,
                       SUM(CASE WHEN l.user_id = ? THEN 1 ELSE 0 END) as user_liked
                FROM posts p
                JOIN users u ON p.user_id = u.id
                LEFT JOIN likes l ON p.id = l.post_id
                WHERE p.is_deleted = 0 
                AND u.is_active = 1
                AND p.user_id NOT IN (SELECT blocked_id FROM blocked_users WHERE blocker_id=?)
                AND (p.user_id IN (SELECT following_id FROM follows WHERE follower_id=?) OR p.user_id=?)
                GROUP BY p.id
                ORDER BY p.created_at DESC
            """, (user_id, user_id, user_id, user_id))
        else:
            c.execute("""
                SELECT p.id, p.user_id, u.username, p.content, p.media_type, p.media_data, p.created_at,
                       COUNT(l.id) as like_count,
                       0 as user_liked
                FROM posts p
                JOIN users u ON p.user_id = u.id
                LEFT JOIN likes l ON p.id = l.post_id
                WHERE p.is_deleted = 0 AND u.is_active = 1
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

def get_user_posts(user_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT p.id, p.user_id, u.username, p.content, p.media_type, p.media_data, p.created_at,
                   COUNT(l.id) as like_count,
                   SUM(CASE WHEN l.user_id = ? THEN 1 ELSE 0 END) as user_liked
            FROM posts p
            JOIN users u ON p.user_id = u.id
            LEFT JOIN likes l ON p.id = l.post_id
            WHERE p.user_id=? AND p.is_deleted=0
            GROUP BY p.id
            ORDER BY p.created_at DESC
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
        # Check if blocked
        if is_blocked(following_id, follower_id):
            st.error("You cannot follow this user as they have blocked you.")
            return False
            
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
        c.execute("DELETE FROM follows WHERE follower极_id=? AND following_id=?", (follower_id, following_id))
        conn.commit()
        return c.rowcount > 0
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
极          c.close()
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
        # Check if blocked
        if is_blocked(receiver_id, sender_id):
            st.error("You cannot message this user as they have blocked you.")
            return False
            
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
        # Check if blocked
        if is_blocked(user2_id, user1_id):
            return []
            
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
            WHERE (m.sender_id = ? OR m.receiver_id = ?)
            AND u.id NOT IN (SELECT blocked_id FROM blocked_users WHERE blocker_id=?)
            GROUP BY other_user_id
            ORDER BY last_message_time DESC
        """, (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id))
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
            AND is_active = 1
            AND id NOT IN (SELECT blocked_id FROM blocked_users WHERE blocker_id=?)
            AND id NOT IN (SELECT following_id FROM follows WHERE follower_id=?)
            ORDER BY RANDOM() 
            LIMIT 5
        """, (user_id, user_id, user_id))
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
# Streamlit UI with Blocking Features
# ===================================
st.set_page_config(page_title="FeedChat", page_icon="💬", layout="wide", initial_sidebar_state="expanded")

# Modern CSS with gradient background
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    .blocked-user {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #f44336;
    }
    
    .delete-btn {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%) !important;
    }
    
    .block-btn {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%) !important;
    }
    
    .unblock-btn {
        background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%) !important;
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
if "active_meeting" not in st.session_state:
    st.session_state.active_meeting = None
if "manage_blocks" not in st.session_state:
    st.session_state.manage_blocks = False

# Sidebar - UPDATED with blocking management
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
        
        pending_calls = get_pending_calls(st.session_state.user[0])
        if pending_calls:
            st.warning(f"📞 {len(pending_calls)} pending video call(s)")
        
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
        
        if st.button("🚫 Blocked Users", use_container_width=True):
            st.session_state.page = "BlockedUsers"
        
        if st.session_state.active_meeting:
            if st.button("🎥 Active Meeting", use_container_width=True):
                st.session_state.page = "VideoCall"
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = "Feed"
            st.session_state.active_meeting = None
            st.rerun()
    else:
        st.info("Please login or sign up to use FeedChat")

# Main App (after login)
else:
    user_id = st.session_state.user[0]
    
    # Blocked Users Page - NEW
    if st.session_state.page == "BlockedUsers":
        st.header("🚫 Blocked Users")
        
        blocked_users = get_blocked_users(user_id)
        if not blocked_users:
            st.info("You haven't blocked any users yet.")
        else:
            for blocked_user in blocked_users:
                with st.container():
                    st.markdown("<div class='blocked-user'>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{blocked_user[1]}**")
                    with col2:
                        if st.button("Unblock", key=f"unblock_{blocked_user[0]}", use_container_width=True):
                            if unblock_user(user_id, blocked_user[0]):
                                st.success(f"Unblocked {blocked_user[1]}")
                                st.rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("Back to Feed", use_container_width=True):
            st.session_state.page = "Feed"
            st.rerun()
    
    # Feed Page - UPDATED with post deletion
    elif st.session_state.page == "Feed":
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
                    
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col1:
                        user_info = get_user(post[1])
                        if user_info and user_info[3]:
                            st.image(io.BytesIO(user_info[3]), width=50, output_format="PNG")
                    with col2:
                        st.write(f"**{post[2]}** · 🕒 {post[6]}")
                    with col3:
                        # Block button for other users' posts
                        if post[1] != user_id:
                            if st.button("🚫", key=f"block_{post[1]}", help="Block User"):
                                if block_user(user_id, post[1]):
                                    st.success(f"Blocked {post[2]}")
                                    st.rerun()
                    
                    st.write(post[3])
                    
                    if post[4] and post[5]:
                        if post[4] == "image":
                            st.image(io.BytesIO(post[5]), use_column_width=True)
                        elif post[4] == "video":
                            st.video(io.BytesIO(post[5]))
                    
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        like_text = "❤️ Unlike" if post[8] else "🤍 Like"
                        if st.button(like_text, key=f"like_{post[0]}"):
                            like_post(user_id, post[0])
                            st.rerun()
                        st.write(f"**{post[7]}** likes")
                    
                    with col2:
                        if st.button("💬 Comment", key=f"comment_{post[0]}"):
                            st.info("Comment feature coming soon!")
                    
                    with col3:
                        # Delete button for own posts
                        if post[1] == user_id:
                            if st.button("🗑️", key=f"delete_{post[0]}", help="Delete Post"):
                                if delete_post(post[0], user_id):
                                    st.success("Post deleted successfully!")
                                    st.rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
    
    # Messages Page - UPDATED with blocking
    elif st.session_state.page == "Messages":
        st.header("💬 Messages")
        
        # Check for pending calls
        pending_calls = get_pending_calls(user_id)
        if pending_calls:
            st.subheader("📞 Pending Video Calls")
            for call in pending_calls:
                call_id, caller_id, meeting_url, created_at = call
                caller_info = get_user(caller_id)
                
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"**{caller_info[1]}** invited you to a video call")
                    st.caption(f"{created_at}")
                
                with col2:
                    if st.button("Join", key=f"join_{call_id}"):
                        st.session_state.active_meeting = meeting_url
                        update_call_status(call_id, "accepted")
                        st.session_state.page = "VideoCall"
                        st.rerun()
                
                with col3:
                    if st.button("Decline", key=f"decline_{call_id}"):
                        update_call_status(call_id, "declined")
                        st.rerun()
                
                with col4:
                    if st.button("🚫", key=f"block_from_call_{caller_id}", help="Block User"):
                        if block_user(user_id, caller_id):
                            st.success(f"Blocked {caller_info[1]}")
                            st.rerun()
        
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
                if user[0] != user_id and not is_blocked(user_id, user[0]):
                    if st.button(f"💬 {user[1]}", key=f"new_{user[0]}", use_container_width=True):
                        st.session_state.current_chat = user[0]
                        st.session_state.last_message_id = 0
                        st.rerun()
        
        with col2:
            if st.session_state.current_chat:
                other_user = get_user(st.session_state.current_chat)
                if other_user:
                    chat_header = st.columns([3, 1, 1])
                    with chat_header[0]:
                        st.subheader(f"Chat with {other_user[1]}")
                    with chat_header[1]:
                        if st.button("📞", help="Start Video Call"):
                            meeting_url = create_video_call(user_id, st.session_state.current_chat)
                            if meeting_url:
                                st.success(f"Video call invitation sent to {other_user[1]}!")
                                st.info("They will receive a notification to join the call.")
                    with chat_header[2]:
                        if st.button("🚫", help="Block User"):
                            if block_user(user_id, st.session_state.current_chat):
                                st.success(f"Blocked {other_user[1]}")
                                st.session_state.current_chat = None
                                st.rerun()
                    
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
                    st.error("User not found or has been blocked")
            else:
                st.info("👆 Select a conversation or start a new chat from the sidebar")
    
    # Discover Page - UPDATED with blocking
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
                        
                        col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
                        with col1:
                            if user_info[3]:
                                st.image(io.BytesIO(user_info[3]), width=60, output_format="PNG")
                        with col2:
                            st.write(f"**{user_info[1]}**")
                            if user_info[4]:
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
                        with col4:
                            if st.button("🚫", key=f"block_{user[0]}", help="Block User"):
                                if block_user(user_id, user[0]):
                                    st.success(f"Blocked {user_info[1]}")
                                    st.rerun()
                        
                        st.markdown("</div>", unsafe_allow_html=True)
    
    # Profile Page - UPDATED with user's posts and deletion
    elif st.session_state.page == "Profile":
        user_info = get_user(user_id)
        
        if user_info:
            st.header(f"👤 {user_info[1]}'s Profile")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if user_info[3]:
                    st.image(io.BytesIO(user_info[3]), width=150, output_format="PNG")
                else:
                    st.info("No profile picture")
                
                followers = get_followers(user_id)
                following = get_following(user_id)
                blocked = get_blocked_users(user_id)
                
                st.subheader("Stats")
                st.metric("Followers", len(followers))
                st.metric("Following", len(following))
                st.metric("Blocked Users", len(blocked))
                
                if st.button("✏️ Edit Profile", use_container_width=True):
                    st.session_state.page = "EditProfile"
                    st.rerun()
                
                if st.button("🚫 Manage Blocked Users", use_container_width=True):
                    st.session_state.page = "BlockedUsers"
                    st.rerun()
            
            with col2:
                st.write(f"**Bio:** {user_info[4] if user_info[4] else 'No bio yet'}")
                
                st.subheader("Your Posts")
                user_posts = get_user_posts(user_id)
                
                if not user_posts:
                    st.info("📝 You haven't posted anything yet. Share your first post!")
                else:
                    for post in user_posts:
                        with st.container():
                            st.markdown(f"<div class='post'>", unsafe_allow_html=True)
                            
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.write(f"**{post[2]}** · 🕒 {post[6]}")
                            with col2:
                                if st.button("🗑️ Delete", key=f"delete_{post[0]}", use_container_width=True):
                                    if delete_post(post[0], user_id):
                                        st.success("Post deleted successfully!")
                                        st.rerun()
                            
                            st.write(post[3])
                            
                            if post[4] and post[5]:
                                if post[4] == "image":
                                    st.image(io.BytesIO(post[5]), use_column_width=True)
                                elif post[4] == "video":
                                    st.video(io.BytesIO(post[5]))
                            
                            st.write(f"❤️ {post[7]} likes")
                            st.markdown("</div>", unsafe_allow_html=True)

# ... [rest of the code remains the same for other pages]

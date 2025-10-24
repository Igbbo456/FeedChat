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
import json

# ===================================
# Database Initialization - ENHANCED
# ===================================
def init_db():
    conn = sqlite3.connect("feedchat.db", check_same_thread=False)
    c = conn.cursor()

    # Users table with proper column addition
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
    
    # Add is_active column if it doesn't exist
    try:
        c.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Posts table with proper column addition
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
    
    # Add is_deleted column if it doesn't exist
    try:
        c.execute("ALTER TABLE posts ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Likes table
    c.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        post_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # NEW: Comments table
    c.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_id INTEGER,
        content TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # NEW: Shares table
    c.execute("""
    CREATE TABLE IF NOT EXISTS shares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # NEW: Saved posts table
    c.execute("""
    CREATE TABLE IF NOT EXISTS saved_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_id INTEGER,
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

    # Blocked users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS blocked_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        blocker_id INTEGER,
        blocked_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(blocker_id, blocked_id)
    )
    """)

    # NEW: User preferences table for dark mode
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_preferences (
        user_id INTEGER PRIMARY KEY,
        dark_mode BOOLEAN DEFAULT FALSE,
        language TEXT DEFAULT 'en',
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    return conn

# Initialize database
conn = init_db()

# ===================================
# NEW FEATURE: Comments System
# ===================================
def add_comment(post_id, user_id, content):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
                 (post_id, user_id, content))
        conn.commit()
        
        # Create notification for post owner
        c.execute("SELECT user_id FROM posts WHERE id=?", (post_id,))
        post_owner = c.fetchone()
        if post_owner and post_owner[0] != user_id:
            commenter = get_user(user_id)
            if commenter:
                c.execute("INSERT INTO notifications (user_id, content) VALUES (?, ?)",
                         (post_owner[0], f"{commenter[1]} commented on your post"))
                conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except Exception:
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
        except Exception:
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
        except Exception:
            pass

# ===================================
# NEW FEATURE: Post Sharing
# ===================================
def share_post(post_id, user_id):
    try:
        c = conn.cursor()
        # Check if already shared
        c.execute("SELECT id FROM shares WHERE post_id=? AND user_id=?", (post_id, user_id))
        if not c.fetchone():
            c.execute("INSERT INTO shares (post_id, user_id) VALUES (?, ?)", (post_id, user_id))
            conn.commit()
            
            # Create notification for post owner
            c.execute("SELECT user_id FROM posts WHERE id=?", (post_id,))
            post_owner = c.fetchone()
            if post_owner and post_owner[0] != user_id:
                sharer = get_user(user_id)
                if sharer:
                    c.execute("INSERT INTO notifications (user_id, content) VALUES (?, ?)",
                             (post_owner[0], f"{sharer[1]} shared your post"))
                    conn.commit()
            return True
        return False
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_share_count(post_id):
    try:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM shares WHERE post_id=?", (post_id,))
        return c.fetchone()[0]
    except sqlite3.Error as e:
        return 0
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# NEW FEATURE: Save Posts
# ===================================
def save_post(post_id, user_id):
    try:
        c = conn.cursor()
        # Check if already saved
        c.execute("SELECT id FROM saved_posts WHERE post_id=? AND user_id=?", (post_id, user_id))
        if not c.fetchone():
            c.execute("INSERT INTO saved_posts (post_id, user_id) VALUES (?, ?)", (post_id, user_id))
            conn.commit()
            return True
        return False
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def unsave_post(post_id, user_id):
    try:
        c = conn.cursor()
        c.execute("DELETE FROM saved_posts WHERE post_id=? AND user_id=?", (post_id, user_id))
        conn.commit()
        return c.rowcount > 0
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def is_post_saved(post_id, user_id):
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM saved_posts WHERE post_id=? AND user_id=?", (post_id, user_id))
        return c.fetchone() is not None
    except sqlite3.Error as e:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_saved_posts(user_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT p.id, p.user_id, u.username, p.content, p.media_type, p.media_data, p.created_at,
                   COUNT(l.id) as like_count,
                   SUM(CASE WHEN l.user_id = ? THEN 1 ELSE 0 END) as user_liked
            FROM saved_posts sp
            JOIN posts p ON sp.post_id = p.id
            JOIN users u ON p.user_id = u.id
            LEFT JOIN likes l ON p.id = l.post_id
            WHERE sp.user_id=? AND p.is_deleted=0
            GROUP BY p.id
            ORDER BY sp.created_at DESC
        """, (user_id, user_id))
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# NEW FEATURE: Dark Mode & User Preferences
# ===================================
def get_user_preferences(user_id):
    try:
        c = conn.cursor()
        c.execute("SELECT dark_mode, language FROM user_preferences WHERE user_id=?", (user_id,))
        result = c.fetchone()
        if result:
            return {'dark_mode': bool(result[0]), 'language': result[1]}
        else:
            # Create default preferences
            c.execute("INSERT INTO user_preferences (user_id, dark_mode, language) VALUES (?, ?, ?)",
                     (user_id, False, 'en'))
            conn.commit()
            return {'dark_mode': False, 'language': 'en'}
    except sqlite3.Error as e:
        return {'dark_mode': False, 'language': 'en'}
    finally:
        try:
            c.close()
        except Exception:
            pass

def update_user_preferences(user_id, dark_mode=None, language=None):
    try:
        c = conn.cursor()
        if dark_mode is not None:
            c.execute("UPDATE user_preferences SET dark_mode=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=?",
                     (dark_mode, user_id))
        if language is not None:
            c.execute("UPDATE user_preferences SET language=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=?",
                     (language, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# NEW FEATURE: Advanced Search
# ===================================
def search_users(query):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT id, username, bio 
            FROM users 
            WHERE username LIKE ? OR bio LIKE ?
            AND is_active=1
            LIMIT 10
        """, (f'%{query}%', f'%{query}%'))
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

def search_posts(query):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT p.id, p.user_id, u.username, p.content, p.media_type, p.media_data, p.created_at,
                   COUNT(l.id) as like_count
            FROM posts p
            JOIN users u ON p.user_id = u.id
            LEFT JOIN likes l ON p.id = l.post_id
            WHERE p.content LIKE ? AND p.is_deleted=0 AND u.is_active=1
            GROUP BY p.id
            ORDER BY p.created_at DESC
            LIMIT 20
        """, (f'%{query}%',))
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# NEW FEATURE: Trending/Hashtags
# ===================================
def extract_hashtags(text):
    import re
    return re.findall(r'#\w+', text)

def get_trending_hashtags():
    try:
        c = conn.cursor()
        # This is a simplified version - in production you'd want more sophisticated trending logic
        c.execute("""
            SELECT content FROM posts 
            WHERE created_at > datetime('now', '-7 days') 
            AND is_deleted=0
            ORDER BY created_at DESC
            LIMIT 100
        """)
        posts = c.fetchall()
        
        hashtags = {}
        for post in posts:
            tags = extract_hashtags(post[0])
            for tag in tags:
                hashtags[tag] = hashtags.get(tag, 0) + 1
        
        return sorted(hashtags.items(), key=lambda x: x[1], reverse=True)[:10]
    except sqlite3.Error as e:
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# Existing Functions (keeping for reference)
# ===================================
def is_valid_image(image_data):
    """Check if the image data is valid and can be opened by PIL"""
    try:
        if image_data is None:
            return False
        image = Image.open(io.BytesIO(image_data))
        image.verify()
        return True
    except (IOError, SyntaxError, Exception):
        return False

def display_image_safely(image_data, caption="", width=None, use_container_width=False):
    """Safely display an image with error handling"""
    try:
        if image_data and is_valid_image(image_data):
            if width:
                st.image(io.BytesIO(image_data), caption=caption, width=width)
            elif use_container_width:
                st.image(io.BytesIO(image_data), caption=caption, use_container_width=True)
            else:
                st.image(io.BytesIO(image_data), caption=caption)
        else:
            st.warning("Unable to display image (corrupted or invalid format)")
    except Exception as e:
        st.warning(f"Error displaying image: {str(e)}")

# ... (Keep all your existing functions like block_user, create_user, verify_user, etc.)
# [Include all your existing functions here - they remain the same]

# ===================================
# Streamlit UI with NEW FEATURES
# ===================================
st.set_page_config(page_title="FeedChat", page_icon="💬", layout="wide", initial_sidebar_state="expanded")

# Initialize session state with new features
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
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "show_comments" not in st.session_state:
    st.session_state.show_comments = {}
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

# Apply dark mode CSS
def apply_theme(dark_mode):
    if dark_mode:
        st.markdown("""
            <style>
            .stApp {
                background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                color: #ffffff;
            }
            .post {
                background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
                color: #ffffff;
                border: 1px solid #4a5f7a;
            }
            .user-card {
                background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
                color: #ffffff;
                border: 1px solid #4a5f7a;
            }
            .notification {
                background: linear-gradient(135deg, #2980b9 0%, #3498db 100%);
                color: #ffffff;
            }
            .blocked-user {
                background: linear-gradient(135deg, #c0392b 0%, #e74c3c 100%);
                color: #ffffff;
            }
            .message.sent {
                background-color: #27ae60;
                color: white;
            }
            .message.received {
                background-color: #34495e;
                color: white;
            }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            .stApp {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .post {
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            }
            .user-card {
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            }
            .notification {
                background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            }
            .blocked-user {
                background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
            }
            .message.sent {
                background-color: #dcf8c6;
            }
            .message.received {
                background-color: #ffffff;
            }
            </style>
        """, unsafe_allow_html=True)

# Sidebar with new features
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h1 style='color: white; margin-bottom: 30px;'>💬 FeedChat</h1>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.user:
        user_info = get_user(st.session_state.user[0])
        if user_info and user_info[3]:
            display_image_safely(user_info[3], width=80)
        st.success(f"**Welcome, {user_info[1]}!**" if user_info else "**Welcome!**")
        
        # Dark mode toggle
        col1, col2 = st.columns([2, 1])
        with col1:
            dark_mode = st.toggle("Dark Mode", value=st.session_state.dark_mode)
            if dark_mode != st.session_state.dark_mode:
                st.session_state.dark_mode = dark_mode
                if st.session_state.user:
                    update_user_preferences(st.session_state.user[0], dark_mode=dark_mode)
        
        st.markdown("---")
        
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
        
        if st.button("🔍 Search", use_container_width=True):
            st.session_state.page = "Search"
        
        if st.button("💾 Saved Posts", use_container_width=True):
            st.session_state.page = "SavedPosts"
        
        if st.button("🚫 Blocked Users", use_container_width=True):
            st.session_state.page = "BlockedUsers"
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = "Feed"
            st.session_state.current_chat = None
            st.session_state.active_meeting = None
            st.rerun()
    else:
        st.info("Please login or sign up to use FeedChat")

# Apply theme
apply_theme(st.session_state.dark_mode)

# Main content
if not st.session_state.user:
    # Auth pages (same as before)
    # [Keep your existing auth pages code]
    pass
else:
    user_id = st.session_state.user[0]
    
    # NEW PAGE: Search
    if st.session_state.page == "Search":
        st.header("🔍 Search")
        
        search_tab1, search_tab2, search_tab3 = st.tabs(["Users", "Posts", "Trending"])
        
        with search_tab1:
            user_query = st.text_input("Search users by username or bio", key="user_search")
            if user_query:
                users = search_users(user_query)
                if users:
                    for user in users:
                        with st.container():
                            st.markdown("<div class='user-card'>", unsafe_allow_html=True)
                            col1, col2, col3 = st.columns([1, 3, 1])
                            with col1:
                                user_info = get_user(user[0])
                                if user_info and user_info[3]:
                                    display_image_safely(user_info[3], width=50)
                            with col2:
                                st.write(f"**{user[1]}**")
                                if user[2]:
                                    st.caption(user[2])
                            with col3:
                                if not is_following(user_id, user[0]):
                                    if st.button("Follow", key=f"follow_search_{user[0]}"):
                                        follow_user(user_id, user[0])
                                        st.rerun()
                                else:
                                    if st.button("Unfollow", key=f"unfollow_search_{user[0]}"):
                                        unfollow_user(user_id, user[0])
                                        st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.info("No users found")
        
        with search_tab2:
            post_query = st.text_input("Search posts by content", key="post_search")
            if post_query:
                posts = search_posts(post_query)
                if posts:
                    for post in posts:
                        display_post(post, user_id)
                else:
                    st.info("No posts found")
        
        with search_tab3:
            st.subheader("🔥 Trending Hashtags")
            trending = get_trending_hashtags()
            if trending:
                cols = st.columns(3)
                for i, (hashtag, count) in enumerate(trending):
                    with cols[i % 3]:
                        if st.button(f"{hashtag} ({count})", use_container_width=True):
                            st.session_state.search_query = hashtag
                            st.session_state.page = "Search"
                            st.rerun()
            else:
                st.info("No trending hashtags yet")
    
    # NEW PAGE: Saved Posts
    elif st.session_state.page == "SavedPosts":
        st.header("💾 Saved Posts")
        
        saved_posts = get_saved_posts(user_id)
        if not saved_posts:
            st.info("You haven't saved any posts yet. Click the bookmark icon on posts to save them!")
        else:
            for post in saved_posts:
                display_post(post, user_id, show_save_option=False)
    
    # Enhanced Feed Page with new features
    elif st.session_state.page == "Feed":
        st.header("📱 Your Feed")
        
        # Show trending hashtags in feed
        trending = get_trending_hashtags()
        if trending:
            with st.expander("🔥 Trending Hashtags", expanded=False):
                cols = st.columns(4)
                for i, (hashtag, count) in enumerate(trending[:8]):
                    with cols[i % 4]:
                        if st.button(f"{hashtag} ({count})", use_container_width=True, key=f"trend_{i}"):
                            st.session_state.search_query = hashtag
                            st.session_state.page = "Search"
                            st.rerun()
        
        with st.expander("➕ Create New Post", expanded=False):
            post_content = st.text_area("What's on your mind?", placeholder="Share your thoughts... Use #hashtags to categorize your posts!", height=100)
            media_type = st.selectbox("Media type", ["None", "Image", "Video"])
            media_file = st.file_uploader("Upload media", type=["jpg", "png", "jpeg", "mp4", "mov"])
            
            if st.button("Post", use_container_width=True):
                if post_content or media_file:
                    media_data = media_file.read() if media_file else None
                    media_type_val = media_type.lower() if media_file else None
                    if create_post(user_id, post_content, media_type_val, media_data):
                        st.success("Posted successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to create post")
                else:
                    st.warning("Please add some content or media to your post")
        
        posts = get_posts(user_id)
        if not posts:
            st.info("✨ No posts yet. Follow some users to see their posts here!")
        else:
            for post in posts:
                display_post(post, user_id)

# Enhanced post display function with new features
def display_post(post, user_id, show_save_option=True):
    with st.container():
        st.markdown(f"<div class='post'>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            user_info = get_user(post[1])
            if user_info and user_info[3]:
                display_image_safely(user_info[3], width=50)
        with col2:
            st.write(f"**{post[2]}** · 🕒 {post[6]}")
        with col3:
            if post[1] != user_id:
                if st.button("🚫", key=f"block_{post[0]}_{post[1]}", help="Block User"):
                    if block_user(user_id, post[1]):
                        st.success(f"Blocked {post[2]}")
                        st.rerun()
        
        st.write(post[3])
        
        # Display hashtags
        hashtags = extract_hashtags(post[3])
        if hashtags:
            tag_cols = st.columns(8)
            for i, tag in enumerate(hashtags[:8]):
                with tag_cols[i % 8]:
                    if st.button(tag, key=f"tag_{post[0]}_{i}", use_container_width=True):
                        st.session_state.search_query = tag
                        st.session_state.page = "Search"
                        st.rerun()
        
        if post[4] and post[5]:
            if post[4] == "image":
                display_image_safely(post[5], use_container_width=True)
            elif post[4] == "video":
                try:
                    st.video(io.BytesIO(post[5]))
                except Exception as e:
                    st.warning("Unable to display video")
        
        # Enhanced interaction buttons
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            like_text = "❤️ Unlike" if post[8] else "🤍 Like"
            if st.button(like_text, key=f"like_{post[0]}"):
                like_post(user_id, post[0])
                st.rerun()
            st.write(f"**{post[7]}**")
        
        with col2:
            comment_count = get_comment_count(post[0])
            if st.button(f"💬 {comment_count}", key=f"comment_btn_{post[0]}"):
                if post[0] in st.session_state.show_comments:
                    st.session_state.show_comments[post[0]] = not st.session_state.show_comments[post[0]]
                else:
                    st.session_state.show_comments[post[0]] = True
                st.rerun()
        
        with col3:
            share_count = get_share_count(post[0])
            if st.button(f"🔄 {share_count}", key=f"share_{post[0]}"):
                if share_post(post[0], user_id):
                    st.success("Post shared!")
                    st.rerun()
        
        with col4:
            if show_save_option:
                if is_post_saved(post[0], user_id):
                    if st.button("💾 Saved", key=f"unsave_{post[0]}"):
                        unsave_post(post[0], user_id)
                        st.rerun()
                else:
                    if st.button("📑 Save", key=f"save_{post[0]}"):
                        save_post(post[0], user_id)
                        st.success("Post saved!")
                        st.rerun()
        
        with col5:
            if post[1] == user_id:
                if st.button("🗑️", key=f"delete_{post[0]}", help="Delete Post"):
                    if delete_post(post[0], user_id):
                        st.success("Post deleted!")
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
                        st.caption(f"🕒 {comment[4]}")
            
            # Add new comment
            with st.form(key=f"comment_form_{post[0]}", clear_on_submit=True):
                new_comment = st.text_input("Add a comment...", key=f"comment_input_{post[0]}")
                if st.form_submit_button("Post Comment"):
                    if new_comment:
                        if add_comment(post[0], user_id, new_comment):
                            st.success("Comment added!")
                            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

# Keep all your existing pages (Messages, Notifications, Discover, Profile, etc.)
# [Include all your existing page code here]

# Enhanced Profile Page with saved posts count
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
            
            followers = get_followers(user_id)
            following = get_following(user_id)
            blocked = get_blocked_users(user_id)
            saved_posts_count = len(get_saved_posts(user_id))
            
            st.subheader("Stats")
            st.metric("Followers", len(followers))
            st.metric("Following", len(following))
            st.metric("Saved Posts", saved_posts_count)
            st.metric("Blocked Users", len(blocked))
            
            if st.button("✏️ Edit Profile", use_container_width=True):
                st.session_state.page = "EditProfile"
                st.rerun()
            
            if st.button("💾 Saved Posts", use_container_width=True):
                st.session_state.page = "SavedPosts"
                st.rerun()
            
            if st.button("🚫 Blocked Users", use_container_width=True):
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
                    display_post(post, user_id, show_save_option=False)

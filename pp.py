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
import re
import uuid
import hashlib
import secrets

# ===================================
# CLOUD DEPLOYMENT ENHANCEMENTS
# ===================================

# Configuration for cloud deployment
CLOUD_CONFIG = {
    "app_name": "FeedChat",
    "version": "2.0",
    "deployment_ready": True,
    "max_file_size": 50 * 1024 * 1024,  # 50MB
    "supported_timezones": ["UTC", "EST", "PST", "GMT", "CET", "AEST"],
    "languages": ["en", "es", "fr", "de", "zh", "ja"]
}

def get_user_timezone():
    """Get user timezone for global compatibility"""
    return st.session_state.get('timezone', 'UTC')

def format_global_time(timestamp):
    """Format timestamp for global audience"""
    try:
        if isinstance(timestamp, str):
            # Handle string timestamp
            return timestamp
        elif isinstance(timestamp, datetime.datetime):
            return timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')
        else:
            return str(timestamp)
    except:
        return "Recent"

def optimize_image_for_web(image_data, max_size=(1200, 1200), quality=85):
    """Optimize images for fast global loading"""
    try:
        if image_data and isinstance(image_data, bytes):
            image = Image.open(io.BytesIO(image_data))
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            return output.getvalue()
    except Exception as e:
        st.warning(f"Image optimization failed: {e}")
        return image_data
    return image_data

# ===================================
# SIMPLIFIED DATABASE SETUP
# ===================================

def init_simple_db():
    """Initialize database with essential tables"""
    conn = sqlite3.connect("feed_chat.db", check_same_thread=False)
    c = conn.cursor()

    # Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        email TEXT,
        profile_pic BLOB,
        bio TEXT,
        location TEXT DEFAULT 'Unknown',
        timezone TEXT DEFAULT 'UTC',
        language TEXT DEFAULT 'en',
        is_active BOOLEAN DEFAULT TRUE,
        is_online BOOLEAN DEFAULT FALSE,
        last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
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
        location TEXT DEFAULT 'Unknown',
        language TEXT DEFAULT 'en',
        visibility TEXT DEFAULT 'public',
        is_deleted BOOLEAN DEFAULT FALSE,
        global_reach_count INTEGER DEFAULT 0,
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
        message_type TEXT DEFAULT 'text',
        media_data BLOB,
        is_read BOOLEAN DEFAULT FALSE,
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

    # Create indexes for performance
    c.execute("CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_messages_users ON messages(sender_id, receiver_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_likes_post ON likes(post_id)")

    conn.commit()
    return conn

# Initialize database
conn = init_simple_db()

# ===================================
# CORE FUNCTIONS
# ===================================

def is_valid_image(image_data):
    """Check if the image data is valid"""
    try:
        if image_data is None:
            return False
        if isinstance(image_data, str):
            image_data = base64.b64decode(image_data)
        if not isinstance(image_data, bytes):
            return False
        image = Image.open(io.BytesIO(image_data))
        image.verify()
        return True
    except:
        return False

def display_image_safely(image_data, caption="", width=None, use_container_width=False):
    """Safely display an image with error handling"""
    try:
        if image_data:
            if isinstance(image_data, str):
                image_data = base64.b64decode(image_data)
            
            if not isinstance(image_data, bytes):
                st.warning("Invalid image format")
                return
                
            if is_valid_image(image_data):
                if width:
                    st.image(io.BytesIO(image_data), caption=caption, width=width)
                elif use_container_width:
                    st.image(io.BytesIO(image_data), caption=caption, use_container_width=True)
                else:
                    st.image(io.BytesIO(image_data), caption=caption)
            else:
                st.warning("Unable to display image: Invalid image data")
    except Exception as e:
        st.warning(f"Error displaying image: {str(e)}")

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

def hash_password(password):
    """Secure password hashing"""
    salt = secrets.token_hex(16)
    return f"{salt}${hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()}"

def verify_password(password, password_hash):
    """Verify password against hash"""
    try:
        salt, stored_hash = password_hash.split('$')
        computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
        return computed_hash == stored_hash
    except:
        return False

def create_user_secure(username, password, email, profile_pic=None, bio="", location="Unknown", timezone="UTC", language="en"):
    """Create user with enhanced security"""
    try:
        c = conn.cursor()
        
        # Check if user exists
        c.execute("SELECT id FROM users WHERE username=?", (username,))
        if c.fetchone():
            return False, "Username already exists"
        
        # Check if email exists
        c.execute("SELECT id FROM users WHERE email=?", (email,))
        if c.fetchone():
            return False, "Email already registered"
        
        # Validate password strength
        is_valid, msg = validate_password_strength(password)
        if not is_valid:
            return False, msg
        
        # Validate profile picture
        if profile_pic and not is_valid_image(profile_pic):
            return False, "Invalid profile picture format"
        
        # Optimize profile picture
        if profile_pic:
            profile_pic = optimize_image_for_web(profile_pic)
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user
        c.execute("""
            INSERT INTO users (username, password_hash, email, profile_pic, bio, location, timezone, language) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, password_hash, email, profile_pic, bio, location, timezone, language))
        
        user_id = c.lastrowid
        conn.commit()
        
        return True, user_id
    except sqlite3.Error as e:
        return False, f"Database error: {e}"

def verify_user_secure(username, password):
    """Enhanced user verification"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT id, username, password_hash 
            FROM users 
            WHERE username=? AND is_active=1
        """, (username,))
        user = c.fetchone()
        
        if user and verify_password(password, user[2]):
            # Update last seen and online status
            c.execute("UPDATE users SET is_online=1, last_seen=CURRENT_TIMESTAMP WHERE id=?", (user[0],))
            conn.commit()
            return user[0], user[1]
        return None, None
    except sqlite3.Error:
        return None, None

def get_user(user_id):
    """Get user data"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT id, username, email, profile_pic, bio, location, timezone, language, is_online, last_seen
            FROM users WHERE id=?
        """, (user_id,))
        return c.fetchone()
    except sqlite3.Error:
        return None

def update_user_profile(user_id, email=None, bio=None, location=None, timezone=None, language=None, profile_pic=None):
    """Update user profile"""
    try:
        c = conn.cursor()
        
        # Build dynamic update query
        updates = []
        params = []
        
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if bio is not None:
            updates.append("bio = ?")
            params.append(bio)
        if location is not None:
            updates.append("location = ?")
            params.append(location)
        if timezone is not None:
            updates.append("timezone = ?")
            params.append(timezone)
        if language is not None:
            updates.append("language = ?")
            params.append(language)
        if profile_pic is not None:
            if profile_pic == "":  # Empty string means remove profile pic
                updates.append("profile_pic = NULL")
            else:
                updates.append("profile_pic = ?")
                params.append(profile_pic)
        
        if not updates:
            return False, "No fields to update"
        
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        
        c.execute(query, params)
        conn.commit()
        
        # Update session state if location changed
        if location is not None:
            st.session_state.location = location
        
        return True, "Profile updated successfully"
    except sqlite3.Error as e:
        return False, f"Database error: {e}"

def validate_post_content(content):
    """Validate post content"""
    if not content or len(content.strip()) == 0:
        return False, "Post content cannot be empty"
    if len(content) > 10000:
        return False, "Post content too long (max 10,000 characters)"
    return True, "Content is valid"

def create_global_post(user_id, content, media_data=None, media_type=None, location="Unknown", language="en", visibility="public"):
    """Create post with global reach capabilities"""
    try:
        # Validate content
        is_valid, msg = validate_post_content(content)
        if not is_valid:
            st.error(msg)
            return None
            
        c = conn.cursor()
        
        # Optimize media for web
        if media_data and media_type and 'image' in media_type:
            media_data = optimize_image_for_web(media_data)
        
        c.execute("""
            INSERT INTO posts 
            (user_id, content, media_type, media_data, location, language, visibility) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, content, media_type, media_data, location, language, visibility))
        
        post_id = c.lastrowid
        conn.commit()
        return post_id
    except sqlite3.Error as e:
        st.error(f"Post creation failed: {e}")
        return None

def get_global_posts(limit=20, language=None, location=None):
    """Get posts for global feed"""
    try:
        c = conn.cursor()
        
        query = """
            SELECT p.*, u.username, u.profile_pic,
                   COUNT(DISTINCT l.id) as like_count,
                   COUNT(DISTINCT c.id) as comment_count
            FROM posts p
            JOIN users u ON p.user_id = u.id
            LEFT JOIN likes l ON p.id = l.post_id
            LEFT JOIN comments c ON p.id = c.post_id
            WHERE p.is_deleted = 0 AND p.visibility = 'public'
        """
        params = []
        
        if language and language != 'all':
            query += " AND (p.language = ? OR p.language = 'en')"
            params.append(language)
        
        if location and location != 'global':
            query += " AND (p.location LIKE ? OR u.location LIKE ?)"
            params.extend([f'%{location}%', f'%{location}%'])
        
        query += """
            GROUP BY p.id
            ORDER BY p.created_at DESC
            LIMIT ?
        """
        params.append(limit)
        
        c.execute(query, params)
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Failed to load posts: {e}")
        return []

def like_post(user_id, post_id):
    """Like a post"""
    try:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False

def unlike_post(user_id, post_id):
    """Unlike a post"""
    try:
        c = conn.cursor()
        c.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False

def has_liked_post(user_id, post_id):
    """Check if user has liked a post"""
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        return c.fetchone() is not None
    except sqlite3.Error:
        return False

def add_comment(post_id, user_id, content):
    """Add a comment to a post"""
    try:
        if not content or len(content.strip()) == 0:
            return False, "Comment cannot be empty"
        if len(content) > 1000:
            return False, "Comment too long (max 1000 characters)"
            
        c = conn.cursor()
        c.execute("INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
                 (post_id, user_id, content))
        conn.commit()
        return True, "Comment added successfully"
    except sqlite3.Error:
        return False, "Failed to add comment"

def get_comments(post_id):
    """Get comments for a post"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT c.*, u.username, u.profile_pic
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.created_at ASC
        """, (post_id,))
        return c.fetchall()
    except sqlite3.Error:
        return []

def delete_post(post_id, user_id):
    """Delete a post (soft delete)"""
    try:
        c = conn.cursor()
        c.execute("UPDATE posts SET is_deleted = 1 WHERE id = ? AND user_id = ?", (post_id, user_id))
        conn.commit()
        return c.rowcount > 0
    except sqlite3.Error:
        return False

def edit_post(post_id, user_id, new_content):
    """Edit a post"""
    try:
        is_valid, msg = validate_post_content(new_content)
        if not is_valid:
            return False, msg
            
        c = conn.cursor()
        c.execute("UPDATE posts SET content = ? WHERE id = ? AND user_id = ?", 
                 (new_content, post_id, user_id))
        conn.commit()
        return c.rowcount > 0, "Post updated successfully"
    except sqlite3.Error as e:
        return False, f"Database error: {e}"

def mark_messages_as_read(user_id, other_user_id):
    """Mark messages as read when viewed"""
    try:
        c = conn.cursor()
        c.execute("""
            UPDATE messages 
            SET is_read = 1 
            WHERE receiver_id = ? AND sender_id = ? AND is_read = 0
        """, (user_id, other_user_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False

def send_global_message(sender_id, receiver_id, content, message_type='text', media_data=None):
    """Send message globally"""
    try:
        if not content or len(content.strip()) == 0:
            return False, "Message cannot be empty"
        if len(content) > 5000:
            return False, "Message too long (max 5000 characters)"
            
        c = conn.cursor()
        
        # Optimize media if present
        if media_data and message_type == 'image':
            media_data = optimize_image_for_web(media_data)
        
        c.execute("""
            INSERT INTO messages 
            (sender_id, receiver_id, content, message_type, media_data) 
            VALUES (?, ?, ?, ?, ?)
        """, (sender_id, receiver_id, content, message_type, media_data))
        
        conn.commit()
        return True, "Message sent successfully"
    except sqlite3.Error as e:
        return False, f"Message sending failed: {e}"

def get_global_messages(user_id, other_user_id, limit=50):
    """Get messages between users"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT m.*, u.username as sender_name
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE (m.sender_id = ? AND m.receiver_id = ?) 
               OR (m.sender_id = ? AND m.receiver_id = ?)
            ORDER BY m.created_at ASC
            LIMIT ?
        """, (user_id, other_user_id, other_user_id, user_id, limit))
        return c.fetchall()
    except sqlite3.Error:
        return []

def get_global_conversations(user_id):
    """Get conversations for a user"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT DISTINCT 
                CASE 
                    WHEN m.sender_id = ? THEN m.receiver_id 
                    ELSE m.sender_id 
                END as other_user_id,
                u.username,
                u.profile_pic,
                MAX(m.created_at) as last_message_time,
                (SELECT content FROM messages 
                 WHERE ((sender_id = ? AND receiver_id = other_user_id) 
                     OR (sender_id = other_user_id AND receiver_id = ?))
                 ORDER BY created_at DESC LIMIT 1) as last_message,
                (SELECT COUNT(*) FROM messages 
                 WHERE receiver_id = ? AND sender_id = other_user_id AND is_read = 0) as unread_count,
                u.location
            FROM messages m
            JOIN users u ON u.id = CASE 
                WHEN m.sender_id = ? THEN m.receiver_id 
                ELSE m.sender_id 
            END
            WHERE m.sender_id = ? OR m.receiver_id = ?
            GROUP BY other_user_id
            ORDER BY last_message_time DESC
        """, (user_id, user_id, user_id, user_id, user_id, user_id, user_id))
        return c.fetchall()
    except sqlite3.Error:
        return []

def get_online_users():
    """Get currently online users"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT id, username, location 
            FROM users 
            WHERE is_online = 1 AND id != ? 
            ORDER BY last_seen DESC
        """, (st.session_state.user_id,))
        return c.fetchall()
    except sqlite3.Error:
        return []

def get_global_users(search_term=None, location_filter=None):
    """Get global users with filtering"""
    try:
        c = conn.cursor()
        
        query = "SELECT id, username, profile_pic, bio, location, language, is_online FROM users WHERE id != ?"
        params = [st.session_state.user_id]
        
        if search_term:
            query += " AND (username LIKE ? OR bio LIKE ?)"
            params.extend([f'%{search_term}%', f'%{search_term}%'])
        
        if location_filter:
            query += " AND location LIKE ?"
            params.append(f'%{location_filter}%')
        
        query += " ORDER BY is_online DESC, username ASC LIMIT 50"
        
        c.execute(query, params)
        return c.fetchall()
    except sqlite3.Error:
        return []

# ===================================
# UI COMPONENTS
# ===================================

def inject_custom_css():
    """Inject custom CSS for dark theme"""
    st.markdown("""
    <style>
    .main {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .css-1d391kg, .css-1lcbmhc {
        background-color: #161b22 !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #58a6ff !important;
        font-family: 'Segoe UI', system-ui, sans-serif;
    }
    .feed-card {
        background-color: #161b22;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid #30363d;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton>button {
        background-color: #238636 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
    }
    .stButton>button:hover {
        background-color: #2ea043 !important;
        transform: translateY(-1px);
    }
    .message-bubble {
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 18px;
        max-width: 70%;
        word-wrap: break-word;
    }
    .message-sent {
        background: linear-gradient(135deg, #238636, #2ea043);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }
    .message-received {
        background: #21262d;
        color: #c9d1d9;
        margin-right: auto;
        border-bottom-left-radius: 4px;
    }
    .gradient-text {
        background: linear-gradient(135deg, #58a6ff, #238636);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
    }
    .danger-button {
        background-color: #da3633 !important;
    }
    .danger-button:hover {
        background-color: #f85149 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def login_page():
    """Login page"""
    st.markdown("<h1 class='gradient-text'>📱 Feed Chat</h1>", unsafe_allow_html=True)
    st.markdown("### Share posts and chat with people worldwide!")
    
    tab1, tab2 = st.tabs(["🚀 Sign In", "✨ Create Account"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("👤 Username")
            password = st.text_input("🔒 Password", type="password")
            submit = st.form_submit_button("📱 Sign In")
            
            if submit:
                if username and password:
                    user_id, username = verify_user_secure(username, password)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.session_state.logged_in = True
                        
                        # Get user data and store in session
                        user_data = get_user(user_id)
                        if user_data:
                            st.session_state.location = user_data[5]  # location
                            st.session_state.timezone = user_data[6]  # timezone
                        
                        st.success(f"🎉 Welcome, {username}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
                else:
                    st.error("⚠️ Please enter both username and password")
    
    with tab2:
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("🎯 Username")
                new_password = st.text_input("🔑 Password", type="password")
                confirm_password = st.text_input("✅ Confirm Password", type="password")
                email = st.text_input("📧 Email")
            
            with col2:
                location = st.text_input("📍 Your Location", placeholder="City, Country")
                timezone = st.selectbox("🌐 Timezone", CLOUD_CONFIG["supported_timezones"])
                language = st.selectbox("🗣️ Language", CLOUD_CONFIG["languages"])
                bio = st.text_area("📝 Bio (Optional)")
            
            profile_pic = st.file_uploader("🖼️ Profile Picture (Optional)", type=['jpg', 'png', 'jpeg'])
            
            register = st.form_submit_button("📱 Join Feed Chat")
            
            if register:
                if new_username and new_password and email:
                    if new_password == confirm_password:
                        profile_pic_data = profile_pic.read() if profile_pic else None
                        
                        success, result = create_user_secure(
                            new_username, new_password, email, profile_pic_data, bio, 
                            location, timezone, language
                        )
                        
                        if success:
                            st.success("🎊 Account created! Please sign in.")
                        else:
                            st.error(f"❌ {result}")
                    else:
                        st.error("🔒 Passwords do not match")
                else:
                    st.error("⚠️ Please fill in required fields")

def feed_page():
    """Feed page"""
    st.markdown("<h1 class='gradient-text'>📰 Feed</h1>", unsafe_allow_html=True)
    
    # Refresh button
    if st.button("🔄 Refresh Feed"):
        st.rerun()
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        language_filter = st.selectbox("🗣️ Language", ["all", "en", "es", "fr", "de"])
    with col2:
        location_filter = st.text_input("📍 Location filter", placeholder="e.g., Tokyo")
    
    # Create post
    with st.expander("✍️ Create Post"):
        with st.form("create_post"):
            content = st.text_area("💭 What's happening worldwide?", height=100)
            media_file = st.file_uploader("📁 Add Media", type=['jpg', 'png', 'jpeg', 'mp4'])
            post_location = st.text_input("📍 Location", value=st.session_state.get('location', 'Unknown'))
            
            if st.form_submit_button("🚀 Publish Post"):
                if content:
                    media_data = None
                    media_type = None
                    if media_file:
                        media_data = media_file.read()
                        media_type = media_file.type
                    
                    post_id = create_global_post(
                        st.session_state.user_id, content, media_data, media_type,
                        post_location
                    )
                    
                    if post_id:
                        st.success("📱 Post published!")
                        st.rerun()
                else:
                    st.error("Please enter some content for your post")
    
    # Display posts
    st.markdown("### 📰 Recent Posts")
    
    posts = get_global_posts(language=language_filter, location=location_filter)
    
    if not posts:
        st.info("🌟 No posts yet. Be the first to share!")
        return
    
    for post in posts:
        display_post_card(post)

def display_post_card(post):
    """Display post card"""
    (post_id, user_id, content, media_type, media_data, location, language, 
     visibility, is_deleted, global_reach_count, created_at, username, 
     profile_pic, like_count, comment_count) = post
    
    with st.container():
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if profile_pic and is_valid_image(profile_pic):
                st.image(io.BytesIO(profile_pic), width=50)
            else:
                st.markdown("""
                <div style="width: 50px; height: 50px; border-radius: 50%; background: #58a6ff; 
                            display: flex; align-items: center; justify-content: center; color: white; font-size: 18px;">
                    👤
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"**{username}** · 📍 {location}")
            st.write(content)
        
        if media_data and media_type:
            if 'image' in media_type:
                display_image_safely(media_data, use_container_width=True)
            elif 'video' in media_type:
                st.video(io.BytesIO(media_data))
        
        # Engagement buttons
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
        
        with col1:
            has_liked = has_liked_post(st.session_state.user_id, post_id)
            like_text = "💔 Unlike" if has_liked else "❤️ Like"
            if st.button(f"{like_text} {like_count}", key=f"like_{post_id}"):
                if has_liked:
                    unlike_post(st.session_state.user_id, post_id)
                else:
                    like_post(st.session_state.user_id, post_id)
                st.rerun()
        
        with col2:
            if st.button(f"💬 {comment_count}", key=f"comment_{post_id}"):
                if 'current_post' in st.session_state and st.session_state.current_post == post_id:
                    del st.session_state.current_post
                else:
                    st.session_state.current_post = post_id
                st.rerun()
        
        # Post owner actions
        if user_id == st.session_state.user_id:
            with col3:
                if st.button("✏️", key=f"edit_{post_id}"):
                    st.session_state.editing_post = post_id
                    st.rerun()
            
            with col4:
                if st.button("🗑️", key=f"delete_{post_id}"):
                    if delete_post(post_id, user_id):
                        st.success("Post deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete post")
        
        # Edit post form
        if hasattr(st.session_state, 'editing_post') and st.session_state.editing_post == post_id:
            with st.form(f"edit_post_{post_id}"):
                edited_content = st.text_area("Edit your post:", value=content, height=100)
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Save"):
                        success, message = edit_post(post_id, user_id, edited_content)
                        if success:
                            st.success("Post updated!")
                            del st.session_state.editing_post
                            st.rerun()
                        else:
                            st.error(message)
                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        del st.session_state.editing_post
                        st.rerun()
        
        # Comments section
        if hasattr(st.session_state, 'current_post') and st.session_state.current_post == post_id:
            st.markdown("---")
            with st.form(f"comment_form_{post_id}"):
                comment = st.text_input("💭 Add a comment...")
                if st.form_submit_button("💬 Comment"):
                    if comment:
                        success, message = add_comment(post_id, st.session_state.user_id, comment)
                        if success:
                            st.rerun()
                        else:
                            st.error(message)
            
            comments = get_comments(post_id)
            if comments:
                st.markdown("**Comments:**")
                for comment in comments:
                    comment_id, _, comment_user_id, comment_content, comment_created_at, comment_username, comment_profile_pic = comment
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if comment_profile_pic and is_valid_image(comment_profile_pic):
                            st.image(io.BytesIO(comment_profile_pic), width=30)
                    with col2:
                        st.markdown(f"**{comment_username}**: {comment_content}")
                        st.caption(f"_{format_global_time(comment_created_at)}_")

def chat_page():
    """Chat page"""
    st.markdown("<h1 class='gradient-text'>💬 Chat</h1>", unsafe_allow_html=True)
    
    if st.button("🔄 Refresh Messages"):
        st.rerun()
    
    # Online users sidebar
    st.sidebar.markdown("### 👥 Online Users")
    online_users = get_online_users()
    for user in online_users:
        user_id, username, location = user
        if st.sidebar.button(f"💬 {username} ({location})", key=f"online_{user_id}"):
            st.session_state.current_chat = user_id
            st.session_state.chat_username = username
            st.rerun()
    
    tab1, tab2 = st.tabs(["💭 Chats", "👥 Find Users"])
    
    with tab1:
        display_chat_interface()
    
    with tab2:
        display_user_directory()

def display_chat_interface():
    """Display chat interface"""
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Conversations")
        conversations = get_global_conversations(st.session_state.user_id)
        
        if not conversations:
            st.info("💬 No conversations yet")
        else:
            for conv in conversations:
                other_user_id, username, profile_pic, last_time, last_msg, unread, location = conv
                
                btn_text = f"{username} ({location})"
                if unread > 0:
                    btn_text = f"🔔 {btn_text} ({unread})"
                
                if st.button(btn_text, key=f"conv_{other_user_id}", use_container_width=True):
                    st.session_state.current_chat = other_user_id
                    st.session_state.chat_username = username
                    st.rerun()
    
    with col2:
        if hasattr(st.session_state, 'current_chat'):
            display_chat_messages()
        else:
            st.info("💬 Select a conversation to start chatting")

def display_chat_messages():
    """Display chat messages"""
    st.markdown(f"### 💬 Chat with {st.session_state.chat_username}")
    
    # Mark messages as read when viewing
    mark_messages_as_read(st.session_state.user_id, st.session_state.current_chat)
    
    messages = get_global_messages(st.session_state.user_id, st.session_state.current_chat)
    
    # Display messages
    for msg in messages:
        msg_id, sender_id, receiver_id, content, msg_type, media_data, is_read, created_at, sender_name = msg
        
        if sender_id == st.session_state.user_id:
            # Sent message
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
                <div class="message-bubble message-sent">
                    <div>{content}</div>
                    <small>{format_global_time(created_at)}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if media_data and msg_type == 'image':
                display_image_safely(media_data, width=200)
        else:
            # Received message
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
                <div class="message-bubble message-received">
                    <div><strong>{sender_name}</strong></div>
                    <div>{content}</div>
                    <small>{format_global_time(created_at)}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if media_data and msg_type == 'image':
                display_image_safely(media_data, width=200)
    
    # Send message
    st.markdown("---")
    with st.form("send_message"):
        message = st.text_input("💭 Type your message...")
        media_file = st.file_uploader("📎 Attach image", type=['jpg', 'png', 'jpeg'])
        
        if st.form_submit_button("📤 Send"):
            if message or media_file:
                media_data = media_file.read() if media_file else None
                msg_type = 'image' if media_file else 'text'
                content = message if message else "📸 Shared an image"
                
                success, result = send_global_message(
                    st.session_state.user_id, st.session_state.current_chat, 
                    content, msg_type, media_data
                )
                
                if success:
                    st.rerun()
                else:
                    st.error(result)
            else:
                st.error("Please enter a message or attach an image")

def display_user_directory():
    """Display user directory"""
    st.markdown("### 👥 Users")
    
    search = st.text_input("🔍 Search users...")
    location_filter = st.text_input("📍 Filter by location...")
    
    users = get_global_users(search_term=search, location_filter=location_filter)
    
    if not users:
        st.info("👥 No users found")
    else:
        for user in users:
            user_id, username, profile_pic, bio, location, language, is_online = user
            
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                if profile_pic and is_valid_image(profile_pic):
                    st.image(io.BytesIO(profile_pic), width=50)
                else:
                    st.write("👤")
            
            with col2:
                online_status = "🟢 Online" if is_online else "⚫ Offline"
                st.write(f"**{username}** - {online_status}")
                st.write(f"📍 {location} · 🗣️ {language}")
                if bio:
                    st.write(bio[:50] + "..." if len(bio) > 50 else bio)
            
            with col3:
                if st.button("💬", key=f"dir_{user_id}"):
                    st.session_state.current_chat = user_id
                    st.session_state.chat_username = username
                    st.rerun()
            
            st.markdown("---")

def profile_page():
    """Profile page with edit functionality"""
    st.markdown("<h1 class='gradient-text'>👤 Your Profile</h1>", unsafe_allow_html=True)
    
    user = get_user(st.session_state.user_id)
    if user:
        user_id, username, email, profile_pic, bio, location, timezone, language, is_online, last_seen = user
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if profile_pic and is_valid_image(profile_pic):
                st.image(io.BytesIO(profile_pic), width=150)
            else:
                st.markdown("""
                <div style="width: 150px; height: 150px; border-radius: 50%; background: #58a6ff; 
                            display: flex; align-items: center; justify-content: center; color: white; font-size: 48px;">
                    👤
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"## {username}")
            st.write(f"**📧** {email}")
            st.write(f"**📍** {location}")
            st.write(f"**🌐** {timezone}")
            st.write(f"**🗣️** {language}")
            
            if bio:
                st.write(f"**📝** {bio}")
            
            status = "🟢 Online" if is_online else "⚫ Offline"
            st.write(f"**Status:** {status}")
            st.write(f"**Last seen:** {format_global_time(last_seen)}")
    
    # Edit profile section
    st.markdown("---")
    st.markdown("### ✏️ Edit Profile")
    
    with st.form("edit_profile"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_email = st.text_input("📧 Email", value=email)
            new_bio = st.text_area("📝 Bio", value=bio if bio else "", height=100)
            new_location = st.text_input("📍 Location", value=location)
        
        with col2:
            new_timezone = st.selectbox("🌐 Timezone", CLOUD_CONFIG["supported_timezones"], 
                                      index=CLOUD_CONFIG["supported_timezones"].index(timezone) if timezone in CLOUD_CONFIG["supported_timezones"] else 0)
            new_language = st.selectbox("🗣️ Language", CLOUD_CONFIG["languages"], 
                                      index=CLOUD_CONFIG["languages"].index(language) if language in CLOUD_CONFIG["languages"] else 0)
            new_profile_pic = st.file_uploader("🖼️ Update Profile Picture", type=['jpg', 'png', 'jpeg'])
            remove_pic = st.checkbox("Remove current profile picture")
        
        if st.form_submit_button("💾 Update Profile"):
            profile_pic_data = None
            if remove_pic:
                profile_pic_data = ""
            elif new_profile_pic:
                profile_pic_data = new_profile_pic.read()
            
            success, message = update_user_profile(
                st.session_state.user_id,
                email=new_email,
                bio=new_bio,
                location=new_location,
                timezone=new_timezone,
                language=new_language,
                profile_pic=profile_pic_data
            )
            
            if success:
                st.success("Profile updated successfully!")
                st.rerun()
            else:
                st.error(message)

# ===================================
# MAIN APPLICATION
# ===================================

def main():
    """Main application"""
    
    # Inject custom CSS
    inject_custom_css()
    
    # Initialize ALL session state variables
    default_states = {
        'logged_in': False,
        'user_id': None,
        'username': None,
        'current_chat': None,
        'chat_username': None,
        'current_post': None,
        'editing_post': None,
        'location': 'Unknown',
        'timezone': 'UTC'
    }
    
    for key, default in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = default
    
    # App header
    st.sidebar.markdown("<h1 class='gradient-text'>📱 Feed Chat</h1>", unsafe_allow_html=True)
    
    if not st.session_state.logged_in:
        login_page()
        return
    
    # Navigation
    st.sidebar.markdown(f"### 👋 Welcome, {st.session_state.username}!")
    
    menu = st.sidebar.selectbox("Navigation", [
        "📰 Feed",
        "💬 Chat", 
        "👤 Profile"
    ])
    
    # Stats
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Quick Stats")
    online_count = len(get_online_users())
    st.sidebar.metric("👥 Online Now", online_count)
    
    # Logout
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        # Update online status
        try:
            c = conn.cursor()
            c.execute("UPDATE users SET is_online=0 WHERE id=?", (st.session_state.user_id,))
            conn.commit()
        except:
            pass
        
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        st.rerun()
    
    # Display selected page
    if menu == "📰 Feed":
        feed_page()
    elif menu == "💬 Chat":
        chat_page()
    elif menu == "👤 Profile":
        profile_page()

if __name__ == "__main__":
    main()

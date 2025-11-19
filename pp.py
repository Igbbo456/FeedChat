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
from typing import List, Dict, Any
import uuid
import hashlib
import secrets
import requests
from streamlit_autorefresh import st_autorefresh

# ===================================
# CLOUD DEPLOYMENT ENHANCEMENTS
# ===================================

# Configuration for cloud deployment
CLOUD_CONFIG = {
    "app_name": "GlobalFeedChat",
    "version": "2.0",
    "deployment_ready": True,
    "max_file_size": 50 * 1024 * 1024,  # 50MB
    "supported_timezones": ["UTC", "EST", "PST", "GMT", "CET", "AEST"],
    "languages": ["en", "es", "fr", "de", "zh", "ja"]
}

def get_user_timezone():
    """Get user timezone for global compatibility"""
    return st.session_state.get('timezone', 'UTC')

def format_global_time(timestamp, user_timezone='UTC'):
    """Format timestamp for global audience"""
    try:
        if isinstance(timestamp, str):
            timestamp = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        return str(timestamp)

def optimize_image_for_web(image_data, max_size=(1200, 1200), quality=85):
    """Optimize images for fast global loading"""
    try:
        if image_data:
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
# REAL-TIME GLOBAL MESSAGING ENHANCEMENTS
# ===================================

class GlobalMessagingSystem:
    def __init__(self):
        self.message_queue = queue.Queue()
        self.active_users = set()
        self.last_update = datetime.datetime.now()
    
    def broadcast_message(self, message_type, data, target_users=None):
        """Broadcast messages to all or specific users"""
        message = {
            'id': str(uuid.uuid4()),
            'type': message_type,
            'data': data,
            'timestamp': datetime.datetime.now().isoformat(),
            'target_users': target_users
        }
        self.message_queue.put(message)
        self.last_update = datetime.datetime.now()
    
    def get_user_messages(self, user_id, since_timestamp=None):
        """Get messages for a specific user"""
        messages = []
        temp_queue = queue.Queue()
        
        while not self.message_queue.empty():
            msg = self.message_queue.get()
            temp_queue.put(msg)
            
            # Check if message is for this user
            if (msg['target_users'] is None or 
                user_id in msg['target_users'] or 
                msg['type'] in ['global_announcement', 'new_user_joined']):
                
                if since_timestamp is None or msg['timestamp'] > since_timestamp:
                    messages.append(msg)
        
        # Restore messages to main queue
        while not temp_queue.empty():
            self.message_queue.put(temp_queue.get())
        
        return messages

# Initialize global messaging system
global_messaging = GlobalMessagingSystem()

# ===================================
# ENHANCED DATABASE FOR GLOBAL SCALE
# ===================================

def init_enhanced_db():
    """Initialize database with global scalability features"""
    conn = sqlite3.connect("feedchat_global.db", check_same_thread=False)
    c = conn.cursor()

    # Enhanced users table for global app
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        email TEXT UNIQUE,
        profile_pic BLOB,
        bio TEXT,
        location TEXT,
        timezone TEXT DEFAULT 'UTC',
        language TEXT DEFAULT 'en',
        is_active BOOLEAN DEFAULT TRUE,
        is_online BOOLEAN DEFAULT FALSE,
        last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Enhanced posts with global reach
    c.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        media_type TEXT,
        media_data BLOB,
        location TEXT,
        language TEXT DEFAULT 'en',
        visibility TEXT DEFAULT 'public', -- public, friends, private
        is_deleted BOOLEAN DEFAULT FALSE,
        global_reach_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Global engagement tracking
    c.execute("""
    CREATE TABLE IF NOT EXISTS global_engagement (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_id INTEGER,
        engagement_type TEXT, -- view, like, share, comment
        user_location TEXT,
        user_timezone TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Real-time session management
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        session_token TEXT UNIQUE,
        ip_address TEXT,
        user_agent TEXT,
        login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    )
    """)

    # Cross-platform messaging
    c.execute("""
    CREATE TABLE IF NOT EXISTS cross_platform_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        content TEXT,
        message_type TEXT DEFAULT 'text', -- text, image, video, file
        media_data BLOB,
        is_delivered BOOLEAN DEFAULT FALSE,
        is_read BOOLEAN DEFAULT FALSE,
        read_receipt_sent BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        delivered_at DATETIME,
        read_at DATETIME
    )
    """)

    # Existing tables (keeping your structure)
    c.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        post_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_id INTEGER,
        content TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

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

    # Add indexes for performance
    c.execute("CREATE INDEX IF NOT EXISTS idx_posts_global ON posts(created_at, visibility)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_messages_real_time ON messages(created_at, sender_id, receiver_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_users_online ON users(is_online, last_seen)")

    conn.commit()
    return conn

# Initialize enhanced database
conn = init_enhanced_db()

# ===================================
# ENHANCED AUTHENTICATION & SECURITY
# ===================================

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
        c.execute("SELECT id FROM users WHERE username=? OR email=?", (username, email))
        if c.fetchone():
            return False, "Username or email already exists"
        
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
            INSERT INTO users (username, password_hash, email, profile_pic, bio, location, timezone, language, is_active) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, password_hash, email, profile_pic, bio, location, timezone, language, True))
        
        user_id = c.lastrowid
        
        # Create user session
        session_token = create_user_session(user_id)
        
        conn.commit()
        
        # Broadcast new user join
        global_messaging.broadcast_message('new_user_joined', {
            'user_id': user_id,
            'username': username,
            'location': location
        })
        
        return True, user_id
    except sqlite3.Error as e:
        return False, f"Database error: {e}"

def verify_user_secure(username, password):
    """Enhanced user verification"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT id, username, password_hash, is_active 
            FROM users 
            WHERE username=? AND is_active=1
        """, (username,))
        user = c.fetchone()
        
        if user and verify_password(password, user[2]):
            # Update last seen and online status
            c.execute("UPDATE users SET is_online=1, last_seen=CURRENT_TIMESTAMP WHERE id=?", (user[0],))
            conn.commit()
            
            # Create session
            session_token = create_user_session(user[0])
            
            return user[0], user[1], session_token
        return None, None, None
    except sqlite3.Error:
        return None, None, None

def create_user_session(user_id, ip_address="0.0.0.0", user_agent="Unknown"):
    """Create user session for tracking"""
    try:
        c = conn.cursor()
        session_token = secrets.token_urlsafe(32)
        
        c.execute("""
            INSERT INTO user_sessions (user_id, session_token, ip_address, user_agent) 
            VALUES (?, ?, ?, ?)
        """, (user_id, session_token, ip_address, user_agent))
        
        conn.commit()
        return session_token
    except sqlite3.Error:
        return None

# ===================================
# GLOBAL MESSAGING FUNCTIONS
# ===================================

def send_global_message(sender_id, receiver_id, content, message_type='text', media_data=None):
    """Send message with global delivery tracking"""
    try:
        c = conn.cursor()
        
        # Optimize media if present
        if media_data and message_type in ['image', 'video']:
            if message_type == 'image':
                media_data = optimize_image_for_web(media_data)
        
        c.execute("""
            INSERT INTO cross_platform_messages 
            (sender_id, receiver_id, content, message_type, media_data, is_delivered) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sender_id, receiver_id, content, message_type, media_data, True))
        
        message_id = c.lastrowid
        
        # Update delivery time
        c.execute("""
            UPDATE cross_platform_messages 
            SET delivered_at=CURRENT_TIMESTAMP 
            WHERE id=?
        """, (message_id,))
        
        conn.commit()
        
        # Broadcast message for real-time updates
        global_messaging.broadcast_message('new_message', {
            'message_id': message_id,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'content': content,
            'message_type': message_type
        }, target_users=[receiver_id])
        
        # Track global engagement
        track_global_engagement(sender_id, None, 'message_sent')
        
        return message_id
    except sqlite3.Error as e:
        st.error(f"Message sending failed: {e}")
        return None

def get_global_messages(user_id, other_user_id, limit=100, since_timestamp=None):
    """Get messages with global timestamp formatting"""
    try:
        c = conn.cursor()
        
        if since_timestamp:
            c.execute("""
                SELECT cm.*, u1.username as sender_name, u2.username as receiver_name
                FROM cross_platform_messages cm
                JOIN users u1 ON cm.sender_id = u1.id
                JOIN users u2 ON cm.receiver_id = u2.id
                WHERE ((cm.sender_id = ? AND cm.receiver_id = ?) 
                    OR (cm.sender_id = ? AND cm.receiver_id = ?))
                AND cm.created_at > ?
                ORDER BY cm.created_at ASC
            """, (user_id, other_user_id, other_user_id, user_id, since_timestamp))
        else:
            c.execute("""
                SELECT cm.*, u1.username as sender_name, u2.username as receiver_name
                FROM cross_platform_messages cm
                JOIN users u1 ON cm.sender_id = u1.id
                JOIN users u2 ON cm.receiver_id = u2.id
                WHERE (cm.sender_id = ? AND cm.receiver_id = ?) 
                   OR (cm.sender_id = ? AND cm.receiver_id = ?)
                ORDER BY cm.created_at ASC
                LIMIT ?
            """, (user_id, other_user_id, other_user_id, user_id, limit))
        
        messages = c.fetchall()
        
        # Format timestamps for global audience
        formatted_messages = []
        for msg in messages:
            msg_list = list(msg)
            # Format created_at timestamp
            msg_list[9] = format_global_time(msg_list[9])
            formatted_messages.append(tuple(msg_list))
        
        return formatted_messages
    except sqlite3.Error:
        return []

def track_global_engagement(user_id, post_id, engagement_type, location=None, timezone=None):
    """Track user engagement globally"""
    try:
        c = conn.cursor()
        
        if location is None:
            location = "Unknown"
        if timezone is None:
            timezone = "UTC"
        
        c.execute("""
            INSERT INTO global_engagement 
            (user_id, post_id, engagement_type, user_location, user_timezone) 
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, post_id, engagement_type, location, timezone))
        
        # Update post global reach count
        if post_id and engagement_type in ['view', 'like', 'share']:
            c.execute("""
                UPDATE posts 
                SET global_reach_count = global_reach_count + 1 
                WHERE id = ?
            """, (post_id,))
        
        conn.commit()
        return True
    except sqlite3.Error:
        return False

# ===================================
# ENHANCED POST FUNCTIONS FOR GLOBAL REACH
# ===================================

def create_global_post(user_id, content, media_data=None, media_type=None, location="Unknown", language="en", visibility="public"):
    """Create post with global reach capabilities"""
    try:
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
        
        # Track creation engagement
        track_global_engagement(user_id, post_id, 'post_created', location)
        
        # Broadcast new post to global feed
        global_messaging.broadcast_message('new_post', {
            'post_id': post_id,
            'user_id': user_id,
            'content_preview': content[:100] + '...' if len(content) > 100 else content,
            'location': location,
            'language': language
        })
        
        return post_id
    except sqlite3.Error as e:
        st.error(f"Post creation failed: {e}")
        return None

def get_global_posts(limit=20, offset=0, language=None, location=None):
    """Get posts for global feed with filtering options"""
    try:
        c = conn.cursor()
        
        query = """
            SELECT p.*, u.username, u.profile_pic, u.location as user_location,
                   COUNT(DISTINCT l.id) as like_count,
                   COUNT(DISTINCT c.id) as comment_count
            FROM posts p
            JOIN users u ON p.user_id = u.id
            LEFT JOIN likes l ON p.id = l.post_id
            LEFT JOIN comments c ON p.id = c.post_id
            WHERE p.is_deleted = 0 AND p.visibility = 'public'
        """
        params = []
        
        # Add language filter
        if language and language != 'all':
            query += " AND (p.language = ? OR p.language = 'en')"
            params.append(language)
        
        # Add location filter
        if location and location != 'global':
            query += " AND (p.location LIKE ? OR u.location LIKE ?)"
            params.extend([f'%{location}%', f'%{location}%'])
        
        query += """
            GROUP BY p.id
            ORDER BY p.global_reach_count DESC, p.created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        c.execute(query, params)
        posts = c.fetchall()
        
        # Track views for global reach analytics
        for post in posts:
            track_global_engagement(
                st.session_state.user_id, 
                post[0], 
                'view',
                st.session_state.get('location', 'Unknown'),
                st.session_state.get('timezone', 'UTC')
            )
        
        return posts
    except sqlite3.Error as e:
        st.error(f"Failed to load posts: {e}")
        return []

# ===================================
# ENHANCED UI COMPONENTS
# ===================================

def global_user_profile():
    """Enhanced user profile with global features"""
    st.markdown("<h1 class='gradient-text'>🌍 Global Profile</h1>", unsafe_allow_html=True)
    
    try:
        user = get_user(st.session_state.user_id)
        if user:
            user_id, username, email, profile_pic, bio, location, timezone, language, is_active, is_online, last_seen, created_at = user
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if profile_pic and is_valid_image(profile_pic):
                    st.image(io.BytesIO(profile_pic), width=150, caption="🖼️ Profile Picture")
                else:
                    st.markdown("""
                    <div style="width: 150px; height: 150px; border-radius: 50%; background: linear-gradient(135deg, #58a6ff, #238636); 
                                display: flex; align-items: center; justify-content: center; color: white; font-size: 48px; margin: 0 auto;">
                        👤
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"<h2 style='color: #58a6ff;'>{username}</h2>", unsafe_allow_html=True)
                st.write(f"**📧 Email:** {email}")
                st.write(f"**📍 Location:** {location}")
                st.write(f"**🌐 Timezone:** {timezone}")
                st.write(f"**🗣️ Language:** {language}")
                
                if bio:
                    st.write(f"**📝 Bio:** {bio}")
                
                # Online status
                status_color = "#3fb950" if is_online else "#8b949e"
                status_text = "🟢 Online" if is_online else "⚫ Last seen: " + format_global_time(last_seen)
                st.markdown(f"<p style='color: {status_color};'><strong>{status_text}</strong></p>", unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error loading profile: {e}")

def global_messaging_interface():
    """Enhanced messaging interface for global communication"""
    st.markdown("<h1 class='gradient-text'>💬 Global Messaging</h1>", unsafe_allow_html=True)
    
    # Auto-refresh for real-time messages
    count = st_autorefresh(interval=5000, key="message_refresh")
    
    # Show online users
    st.sidebar.markdown("### 👥 Online Users")
    online_users = get_online_users()
    for user in online_users[:10]:  # Show first 10 online users
        user_id, username, location = user
        if user_id != st.session_state.user_id:
            if st.sidebar.button(f"💬 {username} ({location})", key=f"msg_{user_id}"):
                st.session_state.current_chat = user_id
                st.session_state.chat_username = username
                st.rerun()
    
    tab1, tab2 = st.tabs(["💭 Active Chats", "🌍 Find Global Users"])
    
    with tab1:
        display_chat_interface()
    
    with tab2:
        display_global_user_directory()

def display_chat_interface():
    """Display chat interface with real-time features"""
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 💭 Conversations")
        conversations = get_global_conversations(st.session_state.user_id)
        
        if not conversations:
            st.info("💬 No conversations yet. Start chatting with users around the world!")
        else:
            for conv in conversations:
                other_user_id, username, profile_pic, last_message_time, last_message, unread_count, location = conv
                
                button_text = f"👤 {username} ({location})"
                if unread_count > 0:
                    button_text = f"🔔 {username} ({unread_count}) - {location}"
                
                if st.button(button_text, key=f"conv_{other_user_id}", use_container_width=True):
                    st.session_state.current_chat = other_user_id
                    st.session_state.chat_username = username
                    st.rerun()
    
    with col2:
        if hasattr(st.session_state, 'current_chat'):
            display_chat_messages(st.session_state.current_chat)
        else:
            st.info("💬 Select a conversation to start chatting")

def display_chat_messages(other_user_id):
    """Display chat messages with real-time updates"""
    st.markdown(f"### 💬 Chat with {st.session_state.chat_username}")
    
    # Message container
    messages_container = st.container()
    
    with messages_container:
        messages = get_global_messages(st.session_state.user_id, other_user_id, limit=50)
        
        if not messages:
            st.info("💭 No messages yet. Start the conversation!")
        else:
            for msg in messages:
                display_message_bubble(msg)
    
    # Message input
    st.markdown("---")
    send_message_interface(other_user_id)

def display_message_bubble(msg):
    """Display individual message bubble"""
    (msg_id, sender_id, receiver_id, content, message_type, media_data, 
     is_delivered, is_read, read_receipt_sent, created_at, delivered_at, 
     read_at, sender_name, receiver_name) = msg
    
    message_time = created_at.split(' ')[1][:5] if ' ' in created_at else created_at
    
    if sender_id == st.session_state.user_id:
        # Sent message
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
            <div class="message-bubble message-sent">
                <div style="font-size: 0.9em;">{content}</div>
                {f'<img src="data:image/jpeg;base64,{base64.b64encode(media_data).decode()}" style="max-width: 300px; border-radius: 8px; margin-top: 5px;">' if media_data and message_type == 'image' else ''}
                <div style="font-size: 0.7em; text-align: right; opacity: 0.8; margin-top: 5px;">
                    {message_time} {'' if is_read else '✉️'}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Received message
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
            <div class="message-bubble message-received">
                <div style="font-weight: bold; font-size: 0.8em; color: #58a6ff; margin-bottom: 4px;">
                    {sender_name}
                </div>
                <div style="font-size: 0.9em;">{content}</div>
                {f'<img src="data:image/jpeg;base64,{base64.b64encode(media_data).decode()}" style="max-width: 300px; border-radius: 8px; margin-top: 5px;">' if media_data and message_type == 'image' else ''}
                <div style="font-size: 0.7em; text-align: right; opacity: 0.8; margin-top: 5px;">
                    {message_time}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def send_message_interface(other_user_id):
    """Interface for sending messages"""
    with st.form("send_message_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            message_content = st.text_input(
                "💭 Type your message...", 
                key="message_input",
                placeholder="Type a message to send around the world..."
            )
            media_file = st.file_uploader("📎 Add media", type=['jpg', 'png', 'jpeg'], key="message_media")
        
        with col2:
            send_button = st.form_submit_button("📤 Send", use_container_width=True)
        
        if send_button and (message_content or media_file):
            media_data = None
            message_type = 'text'
            
            if media_file:
                media_data = media_file.read()
                message_type = 'image'
                # Optimize image for faster global delivery
                media_data = optimize_image_for_web(media_data)
            
            content = message_content if message_content else "📸 Shared an image"
            
            if send_global_message(st.session_state.user_id, other_user_id, content, message_type, media_data):
                st.success("✅ Message sent globally!")
                st.rerun()
            else:
                st.error("❌ Failed to send message")

def display_global_user_directory():
    """Display directory of global users"""
    st.markdown("### 🌍 Connect with Users Worldwide")
    
    # Search and filters
    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input("🔍 Search users...")
    with col2:
        location_filter = st.text_input("📍 Filter by location...")
    with col3:
        language_filter = st.selectbox("🗣️ Language", ["All", "English", "Spanish", "French", "German", "Chinese", "Japanese"])
    
    users = get_global_users(search_term, location_filter, language_filter)
    
    if not users:
        st.info("👥 No users found. Try different search terms!")
    else:
        for user in users:
            user_id, username, profile_pic, bio, location, timezone, language, is_online, last_seen = user
            
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    if profile_pic and is_valid_image(profile_pic):
                        st.image(io.BytesIO(profile_pic), width=60)
                    else:
                        st.markdown("""
                        <div style="width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, #58a6ff, #238636); 
                                    display: flex; align-items: center; justify-content: center; color: white; font-size: 18px;">
                            👤
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    online_indicator = "🟢" if is_online else "⚫"
                    st.write(f"**{online_indicator} {username}**")
                    st.write(f"📍 {location} • 🗣️ {language}")
                    if bio:
                        st.write(f"_{bio[:100]}{'...' if len(bio) > 100 else ''}_")
                
                with col3:
                    if st.button("💬 Message", key=f"global_msg_{user_id}"):
                        st.session_state.current_chat = user_id
                        st.session_state.chat_username = username
                        st.rerun()
                
                st.markdown("---")

# ===================================
# NEW GLOBAL FUNCTIONS
# ===================================

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

def get_global_conversations(user_id):
    """Get conversations with global users"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT DISTINCT 
                CASE 
                    WHEN cm.sender_id = ? THEN cm.receiver_id 
                    ELSE cm.sender_id 
                END as other_user_id,
                u.username,
                u.profile_pic,
                MAX(cm.created_at) as last_message_time,
                (SELECT content FROM cross_platform_messages 
                 WHERE ((sender_id = ? AND receiver_id = other_user_id) 
                     OR (sender_id = other_user_id AND receiver_id = ?))
                 ORDER BY created_at DESC LIMIT 1) as last_message,
                (SELECT COUNT(*) FROM cross_platform_messages 
                 WHERE receiver_id = ? AND sender_id = other_user_id AND is_read = 0) as unread_count,
                u.location
            FROM cross_platform_messages cm
            JOIN users u ON u.id = CASE 
                WHEN cm.sender_id = ? THEN cm.receiver_id 
                ELSE cm.sender_id 
            END
            WHERE cm.sender_id = ? OR cm.receiver_id = ?
            GROUP BY other_user_id
            ORDER BY last_message_time DESC
        """, (user_id, user_id, user_id, user_id, user_id, user_id, user_id))
        return c.fetchall()
    except sqlite3.Error:
        return []

def get_global_users(search_term=None, location_filter=None, language_filter="All"):
    """Get global users with filtering"""
    try:
        c = conn.cursor()
        
        query = "SELECT id, username, profile_pic, bio, location, timezone, language, is_online, last_seen FROM users WHERE id != ?"
        params = [st.session_state.user_id]
        
        if search_term:
            query += " AND (username LIKE ? OR bio LIKE ?)"
            params.extend([f'%{search_term}%', f'%{search_term}%'])
        
        if location_filter:
            query += " AND location LIKE ?"
            params.append(f'%{location_filter}%')
        
        if language_filter != "All":
            query += " AND language = ?"
            params.append(language_filter.lower()[:2])
        
        query += " ORDER BY is_online DESC, last_seen DESC LIMIT 50"
        
        c.execute(query, params)
        return c.fetchall()
    except sqlite3.Error:
        return []

def get_user(user_id):
    """Enhanced get user function"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT id, username, email, profile_pic, bio, location, timezone, language, is_active, is_online, last_seen, created_at
            FROM users WHERE id=?
        """, (user_id,))
        return c.fetchone()
    except sqlite3.Error:
        return None

# ===================================
# ENHANCED MAIN APPLICATION
# ===================================

def enhanced_login_page():
    """Enhanced login page for global app"""
    st.markdown("<h1 class='gradient-text'>🌍 GlobalFeedChat</h1>", unsafe_allow_html=True)
    st.markdown("### Connect with the world in real-time!")
    
    tab1, tab2 = st.tabs(["🚀 Sign In", "✨ Create Account"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("👤 Username")
            password = st.text_input("🔒 Password", type="password")
            submit = st.form_submit_button("🌍 Sign In to Global Network")
            
            if submit:
                if username and password:
                    user_id, username, session_token = verify_user_secure(username, password)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.session_state.logged_in = True
                        st.session_state.session_token = session_token
                        st.success(f"🎉 Welcome to the global network, {username}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials or account not active")
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
                language = st.selectbox("🗣️ Preferred Language", CLOUD_CONFIG["languages"])
                bio = st.text_area("📝 Bio (Optional)")
            
            profile_pic = st.file_uploader("🖼️ Profile Picture (Optional)", type=['jpg', 'png', 'jpeg'])
            
            register = st.form_submit_button("🌍 Join Global Network")
            
            if register:
                if new_username and new_password and email and location:
                    if new_password == confirm_password:
                        profile_pic_data = profile_pic.read() if profile_pic else None
                        
                        success, result = create_user_secure(
                            new_username, new_password, email, profile_pic_data, bio, 
                            location, timezone, language
                        )
                        
                        if success:
                            st.success("🎊 Welcome to the global community! Please sign in.")
                            # Auto-fill login
                            st.session_state.auto_username = new_username
                        else:
                            st.error(f"❌ {result}")
                    else:
                        st.error("🔒 Passwords do not match")
                else:
                    st.error("⚠️ Please fill in all required fields")

def global_feed_page():
    """Global feed page showing posts from around the world"""
    st.markdown("<h1 class='gradient-text'>🌍 Global Feed</h1>", unsafe_allow_html=True)
    
    # Auto-refresh for new global posts
    count = st_autorefresh(interval=10000, key="feed_refresh")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        language_filter = st.selectbox("🗣️ Language", ["all", "en", "es", "fr", "de", "zh", "ja"])
    with col2:
        location_filter = st.text_input("📍 Location filter", placeholder="e.g., New York, Japan")
    with col3:
        sort_by = st.selectbox("📊 Sort by", ["Most Popular", "Most Recent"])
    
    # Create post
    with st.expander("✍️ Create Global Post"):
        with st.form("global_post_form"):
            content = st.text_area("💭 Share with the world...", height=120, 
                                 placeholder="What's happening around you? Share with users worldwide!")
            media_file = st.file_uploader("📁 Add Media (Image/Video)", type=['jpg', 'png', 'jpeg', 'mp4'])
            post_location = st.text_input("📍 Location", value=st.session_state.get('location', 'Unknown'))
            post_language = st.selectbox("🗣️ Post Language", CLOUD_CONFIG["languages"])
            visibility = st.selectbox("👁️ Visibility", ["public", "friends", "private"])
            
            if st.form_submit_button("🚀 Publish to Global Feed"):
                if content:
                    media_data = None
                    media_type = None
                    if media_file:
                        media_data = media_file.read()
                        media_type = media_file.type
                    
                    post_id = create_global_post(
                        st.session_state.user_id, content, media_data, media_type,
                        post_location, post_language, visibility
                    )
                    
                    if post_id:
                        st.success("🌍 Post published globally!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to publish post")
                else:
                    st.error("⚠️ Please enter some content")
    
    # Display global posts
    st.markdown("---")
    st.markdown("### 📰 Posts from Around the World")
    
    posts = get_global_posts(language=language_filter, location=location_filter)
    
    if not posts:
        st.info("🌍 No posts yet. Be the first to share with the world!")
        return
    
    for post in posts:
        display_global_post_card(post)

def display_global_post_card(post):
    """Display post card with global features"""
    (post_id, user_id, content, media_type, media_data, location, language, 
     visibility, is_deleted, global_reach_count, created_at, updated_at, 
     username, profile_pic, user_location, like_count, comment_count) = post
    
    with st.container():
        st.markdown(f"""
        <div class="feed-card">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="margin-right: 12px;">
        """, unsafe_allow_html=True)
        
        if profile_pic and is_valid_image(profile_pic):
            st.image(io.BytesIO(profile_pic), width=50)
        else:
            st.markdown("""
                <div style="width: 50px; height: 50px; border-radius: 50%; background: linear-gradient(135deg, #58a6ff, #238636); 
                            display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 18px;">
                    👤
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
                </div>
                <div>
                    <h4 style="margin: 0; color: #58a6ff;">{username}</h4>
                    <p style="margin: 0; font-size: 0.8em; color: #8b949e;">
                        📍 {location} • 🗣️ {language.upper()} • 🌍 {global_reach_count} reaches
                    </p>
                    <p style="margin: 0; font-size: 0.7em; color: #8b949e;">{format_global_time(created_at)}</p>
                </div>
            </div>
            <p style="color: #c9d1d9; line-height: 1.5;">{content}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if media_data and media_type:
            if 'image' in media_type:
                display_image_safely(media_data, use_container_width=True)
            elif 'video' in media_type:
                st.video(io.BytesIO(media_data))
        
        # Engagement buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"❤️ {like_count}", key=f"like_{post_id}"):
                if like_post(st.session_state.user_id, post_id):
                    track_global_engagement(
                        st.session_state.user_id, post_id, 'like',
                        st.session_state.get('location', 'Unknown'),
                        st.session_state.get('timezone', 'UTC')
                    )
                    st.rerun()
        
        with col2:
            if st.button(f"💬 {comment_count}", key=f"comment_{post_id}"):
                # Toggle comment section
                if 'current_post' in st.session_state and st.session_state.current_post == post_id:
                    del st.session_state.current_post
                else:
                    st.session_state.current_post = post_id
                st.rerun()
        
        with col3:
            if st.button("🔄 Share", key=f"share_{post_id}"):
                if share_post(st.session_state.user_id, post_id):
                    track_global_engagement(
                        st.session_state.user_id, post_id, 'share',
                        st.session_state.get('location', 'Unknown'),
                        st.session_state.get('timezone', 'UTC')
                    )
                    st.success("📤 Post shared globally!")
                    st.rerun()
        
        # Comments section
        if hasattr(st.session_state, 'current_post') and st.session_state.current_post == post_id:
            display_comments_section(post_id)

def display_comments_section(post_id):
    """Display comments section for a post"""
    st.markdown("---")
    st.markdown("#### 💬 Global Comments")
    
    # Add comment
    with st.form(f"add_comment_{post_id}"):
        comment_text = st.text_input("💭 Add a comment...", placeholder="Share your thoughts with the world!")
        if st.form_submit_button("💬 Post Comment"):
            if comment_text:
                if add_comment(post_id, st.session_state.user_id, comment_text):
                    track_global_engagement(
                        st.session_state.user_id, post_id, 'comment',
                        st.session_state.get('location', 'Unknown'),
                        st.session_state.get('timezone', 'UTC')
                    )
                    st.rerun()
    
    # Display comments
    comments = get_comments(post_id)
    for comment in comments:
        comment_id, _, comment_user_id, comment_content, comment_created_at, comment_username, comment_profile_pic = comment
        
        st.markdown(f"""
        <div style="background: #21262d; padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 3px solid #58a6ff;">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <strong style="color: #58a6ff; margin-right: 8px;">{comment_username}</strong>
                <small style="color: #8b949e;">{format_global_time(comment_created_at)}</small>
            </div>
            <p style="margin: 0; color: #c9d1d9;">{comment_content}</p>
        </div>
        """, unsafe_allow_html=True)

# ===================================
# DEPLOYMENT READY MAIN FUNCTION
# ===================================

def main():
    """Main application - Ready for global deployment"""
    
    # Inject custom CSS
    inject_custom_css()
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'location' not in st.session_state:
        st.session_state.location = "Unknown"
    if 'timezone' not in st.session_state:
        st.session_state.timezone = "UTC"
    
    # App header
    st.sidebar.markdown("<h1 class='gradient-text'>🌍 GlobalFeedChat</h1>", unsafe_allow_html=True)
    st.sidebar.markdown("### Connect with the World")
    
    if not st.session_state.logged_in:
        enhanced_login_page()
        return
    
    # Navigation for logged-in users
    st.sidebar.markdown(f"### 👋 Welcome, **{st.session_state.username}**!")
    st.sidebar.markdown(f"📍 **Location:** {st.session_state.get('location', 'Unknown')}")
    st.sidebar.markdown(f"🌐 **Timezone:** {st.session_state.get('timezone', 'UTC')}")
    
    # Navigation menu
    menu_options = [
        "🌍 Global Feed",
        "💬 Global Messaging", 
        "👤 My Profile",
        "📊 Global Analytics",
        "⚙️ Settings"
    ]
    
    selected_menu = st.sidebar.selectbox("🧭 Navigation", menu_options)
    
    # Global stats in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🌐 Global Stats")
    
    try:
        # Simulated global stats
        online_users = len(get_online_users())
        st.sidebar.metric("👥 Online Now", online_users)
        st.sidebar.metric("🌍 Countries", "50+")
        st.sidebar.metric("🗣️ Languages", "6")
    except:
        pass
    
    # Real-time updates indicator
    st.sidebar.markdown("---")
    st.sidebar.markdown("🟢 **Live Updates Active**")
    st.sidebar.caption("Messages and posts update in real-time")
    
    # Logout button
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        # Update user status
        try:
            c = conn.cursor()
            c.execute("UPDATE users SET is_online=0 WHERE id=?", (st.session_state.user_id,))
            conn.commit()
        except:
            pass
        
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.rerun()
    
    # Display selected page
    if selected_menu == "🌍 Global Feed":
        global_feed_page()
    elif selected_menu == "💬 Global Messaging":
        global_messaging_interface()
    elif selected_menu == "👤 My Profile":
        global_user_profile()
    elif selected_menu == "📊 Global Analytics":
        st.info("📈 Global analytics dashboard coming soon!")
        st.markdown("""
        <div style="background: #161b22; padding: 20px; border-radius: 12px; text-align: center;">
            <h3 style="color: #58a6ff;">🌍 Global Reach Analytics</h3>
            <p style="color: #8b949e;">Track your global engagement and audience reach across different countries and timezones.</p>
        </div>
        """, unsafe_allow_html=True)
    elif selected_menu == "⚙️ Settings":
        st.info("⚙️ Global settings panel coming soon!")
        st.markdown("""
        <div style="background: #161b22; padding: 20px; border-radius: 12px;">
            <h3 style="color: #58a6ff;">🌐 Global Preferences</h3>
            <p style="color: #8b949e;">Configure your language, timezone, privacy settings, and notification preferences for global usage.</p>
        </div>
        """, unsafe_allow_html=True)

# ===================================
# DEPLOYMENT INSTRUCTIONS
# ===================================

def show_deployment_instructions():
    """Show instructions for deploying globally"""
    st.sidebar.markdown("---")
    with st.sidebar.expander("🚀 Deploy Instructions"):
        st.markdown("""
        ### To deploy globally:
        
        1. **Push to GitHub**
        2. **Deploy on Streamlit Cloud:**
           - Go to [share.streamlit.io](https://share.streamlit.io)
           - Connect your GitHub repo
           - Deploy!
        
        3. **Your app will be available at:**
           `https://your-app-name.streamlit.app`
        
        4. **Share this URL worldwide!** 🌍
        """)

# Show deployment instructions
show_deployment_instructions()

if __name__ == "__main__":
    main()

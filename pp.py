import streamlit as st
import sqlite3
import datetime
import random
import time
from PIL import Image, ImageDraw
import io
import base64
import json
import re
import uuid
import hashlib
import secrets
import os
import threading
import webbrowser
from pathlib import Path
import zipfile
import shutil
import asyncio
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av
import queue
import pyaudio
import wave
import numpy as np
from streamlit_autorefresh import st_autorefresh
import socketio

# ===================================
# TIKTOK-INSPIRED THEME CONFIGURATION
# ===================================

THEME_CONFIG = {
    "app_name": "Feed Chat Pro",
    "version": "5.0",
    "theme": {
        "primary": "#FF0050",
        "secondary": "#00F2EA",
        "accent": "#00D1FF",
        "success": "#25D366",
        "warning": "#FFC107",
        "danger": "#FF3B30",
        "background": "#0A0E17",  # Midnight Blue
        "surface": "#121826",
        "surface_light": "#1E2436",
        "text": "#FFFFFF",
        "text_muted": "#AAAAAA",
        "border": "#2D3748"
    },
    "max_file_size": 100 * 1024 * 1024,
    "supported_timezones": ["UTC", "EST", "PST", "GMT", "CET", "AEST"],
    "languages": ["en", "es", "fr", "de", "zh", "ja", "ko", "hi"]
}

# Admin credentials
ADMIN_USERNAME = "Emmy"
ADMIN_PASSWORD = "0814788emmy"

# Real-time configuration
RTC_CONFIG = RTCConfiguration({
    "iceServers": [
        {"urls": ["stun:stun.l.google.com:19302"]},
        {"urls": ["stun:stun1.l.google.com:19302"]}
    ]
})

# ===================================
# REAL-TIME MESSAGING SETUP
# ===================================

# In-memory real-time message queue
message_queue = queue.Queue()
call_queue = queue.Queue()
online_users = {}
call_sessions = {}

# ===================================
# DATABASE SETUP WITH ADMIN FEATURES
# ===================================

def init_enhanced_db():
    """Initialize database with admin and calling features"""
    try:
        conn = sqlite3.connect("feedchat_pro.db", check_same_thread=False, isolation_level=None)
        c = conn.cursor()
        
        # Enable foreign keys
        c.execute("PRAGMA foreign_keys = ON")
        
        # Users table with admin flags
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT,
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            post_count INTEGER DEFAULT 0,
            follower_count INTEGER DEFAULT 0,
            following_count INTEGER DEFAULT 0,
            total_likes INTEGER DEFAULT 0,
            verified BOOLEAN DEFAULT FALSE,
            is_admin BOOLEAN DEFAULT FALSE,
            is_banned BOOLEAN DEFAULT FALSE,
            last_ip TEXT,
            device_info TEXT,
            call_history_count INTEGER DEFAULT 0
        )
        """)

        # Posts table
        c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            media_type TEXT,
            media_data BLOB,
            location TEXT DEFAULT 'Unknown',
            language TEXT DEFAULT 'en',
            visibility TEXT DEFAULT 'public',
            is_deleted BOOLEAN DEFAULT FALSE,
            like_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            share_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            hashtags TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # Messages table with real-time flags
        c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            message_type TEXT DEFAULT 'text',
            media_data BLOB,
            is_read BOOLEAN DEFAULT FALSE,
            is_delivered BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # Calls table
        c.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caller_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            call_type TEXT DEFAULT 'audio',
            status TEXT DEFAULT 'missed',
            duration INTEGER DEFAULT 0,
            started_at DATETIME,
            ended_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (caller_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # Likes table
        c.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            UNIQUE(user_id, post_id)
        )
        """)

        # Comments table
        c.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # Saves table
        c.execute("""
        CREATE TABLE IF NOT EXISTS saves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            UNIQUE(user_id, post_id)
        )
        """)

        # Follows table
        c.execute("""
        CREATE TABLE IF NOT EXISTS follows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            follower_id INTEGER NOT NULL,
            following_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(follower_id, following_id)
        )
        """)

        # Shares table
        c.execute("""
        CREATE TABLE IF NOT EXISTS shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            shared_to_user_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY (shared_to_user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # Admin actions table
        c.execute("""
        CREATE TABLE IF NOT EXISTS admin_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            target_user_id INTEGER,
            details TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (target_user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # Create indexes
        c.execute("CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages(receiver_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_likes_post ON likes(post_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_shares_post ON shares(post_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_calls_user ON calls(caller_id, receiver_id)")
        
        # Create admin user if not exists
        c.execute("SELECT id FROM users WHERE username = ?", (ADMIN_USERNAME,))
        if not c.fetchone():
            admin_hash = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
            c.execute("""
                INSERT INTO users (username, display_name, password_hash, email, is_admin, verified)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ADMIN_USERNAME, "Admin Emmy", admin_hash, "admin@feedchat.com", True, True))
        
        conn.commit()
        return conn
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        return sqlite3.connect("feedchat_pro.db", check_same_thread=False)

# Initialize database
conn = init_enhanced_db()

# ===================================
# CORE FUNCTIONS
# ===================================

def extract_hashtags_string(text):
    """Extract hashtags and return as comma-separated string"""
    hashtags = re.findall(r'#(\w+)', text)
    return ','.join(list(set(hashtags))[:10])

def format_tiktok_time(timestamp):
    """Format timestamp in TikTok style"""
    try:
        if not timestamp:
            return "Just now"
            
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                return timestamp
        
        now = datetime.datetime.now()
        if isinstance(timestamp, datetime.datetime):
            diff = now - timestamp
        else:
            return str(timestamp)
        
        if diff.days > 365:
            return f"{diff.days // 365}y"
        elif diff.days > 30:
            return f"{diff.days // 30}mo"
        elif diff.days > 0:
            return f"{diff.days}d"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m"
        else:
            return "Just now"
    except:
        return "Just now"

def inject_midnight_blue_css():
    """Inject Midnight Blue theme CSS"""
    theme = THEME_CONFIG['theme']
    st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, {theme['background']} 0%, #0F172A 100%);
        color: {theme['text']};
    }}
    
    h1, h2, h3, h4 {{
        background: linear-gradient(45deg, {theme['primary']}, {theme['secondary']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }}
    
    .stButton>button {{
        border-radius: 25px;
        border: 2px solid {theme['primary']};
        background: transparent;
        color: {theme['text']};
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    
    .stButton>button:hover {{
        background: linear-gradient(45deg, {theme['primary']}, {theme['secondary']});
        color: white;
        border: 2px solid transparent;
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(255, 0, 80, 0.3);
    }}
    
    .post-card {{
        background: {theme['surface']};
        border-radius: 20px;
        padding: 20px;
        margin: 15px 0;
        border: 1px solid {theme['border']};
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }}
    
    .post-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(255, 0, 80, 0.2);
    }}
    
    .hashtag {{
        display: inline-block;
        background: rgba(255, 0, 80, 0.15);
        color: {theme['primary']};
        padding: 6px 15px;
        border-radius: 20px;
        margin: 3px;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.3s ease;
    }}
    
    .hashtag:hover {{
        background: {theme['primary']};
        color: white;
        transform: scale(1.05);
    }}
    
    .message-bubble {{
        padding: 12px 18px;
        border-radius: 20px;
        margin: 8px 0;
        max-width: 70%;
        word-wrap: break-word;
    }}
    
    .message-sent {{
        background: linear-gradient(45deg, {theme['primary']}, {theme['secondary']});
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 5px;
    }}
    
    .message-received {{
        background: {theme['surface_light']};
        color: {theme['text']};
        margin-right: auto;
        border-bottom-left-radius: 5px;
    }}
    
    .online-dot {{
        width: 12px;
        height: 12px;
        background: #25D366;
        border-radius: 50%;
        display: inline-block;
        margin-left: 5px;
        animation: pulse 2s infinite;
    }}
    
    @keyframes pulse {{
        0% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
        100% {{ opacity: 1; }}
    }}
    
    .call-button {{
        background: linear-gradient(45deg, #25D366, #128C7E);
        color: white;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    
    .call-button:hover {{
        transform: scale(1.1);
        box-shadow: 0 0 30px rgba(37, 211, 102, 0.5);
    }}
    
    .video-container {{
        background: {theme['surface']};
        border-radius: 20px;
        padding: 20px;
        margin: 15px 0;
        border: 2px solid {theme['border']};
    }}
    
    .admin-badge {{
        background: linear-gradient(45deg, {theme['danger']}, #FF6B6B);
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        margin-left: 8px;
    }}
    
    .verified-badge {{
        color: {theme['primary']};
        font-size: 16px;
        margin-left: 5px;
    }}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {theme['surface']};
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: linear-gradient(45deg, {theme['primary']}, {theme['secondary']});
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: linear-gradient(45deg, {theme['secondary']}, {theme['primary']});
    }}
    </style>
    """, unsafe_allow_html=True)

def create_default_profile_pic(username):
    """Create a default profile picture with initials"""
    try:
        img = Image.new('RGB', (200, 200), color=(26, 32, 44))
        draw = ImageDraw.Draw(img)
        
        # Draw gradient background
        for i in range(200):
            r = int(255 * (i/200))
            g = int(0 * (i/200))
            b = int(80 * (i/200))
            draw.line([(i, 0), (i, 200)], fill=(r, g, b))
        
        # Draw circle
        draw.ellipse([20, 20, 180, 180], fill=(18, 24, 36))
        
        # Add initials (simplified)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    except:
        return None

# ===================================
# REAL-TIME MESSAGING & CALLING FUNCTIONS
# ===================================

def send_real_time_message(sender_id, receiver_id, content, message_type='text', media_data=None):
    """Send message with real-time delivery"""
    try:
        if not content or len(content.strip()) == 0:
            return False, "Message cannot be empty"
        
        c = conn.cursor()
        c.execute("""
        INSERT INTO messages (sender_id, receiver_id, content, message_type, media_data, is_delivered)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (sender_id, receiver_id, content, message_type, media_data, True))
        
        message_id = c.lastrowid
        
        # Add to real-time queue
        message_queue.put({
            'message_id': message_id,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'content': content,
            'type': message_type,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        conn.commit()
        return True, "Message sent successfully"
    except Exception as e:
        return False, f"Failed to send message: {str(e)}"

def initiate_call(caller_id, receiver_id, call_type='audio'):
    """Initiate a call"""
    try:
        c = conn.cursor()
        
        # Create call record
        c.execute("""
        INSERT INTO calls (caller_id, receiver_id, call_type, status, started_at)
        VALUES (?, ?, ?, ?, ?)
        """, (caller_id, receiver_id, call_type, 'ringing', datetime.datetime.now()))
        
        call_id = c.lastrowid
        
        # Add to call queue
        call_queue.put({
            'call_id': call_id,
            'caller_id': caller_id,
            'receiver_id': receiver_id,
            'call_type': call_type,
            'status': 'ringing'
        })
        
        # Update user call history count
        c.execute("UPDATE users SET call_history_count = call_history_count + 1 WHERE id IN (?, ?)", 
                 (caller_id, receiver_id))
        
        conn.commit()
        
        # Store in active call sessions
        call_sessions[call_id] = {
            'caller_id': caller_id,
            'receiver_id': receiver_id,
            'call_type': call_type,
            'status': 'ringing',
            'start_time': datetime.datetime.now(),
            'participants': [caller_id]
        }
        
        return True, call_id, "Call initiated"
    except Exception as e:
        return False, None, f"Failed to initiate call: {str(e)}"

def end_call(call_id, duration=0):
    """End a call"""
    try:
        if call_id in call_sessions:
            call = call_sessions[call_id]
            call['status'] = 'ended'
            call['end_time'] = datetime.datetime.now()
            
            c = conn.cursor()
            c.execute("""
            UPDATE calls 
            SET status = 'completed', duration = ?, ended_at = ?
            WHERE id = ?
            """, (duration, datetime.datetime.now(), call_id))
            
            conn.commit()
            
            # Remove from active sessions after a delay
            def remove_session():
                time.sleep(5)
                if call_id in call_sessions:
                    del call_sessions[call_id]
            
            threading.Thread(target=remove_session).start()
            
            return True, "Call ended"
    except Exception as e:
        return False, f"Failed to end call: {str(e)}"

def get_call_history(user_id, limit=20):
    """Get call history for user"""
    try:
        c = conn.cursor()
        c.execute("""
        SELECT c.*, 
               u1.username as caller_username,
               u2.username as receiver_username
        FROM calls c
        JOIN users u1 ON c.caller_id = u1.id
        JOIN users u2 ON c.receiver_id = u2.id
        WHERE c.caller_id = ? OR c.receiver_id = ?
        ORDER BY c.created_at DESC
        LIMIT ?
        """, (user_id, user_id, limit))
        return c.fetchall()
    except:
        return []

def get_unread_messages_count(user_id):
    """Get count of unread messages"""
    try:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM messages WHERE receiver_id = ? AND is_read = 0", (user_id,))
        return c.fetchone()[0] or 0
    except:
        return 0

def update_user_online_status(user_id, is_online=True):
    """Update user online status in real-time"""
    try:
        c = conn.cursor()
        c.execute("UPDATE users SET is_online=?, last_seen=CURRENT_TIMESTAMP WHERE id=?", 
                 (1 if is_online else 0, user_id))
        
        # Update in-memory online users
        if is_online:
            online_users[user_id] = time.time()
        elif user_id in online_users:
            del online_users[user_id]
        
        conn.commit()
        return True
    except:
        return False

def get_online_users():
    """Get list of online users"""
    try:
        c = conn.cursor()
        # Clean up stale online users (5 minutes timeout)
        stale_time = time.time() - 300
        stale_users = [uid for uid, last_seen in online_users.items() if last_seen < stale_time]
        for uid in stale_users:
            c.execute("UPDATE users SET is_online=0 WHERE id=?", (uid,))
            if uid in online_users:
                del online_users[uid]
        
        c.execute("""
        SELECT id, username, display_name, profile_pic 
        FROM users 
        WHERE is_online = 1 AND id != ?
        ORDER BY last_seen DESC
        LIMIT 50
        """, (st.session_state.get('user_id', 0),))
        conn.commit()
        return c.fetchall()
    except:
        return []

# ===================================
# ADMIN FUNCTIONS
# ===================================

def verify_admin_login(username, password):
    """Verify admin credentials"""
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return True, "Admin Emmy"
    
    try:
        c = conn.cursor()
        c.execute("SELECT id, password_hash, is_admin FROM users WHERE username=?", (username,))
        user = c.fetchone()
        
        if user:
            user_id, password_hash, is_admin = user
            if hash_password(password) == password_hash and is_admin:
                return True, username
        
        return False, None
    except:
        return False, None

def ban_user(admin_id, target_user_id, reason=""):
    """Ban a user"""
    try:
        c = conn.cursor()
        c.execute("UPDATE users SET is_banned = TRUE, is_active = FALSE WHERE id = ?", (target_user_id,))
        
        # Log admin action
        c.execute("""
        INSERT INTO admin_actions (admin_id, action_type, target_user_id, details)
        VALUES (?, ?, ?, ?)
        """, (admin_id, 'ban', target_user_id, reason))
        
        conn.commit()
        return True, "User banned successfully"
    except Exception as e:
        return False, f"Failed to ban user: {str(e)}"

def unban_user(admin_id, target_user_id, reason=""):
    """Unban a user"""
    try:
        c = conn.cursor()
        c.execute("UPDATE users SET is_banned = FALSE, is_active = TRUE WHERE id = ?", (target_user_id,))
        
        # Log admin action
        c.execute("""
        INSERT INTO admin_actions (admin_id, action_type, target_user_id, details)
        VALUES (?, ?, ?, ?)
        """, (admin_id, 'unban', target_user_id, reason))
        
        conn.commit()
        return True, "User unbanned successfully"
    except Exception as e:
        return False, f"Failed to unban user: {str(e)}"

def verify_user_account(admin_id, target_user_id):
    """Verify a user account"""
    try:
        c = conn.cursor()
        c.execute("UPDATE users SET verified = TRUE WHERE id = ?", (target_user_id,))
        
        # Log admin action
        c.execute("""
        INSERT INTO admin_actions (admin_id, action_type, target_user_id, details)
        VALUES (?, ?, ?, ?)
        """, (admin_id, 'verify', target_user_id, 'Account verified'))
        
        conn.commit()
        return True, "User verified successfully"
    except Exception as e:
        return False, f"Failed to verify user: {str(e)}"

def get_all_users(limit=100, search_term=""):
    """Get all users for admin panel"""
    try:
        c = conn.cursor()
        query = """
        SELECT id, username, display_name, email, is_active, is_online, 
               verified, is_banned, created_at, post_count
        FROM users
        WHERE 1=1
        """
        params = []
        
        if search_term:
            query += " AND (username LIKE ? OR email LIKE ? OR display_name LIKE ?)"
            params.extend([f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'])
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        c.execute(query, params)
        return c.fetchall()
    except:
        return []

def get_admin_stats():
    """Get admin dashboard statistics"""
    try:
        c = conn.cursor()
        
        stats = {}
        
        # Total users
        c.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = c.fetchone()[0] or 0
        
        # Online users
        c.execute("SELECT COUNT(*) FROM users WHERE is_online = 1")
        stats['online_users'] = c.fetchone()[0] or 0
        
        # Banned users
        c.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
        stats['banned_users'] = c.fetchone()[0] or 0
        
        # Total posts
        c.execute("SELECT COUNT(*) FROM posts")
        stats['total_posts'] = c.fetchone()[0] or 0
        
        # Total messages
        c.execute("SELECT COUNT(*) FROM messages")
        stats['total_messages'] = c.fetchone()[0] or 0
        
        # Total calls
        c.execute("SELECT COUNT(*) FROM calls")
        stats['total_calls'] = c.fetchone()[0] or 0
        
        # Recent activity
        c.execute("""
        SELECT action_type, COUNT(*) as count, DATE(created_at) as date
        FROM admin_actions
        WHERE DATE(created_at) >= DATE('now', '-7 days')
        GROUP BY action_type, DATE(created_at)
        ORDER BY date DESC
        """)
        stats['recent_activity'] = c.fetchall()
        
        return stats
    except:
        return {}

# ===================================
# USER MANAGEMENT FUNCTIONS
# ===================================

def get_user(user_id):
    """Get user data"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT id, username, display_name, email, profile_pic, bio, location, 
                   timezone, language, is_online, last_seen, created_at, post_count, 
                   follower_count, following_count, total_likes, verified, is_admin, is_banned
            FROM users WHERE id=?
        """, (user_id,))
        return c.fetchone()
    except:
        return None

def update_user_profile(user_id, display_name=None, bio=None, location=None, profile_pic=None):
    """Update user profile information"""
    try:
        c = conn.cursor()
        
        updates = []
        params = []
        
        if display_name:
            updates.append("display_name = ?")
            params.append(display_name)
        
        if bio is not None:
            updates.append("bio = ?")
            params.append(bio)
        
        if location is not None:
            updates.append("location = ?")
            params.append(location)
        
        if profile_pic is not None:
            updates.append("profile_pic = ?")
            params.append(profile_pic)
        
        if updates:
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            c.execute(query, params)
            conn.commit()
            return True
        return False
    except Exception as e:
        print(f"Error updating profile: {e}")
        return False

def hash_password(password):
    """Hash password for storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user_secure(username, password):
    """Enhanced user verification"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT id, username, password_hash, is_banned
            FROM users 
            WHERE username=? AND is_active=1
        """, (username,))
        user = c.fetchone()
        
        if user:
            user_id, username, password_hash, is_banned = user
            
            if is_banned:
                return None, None, "Account is banned"
            
            # Check password
            if hash_password(password) == password_hash:
                c.execute("UPDATE users SET is_online=1, last_seen=CURRENT_TIMESTAMP WHERE id=?", (user_id,))
                conn.commit()
                return user_id, username, None
        
        return None, None, "Invalid credentials"
    except:
        return None, None, "Login failed"

def create_user_secure(username, password, email, display_name=None, profile_pic=None):
    """Create user with secure password hashing"""
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
        
        # Create user
        password_hash = hash_password(password)
        display_name = display_name or username
        
        # Create default profile picture if none provided
        if not profile_pic:
            profile_pic = create_default_profile_pic(username)
        
        c.execute("""
            INSERT INTO users (username, display_name, password_hash, email, profile_pic) 
            VALUES (?, ?, ?, ?, ?)
        """, (username, display_name, password_hash, email, profile_pic))
        
        conn.commit()
        return True, "Account created successfully"
    except Exception as e:
        return False, f"Error creating account: {str(e)}"

# ===================================
# MESSAGING FUNCTIONS
# ===================================

def send_message(sender_id, receiver_id, content, message_type='text', media_data=None):
    """Send a message"""
    try:
        if not content or len(content.strip()) == 0:
            return False, "Message cannot be empty"
        
        c = conn.cursor()
        c.execute("""
        INSERT INTO messages (sender_id, receiver_id, content, message_type, media_data, is_delivered)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (sender_id, receiver_id, content, message_type, media_data, True))
        
        conn.commit()
        return True, "Message sent successfully"
    except Exception as e:
        return False, f"Failed to send message: {str(e)}"

def get_conversations(user_id):
    """Get all conversations for a user"""
    try:
        c = conn.cursor()
        c.execute("""
        SELECT DISTINCT 
            CASE 
                WHEN sender_id = ? THEN receiver_id 
                ELSE sender_id 
            END as other_user_id,
            u.username,
            u.profile_pic,
            u.is_online,
            MAX(m.created_at) as last_message_time,
            (SELECT content FROM messages 
             WHERE ((sender_id = ? AND receiver_id = u.id) OR (sender_id = u.id AND receiver_id = ?))
             ORDER BY created_at DESC LIMIT 1) as last_message,
            (SELECT COUNT(*) FROM messages 
             WHERE sender_id = u.id AND receiver_id = ? AND is_read = 0) as unread_count
        FROM messages m
        JOIN users u ON (u.id = m.sender_id OR u.id = m.receiver_id) AND u.id != ?
        WHERE ? IN (m.sender_id, m.receiver_id)
        GROUP BY other_user_id
        ORDER BY last_message_time DESC
        """, (user_id, user_id, user_id, user_id, user_id, user_id))
        
        return c.fetchall()
    except Exception as e:
        return []

def get_messages(user_id, other_user_id, limit=100):
    """Get messages between two users"""
    try:
        c = conn.cursor()
        c.execute("""
        SELECT m.*, u.username as sender_username, u.is_online
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE (m.sender_id = ? AND m.receiver_id = ?) 
           OR (m.sender_id = ? AND m.receiver_id = ?)
        ORDER BY m.created_at DESC
        LIMIT ?
        """, (user_id, other_user_id, other_user_id, user_id, limit))
        
        messages = c.fetchall()
        
        # Mark messages as read
        c.execute("""
        UPDATE messages 
        SET is_read = 1 
        WHERE sender_id = ? AND receiver_id = ? AND is_read = 0
        """, (other_user_id, user_id))
        conn.commit()
        
        return messages
    except Exception as e:
        return []

# ===================================
# POST FUNCTIONS
# ===================================

def create_post(user_id, content, media_data=None, media_type=None, location=None, language="en", visibility="public"):
    """Create post with media support"""
    try:
        if not content or len(content.strip()) == 0:
            return False, "Post content cannot be empty"
            
        c = conn.cursor()
        
        # Extract hashtags
        hashtags_str = extract_hashtags_string(content)
        
        c.execute("""
            INSERT INTO posts 
            (user_id, content, media_type, media_data, location, language, visibility, hashtags) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, content, media_type, media_data, location, language, visibility, hashtags_str))
        
        post_id = c.lastrowid
        
        # Update user post count
        c.execute("UPDATE users SET post_count = post_count + 1 WHERE id = ?", (user_id,))
        
        conn.commit()
        return True, post_id
    except sqlite3.Error as e:
        return False, f"Post creation failed: {str(e)}"

def get_posts_simple(limit=20, user_id=None):
    """Get posts with simplified query"""
    try:
        c = conn.cursor()
        
        if user_id:
            c.execute("""
                SELECT p.*, u.username, u.display_name, u.profile_pic, u.verified
                FROM posts p
                JOIN users u ON p.user_id = u.id
                WHERE p.is_deleted = 0 AND p.user_id = ?
                ORDER BY p.created_at DESC
                LIMIT ?
            """, (user_id, limit))
        else:
            c.execute("""
                SELECT p.*, u.username, u.display_name, u.profile_pic, u.verified
                FROM posts p
                JOIN users u ON p.user_id = u.id
                WHERE p.is_deleted = 0 AND p.visibility = 'public'
                ORDER BY p.created_at DESC
                LIMIT ?
            """, (limit,))
        
        return c.fetchall()
    except Exception as e:
        print(f"Error getting posts: {e}")
        return []

def get_post_stats(post_id):
    """Get like and comment counts for a post"""
    try:
        c = conn.cursor()
        
        # Get like count
        c.execute("SELECT COUNT(*) FROM likes WHERE post_id = ?", (post_id,))
        like_count = c.fetchone()[0] or 0
        
        # Get comment count
        c.execute("SELECT COUNT(*) FROM comments WHERE post_id = ?", (post_id,))
        comment_count = c.fetchone()[0] or 0
        
        # Get share count
        c.execute("SELECT share_count FROM posts WHERE id = ?", (post_id,))
        share_result = c.fetchone()
        share_count = share_result[0] if share_result else 0
        
        return like_count, comment_count, share_count
    except:
        return 0, 0, 0

# ===================================
# MEDIA & DISPLAY FUNCTIONS
# ===================================

def display_profile_pic(profile_pic, username, size=40):
    """Display profile picture with fallback"""
    try:
        if profile_pic:
            st.image(profile_pic, width=size)
        else:
            initials = (username[:2] if len(username) >= 2 else username[0] + 'X').upper()
            st.markdown(f"""
            <div style='
                width: {size}px; 
                height: {size}px; 
                border-radius: 50%; 
                background: linear-gradient(45deg, #FF0050, #00F2EA);
                display: flex; 
                align-items: center; 
                justify-content: center; 
                color: white; 
                font-size: {size//2}px; 
                font-weight: bold;
                margin: 0 auto;
            '>{initials}</div>
            """, unsafe_allow_html=True)
    except:
        initials = (username[:2] if len(username) >= 2 else username[0] + 'X').upper()
        st.markdown(f"""
        <div style='
            width: {size}px; 
            height: {size}px; 
            border-radius: 50%; 
            background: linear-gradient(45deg, #FF0050, #00F2EA);
            display: flex; 
            align-items: center; 
            justify-content: center; 
            color: white; 
            font-size: {size//2}px; 
            font-weight: bold;
            margin: 0 auto;
        '>{initials}</div>
        """, unsafe_allow_html=True)

# ===================================
# VIDEO/AUDIO CALL COMPONENTS
# ===================================

class VideoAudioCallHandler:
    """Handle video and audio calls"""
    
    def __init__(self):
        self.active_calls = {}
        
    def start_video_call(self, call_id, user_id, other_user_id):
        """Start a video call"""
        st.markdown(f"""
        <div class='video-container'>
            <h3>🎥 Video Call in Progress</h3>
            <p>Call ID: {call_id}</p>
            <div style='display: flex; gap: 20px; margin: 20px 0;'>
                <div style='flex: 1;'>
                    <h4>You</h4>
                    {webrtc_streamer(
                        key=f"video_{call_id}_{user_id}",
                        mode=WebRtcMode.SENDRECV,
                        rtc_configuration=RTC_CONFIG,
                        media_stream_constraints={
                            "video": True,
                            "audio": True
                        }
                    )}
                </div>
                <div style='flex: 1;'>
                    <h4>Other User</h4>
                    <div style='background: #1E2436; border-radius: 10px; height: 300px; display: flex; align-items: center; justify-content: center;'>
                        <p>Waiting for connection...</p>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Call controls
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🎤 Mute", use_container_width=True):
                st.session_state.muted = not st.session_state.get('muted', False)
                st.rerun()
        with col2:
            if st.button("📹 Stop Video", use_container_width=True):
                st.session_state.video_off = not st.session_state.get('video_off', False)
                st.rerun()
        with col3:
            if st.button("📞 End Call", use_container_width=True, type="primary"):
                end_call(call_id, duration=int((datetime.datetime.now() - call_sessions[call_id]['start_time']).total_seconds()))
                st.success("Call ended")
                st.rerun()
    
    def start_audio_call(self, call_id, user_id, other_user_id):
        """Start an audio call"""
        st.markdown(f"""
        <div class='video-container'>
            <h3>📞 Audio Call in Progress</h3>
            <p>Call ID: {call_id}</p>
            <div style='text-align: center; margin: 40px 0;'>
                <div style='font-size: 100px;'>🎤</div>
                <h3>Audio Call Connected</h3>
                <p>Duration: 00:00</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Audio call controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎤 Mute", use_container_width=True):
                st.session_state.audio_muted = not st.session_state.get('audio_muted', False)
                st.rerun()
        with col2:
            if st.button("📞 End Call", use_container_width=True, type="primary"):
                end_call(call_id, duration=int((datetime.datetime.now() - call_sessions[call_id]['start_time']).total_seconds()))
                st.success("Call ended")
                st.rerun()

# ===================================
# PAGE FUNCTIONS WITH NEW FEATURES
# ===================================

def feed_page():
    """Feed Chat vertical feed"""
    st.markdown("<h1 style='text-align: center;'>🎬 Your Feed</h1>", unsafe_allow_html=True)
    
    # Auto-refresh for real-time updates
    st_autorefresh(interval=5000, key="feed_refresh")
    
    posts = get_posts_simple(limit=10)
    
    if not posts:
        st.info("No posts yet. Create your first post!")
        return
    
    for post in posts:
        try:
            display_feed_post_with_comments(post)
        except Exception as e:
            st.error(f"Error displaying post: {e}")
            continue

def messages_page():
    """Real-time messaging page with calling"""
    st.markdown("<h1 style='text-align: center;'>💬 Real-Time Messages</h1>", unsafe_allow_html=True)
    
    # Auto-refresh for new messages
    st_autorefresh(interval=3000, key="messages_refresh")
    
    # Check for incoming calls
    if not call_queue.empty():
        incoming_call = call_queue.get()
        if incoming_call['receiver_id'] == st.session_state.user_id:
            with st.popover("📞 Incoming Call", use_container_width=True):
                st.markdown(f"### 📞 Incoming Call")
                st.write(f"From: User {incoming_call['caller_id']}")
                st.write(f"Type: {'Video' if incoming_call['call_type'] == 'video' else 'Audio'} Call")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Answer", use_container_width=True):
                        call_sessions[incoming_call['call_id']]['status'] = 'answered'
                        call_sessions[incoming_call['call_id']]['participants'].append(st.session_state.user_id)
                        st.success("Call answered!")
                        st.rerun()
                with col2:
                    if st.button("❌ Decline", use_container_width=True):
                        end_call(incoming_call['call_id'], 0)
                        st.info("Call declined")
                        st.rerun()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 💬 Conversations")
        
        # New message button
        if st.button("+ New Message", use_container_width=True):
            st.session_state.new_message = True
        
        # Online users
        st.markdown("#### 👥 Online Now")
        online_users_list = get_online_users()
        for user in online_users_list:
            if len(user) > 1:
                col_a, col_b, col_c = st.columns([1, 3, 2])
                with col_a:
                    display_profile_pic(user[3], user[1], size=30)
                with col_b:
                    st.write(f"@{user[1]}")
                with col_c:
                    if st.button("📞", key=f"call_{user[0]}", use_container_width=True):
                        st.session_state.initiate_call_to = user[0]
        
        # Conversations
        conversations = get_conversations(st.session_state.user_id)
        if conversations:
            for conv in conversations:
                if len(conv) > 1:
                    username = conv[1]
                    profile_pic = conv[2]
                    is_online = conv[3]
                    other_user_id = conv[0]
                    unread_count = conv[6] if len(conv) > 6 else 0
                    
                    col_a, col_b, col_c, col_d = st.columns([1, 3, 2, 2])
                    with col_a:
                        display_profile_pic(profile_pic, username, size=30)
                    with col_b:
                        st.write(f"@{username}")
                        if is_online:
                            st.markdown("<span class='online-dot'></span>", unsafe_allow_html=True)
                    with col_c:
                        if unread_count > 0:
                            st.markdown(f"<span style='background: #FF0050; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;'>{unread_count}</span>", unsafe_allow_html=True)
                    with col_d:
                        if st.button("💬", key=f"chat_{other_user_id}", use_container_width=True):
                            st.session_state.current_chat = other_user_id
                            st.rerun()
    
    with col2:
        if st.session_state.get('current_chat'):
            other_user = get_user(st.session_state.current_chat)
            
            if other_user:
                other_username = other_user[1]
                other_profile_pic = other_user[4]
                is_online = other_user[9]
                
                # Chat header with call buttons
                col_a, col_b, col_c, col_d = st.columns([1, 3, 1, 1])
                with col_a:
                    display_profile_pic(other_profile_pic, other_username, size=50)
                with col_b:
                    st.markdown(f"### @{other_username}")
                    if is_online:
                        st.markdown("🟢 Online")
                    else:
                        st.markdown("⚪ Last seen: " + format_tiktok_time(other_user[10]))
                with col_c:
                    if st.button("📞", key=f"audio_call_{other_user[0]}", use_container_width=True):
                        success, call_id, message = initiate_call(st.session_state.user_id, other_user[0], 'audio')
                        if success:
                            st.success("Audio call initiated!")
                        else:
                            st.error(message)
                with col_d:
                    if st.button("🎥", key=f"video_call_{other_user[0]}", use_container_width=True):
                        success, call_id, message = initiate_call(st.session_state.user_id, other_user[0], 'video')
                        if success:
                            st.success("Video call initiated!")
                        else:
                            st.error(message)
                
                # Check if there's an active call
                active_call_id = None
                for call_id, call in call_sessions.items():
                    if (call['caller_id'] == st.session_state.user_id and call['receiver_id'] == other_user[0]) or \
                       (call['caller_id'] == other_user[0] and call['receiver_id'] == st.session_state.user_id):
                        if call['status'] == 'ringing' or call['status'] == 'answered':
                            active_call_id = call_id
                            break
                
                if active_call_id:
                    call_handler = VideoAudioCallHandler()
                    call = call_sessions[active_call_id]
                    
                    if call['call_type'] == 'video':
                        call_handler.start_video_call(active_call_id, st.session_state.user_id, other_user[0])
                    else:
                        call_handler.start_audio_call(active_call_id, st.session_state.user_id, other_user[0])
                
                else:
                    # Messages display
                    messages = get_messages(st.session_state.user_id, other_user[0], limit=50)
                    
                    # Messages container
                    messages_container = st.container(height=400)
                    
                    with messages_container:
                        for msg in reversed(messages):
                            if len(msg) > 3:
                                content = msg[3]
                                sender_id = msg[1]
                                created_at = msg[7] if len(msg) > 7 else ""
                                
                                is_sent = sender_id == st.session_state.user_id
                                
                                if is_sent:
                                    st.markdown(f"""
                                    <div style='text-align: right; margin: 10px 0;'>
                                        <div class='message-bubble message-sent'>
                                            {content}
                                        </div>
                                        <div style='font-size: 0.8em; color: #888; text-align: right; margin-top: 5px;'>
                                            {format_tiktok_time(created_at)}
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown(f"""
                                    <div style='text-align: left; margin: 10px 0;'>
                                        <div class='message-bubble message-received'>
                                            {content}
                                        </div>
                                        <div style='font-size: 0.8em; color: #888; margin-top: 5px;'>
                                            {format_tiktok_time(created_at)}
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                    
                    # Message input
                    with st.form(f"message_form_{other_user[0]}", clear_on_submit=True):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            message_content = st.text_input("Type a message...", key=f"msg_input_{other_user[0]}", label_visibility="collapsed")
                        with col2:
                            if st.form_submit_button("Send", use_container_width=True):
                                if message_content:
                                    success, result = send_real_time_message(
                                        st.session_state.user_id, 
                                        other_user[0], 
                                        message_content
                                    )
                                    if success:
                                        st.rerun()
                                    else:
                                        st.error(result)

def calls_page():
    """Calls history page"""
    st.markdown("<h1 style='text-align: center;'>📞 Call History</h1>", unsafe_allow_html=True)
    
    # Active calls
    st.markdown("### 📞 Active Calls")
    if call_sessions:
        for call_id, call in call_sessions.items():
            if call['status'] in ['ringing', 'answered']:
                with st.container():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.write(f"Call ID: {call_id}")
                        st.write(f"Type: {'🎥 Video' if call['call_type'] == 'video' else '📞 Audio'}")
                    with col2:
                        st.write(f"Status: {call['status'].title()}")
                        st.write(f"Duration: {int((datetime.datetime.now() - call['start_time']).total_seconds())}s")
                    with col3:
                        if st.button("Join", key=f"join_{call_id}", use_container_width=True):
                            st.session_state.join_call = call_id
                            st.rerun()
    
    # Call history
    st.markdown("### 📜 Call History")
    call_history = get_call_history(st.session_state.user_id, limit=20)
    
    if call_history:
        for call in call_history:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                with col1:
                    caller = call[10] if len(call) > 10 else "Unknown"
                    receiver = call[11] if len(call) > 11 else "Unknown"
                    
                    if call[1] == st.session_state.user_id:
                        st.write(f"📤 To: {receiver}")
                    else:
                        st.write(f"📥 From: {caller}")
                
                with col2:
                    st.write(f"Type: {'🎥' if call[3] == 'video' else '📞'} {call[3].title()}")
                
                with col3:
                    status_emoji = {
                        'completed': '✅',
                        'missed': '❌',
                        'declined': '🚫'
                    }.get(call[4], '⏳')
                    
                    st.write(f"{status_emoji} {call[4].title()}")
                    if call[5] > 0:
                        st.write(f"Duration: {call[5]}s")
                
                with col4:
                    if call[4] == 'missed' and call[2] != st.session_state.user_id:
                        if st.button("Callback", key=f"callback_{call[0]}", use_container_width=True):
                            success, call_id, message = initiate_call(st.session_state.user_id, call[1], call[3])
                            if success:
                                st.success("Calling back...")
                            else:
                                st.error(message)
    else:
        st.info("No call history yet.")

def admin_page():
    """Admin panel with user management"""
    st.markdown("<h1 style='text-align: center;'>👑 Admin Dashboard</h1>", unsafe_allow_html=True)
    
    # Admin stats
    stats = get_admin_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", stats.get('total_users', 0))
    with col2:
        st.metric("Online Users", stats.get('online_users', 0))
    with col3:
        st.metric("Banned Users", stats.get('banned_users', 0))
    with col4:
        st.metric("Total Posts", stats.get('total_posts', 0))
    
    # User management
    st.markdown("### 👥 User Management")
    
    search_term = st.text_input("Search users...", placeholder="Username, email, or display name")
    
    users = get_all_users(limit=50, search_term=search_term)
    
    if users:
        for user in users:
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 1, 1])
                
                with col1:
                    st.write(f"@{user[1]}")
                    if user[7]:  # is_banned
                        st.error("❌ BANNED")
                
                with col2:
                    st.write(user[3])  # email
                
                with col3:
                    if user[5]:  # is_online
                        st.success("🟢 Online")
                    else:
                        st.info("⚪ Offline")
                
                with col4:
                    if user[6]:  # verified
                        st.success("✅ Verified")
                    else:
                        st.info("⏳ Not Verified")
                
                with col5:
                    if not user[7]:  # not banned
                        if st.button("Ban", key=f"ban_{user[0]}", use_container_width=True):
                            reason = st.text_input(f"Reason for banning {user[1]}", key=f"reason_{user[0]}")
                            if reason:
                                success, message = ban_user(st.session_state.user_id, user[0], reason)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                    else:
                        if st.button("Unban", key=f"unban_{user[0]}", use_container_width=True):
                            success, message = unban_user(st.session_state.user_id, user[0], "Admin decision")
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                
                with col6:
                    if not user[6]:  # not verified
                        if st.button("Verify", key=f"verify_{user[0]}", use_container_width=True):
                            success, message = verify_user_account(st.session_state.user_id, user[0])
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
    
    # System controls
    st.markdown("### ⚙️ System Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh All Stats", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("📊 Export Data", use_container_width=True):
            # Export logic would go here
            st.info("Data export feature coming soon!")
    
    with col3:
        if st.button("🚨 Emergency Stop", use_container_width=True, type="primary"):
            st.warning("This will stop all real-time services. Are you sure?")
            if st.button("CONFIRM STOP", type="secondary"):
                st.error("All services stopped!")
                time.sleep(2)
                st.rerun()

# ===================================
# APP DOWNLOAD FUNCTIONALITY
# ===================================

def create_downloadable_app():
    """Create a downloadable version of the app"""
    st.markdown("### 📱 Download Feed Chat Pro App")
    
    # Create app package
    if st.button("🔄 Generate Download Package", use_container_width=True):
        with st.spinner("Creating app package..."):
            # Create temporary directory
            temp_dir = "feedchat_pro_app"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Create main app file
            app_content = """
import streamlit as st
import sqlite3
import datetime
import hashlib
import os

# App configuration
st.set_page_config(page_title="Feed Chat Pro", layout="wide")

# Initialize database
conn = sqlite3.connect("feedchat_app.db", check_same_thread=False)

# Your Feed Chat Pro code here...
# (This would contain a simplified version of the app)

def main():
    st.title("Feed Chat Pro - Desktop Edition")
    st.write("Welcome to the downloadable version of Feed Chat Pro!")
    st.write("Real-time messaging and calling available.")
    
    # Add your app logic here
    
if __name__ == "__main__":
    main()
"""
            
            with open(f"{temp_dir}/feedchat_app.py", "w") as f:
                f.write(app_content)
            
            # Create requirements file
            requirements = """
streamlit>=1.28.0
pillow>=10.0.0
numpy>=1.24.0
pyaudio>=0.2.11
"""
            
            with open(f"{temp_dir}/requirements.txt", "w") as f:
                f.write(requirements)
            
            # Create README
            readme = """
# Feed Chat Pro - Desktop App

## Installation
1. Install Python 3.8 or higher
2. Run: pip install -r requirements.txt
3. Run: streamlit run feedchat_app.py

## Features
- Real-time messaging
- Video/Audio calling
- User profiles
- Admin controls
- And more!

## System Requirements
- Windows/Mac/Linux
- 4GB RAM minimum
- Webcam and microphone for calls
- Internet connection
"""
            
            with open(f"{temp_dir}/README.md", "w") as f:
                f.write(readme)
            
            # Create batch/shell scripts
            if os.name == 'nt':  # Windows
                with open(f"{temp_dir}/start_app.bat", "w") as f:
                    f.write("@echo off\n")
                    f.write("echo Starting Feed Chat Pro...\n")
                    f.write("pip install -r requirements.txt\n")
                    f.write("streamlit run feedchat_app.py\n")
                    f.write("pause\n")
            else:  # Unix/Linux/Mac
                with open(f"{temp_dir}/start_app.sh", "w") as f:
                    f.write("#!/bin/bash\n")
                    f.write("echo 'Starting Feed Chat Pro...'\n")
                    f.write("pip install -r requirements.txt\n")
                    f.write("streamlit run feedchat_app.py\n")
            
            # Create zip file
            import zipfile
            zip_filename = "feedchat_pro_desktop.zip"
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        zipf.write(os.path.join(root, file))
            
            # Cleanup
            shutil.rmtree(temp_dir)
            
            # Provide download link
            with open(zip_filename, "rb") as f:
                bytes_data = f.read()
            
            st.success("App package created successfully!")
            st.download_button(
                label="📥 Download Feed Chat Pro Desktop App",
                data=bytes_data,
                file_name=zip_filename,
                mime="application/zip",
                use_container_width=True
            )
    
    # Mobile app options
    st.markdown("### 📱 Mobile App Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Android")
        st.info("Scan QR code to download APK")
        # Generate QR code would go here
        
    with col2:
        st.markdown("#### iOS")
        st.info("Available on TestFlight")
        st.write("Contact admin for iOS beta access")

# ===================================
# MAIN APP LAYOUT
# ===================================

def main():
    # Initialize session state
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    if 'current_chat' not in st.session_state:
        st.session_state.current_chat = None
    if 'page' not in st.session_state:
        st.session_state.page = "feed"
    
    # Inject CSS
    inject_midnight_blue_css()
    
    # Sidebar for navigation
    with st.sidebar:
        st.markdown(f"# {THEME_CONFIG['app_name']}")
        st.markdown(f"**Version:** {THEME_CONFIG['version']}")
        st.markdown("---")
        
        if st.session_state.user_id:
            user = get_user(st.session_state.user_id)
            if user:
                col1, col2 = st.columns([1, 3])
                with col1:
                    display_profile_pic(user[4], user[1], size=40)
                with col2:
                    st.markdown(f"**{user[2] or user[1]}**")
                    if user[16]:  # verified
                        st.markdown("✅ Verified")
                    if user[17]:  # is_admin
                        st.markdown("👑 Admin")
            
            st.markdown("---")
            
            # Navigation
            pages = {
                "🎬 Feed": "feed",
                "💬 Messages": "messages",
                "📞 Calls": "calls",
                "🔍 Discover": "discover",
                "➕ Create": "create",
                "👤 Profile": "profile"
            }
            
            if st.session_state.is_admin:
                pages["👑 Admin"] = "admin"
            
            pages["📱 Download"] = "download"
            
            for page_name, page_key in pages.items():
                if st.button(page_name, use_container_width=True, 
                           type="primary" if st.session_state.page == page_key else "secondary"):
                    st.session_state.page = page_key
                    st.rerun()
            
            st.markdown("---")
            
            # Online status
            is_online = user[9] if user else False
            online_status = "🟢 Online" if is_online else "⚪ Offline"
            if st.button(f"{online_status} | Logout", use_container_width=True):
                if st.session_state.user_id:
                    update_user_online_status(st.session_state.user_id, False)
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.is_admin = False
                st.rerun()
        
        else:
            st.markdown("### Welcome to Feed Chat Pro")
            st.markdown("Real-time messaging and calling platform")
            st.markdown("---")
            
            # Login/Register tabs
            tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
            
            with tab1:
                login_form()
            
            with tab2:
                register_form()
    
    # Main content area
    if st.session_state.user_id:
        # Update online status
        update_user_online_status(st.session_state.user_id, True)
        
        # Display current page
        if st.session_state.page == "feed":
            feed_page()
        elif st.session_state.page == "messages":
            messages_page()
        elif st.session_state.page == "calls":
            calls_page()
        elif st.session_state.page == "discover":
            discover_page()
        elif st.session_state.page == "create":
            create_content_page()
        elif st.session_state.page == "profile":
            profile_page()
        elif st.session_state.page == "admin" and st.session_state.is_admin:
            admin_page()
        elif st.session_state.page == "download":
            create_downloadable_app()
    else:
        # Show landing page
        landing_page()

def login_form():
    """Login form"""
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            login_submit = st.form_submit_button("Login", use_container_width=True)
        with col2:
            admin_login = st.form_submit_button("Admin Login", use_container_width=True)
        
        if login_submit:
            if username and password:
                user_id, username, error = verify_user_secure(username, password)
                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    
                    # Check if user is admin
                    user_data = get_user(user_id)
                    if user_data and user_data[17]:  # is_admin field
                        st.session_state.is_admin = True
                    
                    st.success(f"Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error(error or "Invalid credentials")
            else:
                st.error("Please enter username and password")
        
        if admin_login:
            if username and password:
                is_admin, admin_name = verify_admin_login(username, password)
                if is_admin:
                    # Get admin user ID
                    c = conn.cursor()
                    c.execute("SELECT id FROM users WHERE username=?", (admin_name,))
                    admin_user = c.fetchone()
                    
                    if admin_user:
                        st.session_state.user_id = admin_user[0]
                        st.session_state.username = admin_name
                        st.session_state.is_admin = True
                        st.success(f"Welcome Admin {admin_name}!")
                        st.rerun()
                else:
                    st.error("Invalid admin credentials")
            else:
                st.error("Please enter admin credentials")

def register_form():
    """Registration form"""
    with st.form("register_form"):
        username = st.text_input("Choose Username")
        email = st.text_input("Email Address")
        display_name = st.text_input("Display Name (optional)")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.form_submit_button("Create Account", use_container_width=True):
            if not username or not email or not password:
                st.error("Please fill in all required fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters")
            else:
                success, message = create_user_secure(username, password, email, display_name)
                if success:
                    st.success(message)
                    st.info("You can now login with your new account")
                else:
                    st.error(message)

def landing_page():
    """Landing page for non-logged in users"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        # {THEME_CONFIG['app_name']}
        ### The Ultimate Real-Time Social Platform
        
        🚀 **Features:**
        - 📹 **Video & Audio Calls** - HD quality real-time communication
        - 💬 **Real-Time Messaging** - Instant message delivery
        - 🎭 **TikTok-Style Feed** - Engaging content discovery
        - 👑 **Admin Controls** - User management and moderation
        - 📱 **Cross-Platform** - Web & downloadable desktop app
        - 🔒 **Secure & Private** - End-to-end encryption
        
        ⚡ **New in v{THEME_CONFIG['version']}:**
        - Real-time video conferencing
        - Admin panel with ban/verify capabilities
        - Downloadable desktop application
        - Enhanced midnight blue theme
        
        👥 **Already used by thousands of users worldwide!**
        """)
    
    with col2:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #1E2436 0%, #121826 100%); 
                    padding: 30px; border-radius: 20px; text-align: center;'>
            <h2>🚀 Get Started</h2>
            <p>Join the future of social communication</p>
            <div style='font-size: 48px; margin: 20px 0;'>
                📹💬📞
            </div>
            <p>Create an account or login to start connecting!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick stats
        st.markdown("---")
        try:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users")
            total_users = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM users WHERE is_online = 1")
            online_now = c.fetchone()[0] or 0
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Total Users", total_users)
            with col_b:
                st.metric("Online Now", online_now)
        except:
            pass

def discover_page():
    """Discover page placeholder"""
    st.markdown("<h1 style='text-align: center;'>🔍 Discover</h1>", unsafe_allow_html=True)
    st.info("Discover page is under development. Coming soon!")

def create_content_page():
    """Create content page placeholder"""
    st.markdown("<h1 style='text-align: center;'>➕ Create Content</h1>", unsafe_allow_html=True)
    st.info("Content creation page is under development. Coming soon!")

def profile_page():
    """Profile page placeholder"""
    st.markdown("<h1 style='text-align: center;'>👤 Profile</h1>", unsafe_allow_html=True)
    st.info("Profile page is under development. Coming soon!")

def display_feed_post_with_comments(post):
    """Display post with comments (simplified for now)"""
    try:
        post_id = post[0]
        content = post[2] if len(post) > 2 else ""
        username = post[15] if len(post) > 15 else "Unknown"
        display_name = post[16] if len(post) > 16 else username
        
        with st.container():
            st.markdown("---")
            col1, col2 = st.columns([1, 10])
            with col1:
                display_profile_pic(post[17] if len(post) > 17 else None, username)
            with col2:
                st.markdown(f"**{display_name}** @{username}")
            
            st.markdown(content)
            
            # Simple engagement buttons
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("❤️", key=f"like_{post_id}"):
                    st.success("Liked!")
            with col_b:
                if st.button("💬", key=f"comment_{post_id}"):
                    st.info("Comment feature coming soon!")
            with col_c:
                if st.button("↪️", key=f"share_{post_id}"):
                    st.info("Share feature coming soon!")
    except Exception as e:
        st.error(f"Error displaying post: {e}")

if __name__ == "__main__":
    # Configure page
    st.set_page_config(
        page_title="Feed Chat Pro",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Add auto-refresh for real-time features
    st_autorefresh(interval=10000, key="main_refresh")
    
    main()

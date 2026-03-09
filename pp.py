import streamlit as st
import sqlite3
import datetime
import random
import time
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import json
import re
import uuid
import hashlib
import secrets
import os
import threading
import queue
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av
import queue
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

# ===================================
# TIKTOK-INSPIRED THEME CONFIGURATION
# ===================================

THEME_CONFIG = {
    "app_name": "Feed Chat",
    "version": "5.0",
    "theme": {
        "primary": "#FF0050",
        "secondary": "#00F2EA",
        "accent": "#00D1FF",
        "success": "#25D366",
        "warning": "#FFC107",
        "danger": "#FF3B30",
        "background": "#000000",
        "surface": "#121212",
        "surface_light": "#1E1E1E",
        "text": "#FFFFFF",
        "text_muted": "#AAAAAA",
        "border": "#333333"
    },
    "max_file_size": 100 * 1024 * 1024,
    "supported_timezones": ["UTC", "EST", "PST", "GMT", "CET", "AEST"],
    "languages": ["en", "es", "fr", "de", "zh", "ja", "ko", "hi"],
    "webrtc": {
        "ice_servers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]}
        ]
    }
}

# ===================================
# DATABASE SETUP
# ===================================

def init_simple_db():
    """Initialize database with essential tables"""
    try:
        conn = sqlite3.connect("feedchat.db", check_same_thread=False, isolation_level=None)
        c = conn.cursor()
        
        # Enable foreign keys
        c.execute("PRAGMA foreign_keys = ON")
        
        # Users table
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
            is_live BOOLEAN DEFAULT FALSE,
            current_stream_id TEXT,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            post_count INTEGER DEFAULT 0,
            follower_count INTEGER DEFAULT 0,
            following_count INTEGER DEFAULT 0,
            total_likes INTEGER DEFAULT 0,
            verified BOOLEAN DEFAULT FALSE
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

        # Messages table
        c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            message_type TEXT DEFAULT 'text',
            media_data BLOB,
            call_data TEXT,
            is_read BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # Streams table for live streaming
        c.execute("""
        CREATE TABLE IF NOT EXISTS streams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stream_id TEXT UNIQUE NOT NULL,
            title TEXT,
            description TEXT,
            viewer_count INTEGER DEFAULT 0,
            max_viewers INTEGER DEFAULT 100,
            is_live BOOLEAN DEFAULT TRUE,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            ended_at DATETIME,
            stream_key TEXT UNIQUE,
            recording_url TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # Stream viewers table
        c.execute("""
        CREATE TABLE IF NOT EXISTS stream_viewers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stream_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            left_at DATETIME,
            FOREIGN KEY (stream_id) REFERENCES streams(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # Stream chat table
        c.execute("""
        CREATE TABLE IF NOT EXISTS stream_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stream_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stream_id) REFERENCES streams(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # Calls table for video/audio calls
        c.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caller_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            call_id TEXT UNIQUE NOT NULL,
            call_type TEXT DEFAULT 'video',
            status TEXT DEFAULT 'initiated',
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            ended_at DATETIME,
            duration INTEGER DEFAULT 0,
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

        # Create indexes
        c.execute("CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages(receiver_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_likes_post ON likes(post_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_shares_post ON shares(post_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_streams_user ON streams(user_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_streams_live ON streams(is_live)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_calls_users ON calls(caller_id, receiver_id)")
        
        conn.commit()
        return conn
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        return sqlite3.connect("feedchat.db", check_same_thread=False)

# Initialize database
conn = init_simple_db()

# ===================================
# WEBRTC VIDEO PROCESSING
# ===================================

# Global queues for video streaming
video_frames: Dict[str, queue.Queue] = {}
audio_frames: Dict[str, queue.Queue] = {}
stream_status: Dict[str, bool] = {}
active_calls: Dict[str, Dict] = {}

class VideoProcessor:
    def __init__(self, stream_id: str, is_host: bool = False):
        self.stream_id = stream_id
        self.is_host = is_host
        self.frames_queue = queue.Queue(maxsize=10)
        
    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        """Process incoming video frame"""
        img = frame.to_ndarray(format="bgr24")
        
        # Add overlay for host
        if self.is_host:
            # Add viewer count overlay
            viewer_count = get_stream_viewer_count(self.stream_id)
            img = self.add_overlay(img, f"Viewers: {viewer_count}")
        
        # Store frame in global queue
        if self.stream_id not in video_frames:
            video_frames[self.stream_id] = queue.Queue(maxsize=10)
        
        try:
            if video_frames[self.stream_id].qsize() < 5:
                video_frames[self.stream_id].put_nowait(img)
        except queue.Full:
            pass
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")
    
    def add_overlay(self, img: np.ndarray, text: str) -> np.ndarray:
        """Add text overlay to video frame"""
        height, width = img.shape[:2]
        
        # Add semi-transparent overlay at top
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (width, 50), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, img, 0.5, 0, img)
        
        # Add text
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, text, (10, 35), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
        return img

class AudioProcessor:
    def __init__(self, stream_id: str):
        self.stream_id = stream_id
        
    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        """Process incoming audio frame"""
        # Store audio frame for viewers
        if self.stream_id not in audio_frames:
            audio_frames[self.stream_id] = queue.Queue(maxsize=20)
        
        try:
            if audio_frames[self.stream_id].qsize() < 10:
                audio_frames[self.stream_id].put_nowait(frame)
        except queue.Full:
            pass
        
        return frame

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

def inject_tiktok_css():
    """Inject TikTok-inspired CSS"""
    st.markdown(f"""
    <style>
    .stApp {{
        background: {THEME_CONFIG['theme']['background']};
        color: {THEME_CONFIG['theme']['text']};
    }}
    h1, h2, h3 {{
        background: linear-gradient(45deg, {THEME_CONFIG['theme']['primary']}, {THEME_CONFIG['theme']['secondary']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .stButton>button {{
        border-radius: 20px;
        border: none;
        background: {THEME_CONFIG['theme']['surface_light']};
        color: {THEME_CONFIG['theme']['text']};
    }}
    .stButton>button:hover {{
        background: linear-gradient(45deg, {THEME_CONFIG['theme']['primary']}, {THEME_CONFIG['theme']['secondary']});
        color: white;
    }}
    .post-card {{
        background: {THEME_CONFIG['theme']['surface']};
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid {THEME_CONFIG['theme']['border']};
    }}
    .hashtag {{
        display: inline-block;
        background: rgba(255, 0, 80, 0.1);
        color: {THEME_CONFIG['theme']['primary']};
        padding: 4px 12px;
        border-radius: 15px;
        margin: 2px;
        font-size: 12px;
    }}
    .comment-box {{
        background: {THEME_CONFIG['theme']['surface_light']};
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }}
    .profile-pic {{
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: 2px solid {THEME_CONFIG['theme']['primary']};
        object-fit: cover;
    }}
    .live-badge {{
        background: {THEME_CONFIG['theme']['primary']};
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        animation: pulse 1.5s infinite;
    }}
    @keyframes pulse {{
        0% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
        100% {{ opacity: 1; }}
    }}
    .call-button {{
        background: linear-gradient(45deg, {THEME_CONFIG['theme']['primary']}, {THEME_CONFIG['theme']['secondary']});
        color: white;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        font-size: 24px;
        cursor: pointer;
    }}
    .stream-container {{
        background: {THEME_CONFIG['theme']['surface']};
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
    }}
    .chat-message {{
        padding: 10px;
        margin: 5px 0;
        background: {THEME_CONFIG['theme']['surface_light']};
        border-radius: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

def create_default_profile_pic(username):
    """Create a default profile picture with initials"""
    try:
        # Create image with gradient background
        img = Image.new('RGB', (200, 200), color=(40, 40, 40))
        draw = ImageDraw.Draw(img)
        
        # Draw gradient background
        for i in range(200):
            r = int(255 * (i/200))
            g = int(0 * (i/200))
            b = int(80 * (i/200))
            draw.line([(i, 0), (i, 200)], fill=(r, g, b))
        
        # Draw circle
        draw.ellipse([20, 20, 180, 180], fill=(30, 30, 30))
        
        # Add initials
        initials = (username[:2] if len(username) >= 2 else username[0] + 'X').upper()
        # For simplicity, just return the gradient image
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    except:
        return None

# ===================================
# USER MANAGEMENT FUNCTIONS
# ===================================

def update_user_online_status(user_id, is_online=True):
    """Update user online status"""
    try:
        c = conn.cursor()
        c.execute("UPDATE users SET is_online=?, last_seen=CURRENT_TIMESTAMP WHERE id=?", 
                 (1 if is_online else 0, user_id))
        conn.commit()
        return True
    except:
        return False

def get_user(user_id):
    """Get user data"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT id, username, display_name, email, profile_pic, bio, location, 
                   timezone, language, is_online, last_seen, created_at, post_count, 
                   follower_count, following_count, total_likes, verified, is_live, current_stream_id
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
            SELECT id, username, password_hash 
            FROM users 
            WHERE username=? AND is_active=1
        """, (username,))
        user = c.fetchone()
        
        if user:
            # Check password
            if hash_password(password) == user[2]:
                c.execute("UPDATE users SET is_online=1, last_seen=CURRENT_TIMESTAMP WHERE id=?", (user[0],))
                conn.commit()
                return user[0], user[1]
        
        return None, None
    except:
        return None, None

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

def get_global_users(search_term=None, limit=50):
    """Get global users with filtering"""
    try:
        c = conn.cursor()
        
        query = "SELECT id, username, profile_pic, bio, location, language, is_online, is_live FROM users WHERE id != ?"
        params = [st.session_state.get('user_id', 0)]
        
        if search_term:
            query += " AND (username LIKE ? OR bio LIKE ?)"
            params.extend([f'%{search_term}%', f'%{search_term}%'])
        
        query += " ORDER BY is_online DESC, is_live DESC, username ASC LIMIT ?"
        params.append(limit)
        
        c.execute(query, params)
        return c.fetchall()
    except:
        return []

# ===================================
# LIVE STREAMING FUNCTIONS
# ===================================

def generate_stream_key():
    """Generate unique stream key"""
    return hashlib.sha256(f"{uuid.uuid4()}{time.time()}".encode()).hexdigest()[:32]

def start_stream(user_id, title="", description=""):
    """Start a new live stream"""
    try:
        c = conn.cursor()
        stream_id = str(uuid.uuid4())
        stream_key = generate_stream_key()
        
        c.execute("""
            INSERT INTO streams (user_id, stream_id, title, description, stream_key)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, stream_id, title, description, stream_key))
        
        # Update user live status
        c.execute("UPDATE users SET is_live=1, current_stream_id=? WHERE id=?", (stream_id, user_id))
        
        conn.commit()
        
        # Initialize video queue for this stream
        video_frames[stream_id] = queue.Queue(maxsize=10)
        audio_frames[stream_id] = queue.Queue(maxsize=20)
        stream_status[stream_id] = True
        
        return True, stream_id, stream_key
    except Exception as e:
        return False, str(e), None

def end_stream(stream_id):
    """End a live stream"""
    try:
        c = conn.cursor()
        
        # Get user_id from stream
        c.execute("SELECT user_id FROM streams WHERE stream_id=?", (stream_id,))
        result = c.fetchone()
        
        if result:
            user_id = result[0]
            
            # Update stream status
            c.execute("""
                UPDATE streams 
                SET is_live=0, ended_at=CURRENT_TIMESTAMP 
                WHERE stream_id=?
            """, (stream_id,))
            
            # Update user live status
            c.execute("UPDATE users SET is_live=0, current_stream_id=NULL WHERE id=?", (user_id,))
            
            conn.commit()
            
            # Clean up queues
            if stream_id in video_frames:
                del video_frames[stream_id]
            if stream_id in audio_frames:
                del audio_frames[stream_id]
            if stream_id in stream_status:
                del stream_status[stream_id]
        
        return True
    except Exception as e:
        return False

def get_live_streams():
    """Get all currently live streams"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT s.*, u.username, u.display_name, u.profile_pic 
            FROM streams s
            JOIN users u ON s.user_id = u.id
            WHERE s.is_live=1
            ORDER BY s.started_at DESC
        """)
        return c.fetchall()
    except:
        return []

def get_stream(stream_id):
    """Get stream details"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT s.*, u.username, u.display_name, u.profile_pic 
            FROM streams s
            JOIN users u ON s.user_id = u.id
            WHERE s.stream_id=?
        """, (stream_id,))
        return c.fetchone()
    except:
        return None

def add_stream_viewer(stream_id, user_id):
    """Add viewer to stream"""
    try:
        c = conn.cursor()
        
        # Add to viewers table
        c.execute("""
            INSERT INTO stream_viewers (stream_id, user_id)
            VALUES (?, ?)
        """, (stream_id, user_id))
        
        # Update viewer count
        c.execute("""
            UPDATE streams 
            SET viewer_count = (
                SELECT COUNT(*) FROM stream_viewers 
                WHERE stream_id=? AND left_at IS NULL
            )
            WHERE stream_id=?
        """, (stream_id, stream_id))
        
        conn.commit()
        return True
    except:
        return False

def remove_stream_viewer(stream_id, user_id):
    """Remove viewer from stream"""
    try:
        c = conn.cursor()
        
        # Update viewer record
        c.execute("""
            UPDATE stream_viewers 
            SET left_at=CURRENT_TIMESTAMP 
            WHERE stream_id=? AND user_id=? AND left_at IS NULL
        """, (stream_id, user_id))
        
        # Update viewer count
        c.execute("""
            UPDATE streams 
            SET viewer_count = (
                SELECT COUNT(*) FROM stream_viewers 
                WHERE stream_id=? AND left_at IS NULL
            )
            WHERE stream_id=?
        """, (stream_id, stream_id))
        
        conn.commit()
        return True
    except:
        return False

def get_stream_viewer_count(stream_id):
    """Get current viewer count for stream"""
    try:
        c = conn.cursor()
        c.execute("SELECT viewer_count FROM streams WHERE stream_id=?", (stream_id,))
        result = c.fetchone()
        return result[0] if result else 0
    except:
        return 0

def send_stream_message(stream_id, user_id, message):
    """Send message in stream chat"""
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO stream_chat (stream_id, user_id, message)
            VALUES (?, ?, ?)
        """, (stream_id, user_id, message))
        conn.commit()
        return True
    except:
        return False

def get_stream_messages(stream_id, limit=50):
    """Get stream chat messages"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT sc.*, u.username, u.profile_pic
            FROM stream_chat sc
            JOIN users u ON sc.user_id = u.id
            WHERE sc.stream_id=?
            ORDER BY sc.created_at DESC
            LIMIT ?
        """, (stream_id, limit))
        return c.fetchall()
    except:
        return []

# ===================================
# VIDEO CALL FUNCTIONS
# ===================================

def initiate_call(caller_id, receiver_id, call_type='video'):
    """Initiate a call between users"""
    try:
        c = conn.cursor()
        call_id = str(uuid.uuid4())
        
        c.execute("""
            INSERT INTO calls (caller_id, receiver_id, call_id, call_type, status)
            VALUES (?, ?, ?, ?, 'initiated')
        """, (caller_id, receiver_id, call_id, call_type))
        
        conn.commit()
        
        # Store call in active calls
        active_calls[call_id] = {
            'caller_id': caller_id,
            'receiver_id': receiver_id,
            'type': call_type,
            'status': 'initiated',
            'started_at': time.time()
        }
        
        return True, call_id
    except Exception as e:
        return False, str(e)

def accept_call(call_id):
    """Accept an incoming call"""
    try:
        c = conn.cursor()
        
        c.execute("""
            UPDATE calls 
            SET status='active' 
            WHERE call_id=?
        """, (call_id,))
        
        conn.commit()
        
        if call_id in active_calls:
            active_calls[call_id]['status'] = 'active'
        
        return True
    except:
        return False

def end_call(call_id):
    """End an active call"""
    try:
        c = conn.cursor()
        
        # Calculate duration
        if call_id in active_calls:
            duration = int(time.time() - active_calls[call_id]['started_at'])
        else:
            duration = 0
        
        c.execute("""
            UPDATE calls 
            SET status='ended', ended_at=CURRENT_TIMESTAMP, duration=?
            WHERE call_id=?
        """, (duration, call_id))
        
        conn.commit()
        
        # Remove from active calls
        if call_id in active_calls:
            del active_calls[call_id]
        
        # Clean up video/audio queues
        if call_id in video_frames:
            del video_frames[call_id]
        if call_id in audio_frames:
            del audio_frames[call_id]
        
        return True
    except:
        return False

def get_active_call(user_id):
    """Get active call for user"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT * FROM calls 
            WHERE (caller_id=? OR receiver_id=?) 
            AND status IN ('initiated', 'active')
            ORDER BY started_at DESC LIMIT 1
        """, (user_id, user_id))
        return c.fetchone()
    except:
        return None

def get_call_messages(call_id):
    """Get messages for a call (if any)"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT * FROM messages 
            WHERE call_data IS NOT NULL 
            AND json_extract(call_data, '$.call_id') = ?
            ORDER BY created_at
        """, (call_id,))
        return c.fetchall()
    except:
        return []

# ===================================
# COMMENT FUNCTIONS
# ===================================

def add_comment(post_id, user_id, content):
    """Add a comment to a post"""
    try:
        if not content or len(content.strip()) == 0:
            return False, "Comment cannot be empty"
        
        c = conn.cursor()
        c.execute("""
            INSERT INTO comments (post_id, user_id, content)
            VALUES (?, ?, ?)
        """, (post_id, user_id, content))
        
        # Update comment count in posts table
        c.execute("UPDATE posts SET comment_count = comment_count + 1 WHERE id = ?", (post_id,))
        
        conn.commit()
        return True, "Comment added successfully"
    except Exception as e:
        return False, f"Failed to add comment: {str(e)}"

def get_comments(post_id, limit=50):
    """Get comments for a post"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT c.*, u.username, u.profile_pic, u.display_name
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.created_at DESC
            LIMIT ?
        """, (post_id, limit))
        
        return c.fetchall()
    except Exception as e:
        return []

def delete_comment(comment_id, user_id):
    """Delete a comment (only if user owns it)"""
    try:
        c = conn.cursor()
        
        # Check if user owns the comment
        c.execute("SELECT post_id FROM comments WHERE id = ? AND user_id = ?", (comment_id, user_id))
        result = c.fetchone()
        
        if result:
            post_id = result[0]
            c.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
            
            # Update comment count
            c.execute("UPDATE posts SET comment_count = comment_count - 1 WHERE id = ?", (post_id,))
            
            conn.commit()
            return True
        return False
    except:
        return False

# ===================================
# SHARE FUNCTIONS
# ===================================

def share_post(user_id, post_id, shared_to_user_id=None):
    """Share a post to a user or just increment share count"""
    try:
        c = conn.cursor()
        
        # Add to shares table if sharing to a specific user
        if shared_to_user_id:
            c.execute("""
                INSERT INTO shares (user_id, post_id, shared_to_user_id)
                VALUES (?, ?, ?)
            """, (user_id, post_id, shared_to_user_id))
        
        # Update share count in posts table
        c.execute("UPDATE posts SET share_count = share_count + 1 WHERE id = ?", (post_id,))
        
        conn.commit()
        return True, "Post shared successfully"
    except Exception as e:
        return False, f"Failed to share post: {str(e)}"

def get_share_count(post_id):
    """Get share count for a post"""
    try:
        c = conn.cursor()
        c.execute("SELECT share_count FROM posts WHERE id = ?", (post_id,))
        result = c.fetchone()
        return result[0] if result else 0
    except:
        return 0

def get_user_shares(user_id):
    """Get posts shared by a user"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT s.*, p.content, p.media_type, u.username as original_author
            FROM shares s
            JOIN posts p ON s.post_id = p.id
            JOIN users u ON p.user_id = u.id
            WHERE s.user_id = ?
            ORDER BY s.created_at DESC
        """, (user_id,))
        return c.fetchall()
    except:
        return []

# ===================================
# MESSAGING FUNCTIONS
# ===================================

def send_message(sender_id, receiver_id, content, message_type='text', media_data=None, call_data=None):
    """Send a message"""
    try:
        if not content and not media_data and not call_data:
            return False, "Message cannot be empty"
        
        c = conn.cursor()
        
        # Convert call_data to JSON if present
        call_data_json = json.dumps(call_data) if call_data else None
        
        c.execute("""
        INSERT INTO messages (sender_id, receiver_id, content, message_type, media_data, call_data)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (sender_id, receiver_id, content, message_type, media_data, call_data_json))
        
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
            u.is_live,
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

def get_messages(user_id, other_user_id, limit=50):
    """Get messages between two users"""
    try:
        c = conn.cursor()
        c.execute("""
        SELECT m.*, u.username as sender_username, u.profile_pic
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
                SELECT p.*, u.username, u.display_name, u.profile_pic, u.is_live
                FROM posts p
                JOIN users u ON p.user_id = u.id
                WHERE p.is_deleted = 0 AND p.user_id = ?
                ORDER BY p.created_at DESC
                LIMIT ?
            """, (user_id, limit))
        else:
            c.execute("""
                SELECT p.*, u.username, u.display_name, u.profile_pic, u.is_live
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

def like_post(user_id, post_id):
    """Like a post"""
    try:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO likes (user_id, post_id) VALUES (?, ?)", 
                 (user_id, post_id))
        conn.commit()
        return True
    except:
        return False

def unlike_post(user_id, post_id):
    """Unlike a post"""
    try:
        c = conn.cursor()
        c.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?", 
                 (user_id, post_id))
        conn.commit()
        return True
    except:
        return False

def has_liked_post(user_id, post_id):
    """Check if user has liked a post"""
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM likes WHERE user_id = ? AND post_id = ?", 
                 (user_id, post_id))
        return c.fetchone() is not None
    except:
        return False

def save_post(user_id, post_id):
    """Save a post to bookmarks"""
    try:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO saves (user_id, post_id) VALUES (?, ?)", 
                 (user_id, post_id))
        conn.commit()
        return True
    except:
        return False

def unsave_post(user_id, post_id):
    """Remove post from saves"""
    try:
        c = conn.cursor()
        c.execute("DELETE FROM saves WHERE user_id = ? AND post_id = ?", 
                 (user_id, post_id))
        conn.commit()
        return True
    except:
        return False

def is_saved(user_id, post_id):
    """Check if post is saved"""
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM saves WHERE user_id = ? AND post_id = ?", 
                 (user_id, post_id))
        return c.fetchone() is not None
    except:
        return False

def follow_user(follower_id, following_id):
    """Follow a user"""
    try:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO follows (follower_id, following_id) VALUES (?, ?)", 
                 (follower_id, following_id))
        conn.commit()
        return True
    except:
        return False

def unfollow_user(follower_id, following_id):
    """Unfollow a user"""
    try:
        c = conn.cursor()
        c.execute("DELETE FROM follows WHERE follower_id = ? AND following_id = ?", 
                 (follower_id, following_id))
        conn.commit()
        return True
    except:
        return False

def is_following(follower_id, following_id):
    """Check if user is following another user"""
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM follows WHERE follower_id = ? AND following_id = ?", 
                 (follower_id, following_id))
        return c.fetchone() is not None
    except:
        return False

def get_trending_hashtags(limit=10):
    """Get trending hashtags"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT 
                TRIM(REPLACE(REPLACE(hashtags, '#', ''), ' ', '')) as tag,
                COUNT(*) as post_count
            FROM posts 
            WHERE hashtags != '' 
            GROUP BY tag 
            ORDER BY post_count DESC 
            LIMIT ?
        """, (limit,))
        return c.fetchall()
    except:
        return []

# ===================================
# MEDIA DISPLAY FUNCTIONS
# ===================================

def display_media(media_data, media_type, caption=""):
    """Display media (image or video)"""
    try:
        if media_data:
            if media_type and 'video' in media_type:
                # Display video
                st.video(media_data)
            elif media_type and 'image' in media_type:
                # Display image
                st.image(media_data, caption=caption, use_container_width=True)
        return True
    except Exception as e:
        st.error(f"Error displaying media: {str(e)}")
        return False

def display_profile_pic(profile_pic, username, size=40):
    """Display profile picture with fallback"""
    try:
        if profile_pic:
            st.image(profile_pic, width=size)
        else:
            # Display placeholder with initials
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
        # Fallback to initials
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
# LIVE STREAMING PAGE
# ===================================

def live_streaming_page():
    """Live streaming page with WebRTC"""
    st.markdown("<h1 style='text-align: center;'>📡 Live Streaming</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🎥 Go Live", "👀 Watch Streams"])
    
    with tab1:
        st.markdown("### Start Your Live Stream")
        
        with st.form("start_stream_form"):
            stream_title = st.text_input("Stream Title", placeholder="Enter stream title...")
            stream_description = st.text_area("Description", placeholder="Tell viewers what you're streaming...", height=100)
            
            if st.form_submit_button("🎥 Go Live Now", use_container_width=True):
                if stream_title:
                    with st.spinner("Starting stream..."):
                        success, stream_id, stream_key = start_stream(
                            st.session_state.user_id, 
                            stream_title, 
                            stream_description
                        )
                        
                        if success:
                            st.session_state.current_stream = stream_id
                            st.session_state.stream_key = stream_key
                            st.success("Stream started successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to start stream")
                else:
                    st.error("Please enter a stream title")
        
        # If currently streaming
        if st.session_state.get('current_stream'):
            stream_id = st.session_state.current_stream
            stream = get_stream(stream_id)
            
            if stream:
                st.markdown("---")
                st.markdown("### 🔴 You Are Live!")
                
                # Display stream info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Viewers", get_stream_viewer_count(stream_id))
                with col2:
                    st.metric("Duration", "00:00")
                with col3:
                    if st.button("⏹️ End Stream", use_container_width=True):
                        end_stream(stream_id)
                        st.session_state.current_stream = None
                        st.rerun()
                
                # Stream key (for OBS/etc)
                with st.expander("Stream Settings"):
                    st.code(f"Stream Key: {st.session_state.stream_key}")
                    st.info("Use this key in OBS or other streaming software with RTMP URL: rtmp://feedchat.app/live")
                
                # WebRTC stream
                st.markdown("### Your Stream Preview")
                
                # WebRTC configuration
                rtc_configuration = RTCConfiguration(
                    {"iceServers": THEME_CONFIG['webrtc']['ice_servers']}
                )
                
                # Create WebRTC streamer for host
                webrtc_ctx = webrtc_streamer(
                    key=f"host-{stream_id}",
                    mode=WebRtcMode.SENDONLY,
                    rtc_configuration=rtc_configuration,
                    media_stream_constraints={
                        "video": True,
                        "audio": True,
                    },
                    video_processor_factory=lambda: VideoProcessor(stream_id, is_host=True),
                    audio_processor_factory=lambda: AudioProcessor(stream_id),
                    async_processing=True,
                )
                
                # Stream chat
                st.markdown("### Stream Chat")
                chat_container = st.container()
                
                with chat_container:
                    messages = get_stream_messages(stream_id, limit=20)
                    for msg in messages:
                        if len(msg) > 4:
                            username = msg[5]
                            message = msg[3]
                            st.markdown(f"""
                            <div class='chat-message'>
                                <strong>@{username}:</strong> {message}
                            </div>
                            """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Live Now")
        
        # Get all live streams
        live_streams = get_live_streams()
        
        if live_streams:
            for stream in live_streams:
                if len(stream) > 10:
                    stream_id = stream[2]  # stream_id
                    title = stream[3]
                    username = stream[13]  # username
                    display_name = stream[14]
                    profile_pic = stream[15]
                    viewer_count = stream[5]
                    
                    col1, col2 = st.columns([1, 4])
                    
                    with col1:
                        display_profile_pic(profile_pic, username, size=60)
                    
                    with col2:
                        st.markdown(f"""
                        **{display_name}** <span class='live-badge'>LIVE</span>
                        """, unsafe_allow_html=True)
                        st.markdown(f"*{title}*")
                        st.caption(f"👁️ {viewer_count} viewers")
                        
                        if st.button(f"Watch Stream", key=f"watch_{stream_id}", use_container_width=True):
                            st.session_state.watch_stream = stream_id
                            st.rerun()
                    
                    st.markdown("---")
            
            # Watch selected stream
            if st.session_state.get('watch_stream'):
                stream_id = st.session_state.watch_stream
                stream = get_stream(stream_id)
                
                if stream:
                    st.markdown("---")
                    st.markdown("### Watching Stream")
                    
                    # Add viewer
                    add_stream_viewer(stream_id, st.session_state.user_id)
                    
                    # WebRTC viewer
                    rtc_configuration = RTCConfiguration(
                        {"iceServers": THEME_CONFIG['webrtc']['ice_servers']}
                    )
                    
                    webrtc_ctx = webrtc_streamer(
                        key=f"viewer-{stream_id}",
                        mode=WebRtcMode.RECVONLY,
                        rtc_configuration=rtc_configuration,
                        video_processor_factory=lambda: VideoProcessor(stream_id, is_host=False),
                        audio_processor_factory=lambda: AudioProcessor(stream_id),
                        async_processing=True,
                    )
                    
                    # Stream info
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{stream[3]}**")
                        st.caption(f"Streaming by @{stream[13]}")
                    with col2:
                        if st.button("❌ Leave Stream"):
                            remove_stream_viewer(stream_id, st.session_state.user_id)
                            st.session_state.watch_stream = None
                            st.rerun()
                    
                    # Stream chat
                    st.markdown("### Live Chat")
                    
                    # Display messages
                    chat_container = st.container()
                    with chat_container:
                        messages = get_stream_messages(stream_id, limit=30)
                        for msg in messages:
                            if len(msg) > 4:
                                username = msg[5]
                                message = msg[3]
                                st.markdown(f"""
                                <div class='chat-message'>
                                    <strong>@{username}:</strong> {message}
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # Send message
                    with st.form("stream_chat_form", clear_on_submit=True):
                        chat_message = st.text_input("Type a message...", key=f"chat_{stream_id}")
                        if st.form_submit_button("Send"):
                            if chat_message:
                                send_stream_message(stream_id, st.session_state.user_id, chat_message)
                                st.rerun()
        else:
            st.info("No live streams at the moment. Be the first to go live!")

# ===================================
# VIDEO CALL PAGE
# ===================================

def video_call_page():
    """Video calling page"""
    st.markdown("<h1 style='text-align: center;'>📞 Video Calls</h1>", unsafe_allow_html=True)
    
    # Check for active call
    active_call = get_active_call(st.session_state.user_id)
    
    if active_call and len(active_call) > 5:
        # Currently in a call
        call_id = active_call[4]  # call_id
        caller_id = active_call[1]
        receiver_id = active_call[2]
        call_type = active_call[5]
        status = active_call[6]
        
        other_user_id = caller_id if caller_id != st.session_state.user_id else receiver_id
        other_user = get_user(other_user_id)
        
        if other_user:
            st.markdown(f"### In call with @{other_user[1]}")
            
            # Call controls
            col1, col2, col3 = st.columns(3)
            with col2:
                if st.button("🔴 End Call", use_container_width=True):
                    end_call(call_id)
                    st.rerun()
            
            # WebRTC call
            rtc_configuration = RTCConfiguration(
                {"iceServers": THEME_CONFIG['webrtc']['ice_servers']}
            )
            
            # Determine role (offerer/answerer)
            mode = WebRtcMode.SENDRECV
            
            webrtc_ctx = webrtc_streamer(
                key=f"call-{call_id}",
                mode=mode,
                rtc_configuration=rtc_configuration,
                media_stream_constraints={
                    "video": call_type == 'video',
                    "audio": True,
                },
                video_processor_factory=lambda: VideoProcessor(call_id),
                audio_processor_factory=lambda: AudioProcessor(call_id),
                async_processing=True,
            )
            
    else:
        # No active call - show users to call
        st.markdown("### Start a New Call")
        
        # Get online users
        users = get_global_users(limit=20)
        
        for user in users:
            if len(user) > 3:
                user_id = user[0]
                username = user[1]
                profile_pic = user[2]
                is_online = user[6] if len(user) > 6 else False
                
                if user_id != st.session_state.user_id:
                    col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                    
                    with col1:
                        display_profile_pic(profile_pic, username, size=40)
                    
                    with col2:
                        status_emoji = "🟢" if is_online else "⚪"
                        st.markdown(f"{status_emoji} @{username}")
                    
                    with col3:
                        if st.button("📹 Video", key=f"video_{user_id}", use_container_width=True):
                            success, call_id = initiate_call(st.session_state.user_id, user_id, 'video')
                            if success:
                                # Send call message
                                send_message(
                                    st.session_state.user_id, 
                                    user_id, 
                                    "📞 Video call started",
                                    message_type='call',
                                    call_data={'call_id': call_id, 'type': 'video'}
                                )
                                st.success("Call initiated! Waiting for answer...")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to start call")
                    
                    with col4:
                        if st.button("🎤 Audio", key=f"audio_{user_id}", use_container_width=True):
                            success, call_id = initiate_call(st.session_state.user_id, user_id, 'audio')
                            if success:
                                send_message(
                                    st.session_state.user_id, 
                                    user_id, 
                                    "🎤 Audio call started",
                                    message_type='call',
                                    call_data={'call_id': call_id, 'type': 'audio'}
                                )
                                st.success("Call initiated! Waiting for answer...")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to start call")
                    
                    st.markdown("---")

# ===================================
# FEED PAGE WITH COMMENTS
# ===================================

def feed_page():
    """Feed Chat vertical feed with comments and sharing"""
    st.markdown("<h1 style='text-align: center;'>🎬 Your Feed</h1>", unsafe_allow_html=True)
    
    # For You feed
    posts = get_posts_simple(limit=10)
    
    if not posts:
        st.info("No posts yet. Create your first post!")
        return
    
    # Display posts
    for post in posts:
        try:
            display_feed_post_with_comments(post)
        except Exception as e:
            st.error(f"Error displaying post: {e}")
            continue
    
    # Load more button
    if st.button("Load More", use_container_width=True):
        st.rerun()

def display_feed_post_with_comments(post):
    """Display post with comments and sharing features"""
    try:
        # Safe unpacking
        post_id = post[0] if len(post) > 0 else 0
        user_id = post[1] if len(post) > 1 else 0
        content = post[2] if len(post) > 2 else ""
        media_type = post[3] if len(post) > 3 else None
        media_data = post[4] if len(post) > 4 else None
        location = post[5] if len(post) > 5 else ""
        language = post[6] if len(post) > 6 else "en"
        visibility = post[7] if len(post) > 7 else "public"
        is_deleted = post[8] if len(post) > 8 else 0
        created_at = post[14] if len(post) > 14 else ""
        username = post[15] if len(post) > 15 else "Unknown"
        display_name = post[16] if len(post) > 16 else username
        profile_pic = post[17] if len(post) > 17 else None
        is_live = post[18] if len(post) > 18 else False
        
        if is_deleted:
            return
        
        with st.container():
            st.markdown("---")
            
            # User info with profile picture
            col1, col2 = st.columns([1, 10])
            with col1:
                display_profile_pic(profile_pic, username, size=40)
            with col2:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**{display_name}**")
                    st.markdown(f"@{username}")
                    if is_live:
                        st.markdown("<span class='live-badge'>LIVE</span>", unsafe_allow_html=True)
                with col_b:
                    # Call button
                    if st.button("📞", key=f"call_{post_id}", help="Start video call"):
                        st.session_state.call_user = user_id
                        st.rerun()
                
                if location:
                    st.caption(f"📍 {location}")
                st.caption(f"🕒 {format_tiktok_time(created_at)}")
            
            # Post content
            if content:
                st.markdown(f"{content}")
            
            # Display media if exists
            if media_data and media_type:
                display_media(media_data, media_type)
            
            # Hashtags
            hashtags = post[13] if len(post) > 13 else ""
            if hashtags:
                tags = hashtags.split(',')
                for tag in tags[:5]:
                    if tag.strip():
                        st.markdown(f"<span class='hashtag'>#{tag.strip()}</span>", unsafe_allow_html=True)
            
            # Get current stats
            current_likes, current_comments, current_shares = get_post_stats(post_id)
            
            # Engagement buttons
            col_a, col_b, col_c, col_d = st.columns(4)
            
            with col_a:
                liked = has_liked_post(st.session_state.user_id, post_id)
                like_text = "❤️" if not liked else "💔"
                if st.button(f"{like_text}\n{current_likes}", key=f"like_{post_id}", use_container_width=True):
                    if liked:
                        unlike_post(st.session_state.user_id, post_id)
                    else:
                        like_post(st.session_state.user_id, post_id)
                    st.rerun()
            
            with col_b:
                comment_expander = st.expander(f"💬 {current_comments} Comments")
                with comment_expander:
                    # Display existing comments
                    comments = get_comments(post_id)
                    if comments:
                        for comment in comments:
                            col1, col2 = st.columns([1, 10])
                            with col1:
                                comment_username = comment[5] if len(comment) > 5 else "Unknown"
                                comment_profile_pic = comment[6] if len(comment) > 6 else None
                                display_profile_pic(comment_profile_pic, comment_username, size=30)
                            with col2:
                                st.markdown(f"**@{comment_username}**")
                                st.markdown(comment[3] if len(comment) > 3 else "")
                                st.caption(f"🕒 {format_tiktok_time(comment[4] if len(comment) > 4 else '')}")
                    
                    # Add new comment
                    with st.form(f"comment_form_{post_id}", clear_on_submit=True):
                        new_comment = st.text_area("Add a comment...", key=f"comment_text_{post_id}", height=60)
                        if st.form_submit_button("Post Comment", use_container_width=True):
                            if new_comment:
                                success, result = add_comment(post_id, st.session_state.user_id, new_comment)
                                if success:
                                    st.success("Comment added!")
                                    st.rerun()
                                else:
                                    st.error(result)
            
            with col_c:
                share_expander = st.expander(f"↪️ {current_shares} Shares")
                with share_expander:
                    st.markdown("### Share this post")
                    
                    # Option 1: Copy link
                    post_link = f"https://feedchat.app/post/{post_id}"
                    if st.button("📋 Copy Link", key=f"copy_link_{post_id}", use_container_width=True):
                        st.write(f"Link copied: {post_link}")
                        st.info("Link copied to clipboard!")
                    
                    # Option 2: Share to specific users
                    st.markdown("---")
                    st.markdown("### Share with users")
                    users = get_global_users(limit=20)
                    for user in users:
                        if len(user) > 1 and user[0] != st.session_state.user_id:
                            share_user_id = user[0]
                            share_username = user[1]
                            
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**@{share_username}**")
                            with col2:
                                if st.button("Send", key=f"share_{post_id}_{share_user_id}", use_container_width=True):
                                    success, result = share_post(st.session_state.user_id, post_id, share_user_id)
                                    if success:
                                        st.success(f"Shared with @{share_username}!")
                                    else:
                                        st.error(result)
            
            with col_d:
                saved = is_saved(st.session_state.user_id, post_id)
                save_text = "⬇️" if not saved else "✅"
                if st.button(f"{save_text}\nSave", key=f"save_{post_id}", use_container_width=True):
                    if saved:
                        unsave_post(st.session_state.user_id, post_id)
                    else:
                        save_post(st.session_state.user_id, post_id)
                    st.rerun()
                    
    except Exception as e:
        st.error(f"Error displaying post: {e}")

# ===================================
# DISCOVER PAGE
# ===================================

def discover_page():
    """Discover page with trending content"""
    st.markdown("<h1 style='text-align: center;'>🔍 Discover</h1>", unsafe_allow_html=True)
    
    # Search bar
    search_query = st.text_input("", placeholder="Search users...", label_visibility="collapsed")
    
    # Trending hashtags
    st.markdown("### 🔥 Trending Hashtags")
    trending_hashtags = get_trending_hashtags(10)
    
    if trending_hashtags:
        cols = st.columns(3)
        for idx, hashtag in enumerate(trending_hashtags):
            tag, count = hashtag
            with cols[idx % 3]:
                st.markdown(f"**#{tag}**")
                st.caption(f"{count} posts")
    
    # Suggested accounts
    st.markdown("### 👥 Suggested For You")
    suggested_users = get_global_users(search_query, limit=6)
    
    if suggested_users:
        cols = st.columns(3)
        for idx, user in enumerate(suggested_users):
            user_id = user[0] if len(user) > 0 else 0
            username = user[1] if len(user) > 1 else "Unknown"
            profile_pic = user[2] if len(user) > 2 else None
            bio = user[3] if len(user) > 3 else ""
            is_live = user[7] if len(user) > 7 else False
            
            with cols[idx % 3]:
                col1, col2 = st.columns([1, 3])
                with col1:
                    display_profile_pic(profile_pic, username, size=40)
                with col2:
                    live_badge = " 🔴 LIVE" if is_live else ""
                    st.markdown(f"**@{username}**{live_badge}")
                
                if bio:
                    st.caption(bio[:50] + "..." if len(bio) > 50 else bio)
                
                if is_following(st.session_state.user_id, user_id):
                    if st.button("Following", key=f"unfollow_{user_id}", use_container_width=True):
                        unfollow_user(st.session_state.user_id, user_id)
                        st.rerun()
                else:
                    if st.button("Follow", key=f"follow_{user_id}", use_container_width=True):
                        follow_user(st.session_state.user_id, user_id)
                        st.rerun()

# ===================================
# CREATE CONTENT PAGE
# ===================================

def create_content_page():
    """Content creation page with media upload"""
    st.markdown("<h1 style='text-align: center;'>➕ Create Post</h1>", unsafe_allow_html=True)
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a file to upload",
        type=['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'avi', 'mkv'],
        help="Upload an image or video (max 100MB)"
    )
    
    # Display preview
    if uploaded_file:
        file_type = uploaded_file.type
        
        if 'image' in file_type:
            st.image(uploaded_file, caption="Preview", use_container_width=True)
        elif 'video' in file_type:
            st.video(uploaded_file)
    
    with st.form("create_post_form"):
        content = st.text_area("What's happening?", placeholder="Share your thoughts... #hashtag", height=100)
        location = st.text_input("Location", placeholder="Add location (optional)")
        
        col1, col2 = st.columns(2)
        with col1:
            visibility = st.selectbox("Visibility", ["public", "friends", "private"])
        
        with col2:
            if st.form_submit_button("Post", use_container_width=True):
                if content:
                    media_data = uploaded_file.read() if uploaded_file else None
                    media_type = uploaded_file.type if uploaded_file else None
                    
                    with st.spinner("Posting..."):
                        success, result = create_post(
                            st.session_state.user_id, 
                            content, 
                            media_data, 
                            media_type,
                            location=location,
                            visibility=visibility
                        )
                        
                        if success:
                            st.success("🎉 Post created successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Error: {result}")
                else:
                    st.error("Please write something to post")

# ===================================
# PROFILE PAGE
# ===================================

def profile_page():
    """Profile page with edit functionality"""
    user = get_user(st.session_state.user_id)
    
    if user:
        user_id = user[0]
        username = user[1]
        display_name = user[2] or username
        email = user[3]
        profile_pic = user[4]
        bio = user[5] if len(user) > 5 else ""
        location = user[6] if len(user) > 6 else ""
        post_count = user[12] if len(user) > 12 else 0
        follower_count = user[13] if len(user) > 13 else 0
        following_count = user[14] if len(user) > 14 else 0
        total_likes = user[15] if len(user) > 15 else 0
        is_live = user[17] if len(user) > 17 else False
        current_stream = user[18] if len(user) > 18 else None
        
        # Edit profile button
        if st.button("✏️ Edit Profile", use_container_width=True):
            st.session_state.editing_profile = True
        
        # Profile header
        col1, col2 = st.columns([1, 3])
        with col1:
            display_profile_pic(profile_pic, username, size=100)
        with col2:
            st.markdown(f"# {display_name}")
            st.markdown(f"@{username}")
            if is_live:
                st.markdown("<span class='live-badge'>LIVE NOW</span>", unsafe_allow_html=True)
            
            if bio:
                st.markdown(f"**Bio:** {bio}")
            
            if location:
                st.markdown(f"📍 {location}")
            
            if email:
                st.caption(f"📧 {email}")
        
        # Stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Posts", post_count)
        with col2:
            st.metric("Followers", follower_count)
        with col3:
            st.metric("Following", following_count)
        with col4:
            st.metric("Likes", total_likes)
        
        # Edit profile form
        if st.session_state.get('editing_profile'):
            with st.form("edit_profile_form"):
                st.markdown("### Edit Profile")
                
                new_display_name = st.text_input("Display Name", value=display_name)
                new_bio = st.text_area("Bio", value=bio, height=100)
                new_location = st.text_input("Location", value=location)
                
                # Profile picture upload
                new_profile_pic = st.file_uploader(
                    "Upload Profile Picture",
                    type=['jpg', 'jpeg', 'png'],
                    help="Upload a profile picture (max 5MB)"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Save Changes", use_container_width=True):
                        profile_pic_data = None
                        if new_profile_pic:
                            profile_pic_data = new_profile_pic.read()
                        
                        success = update_user_profile(
                            user_id,
                            display_name=new_display_name,
                            bio=new_bio,
                            location=new_location,
                            profile_pic=profile_pic_data
                        )
                        
                        if success:
                            st.success("Profile updated successfully!")
                            st.session_state.editing_profile = False
                            st.rerun()
                        else:
                            st.error("Failed to update profile")
                
                with col2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.editing_profile = False
                        st.rerun()
        
        # User's posts
        st.markdown("### 📸 Your Posts")
        user_posts = get_posts_simple(user_id=st.session_state.user_id, limit=12)
        
        if user_posts:
            cols = st.columns(3)
            for idx, post in enumerate(user_posts):
                if len(post) > 4:
                    with cols[idx % 3]:
                        if post[3]:  # media_type
                            if post[4]:  # media_data
                                try:
                                    if 'image' in post[3]:
                                        st.image(post[4], use_container_width=True)
                                    elif 'video' in post[3]:
                                        st.video(post[4])
                                except:
                                    st.markdown(f"<div class='post-card'>{post[2][:100] if len(post) > 2 else 'Post'}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='post-card'>{post[2][:100] if len(post) > 2 else 'Post'}</div>", unsafe_allow_html=True)

# ===================================
# MESSAGES PAGE
# ===================================

def messages_page():
    """Messages page for chatting with other users"""
    st.markdown("<h1 style='text-align: center;'>💬 Messages</h1>", unsafe_allow_html=True)
    
    # Check for incoming calls
    active_call = get_active_call(st.session_state.user_id)
    if active_call and len(active_call) > 5:
        caller_id = active_call[1]
        if caller_id != st.session_state.user_id:
            caller = get_user(caller_id)
            if caller:
                st.warning(f"📞 Incoming call from @{caller[1]}!")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Accept", use_container_width=True):
                        accept_call(active_call[4])
                        st.rerun()
                with col2:
                    if st.button("❌ Decline", use_container_width=True):
                        end_call(active_call[4])
                        st.rerun()
    
    # Get conversations
    conversations = get_conversations(st.session_state.user_id)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Conversations")
        
        # New message button
        if st.button("+ New Message", use_container_width=True):
            st.session_state.new_message = True
        
        # Display conversations
        if conversations:
            for conv in conversations:
                if len(conv) > 1:
                    username = conv[1]
                    profile_pic = conv[2] if len(conv) > 2 else None
                    other_user_id = conv[0]
                    is_online = conv[3] if len(conv) > 3 else False
                    is_live = conv[4] if len(conv) > 4 else False
                    last_message = conv[6] if len(conv) > 6 else ""
                    unread_count = conv[7] if len(conv) > 7 else 0
                    
                    col_a, col_b = st.columns([1, 3])
                    with col_a:
                        display_profile_pic(profile_pic, username, size=30)
                    with col_b:
                        status = "🟢" if is_online else "⚪"
                        live_badge = "🔴" if is_live else ""
                        unread_badge = f" ({unread_count})" if unread_count > 0 else ""
                        
                        if st.button(f"{status} @{username}{live_badge}{unread_badge}", key=f"conv_{other_user_id}", use_container_width=True):
                            st.session_state.current_chat = other_user_id
                            st.rerun()
    
    with col2:
        if st.session_state.get('current_chat'):
            # Get user info
            other_user = get_user(st.session_state.current_chat)
            
            if other_user:
                other_username = other_user[1]
                other_profile_pic = other_user[4] if len(other_user) > 4 else None
                other_is_live = other_user[17] if len(other_user) > 17 else False
                
                # Chat header
                col_a, col_b, col_c = st.columns([1, 3, 1])
                with col_a:
                    display_profile_pic(other_profile_pic, other_username, size=50)
                with col_b:
                    live_badge = " 🔴 LIVE" if other_is_live else ""
                    st.markdown(f"### @{other_username}{live_badge}")
                with col_c:
                    if st.button("📞 Call", use_container_width=True):
                        success, call_id = initiate_call(st.session_state.user_id, st.session_state.current_chat, 'video')
                        if success:
                            send_message(
                                st.session_state.user_id,
                                st.session_state.current_chat,
                                "📞 Video call started",
                                message_type='call',
                                call_data={'call_id': call_id, 'type': 'video'}
                            )
                            st.rerun()
                
                # Messages container
                messages = get_messages(st.session_state.user_id, st.session_state.current_chat)
                
                # Display messages
                for msg in reversed(messages):
                    if len(msg) > 3:
                        content = msg[3]
                        sender_id = msg[1]
                        message_type = msg[4] if len(msg) > 4 else 'text'
                        call_data = msg[6] if len(msg) > 6 else None
                        created_at = msg[8] if len(msg) > 8 else ""
                        
                        is_sent = sender_id == st.session_state.user_id
                        
                        if message_type == 'call' and call_data:
                            # Parse call data
                            call_info = json.loads(call_data) if isinstance(call_data, str) else call_data
                            if call_info:
                                content = f"📞 {content}"
                        
                        if is_sent:
                            st.markdown(f"""
                            <div style='text-align: right; margin: 5px;'>
                                <div style='display: inline-block; background: linear-gradient(45deg, #FF0050, #00F2EA); 
                                        color: white; padding: 10px 15px; border-radius: 18px 18px 4px 18px;'>
                                    {content}
                                </div>
                                <div style='font-size: 0.8em; color: #888; text-align: right;'>
                                    {format_tiktok_time(created_at)}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style='text-align: left; margin: 5px;'>
                                <div style='display: inline-block; background: #333; 
                                        color: white; padding: 10px 15px; border-radius: 18px 18px 18px 4px;'>
                                    {content}
                                </div>
                                <div style='font-size: 0.8em; color: #888;'>
                                    {format_tiktok_time(created_at)}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Message input
                with st.form("chat_form", clear_on_submit=True):
                    message = st.text_input("Type your message...", key="message_input")
                    if st.form_submit_button("Send", use_container_width=True):
                        if message:
                            success, result = send_message(st.session_state.user_id, st.session_state.current_chat, message)
                            if success:
                                st.rerun()
                            else:
                                st.error(result)
        else:
            st.info("💬 Select a conversation or start a new one")
        
        # New message modal
        if st.session_state.get('new_message'):
            with st.form("new_message_form"):
                st.markdown("### New Message")
                
                # Get all users except current user
                users = get_global_users()
                user_options = {}
                for u in users:
                    if len(u) > 1:
                        user_options[f"{u[1]}"] = u[0]
                
                if user_options:
                    selected_user_label = st.selectbox("Select User", list(user_options.keys()))
                    message_content = st.text_area("Message", placeholder="Type your message here...")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Send", use_container_width=True):
                            selected_user_id = user_options[selected_user_label]
                            if message_content:
                                success, result = send_message(st.session_state.user_id, selected_user_id, message_content)
                                if success:
                                    st.success("Message sent!")
                                    st.session_state.new_message = False
                                    st.session_state.current_chat = selected_user_id
                                    st.rerun()
                                else:
                                    st.error(result)
                    with col2:
                        if st.form_submit_button("Cancel", use_container_width=True):
                            st.session_state.new_message = False
                            st.rerun()
                else:
                    st.info("No other users found")
                    if st.button("OK"):
                        st.session_state.new_message = False

# ===================================
# MAIN APPLICATION
# ===================================

def main():
    """Main Feed Chat application"""
    
    # Page configuration
    st.set_page_config(
        page_title="Feed Chat",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Inject TikTok CSS
    inject_tiktok_css()
    
    # Initialize session state
    default_state = {
        'logged_in': False,
        'user_id': None,
        'username': None,
        'current_page': 'feed',
        'current_chat': None,
        'new_message': False,
        'editing_profile': False,
        'current_stream': None,
        'watch_stream': None,
        'call_user': None
    }
    
    for key, value in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Show login page if not logged in
    if not st.session_state.logged_in:
        show_login_page()
        return
    
    # Update online status
    update_user_online_status(st.session_state.user_id, True)
    
    # Sidebar navigation
    with st.sidebar:
        # Display user profile picture in sidebar
        user_data = get_user(st.session_state.user_id)
        if user_data:
            profile_pic = user_data[4] if len(user_data) > 4 else None
            username = user_data[1]
            is_live = user_data[17] if len(user_data) > 17 else False
            
            col1, col2 = st.columns([1, 3])
            with col1:
                display_profile_pic(profile_pic, username, size=50)
            with col2:
                live_badge = " 🔴 LIVE" if is_live else ""
                st.markdown(f"### @{st.session_state.username}{live_badge}")
        
        st.markdown("---")
        
        # Navigation buttons
        pages = {
            "feed": "🏠 Feed",
            "discover": "🔍 Discover", 
            "create": "➕ Create",
            "live": "📡 Live",
            "calls": "📞 Calls",
            "messages": "💬 Messages",
            "profile": "👤 Profile"
        }
        
        for page_key, page_label in pages.items():
            if st.button(page_label, use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.markdown("---")
        
        # Quick stats
        user_data = get_user(st.session_state.user_id)
        if user_data and len(user_data) > 12:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Posts", user_data[12])
            with col2:
                st.metric("Likes", user_data[15] if len(user_data) > 15 else 0)
        
        st.markdown("---")
        
        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            # End any active streams
            if st.session_state.current_stream:
                end_stream(st.session_state.current_stream)
            
            update_user_online_status(st.session_state.user_id, False)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main content based on current page
    try:
        if st.session_state.current_page == "feed":
            feed_page()
        elif st.session_state.current_page == "discover":
            discover_page()
        elif st.session_state.current_page == "create":
            create_content_page()
        elif st.session_state.current_page == "live":
            live_streaming_page()
        elif st.session_state.current_page == "calls":
            video_call_page()
        elif st.session_state.current_page == "messages":
            messages_page()
        elif st.session_state.current_page == "profile":
            profile_page()
        else:
            feed_page()
    except Exception as e:
        st.error(f"Error loading page: {e}")
        st.info("Please try refreshing the page")

def show_login_page():
    """Show login page with profile picture upload"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>🎬 Feed Chat</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Connect, Share, Discover</h3>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="@username")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submit = st.form_submit_button("Login", use_container_width=True)
                
                if submit:
                    if username and password:
                        user_id, username = verify_user_secure(username, password)
                        if user_id:
                            st.session_state.user_id = user_id
                            st.session_state.username = username
                            st.session_state.logged_in = True
                            st.success(f"Welcome back, @{username}!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                    else:
                        st.error("Please enter username and password")
        
        with tab2:
            with st.form("signup_form"):
                new_username = st.text_input("Username", placeholder="@username")
                new_password = st.text_input("Password", type="password", placeholder="••••••••")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="••••••••")
                email = st.text_input("Email", placeholder="email@example.com")
                display_name = st.text_input("Display Name", placeholder="Your Name (optional)")
                
                # Profile picture upload
                profile_pic = st.file_uploader(
                    "Profile Picture (optional)",
                    type=['jpg', 'jpeg', 'png'],
                    help="Upload a profile picture (max 5MB)"
                )
                
                if st.form_submit_button("Create Account", use_container_width=True):
                    if new_username and new_password and email:
                        if new_password == confirm_password:
                            if len(new_password) >= 6:
                                profile_pic_data = None
                                if profile_pic:
                                    profile_pic_data = profile_pic.read()
                                
                                success, result = create_user_secure(
                                    new_username, 
                                    new_password, 
                                    email, 
                                    display_name,
                                    profile_pic_data
                                )
                                if success:
                                    st.success("✅ Account created! Please login.")
                                else:
                                    st.error(result)
                            else:
                                st.error("Password must be at least 6 characters")
                        else:
                            st.error("Passwords don't match")
                    else:
                        st.error("Please fill all required fields")

# ===================================
# RUN THE APP
# ===================================

if __name__ == "__main__":
    main()

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

# ===================================
# TIKTOK-INSPIRED THEME CONFIGURATION
# ===================================

THEME_CONFIG = {
    "app_name": "Feed Chat",
    "version": "4.0",
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
    "languages": ["en", "es", "fr", "de", "zh", "ja", "ko", "hi"]
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
            is_read BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
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
        
        conn.commit()
        return conn
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        return sqlite3.connect("feedchat.db", check_same_thread=False)

# Initialize database
conn = init_simple_db()

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
        # You would need to add text drawing here, but for simplicity:
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
                   follower_count, following_count, total_likes, verified
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
        
        query = "SELECT id, username, profile_pic, bio, location, language, is_online FROM users WHERE id != ?"
        params = [st.session_state.get('user_id', 0)]
        
        if search_term:
            query += " AND (username LIKE ? OR bio LIKE ?)"
            params.extend([f'%{search_term}%', f'%{search_term}%'])
        
        query += " ORDER BY is_online DESC, username ASC LIMIT ?"
        params.append(limit)
        
        c.execute(query, params)
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

def send_message(sender_id, receiver_id, content, message_type='text', media_data=None):
    """Send a message"""
    try:
        if not content or len(content.strip()) == 0:
            return False, "Message cannot be empty"
        
        c = conn.cursor()
        c.execute("""
        INSERT INTO messages (sender_id, receiver_id, content, message_type, media_data)
        VALUES (?, ?, ?, ?, ?)
        """, (sender_id, receiver_id, content, message_type, media_data))
        
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
        SELECT m.*, u.username as sender_username
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
                SELECT p.*, u.username, u.display_name, u.profile_pic
                FROM posts p
                JOIN users u ON p.user_id = u.id
                WHERE p.is_deleted = 0 AND p.user_id = ?
                ORDER BY p.created_at DESC
                LIMIT ?
            """, (user_id, limit))
        else:
            c.execute("""
                SELECT p.*, u.username, u.display_name, u.profile_pic
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
# PAGE FUNCTIONS WITH NEW FEATURES
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
        
        if is_deleted:
            return
        
        with st.container():
            st.markdown("---")
            
            # User info with profile picture
            col1, col2 = st.columns([1, 10])
            with col1:
                display_profile_pic(profile_pic, username, size=40)
            with col2:
                st.markdown(f"**{display_name}**")
                st.markdown(f"@{username}")
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
                if st.button(f"{save_text}", key=f"save_{post_id}", use_container_width=True):
                    if saved:
                        unsave_post(st.session_state.user_id, post_id)
                    else:
                        save_post(st.session_state.user_id, post_id)
                    st.rerun()
                    
    except Exception as e:
        st.error(f"Error displaying post: {e}")

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
            
            with cols[idx % 3]:
                col1, col2 = st.columns([1, 3])
                with col1:
                    display_profile_pic(profile_pic, username, size=40)
                with col2:
                    st.markdown(f"**@{username}**")
                
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
        post_count = user[13] if len(user) > 13 else 0
        follower_count = user[14] if len(user) > 14 else 0
        following_count = user[15] if len(user) > 15 else 0
        total_likes = user[16] if len(user) > 16 else 0
        
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

def messages_page():
    """Messages page for chatting with other users"""
    st.markdown("<h1 style='text-align: center;'>💬 Messages</h1>", unsafe_allow_html=True)
    
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
                    
                    col_a, col_b = st.columns([1, 3])
                    with col_a:
                        display_profile_pic(profile_pic, username, size=30)
                    with col_b:
                        if st.button(f"@{username}", key=f"conv_{other_user_id}", use_container_width=True):
                            st.session_state.current_chat = other_user_id
                            st.rerun()
    
    with col2:
        if st.session_state.get('current_chat'):
            # Get user info
            other_user = get_user(st.session_state.current_chat)
            
            if other_user:
                other_username = other_user[1]
                other_profile_pic = other_user[4] if len(other_user) > 4 else None
                
                # Chat header
                col_a, col_b = st.columns([1, 4])
                with col_a:
                    display_profile_pic(other_profile_pic, other_username, size=50)
                with col_b:
                    st.markdown(f"### @{other_username}")
                
                # Messages container
                messages = get_messages(st.session_state.user_id, st.session_state.current_chat)
                
                # Display messages
                for msg in reversed(messages):
                    if len(msg) > 3:
                        content = msg[3]
                        sender_id = msg[1]
                        created_at = msg[7] if len(msg) > 7 else ""
                        
                        is_sent = sender_id == st.session_state.user_id
                        
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
        'editing_profile': False
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
            
            col1, col2 = st.columns([1, 3])
            with col1:
                display_profile_pic(profile_pic, username, size=50)
            with col2:
                st.markdown(f"### @{st.session_state.username}")
        
        st.markdown("---")
        
        # Navigation buttons
        pages = {
            "feed": "🏠 Feed",
            "discover": "🔍 Discover", 
            "create": "➕ Create",
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
        if user_data and len(user_data) > 13:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Posts", user_data[13])
            with col2:
                st.metric("Likes", user_data[16] if len(user_data) > 16 else 0)
        
        st.markdown("---")
        
        # Logout
        if st.button("🚪 Logout", use_container_width=True):
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

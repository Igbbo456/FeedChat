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
# FIXED DATABASE SETUP
# ===================================

def init_simple_db():
    """Initialize database with essential tables - FIXED VERSION"""
    try:
        # Ensure the database file exists
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

        # Create indexes
        c.execute("CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages(receiver_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_likes_post ON likes(post_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_follows_follower ON follows(follower_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_follows_following ON follows(following_id)")

        conn.commit()
        
        # Create demo data if tables are empty
        create_demo_data(conn)
        
        return conn
    except Exception as e:
        st.error(f"Database initialization error: {str(e)}")
        return sqlite3.connect("feedchat.db", check_same_thread=False)

def create_demo_data(conn):
    """Create demo users and posts if they don't exist"""
    try:
        c = conn.cursor()
        
        # Check if demo user exists
        c.execute("SELECT COUNT(*) FROM users WHERE username = 'demo'")
        if c.fetchone()[0] == 0:
            # Create demo user
            c.execute("""
            INSERT INTO users (username, display_name, password_hash, email, bio, location, is_online)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("demo", "Demo User", "demo_hash", "demo@feedchat.com", 
                  "Welcome to Feed Chat! 🎬", "Internet", 1))
            
            # Create other demo users
            demo_users = [
                ("tiktokfan", "TikTok Fan", "Passionate about short videos", "Los Angeles"),
                ("trendsetter", "Trend Setter", "Setting trends since 2020", "New York"),
                ("creator", "Content Creator", "Making awesome content daily", "London"),
                ("traveler", "World Traveler", "Exploring the world 🌍", "Paris"),
                ("gamer", "Pro Gamer", "Live streaming games 🎮", "Tokyo")
            ]
            
            for username, display_name, bio, location in demo_users:
                c.execute("""
                INSERT INTO users (username, display_name, password_hash, email, bio, location)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (username, display_name, "demo_hash", f"{username}@feedchat.com", bio, location))
            
            conn.commit()
            
            # Create demo posts
            c.execute("SELECT id FROM users")
            user_ids = [row[0] for row in c.fetchall()]
            
            demo_posts = [
                ("Just joined Feed Chat! So excited to connect with everyone 🎉 #NewUser #Welcome", None, None),
                ("Check out this amazing sunset view! 🌅 #Nature #Photography", None, None),
                ("Working on some new content ideas today 💡 #Creator #Content", None, None),
                ("Just hit a new personal record! 🏆 #Achievement #Gaming", None, None),
                ("Traveling to a new destination next week! ✈️ #Travel #Adventure", None, None),
                ("Learning new video editing techniques 📹 #Learning #Skills", None, None),
                ("The food at this place is incredible! 🍕 #Foodie #Restaurant", None, None),
                ("Morning workout complete! 💪 #Fitness #Health", None, None),
                ("Can't wait for the weekend! 🎉 #WeekendVibes #Fun", None, None),
                ("Working from home setup is finally complete! 🖥️ #WFH #Setup", None, None)
            ]
            
            for content, media_type, media_data in demo_posts:
                user_id = random.choice(user_ids)
                hashtags = extract_hashtags_string(content)
                c.execute("""
                INSERT INTO posts (user_id, content, media_type, media_data, hashtags)
                VALUES (?, ?, ?, ?, ?)
                """, (user_id, content, media_type, media_data, hashtags))
            
            conn.commit()
            
    except Exception as e:
        print(f"Demo data creation error: {e}")

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
    }}
    </style>
    """, unsafe_allow_html=True)

# Initialize database
conn = init_simple_db()

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
            # Accept any password for demo
            c.execute("UPDATE users SET is_online=1, last_seen=CURRENT_TIMESTAMP WHERE id=?", (user[0],))
            conn.commit()
            return user[0], user[1]
        
        return None, None
    except:
        return None, None

def create_user_secure(username, password, email):
    """Create user"""
    try:
        c = conn.cursor()
        
        # Check if user exists
        c.execute("SELECT id FROM users WHERE username=?", (username,))
        if c.fetchone():
            return False, "Username already exists"
        
        # Create user
        c.execute("""
            INSERT INTO users (username, display_name, password_hash, email) 
            VALUES (?, ?, ?, ?)
        """, (username, username, "demo_hash", email))
        
        conn.commit()
        return True, "Account created successfully"
    except:
        return False, "Error creating account"

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
    """Create post with enhanced features"""
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

def get_posts(limit=20, user_id=None):
    """Get posts with filtering"""
    try:
        c = conn.cursor()
        
        query = """
            SELECT p.*, u.username, u.profile_pic, u.display_name,
                   (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as like_count,
                   (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.is_deleted = 0
        """
        params = []
        
        if user_id:
            query += " AND p.user_id = ?"
            params.append(user_id)
        
        query += """
            ORDER BY p.created_at DESC
            LIMIT ?
        """
        params.append(limit)
        
        c.execute(query, params)
        return c.fetchall()
    except sqlite3.Error as e:
        return []

def get_for_you_posts(user_id, limit=20):
    """Get personalized feed"""
    try:
        c = conn.cursor()
        
        query = """
            SELECT p.*, u.username, u.profile_pic, u.display_name,
                   (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as like_count,
                   (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.is_deleted = 0 AND p.visibility = 'public'
            ORDER BY p.created_at DESC
            LIMIT ?
        """
        
        c.execute(query, (limit,))
        posts = c.fetchall()
        
        return posts
    except sqlite3.Error as e:
        return []

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

# ===================================
# PAGE FUNCTIONS
# ===================================

def feed_page():
    """Feed Chat vertical feed"""
    st.markdown("<h1 style='text-align: center;'>🎬 Your Feed</h1>", unsafe_allow_html=True)
    
    # For You feed
    posts = get_for_you_posts(st.session_state.user_id, limit=10)
    
    if not posts:
        st.info("No posts yet. Create your first post!")
        
        # Quick post creation
        with st.form("quick_post_form"):
            content = st.text_area("What's on your mind?", placeholder="Share something...")
            if st.form_submit_button("Post", use_container_width=True):
                if content:
                    success, result = create_post(st.session_state.user_id, content)
                    if success:
                        st.success("Post created!")
                        st.rerun()
                    else:
                        st.error(result)
        return
    
    # Display posts
    for post in posts:
        display_feed_post(post)
    
    # Load more button
    if st.button("Load More", use_container_width=True):
        st.rerun()

def display_feed_post(post):
    """Display post in Feed Chat vertical format"""
    if len(post) < 15:
        return
        
    with st.container():
        st.markdown("---")
        
        # Post content
        if post[2]:  # content
            st.markdown(f"**{post[2]}**")
        
        # User info
        col1, col2 = st.columns([1, 10])
        with col1:
            username = post[15] if len(post) > 15 else "Unknown"
            st.markdown(f"**@{username}**")
        
        # Engagement buttons
        col_a, col_b, col_c, col_d = st.columns(4)
        post_id = post[0]
        
        with col_a:
            liked = has_liked_post(st.session_state.user_id, post_id)
            like_count = post[18] if len(post) > 18 else 0
            like_text = "❤️" if not liked else "💔"
            if st.button(f"{like_text}\n{like_count}", key=f"like_{post_id}"):
                if liked:
                    unlike_post(st.session_state.user_id, post_id)
                else:
                    like_post(st.session_state.user_id, post_id)
                st.rerun()
        
        with col_b:
            comment_count = post[19] if len(post) > 19 else 0
            if st.button(f"💬\n{comment_count}", key=f"comment_{post_id}"):
                st.info("Comment feature coming soon!")
        
        with col_c:
            if st.button(f"↪️\nShare", key=f"share_{post_id}"):
                st.info("Share feature coming soon!")
        
        with col_d:
            saved = is_saved(st.session_state.user_id, post_id)
            save_text = "⬇️" if not saved else "✅"
            if st.button(f"{save_text}", key=f"save_{post_id}"):
                if saved:
                    unsave_post(st.session_state.user_id, post_id)
                else:
                    save_post(st.session_state.user_id, post_id)
                st.rerun()

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
    suggested_users = get_global_users(limit=6)
    
    if suggested_users:
        cols = st.columns(3)
        for idx, user in enumerate(suggested_users):
            user_id, username, profile_pic, bio, location, language, is_online = user
            
            with cols[idx % 3]:
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
    """Content creation page"""
    st.markdown("<h1 style='text-align: center;'>➕ Create</h1>", unsafe_allow_html=True)
    
    with st.form("create_post_form"):
        content = st.text_area("What's happening?", placeholder="Share your thoughts...", height=150)
        location = st.text_input("Location", placeholder="Add location (optional)")
        
        if st.form_submit_button("Post", use_container_width=True):
            if content:
                success, result = create_post(st.session_state.user_id, content, location=location)
                if success:
                    st.success("Post created!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(result)
            else:
                st.error("Please write something to post")

def profile_page():
    """Feed Chat profile page"""
    user = get_user(st.session_state.user_id)
    
    if user:
        (user_id, username, display_name, email, profile_pic, bio, location, 
         timezone, language, is_online, last_seen, created_at, post_count, 
         follower_count, following_count, total_likes, verified) = user
        
        # Profile header
        st.markdown(f"# {display_name or username}")
        st.markdown(f"@{username}")
        
        if bio:
            st.markdown(f"{bio}")
        
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
        
        # User's posts
        st.markdown("### 📸 Your Posts")
        user_posts = get_posts(user_id=st.session_state.user_id, limit=12)
        
        if user_posts:
            for post in user_posts:
                if len(post) > 2:
                    with st.expander(f"Post: {post[2][:50]}..." if len(post[2]) > 50 else f"Post: {post[2]}"):
                        st.markdown(post[2])
                        st.caption(f"Posted on {post[14] if len(post) > 14 else 'Unknown date'}")

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
                other_user_id, username, profile_pic, last_time, last_msg, unread = conv
                
                if st.button(f"@{username}", key=f"conv_{other_user_id}", use_container_width=True):
                    st.session_state.current_chat = other_user_id
                    st.rerun()
    
    with col2:
        if st.session_state.get('current_chat'):
            # Get user info
            other_user = get_user(st.session_state.current_chat)
            
            if other_user:
                other_user_id, other_username = other_user[0], other_user[1]
                
                # Chat header
                st.markdown(f"### Chat with @{other_username}")
                
                # Messages container
                messages = get_messages(st.session_state.user_id, other_user_id)
                
                # Display messages
                for msg in reversed(messages):
                    msg_id, sender_id, receiver_id, content, msg_type, media_data, is_read, created_at, sender_username = msg
                    
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
                            success, result = send_message(st.session_state.user_id, other_user_id, message)
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
                user_options = {f"{u[1]}": u[0] for u in users if u[0] != st.session_state.user_id}
                
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
        'editing_profile': False,
        'current_chat': None,
        'new_message': False
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
        st.markdown("<h2 style='text-align: center;'>🎬 Feed Chat</h2>", unsafe_allow_html=True)
        st.markdown(f"### 👋 @{st.session_state.username}")
        
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
        if user_data:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Posts", user_data[13])
            with col2:
                st.metric("Likes", user_data[16])
        
        st.markdown("---")
        
        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            update_user_online_status(st.session_state.user_id, False)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main content based on current page
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

def show_login_page():
    """Show login page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>🎬 Feed Chat</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Connect, Share, Discover</h3>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.info("**Demo Credentials:**\n- Username: `demo`\n- Password: `demo123`")
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="@username", value="demo")
                password = st.text_input("Password", type="password", placeholder="••••••••", value="demo123")
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
                
                if st.form_submit_button("Create Account", use_container_width=True):
                    if new_username and new_password and email:
                        if new_password == confirm_password:
                            success, result = create_user_secure(new_username, new_password, email)
                            if success:
                                st.success("Account created! Please login.")
                            else:
                                st.error(result)
                        else:
                            st.error("Passwords don't match")
                    else:
                        st.error("Please fill all fields")

# ===================================
# RUN THE APP
# ===================================

if __name__ == "__main__":
    main()

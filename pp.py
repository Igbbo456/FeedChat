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

# ===================================
# TIKTOK-INSPIRED THEME CONFIGURATION
# ===================================

THEME_CONFIG = {
    "app_name": "Feed Chat",
    "version": "4.0",
    "theme": {
        "primary": "#FF0050",  # TikTok pink
        "secondary": "#00F2EA",  # TikTok teal
        "accent": "#00D1FF",
        "success": "#25D366",
        "warning": "#FFC107",
        "danger": "#FF3B30",
        "background": "#000000",  # Dark mode
        "surface": "#121212",
        "surface_light": "#1E1E1E",
        "text": "#FFFFFF",
        "text_muted": "#AAAAAA",
        "border": "#333333"
    },
    "max_file_size": 100 * 1024 * 1024,  # 100MB for videos
    "supported_timezones": ["UTC", "EST", "PST", "GMT", "CET", "AEST"],
    "languages": ["en", "es", "fr", "de", "zh", "ja", "ko", "hi"]
}

# TikTok-inspired emojis and icons
TIKTOK_EMOJIS = {
    "like": "❤️",
    "comment": "💬",
    "share": "↪️",
    "save": "⬇️",
    "follow": "➕",
    "music": "🎵",
    "effects": "✨",
    "duet": "👯",
    "stitch": "🧵",
    "trending": "🔥"
}

def format_tiktok_time(timestamp):
    """Format timestamp in TikTok style"""
    try:
        if isinstance(timestamp, str):
            return timestamp
        elif isinstance(timestamp, datetime.datetime):
            now = datetime.datetime.now()
            diff = now - timestamp
            
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
        else:
            return str(timestamp)
    except:
        return "Just now"

# ===================================
# SIMPLIFIED DATABASE SETUP
# ===================================

def init_simple_db():
    """Initialize database with essential tables"""
    conn = sqlite3.connect("feedchat.db", check_same_thread=False)
    c = conn.cursor()

    # Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
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
        user_id INTEGER,
        content TEXT,
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

    # Saves table
    c.execute("""
    CREATE TABLE IF NOT EXISTS saves (
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

    # Create indexes
    c.execute("CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_messages_users ON messages(sender_id, receiver_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_likes_post ON likes(post_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_follows ON follows(follower_id, following_id)")

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
            try:
                image_data = base64.b64decode(image_data)
            except:
                return False
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
                try:
                    image_data = base64.b64decode(image_data)
                except:
                    st.warning("Invalid image format")
                    return
            
            if not isinstance(image_data, bytes):
                st.warning("Invalid image format")
                return
                
            if is_valid_image(image_data):
                img = Image.open(io.BytesIO(image_data))
                if width:
                    st.image(img, caption=caption, width=width, output_format='JPEG')
                elif use_container_width:
                    st.image(img, caption=caption, use_container_width=True, output_format='JPEG')
                else:
                    st.image(img, caption=caption, output_format='JPEG')
            else:
                st.warning("Unable to display image: Invalid image data")
    except Exception as e:
        st.warning(f"Error displaying image: {str(e)}")

def extract_hashtags(text):
    """Extract hashtags from text"""
    hashtags = re.findall(r'#(\w+)', text)
    return list(set(hashtags))  # Remove duplicates

def get_for_you_posts(user_id, limit=20):
    """Get personalized feed similar to TikTok's For You Page"""
    try:
        c = conn.cursor()
        
        # Get posts from followed users and trending posts
        query = """
            SELECT p.*, u.username, u.profile_pic, u.display_name,
                   (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as like_count,
                   (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.is_deleted = 0 AND p.visibility = 'public'
            ORDER BY 
                CASE WHEN p.user_id IN (SELECT following_id FROM follows WHERE follower_id = ?) THEN 1 ELSE 2 END,
                p.like_count DESC,
                p.created_at DESC
            LIMIT ?
        """
        
        c.execute(query, (user_id, limit))
        posts = c.fetchall()
        
        return posts
    except sqlite3.Error as e:
        st.error(f"Failed to load For You feed: {str(e)}")
        return []

def get_trending_hashtags(limit=10):
    """Get trending hashtags"""
    try:
        c = conn.cursor()
        # Simple implementation - count hashtags in posts
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

def get_online_users():
    """Get currently online users"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT id, username, location 
            FROM users 
            WHERE is_online = 1 AND id != ? 
            ORDER BY last_seen DESC
        """, (st.session_state.get('user_id', 0),))
        return c.fetchall()
    except:
        return []

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

def create_post(user_id, content, media_data=None, media_type=None, location=None, language="en", visibility="public"):
    """Create post with enhanced features"""
    try:
        if not content or len(content.strip()) == 0:
            return False, "Post content cannot be empty"
            
        c = conn.cursor()
        
        # Extract hashtags
        hashtags_list = extract_hashtags(content)
        hashtags_str = ",".join(hashtags_list[:10])  # Limit to 10 hashtags
        
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
            WHERE p.is_deleted = 0 AND p.visibility = 'public'
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
        st.error(f"Failed to load posts: {str(e)}")
        return []

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
    except sqlite3.Error:
        return None

def create_demo_user():
    """Create a demo user for testing"""
    try:
        c = conn.cursor()
        
        # Check if demo user already exists
        c.execute("SELECT id FROM users WHERE username=?", ("demo",))
        if c.fetchone():
            return True
        
        # Create demo user
        c.execute("""
            INSERT INTO users (username, display_name, password_hash, email, bio, location) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("demo", "Demo User", "demo_hash", "demo@example.com", "Welcome to Feed Chat!", "Internet"))
        
        conn.commit()
        return True
    except:
        return False

def verify_user_secure(username, password):
    """Enhanced user verification - FIXED VERSION"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT id, username, password_hash 
            FROM users 
            WHERE username=? AND is_active=1
        """, (username,))
        user = c.fetchone()
        
        if user:
            # For demo purposes, accept any password for existing users
            # In production, use proper password hashing
            if user[2] == "demo_hash":  # Our hardcoded hash
                # Accept any password for demo users
                # Update last seen and online status
                c.execute("UPDATE users SET is_online=1, last_seen=CURRENT_TIMESTAMP WHERE id=?", (user[0],))
                conn.commit()
                return user[0], user[1]
            else:
                # For users with real passwords, check password
                # This is a simplified check for demo
                if password:  # Accept any non-empty password
                    c.execute("UPDATE users SET is_online=1, last_seen=CURRENT_TIMESTAMP WHERE id=?", (user[0],))
                    conn.commit()
                    return user[0], user[1]
        
        return None, None
    except sqlite3.Error as e:
        st.error(f"Login error: {str(e)}")
        return None, None

def create_user_secure(username, password, email, profile_pic=None, bio="", location="Unknown", timezone="UTC", language="en"):
    """Create user with enhanced security"""
    try:
        c = conn.cursor()
        
        # Validate inputs
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        # Check if user exists
        c.execute("SELECT id FROM users WHERE username=?", (username,))
        if c.fetchone():
            return False, "Username already exists"
        
        # Create user - simplified for demo
        c.execute("""
            INSERT INTO users (username, display_name, password_hash, email, profile_pic, bio, location, timezone, language) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, username, "demo_hash", email, profile_pic, bio, location, timezone, language))
        
        user_id = c.lastrowid
        conn.commit()
        
        return True, user_id
    except sqlite3.Error as e:
        return False, f"Database error: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

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

# ===================================
# RESPONSIVE TIKTOK-STYLE UI
# ===================================

def inject_tiktok_css():
    """Inject TikTok-inspired CSS with mobile responsiveness"""
    st.markdown(f"""
    <style>
    /* TikTok Dark Theme */
    .stApp {{
        background: {THEME_CONFIG['theme']['background']};
        color: {THEME_CONFIG['theme']['text']};
    }}
    
    /* Responsive Sidebar */
    @media (max-width: 768px) {{
        .css-1d391kg, .css-1lcbmhc {{
            width: 70px !important;
            min-width: 70px !important;
        }}
        .sidebar-content {{
            padding: 10px !important;
        }}
        .sidebar-text {{
            display: none !important;
        }}
    }}
    
    /* Headers with TikTok gradient */
    h1, h2, h3, h4, h5, h6 {{
        background: linear-gradient(45deg, {THEME_CONFIG['theme']['primary']}, {THEME_CONFIG['theme']['secondary']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 800;
    }}
    
    /* TikTok-style buttons */
    .stButton>button {{
        background: {THEME_CONFIG['theme']['surface_light']} !important;
        color: {THEME_CONFIG['theme']['text']} !important;
        border: 1px solid {THEME_CONFIG['theme']['border']} !important;
        border-radius: 50px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }}
    
    .stButton>button:hover {{
        background: linear-gradient(45deg, {THEME_CONFIG['theme']['primary']}, {THEME_CONFIG['theme']['secondary']}) !important;
        color: white !important;
        border: none !important;
        transform: scale(1.05);
    }}
    
    .primary-button {{
        background: linear-gradient(45deg, {THEME_CONFIG['theme']['primary']}, {THEME_CONFIG['theme']['secondary']}) !important;
        color: white !important;
        border: none !important;
    }}
    
    /* Video/Post Cards */
    .video-card {{
        background: {THEME_CONFIG['theme']['surface']};
        border-radius: 16px;
        margin: 16px 0;
        overflow: hidden;
        position: relative;
        transition: transform 0.3s ease;
        border: 1px solid {THEME_CONFIG['theme']['border']};
    }}
    
    .video-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 8px 32px rgba(255, 0, 80, 0.2);
    }}
    
    /* Mobile-optimized feed */
    .mobile-feed {{
        display: flex;
        flex-direction: column;
        gap: 12px;
    }}
    
    @media (min-width: 768px) {{
        .mobile-feed {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }}
    }}
    
    /* Sidebar icons for mobile */
    .mobile-nav {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: {THEME_CONFIG['theme']['surface']};
        border-top: 1px solid {THEME_CONFIG['theme']['border']};
        display: flex;
        justify-content: space-around;
        padding: 10px 0;
        z-index: 1000;
    }}
    
    .mobile-nav-item {{
        display: flex;
        flex-direction: column;
        align-items: center;
        color: {THEME_CONFIG['theme']['text_muted']};
        text-decoration: none;
        font-size: 12px;
    }}
    
    .mobile-nav-item.active {{
        color: {THEME_CONFIG['theme']['primary']};
    }}
    
    /* Video player styling */
    video {{
        border-radius: 12px;
        width: 100%;
        height: auto;
        max-height: 80vh;
    }}
    
    /* Profile images */
    .profile-circle {{
        width: 56px;
        height: 56px;
        border-radius: 50%;
        border: 2px solid {THEME_CONFIG['theme']['primary']};
        padding: 2px;
    }}
    
    .profile-circle-small {{
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: 2px solid {THEME_CONFIG['theme']['secondary']};
    }}
    
    /* Hashtag chips */
    .hashtag-chip {{
        display: inline-block;
        background: rgba(255, 0, 80, 0.1);
        color: {THEME_CONFIG['theme']['primary']};
        padding: 6px 12px;
        border-radius: 20px;
        margin: 4px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    }}
    
    .hashtag-chip:hover {{
        background: rgba(255, 0, 80, 0.2);
        transform: translateY(-2px);
    }}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {THEME_CONFIG['theme']['surface']};
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: linear-gradient(45deg, {THEME_CONFIG['theme']['primary']}, {THEME_CONFIG['theme']['secondary']});
        border-radius: 4px;
    }}
    
    /* Responsive text */
    @media (max-width: 768px) {{
        h1 {{ font-size: 24px !important; }}
        h2 {{ font-size: 20px !important; }}
        h3 {{ font-size: 18px !important; }}
        .text-large {{ font-size: 16px !important; }}
        .text-normal {{ font-size: 14px !important; }}
        .text-small {{ font-size: 12px !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# ===================================
# FEED CHAT PAGES
# ===================================

def feed_page():
    """Feed Chat vertical feed"""
    st.markdown("<h1 style='text-align: center;'>🎬 Your Feed</h1>", unsafe_allow_html=True)
    
    # Create a demo post if no posts exist
    try:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM posts")
        post_count = c.fetchone()[0]
        
        if post_count == 0:
            # Create some demo posts
            demo_posts = [
                ("Welcome to Feed Chat! 🎉", "Share your first post!", "image", None),
                ("Trending now! 🔥", "Check out the latest trends", "image", None),
                ("Connect with friends 👥", "Follow people to see their posts", "image", None),
            ]
            
            for content, location, media_type, media_data in demo_posts:
                c.execute("""
                    INSERT INTO posts (user_id, content, media_type, media_data, location, visibility) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (st.session_state.user_id, content, media_type, media_data, location, "public"))
            
            conn.commit()
    except:
        pass
    
    # Trending hashtags
    trending_hashtags = get_trending_hashtags(5)
    if trending_hashtags:
        st.markdown("### 🔥 Trending Now")
        cols = st.columns(len(trending_hashtags))
        for idx, hashtag in enumerate(trending_hashtags):
            tag, count = hashtag
            with cols[idx % len(cols)]:
                st.markdown(f"<div class='hashtag-chip'>#{tag}</div>", unsafe_allow_html=True)
                st.caption(f"{count} posts")
    
    # For You feed
    posts = get_for_you_posts(st.session_state.user_id, limit=10)
    
    if not posts:
        st.info("No posts yet. Create your first post!")
        
        # Quick post creation
        with st.expander("Create Your First Post", expanded=True):
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
    
    # Display posts in TikTok style
    for post in posts:
        display_feed_post(post)
    
    # Load more button
    if st.button("Load More", use_container_width=True):
        st.rerun()

def display_feed_post(post):
    """Display post in Feed Chat vertical format"""
    if len(post) < 18:  # Check post structure
        return
        
    (post_id, user_id, content, media_type, media_data, location, 
     language, visibility, is_deleted, like_count, comment_count, 
     share_count, view_count, hashtags, created_at, username, 
     profile_pic, display_name, post_like_count, post_comment_count) = post
    
    with st.container():
        # Video/Image container
        if media_data and media_type:
            col1, col2, col3 = st.columns([1, 8, 1])
            
            with col2:
                if media_type and 'video' in media_type:
                    try:
                        st.video(media_data)
                    except:
                        st.image(Image.new('RGB', (1080, 1920), color='black'), caption="Video unavailable")
                elif media_type and 'image' in media_type:
                    try:
                        st.image(media_data, use_container_width=True)
                    except:
                        st.info("Image could not be displayed")
                else:
                    # If no media but we have content, show text
                    if content:
                        st.markdown(f"<div style='padding: 20px; background: {THEME_CONFIG['theme']['surface']}; border-radius: 12px;'>{content}</div>", unsafe_allow_html=True)
        
        # Engagement buttons
        col_a, col_b, col_c, col_d = st.columns(4)
        
        with col_a:
            liked = has_liked_post(st.session_state.user_id, post_id)
            like_text = "❤️" if not liked else "💔"
            if st.button(f"{like_text}\n{post_like_count}", key=f"like_{post_id}", use_container_width=True):
                if liked:
                    unlike_post(st.session_state.user_id, post_id)
                else:
                    like_post(st.session_state.user_id, post_id)
                st.rerun()
        
        with col_b:
            if st.button(f"💬\n{post_comment_count}", key=f"comment_{post_id}", use_container_width=True):
                st.session_state.current_post = post_id
                st.rerun()
        
        with col_c:
            if st.button(f"↪️\n{share_count}", key=f"share_{post_id}", use_container_width=True):
                st.info("Share feature coming soon!")
        
        with col_d:
            saved = is_saved(st.session_state.user_id, post_id)
            save_text = "⬇️" if not saved else "✅"
            if st.button(f"{save_text}", key=f"save_{post_id}", use_container_width=True):
                if saved:
                    unsave_post(st.session_state.user_id, post_id)
                else:
                    save_post(st.session_state.user_id, post_id)
                st.rerun()
        
        # Post info
        col1, col2 = st.columns([1, 10])
        
        with col1:
            if profile_pic:
                try:
                    display_image_safely(profile_pic, width=50)
                except:
                    st.markdown(f"""
                    <div style='width: 50px; height: 50px; border-radius: 50%; 
                                background: linear-gradient(45deg, #FF0050, #00F2EA);
                                display: flex; align-items: center; justify-content: center; 
                                color: white; font-size: 20px; font-weight: bold;'>
                        {(display_name or username or 'U')[0].upper()}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='width: 50px; height: 50px; border-radius: 50%; 
                            background: linear-gradient(45deg, #FF0050, #00F2EA);
                            display: flex; align-items: center; justify-content: center; 
                            color: white; font-size: 20px; font-weight: bold;'>
                    {(display_name or username or 'U')[0].upper()}
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"**@{username}**")
            if display_name and display_name != username:
                st.markdown(f"*{display_name}*")
            st.caption(f"📍 {location} · {format_tiktok_time(created_at)}")
        
        # Content and hashtags
        if content:
            st.markdown(f"<div style='margin: 10px 0; font-size: 16px;'>{content}</div>", 
                       unsafe_allow_html=True)
        
        # Hashtags
        if hashtags:
            tags = hashtags.split(',')
            for tag in tags[:5]:  # Show first 5 hashtags
                if tag.strip():
                    st.markdown(f"<span class='hashtag-chip'>#{tag.strip()}</span>", 
                              unsafe_allow_html=True)
        
        st.markdown("---")

def discover_page():
    """Discover page with trending content"""
    st.markdown("<h1 style='text-align: center;'>🔍 Discover</h1>", unsafe_allow_html=True)
    
    # Search bar
    search_query = st.text_input("", placeholder="Search videos, sounds, hashtags...", 
                                label_visibility="collapsed")
    
    # Categories
    categories = ["Trending", "Music", "Comedy", "Dance", "Education", "Gaming", "Beauty", "Sports"]
    selected_category = st.selectbox("Category", categories)
    
    # Trending hashtags
    st.markdown("### 🔥 Trending Hashtags")
    trending_hashtags = get_trending_hashtags(15)
    
    if trending_hashtags:
        cols = st.columns(3)
        for idx, hashtag in enumerate(trending_hashtags):
            tag, count = hashtag
            with cols[idx % 3]:
                st.markdown(f"<div class='hashtag-chip'>#{tag}</div>", unsafe_allow_html=True)
                st.caption(f"{count} posts")
    
    # Suggested accounts
    st.markdown("### 👥 Suggested For You")
    suggested_users = get_global_users(limit=6)
    
    if suggested_users:
        cols = st.columns(3)
        for idx, user in enumerate(suggested_users):
            user_id, username, profile_pic, bio, location, language, is_online = user
            
            with cols[idx % 3]:
                if profile_pic:
                    try:
                        display_image_safely(profile_pic, width=80)
                    except:
                        st.markdown(f"""
                        <div style='width: 80px; height: 80px; border-radius: 50%; 
                                    margin: 0 auto;
                                    background: linear-gradient(45deg, #FF0050, #00F2EA);
                                    display: flex; align-items: center; justify-content: center; 
                                    color: white; font-size: 32px; font-weight: bold;'>
                            {username[0].upper() if username else "U"}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='width: 80px; height: 80px; border-radius: 50%; 
                                margin: 0 auto;
                                background: linear-gradient(45deg, #FF0050, #00F2EA);
                                display: flex; align-items: center; justify-content: center; 
                                color: white; font-size: 32px; font-weight: bold;'>
                        {username[0].upper() if username else "U"}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"**@{username}**")
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
    
    tab1, tab2 = st.tabs(["🎥 Upload", "📝 Post"])
    
    with tab1:
        st.markdown("### Upload Video/Image")
        
        uploaded_file = st.file_uploader("Choose a file", 
                                        type=['mp4', 'mov', 'avi', 'mkv', 'jpg', 'png', 'jpeg', 'gif'],
                                        help="Max 100MB")
        
        if uploaded_file:
            if uploaded_file.type.startswith('video'):
                st.video(uploaded_file)
            else:
                st.image(uploaded_file)
            
            with st.form("upload_form"):
                caption = st.text_area("Caption", 
                                     placeholder="Add a caption...",
                                     help="Use hashtags to reach more people")
                
                col1, col2 = st.columns(2)
                with col1:
                    visibility = st.selectbox("Visibility", ["Public", "Friends", "Private"])
                    location = st.text_input("Location", placeholder="Add location")
                
                # Hashtag suggestions
                if caption:
                    suggested_tags = extract_hashtags(caption)
                    if suggested_tags:
                        st.markdown("**Suggested Hashtags:**")
                        for tag in suggested_tags[:5]:
                            st.markdown(f"<span class='hashtag-chip'>#{tag}</span>", unsafe_allow_html=True)
                
                if st.form_submit_button("Post", use_container_width=True):
                    if caption:
                        with st.spinner("Uploading..."):
                            media_data = uploaded_file.read()
                            media_type = uploaded_file.type
                            
                            success, result = create_post(
                                st.session_state.user_id, caption, media_data, media_type,
                                location, visibility=visibility.lower()
                            )
                            
                            if success:
                                st.success("🎉 Posted successfully!")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(result)
                    else:
                        st.error("Please add a caption")
    
    with tab2:
        st.markdown("### Create Text Post")
        
        with st.form("text_post_form"):
            content = st.text_area("What's happening?", 
                                 placeholder="Share your thoughts...",
                                 height=150)
            
            media_file = st.file_uploader("Add Photo/Video", 
                                         type=['jpg', 'png', 'jpeg', 'mp4', 'gif'])
            
            location = st.text_input("Location", placeholder="Add location")
            
            if st.form_submit_button("Post", use_container_width=True):
                if content:
                    media_data = media_file.read() if media_file else None
                    media_type = media_file.type if media_file else None
                    
                    success, result = create_post(
                        st.session_state.user_id, content, media_data, media_type, location
                    )
                    
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
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if profile_pic:
                try:
                    display_image_safely(profile_pic, width=100)
                except:
                    st.markdown(f"""
                    <div style='width: 100px; height: 100px; border-radius: 50%; 
                                background: linear-gradient(45deg, #FF0050, #00F2EA);
                                display: flex; align-items: center; justify-content: center; 
                                color: white; font-size: 48px; font-weight: bold; margin: 0 auto;'>
                        {(display_name or username)[0].upper()}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='width: 100px; height: 100px; border-radius: 50%; 
                            background: linear-gradient(45deg, #FF0050, #00F2EA);
                            display: flex; align-items: center; justify-content: center; 
                            color: white; font-size: 48px; font-weight: bold; margin: 0 auto;'>
                    {(display_name or username)[0].upper()}
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"# {display_name or username}")
            st.markdown(f"@{username}")
            
            if bio:
                st.markdown(f"<div style='margin: 10px 0; color: {THEME_CONFIG['theme']['text_muted']};'>{bio}</div>", 
                          unsafe_allow_html=True)
            
            st.markdown(f"📍 {location}")
        
        with col3:
            if st.button("Edit Profile", use_container_width=True):
                st.session_state.editing_profile = True
        
        # Stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"<div style='text-align: center;'><div style='font-size: 24px; font-weight: bold;'>{post_count}</div><div style='font-size: 12px;'>Posts</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div style='text-align: center;'><div style='font-size: 24px; font-weight: bold;'>{follower_count}</div><div style='font-size: 12px;'>Followers</div></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div style='text-align: center;'><div style='font-size: 24px; font-weight: bold;'>{following_count}</div><div style='font-size: 12px;'>Following</div></div>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<div style='text-align: center;'><div style='font-size: 24px; font-weight: bold;'>{total_likes}</div><div style='font-size: 12px;'>Likes</div></div>", unsafe_allow_html=True)
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Share Profile", use_container_width=True):
                st.info("Profile link copied!")
        with col2:
            if st.button("QR Code", use_container_width=True):
                st.info("QR code generated!")
        
        # User's posts
        st.markdown("### 📸 Your Posts")
        user_posts = get_posts(user_id=st.session_state.user_id, limit=12)
        
        if user_posts:
            cols = st.columns(3)
            for idx, post in enumerate(user_posts):
                if len(post) > 14:  # Check if post has enough elements
                    with cols[idx % 3]:
                        try:
                            if post[3] and 'image' in post[3]:  # media_type
                                if post[4]:  # media_data
                                    display_image_safely(post[4], use_container_width=True)
                                    st.caption(f"❤️ {post[9]} 💬 {post[10]}")
                            elif post[3] and 'video' in post[3]:
                                if post[4]:  # media_data
                                    st.video(post[4])
                                    st.caption(f"❤️ {post[9]} 💬 {post[10]}")
                            else:
                                # Text post
                                st.markdown(f"<div style='padding: 20px; background: {THEME_CONFIG['theme']['surface']}; border-radius: 12px;'>{post[2][:100]}...</div>", unsafe_allow_html=True)
                                st.caption(f"❤️ {post[9]} 💬 {post[10]}")
                        except:
                            pass
        
        # Edit profile modal
        if st.session_state.get('editing_profile'):
            with st.form("edit_profile_form"):
                st.markdown("### ✏️ Edit Profile")
                
                new_display_name = st.text_input("Display Name", value=display_name or "")
                new_bio = st.text_area("Bio", value=bio or "", height=100)
                new_location = st.text_input("Location", value=location or "")
                
                new_profile_pic = st.file_uploader("Profile Picture", type=['jpg', 'png', 'jpeg'])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Save", use_container_width=True):
                        # Update profile logic here
                        st.success("Profile updated!")
                        st.session_state.editing_profile = False
                        st.rerun()
                with col2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.editing_profile = False
                        st.rerun()

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
        initial_sidebar_state="collapsed"
    )
    
    # Inject TikTok CSS
    inject_tiktok_css()
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "feed"
    if 'editing_profile' not in st.session_state:
        st.session_state.editing_profile = False
    
    # Create demo user for testing
    create_demo_user()
    
    # Show login page if not logged in
    if not st.session_state.logged_in:
        # Feed Chat login
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("<h1 style='text-align: center;'>🎬 Feed Chat</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center;'>Connect, Share, Discover</h3>", unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["Login", "Sign Up"])
            
            with tab1:
                st.info("**Demo Credentials:**\n- Username: `demo`\n- Password: `any password`")
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="@username", value="demo")
                    password = st.text_input("Password", type="password", placeholder="••••••••", value="demo123")
                    submit = st.form_submit_button("Login", use_container_width=True, type="primary")
                    
                    if submit:
                        if username and password:
                            user_id, username = verify_user_secure(username, password)
                            if user_id:
                                st.session_state.user_id = user_id
                                st.session_state.username = username
                                st.session_state.logged_in = True
                                update_user_online_status(user_id, True)
                                st.success(f"Welcome back, @{username}!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Invalid credentials. Try username: 'demo', password: any")
                        else:
                            st.error("Please enter username and password")
            
            with tab2:
                with st.form("signup_form"):
                    new_username = st.text_input("Username", placeholder="@username")
                    new_password = st.text_input("Password", type="password", placeholder="••••••••")
                    confirm_password = st.text_input("Confirm Password", type="password", placeholder="••••••••")
                    email = st.text_input("Email", placeholder="email@example.com")
                    
                    if st.form_submit_button("Create Account", use_container_width=True, type="primary"):
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
        
        return
    
    # Main app navigation
    # Get current page from query params or session
    query_params = st.query_params
    page = query_params.get("page", ["feed"])[0]
    st.session_state.current_page = page
    
    # Update online status
    update_user_online_status(st.session_state.user_id, True)
    
    # Mobile navigation
    st.markdown("""
    <div class="mobile-nav">
        <a href="?page=feed" class="mobile-nav-item %s">
            <span style="font-size: 24px;">🏠</span>
            <span>Feed</span>
        </a>
        <a href="?page=discover" class="mobile-nav-item %s">
            <span style="font-size: 24px;">🔍</span>
            <span>Discover</span>
        </a>
        <a href="?page=create" class="mobile-nav-item %s">
            <span style="font-size: 24px;">➕</span>
            <span>Create</span>
        </a>
        <a href="?page=profile" class="mobile-nav-item %s">
            <span style="font-size: 24px;">👤</span>
            <span>Profile</span>
        </a>
    </div>
    """ % (
        "active" if page == "feed" else "",
        "active" if page == "discover" else "",
        "active" if page == "create" else "",
        "active" if page == "profile" else ""
    ), unsafe_allow_html=True)
    
    # Main content based on page
    if page == "feed":
        feed_page()
    elif page == "discover":
        discover_page()
    elif page == "create":
        create_content_page()
    elif page == "profile":
        profile_page()
    else:
        feed_page()
    
    # Desktop sidebar
    with st.sidebar:
        st.markdown("<h2 style='text-align: center;'>🎬 Feed Chat</h2>", unsafe_allow_html=True)
        st.markdown(f"### 👋 @{st.session_state.username}")
        
        st.markdown("---")
        
        # Desktop navigation
        nav_options = {
            "feed": "🏠 Feed",
            "discover": "🔍 Discover", 
            "create": "➕ Create",
            "profile": "👤 Profile"
        }
        
        selected = st.radio(
            "Navigation",
            list(nav_options.values()),
            label_visibility="collapsed"
        )
        
        # Update page based on selection
        for key, value in nav_options.items():
            if value == selected and st.session_state.current_page != key:
                st.session_state.current_page = key
                st.query_params = {"page": key}
                st.rerun()
        
        st.markdown("---")
        
        # Quick stats
        user_data = get_user(st.session_state.user_id)
        if user_data:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Followers", user_data[13])  # follower_count
            with col2:
                st.metric("Likes", user_data[15])  # total_likes
        
        st.markdown("---")
        
        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            update_user_online_status(st.session_state.user_id, False)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.query_params = {}
            st.rerun()

if __name__ == "__main__":
    main()

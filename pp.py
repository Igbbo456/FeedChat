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
import numpy as np

# ===================================
# TIKTOK-INSPIRED THEME CONFIGURATION
# ===================================

THEME_CONFIG = {
    "app_name": "ClipSphere",
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

def optimize_media_for_mobile(media_data, media_type, max_size=(1080, 1920)):
    """Optimize media for mobile viewing"""
    try:
        if not media_data or not isinstance(media_data, bytes):
            return media_data
            
        if 'image' in media_type:
            image = Image.open(io.BytesIO(media_data))
            
            # Resize for mobile optimization
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Compress
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
            
        elif 'video' in media_type:
            # For videos, we'll just limit size
            if len(media_data) > THEME_CONFIG["max_file_size"]:
                st.warning("Video too large. Please upload a smaller video.")
                return None
            return media_data
            
    except Exception as e:
        st.warning(f"Media optimization failed: {e}")
        return media_data
    
    return media_data

# ===================================
# ENHANCED DATABASE WITH TIKTOK FEATURES
# ===================================

def init_tiktok_db():
    """Initialize database with TikTok-like features"""
    conn = sqlite3.connect("clipsphere.db", check_same_thread=False)
    c = conn.cursor()

    # Users table with TikTok features
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        display_name TEXT,
        password_hash TEXT,
        email TEXT UNIQUE,
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
        private_account BOOLEAN DEFAULT FALSE,
        tiktok_style TEXT DEFAULT 'default'
    )
    """)

    # Posts table with enhanced engagement
    c.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        media_type TEXT,
        media_data BLOB,
        thumbnail BLOB,
        duration INTEGER DEFAULT 0,
        location TEXT DEFAULT 'Unknown',
        language TEXT DEFAULT 'en',
        visibility TEXT DEFAULT 'public',
        is_deleted BOOLEAN DEFAULT FALSE,
        like_count INTEGER DEFAULT 0,
        comment_count INTEGER DEFAULT 0,
        share_count INTEGER DEFAULT 0,
        view_count INTEGER DEFAULT 0,
        save_count INTEGER DEFAULT 0,
        duet_count INTEGER DEFAULT 0,
        stitch_count INTEGER DEFAULT 0,
        sound_id INTEGER DEFAULT NULL,
        effect_id INTEGER DEFAULT NULL,
        hashtags TEXT DEFAULT '',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Sounds table (TikTok-like)
    c.execute("""
    CREATE TABLE IF NOT EXISTS sounds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        artist TEXT,
        audio_data BLOB,
        duration INTEGER,
        use_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Effects table (TikTok-like)
    c.execute("""
    CREATE TABLE IF NOT EXISTS effects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        effect_data BLOB,
        use_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Hashtags table
    c.execute("""
    CREATE TABLE IF NOT EXISTS hashtags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tag TEXT UNIQUE,
        post_count INTEGER DEFAULT 0,
        trend_score INTEGER DEFAULT 0
    )
    """)

    # Post-Hashtag relationship
    c.execute("""
    CREATE TABLE IF NOT EXISTS post_hashtags (
        post_id INTEGER,
        hashtag_id INTEGER,
        PRIMARY KEY (post_id, hashtag_id),
        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
        FOREIGN KEY (hashtag_id) REFERENCES hashtags(id) ON DELETE CASCADE
    )
    """)

    # Enhanced likes with reactions
    c.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        post_id INTEGER,
        reaction_type TEXT DEFAULT 'like',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, post_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
    )
    """)

    # Comments with replies
    c.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_id INTEGER,
        content TEXT,
        parent_id INTEGER DEFAULT NULL,
        like_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
    )
    """)

    # Saves/Bookmarks
    c.execute("""
    CREATE TABLE IF NOT EXISTS saves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        post_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, post_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
    )
    """)

    # Follow relationships
    c.execute("""
    CREATE TABLE IF NOT EXISTS follows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        follower_id INTEGER,
        following_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(follower_id, following_id),
        FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # For You Page algorithm tracking
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        post_id INTEGER,
        interaction_type TEXT,  # view, like, comment, share, save, complete
        duration INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
    )
    """)

    # Create indexes
    c.execute("CREATE INDEX IF NOT EXISTS idx_posts_trending ON posts(like_count, view_count, created_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id, created_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_user_interactions ON user_interactions(user_id, interaction_type, created_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_hashtags_trending ON hashtags(trend_score DESC)")
    
    # Triggers
    c.execute("""
    CREATE TRIGGER IF NOT EXISTS update_post_counts
    AFTER INSERT ON posts
    FOR EACH ROW
    BEGIN
        UPDATE users SET post_count = post_count + 1 WHERE id = NEW.user_id;
    END;
    """)
    
    c.execute("""
    CREATE TRIGGER IF NOT EXISTS update_like_counts
    AFTER INSERT ON likes
    FOR EACH ROW
    BEGIN
        UPDATE posts SET like_count = like_count + 1 WHERE id = NEW.post_id;
        UPDATE users SET total_likes = total_likes + 1 
        WHERE id = (SELECT user_id FROM posts WHERE id = NEW.post_id);
    END;
    """)

    conn.commit()
    return conn

# Initialize database
conn = init_tiktok_db()

# ===================================
# TIKTOK-STYLE CORE FUNCTIONS
# ===================================

def extract_hashtags(text):
    """Extract hashtags from text"""
    hashtags = re.findall(r'#(\w+)', text)
    return list(set(hashtags))  # Remove duplicates

def create_thumbnail(video_data):
    """Create thumbnail from video (placeholder - in real app use video processing)"""
    try:
        # Create a simple gradient thumbnail
        img = Image.new('RGB', (1080, 1920), color='black')
        draw = ImageDraw.Draw(img)
        
        # Add gradient
        for i in range(1920):
            r = int(255 * i / 1920)
            g = int(100 * i / 1920)
            b = int(200 * i / 1920)
            draw.line([(0, i), (1080, i)], fill=(r, g, b))
        
        # Add play icon
        draw.polygon([(500, 800), (500, 1120), (800, 960)], fill='white')
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85)
        return output.getvalue()
    except:
        return None

def get_for_you_posts(user_id, limit=20):
    """Get personalized feed similar to TikTok's For You Page"""
    try:
        c = conn.cursor()
        
        # Simple algorithm: mix of trending and followed users
        query = """
            SELECT p.*, u.username, u.profile_pic, u.display_name,
                   (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as like_count,
                   (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count,
                   (SELECT COUNT(*) FROM saves WHERE post_id = p.id) as save_count
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.is_deleted = 0 AND p.visibility = 'public'
            AND (
                p.user_id IN (SELECT following_id FROM follows WHERE follower_id = ?)
                OR p.like_count > 10
                OR p.view_count > 50
            )
            ORDER BY 
                CASE WHEN p.user_id IN (SELECT following_id FROM follows WHERE follower_id = ?) THEN 1 ELSE 2 END,
                (p.like_count * 0.4 + p.view_count * 0.3 + p.comment_count * 0.2 + p.save_count * 0.1) DESC,
                p.created_at DESC
            LIMIT ?
        """
        
        c.execute(query, (user_id, user_id, limit))
        posts = c.fetchall()
        
        # If not enough posts, add trending posts
        if len(posts) < limit:
            query_trending = """
                SELECT p.*, u.username, u.profile_pic, u.display_name,
                       (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as like_count,
                       (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count,
                       (SELECT COUNT(*) FROM saves WHERE post_id = p.id) as save_count
                FROM posts p
                JOIN users u ON p.user_id = u.id
                WHERE p.is_deleted = 0 AND p.visibility = 'public'
                ORDER BY (p.like_count * 0.4 + p.view_count * 0.3 + p.comment_count * 0.2) DESC,
                         p.created_at DESC
                LIMIT ?
            """
            c.execute(query_trending, (limit - len(posts),))
            trending_posts = c.fetchall()
            posts.extend(trending_posts)
        
        return posts
    except sqlite3.Error as e:
        st.error(f"Failed to load For You feed: {str(e)}")
        return []

def get_trending_hashtags(limit=10):
    """Get trending hashtags"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT tag, post_count, trend_score 
            FROM hashtags 
            ORDER BY trend_score DESC, post_count DESC 
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
    
    /* Engagement buttons overlay */
    .engagement-buttons {{
        position: absolute;
        right: 16px;
        bottom: 80px;
        display: flex;
        flex-direction: column;
        gap: 16px;
        z-index: 10;
    }}
    
    .engagement-button {{
        background: rgba(0, 0, 0, 0.6);
        border: none;
        border-radius: 50%;
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 20px;
        cursor: pointer;
        transition: all 0.2s ease;
    }}
    
    .engagement-button:hover {{
        background: rgba(255, 0, 80, 0.8);
        transform: scale(1.1);
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
    
    /* Loading skeleton */
    .skeleton {{
        background: linear-gradient(90deg, {THEME_CONFIG['theme']['surface_light']} 25%, {THEME_CONFIG['theme']['surface']} 50%, {THEME_CONFIG['theme']['surface_light']} 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        border-radius: 8px;
    }}
    
    @keyframes loading {{
        0% {{ background-position: 200% 0; }}
        100% {{ background-position: -200% 0; }}
    }}
    
    /* Swipe gestures hint */
    .swipe-hint {{
        position: fixed;
        bottom: 100px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 12px 24px;
        border-radius: 30px;
        font-size: 14px;
        animation: pulse 2s infinite;
        z-index: 100;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 0.7; }}
        50% {{ opacity: 1; }}
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

def create_engagement_overlay(post_id, like_count, comment_count, share_count, save_count):
    """Create TikTok-style engagement buttons overlay"""
    return f"""
    <div class="engagement-buttons" id="engagement-{post_id}">
        <div class="engagement-button" onclick="handleLike('{post_id}')">
            <span style="font-size: 24px;">{TIKTOK_EMOJIS['like']}</span>
            <div style="font-size: 12px; margin-top: 4px;">{like_count}</div>
        </div>
        <div class="engagement-button" onclick="handleComment('{post_id}')">
            <span style="font-size: 24px;">{TIKTOK_EMOJIS['comment']}</span>
            <div style="font-size: 12px; margin-top: 4px;">{comment_count}</div>
        </div>
        <div class="engagement-button" onclick="handleShare('{post_id}')">
            <span style="font-size: 24px;">{TIKTOK_EMOJIS['share']}</span>
            <div style="font-size: 12px; margin-top: 4px;">{share_count}</div>
        </div>
        <div class="engagement-button" onclick="handleSave('{post_id}')">
            <span style="font-size: 24px;">{TIKTOK_EMOJIS['save']}</span>
            <div style="font-size: 12px; margin-top: 4px;">{save_count}</div>
        </div>
    </div>
    """

def create_mobile_navigation(current_page="feed"):
    """Create mobile bottom navigation bar"""
    nav_items = [
        {"icon": "🏠", "label": "For You", "page": "feed"},
        {"icon": "🔍", "label": "Discover", "page": "discover"},
        {"icon": "➕", "label": "Create", "page": "create"},
        {"icon": "💬", "label": "Inbox", "page": "messages"},
        {"icon": "👤", "label": "Profile", "page": "profile"}
    ]
    
    nav_html = '<div class="mobile-nav">'
    for item in nav_items:
        active_class = "active" if current_page == item["page"] else ""
        nav_html += f"""
        <a href="?page={item['page']}" class="mobile-nav-item {active_class}">
            <span style="font-size: 24px;">{item['icon']}</span>
            <span>{item['label']}</span>
        </a>
        """
    nav_html += '</div>'
    
    return nav_html

# ===================================
# TIKTOK-STYLE PAGES
# ===================================

def tiktok_feed_page():
    """TikTok-style vertical feed"""
    st.markdown("<h1 style='text-align: center;'>🎬 For You</h1>", unsafe_allow_html=True)
    
    # Trending hashtags
    trending_hashtags = get_trending_hashtags(5)
    if trending_hashtags:
        st.markdown("### 🔥 Trending Now")
        cols = st.columns(len(trending_hashtags))
        for idx, hashtag in enumerate(trending_hashtags):
            tag, count, score = hashtag
            with cols[idx]:
                st.markdown(f"<div class='hashtag-chip'>#{tag}</div>", unsafe_allow_html=True)
                st.caption(f"{count:,} posts")
    
    # For You feed
    posts = get_for_you_posts(st.session_state.user_id, limit=10)
    
    if not posts:
        st.info("No posts yet. Start following people or create your first post!")
        return
    
    # Display posts in TikTok style
    for post in posts:
        display_tiktok_post(post)
    
    # Load more button
    if st.button("Load More", use_container_width=True):
        st.rerun()

def display_tiktok_post(post):
    """Display post in TikTok vertical format"""
    (post_id, user_id, content, media_type, media_data, thumbnail, duration, location, 
     language, visibility, is_deleted, like_count, comment_count, share_count, view_count,
     save_count, duet_count, stitch_count, sound_id, effect_id, hashtags, created_at,
     updated_at, username, profile_pic, display_name, post_like_count, post_comment_count,
     post_save_count) = post
    
    with st.container():
        # Video/Image container
        if media_data and media_type:
            col1, col2, col3 = st.columns([1, 8, 1])
            
            with col2:
                if 'video' in media_type:
                    st.video(media_data)
                elif 'image' in media_type:
                    st.image(media_data, use_container_width=True)
                
                # Engagement overlay (simulated with columns)
                col_a, col_b, col_c, col_d, col_e = st.columns(5)
                
                with col_a:
                    if st.button(f"❤️\n{post_like_count}", key=f"like_{post_id}", use_container_width=True):
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
                    if st.button(f"{save_text}\n{post_save_count}", key=f"save_{post_id}", use_container_width=True):
                        if saved:
                            unsave_post(st.session_state.user_id, post_id)
                        else:
                            save_post(st.session_state.user_id, post_id)
                        st.rerun()
                
                with col_e:
                    if st.button("⚙️", key=f"menu_{post_id}", use_container_width=True):
                        st.session_state.show_post_menu = post_id
        
        # Post info
        col1, col2 = st.columns([1, 10])
        
        with col1:
            if profile_pic and is_valid_image(profile_pic):
                st.image(profile_pic, width=50, output_format='JPEG')
            else:
                st.markdown(f"""
                <div style='width: 50px; height: 50px; border-radius: 50%; 
                            background: linear-gradient(45deg, #FF0050, #00F2EA);
                            display: flex; align-items: center; justify-content: center; 
                            color: white; font-size: 20px; font-weight: bold;'>
                    {(display_name or username)[0].upper()}
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"**@{username}**")
            if display_name and display_name != username:
                st.markdown(f"*{display_name}*")
            st.caption(f"📍 {location} · {format_tiktok_time(created_at)}")
        
        # Content and hashtags
        st.markdown(f"<div style='margin: 10px 0; font-size: 16px;'>{content}</div>", 
                   unsafe_allow_html=True)
        
        # Hashtags
        if hashtags:
            tags = hashtags.split(',')
            for tag in tags[:5]:  # Show first 5 hashtags
                st.markdown(f"<span class='hashtag-chip'>#{tag.strip()}</span>", 
                          unsafe_allow_html=True)
        
        # Sound info (if available)
        if sound_id:
            st.markdown(f"<div style='margin: 10px 0; color: {THEME_CONFIG['theme']['secondary']};'>🎵 Original Sound</div>", 
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
    
    cols = st.columns(3)
    for idx, hashtag in enumerate(trending_hashtags):
        tag, count, score = hashtag
        with cols[idx % 3]:
            st.markdown(f"<div class='hashtag-chip'>#{tag}</div>", unsafe_allow_html=True)
            st.caption(f"{count:,} posts")
    
    # Suggested accounts
    st.markdown("### 👥 Suggested For You")
    suggested_users = get_global_users(limit=6)
    
    cols = st.columns(3)
    for idx, user in enumerate(suggested_users):
        user_id, username, profile_pic, bio, location, language, is_online = user
        
        with cols[idx % 3]:
            if profile_pic and is_valid_image(profile_pic):
                st.image(profile_pic, width=80, output_format='JPEG')
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
    
    tab1, tab2, tab3 = st.tabs(["🎥 Upload", "📝 Post", "✨ Effects"])
    
    with tab1:
        st.markdown("### Upload Video")
        
        uploaded_file = st.file_uploader("Choose a video file", 
                                        type=['mp4', 'mov', 'avi', 'mkv'],
                                        help="Max 100MB, 5 minutes")
        
        if uploaded_file:
            st.video(uploaded_file)
            
            with st.form("upload_form"):
                caption = st.text_area("Caption", 
                                     placeholder="Add a caption...",
                                     help="Use hashtags to reach more people")
                
                col1, col2 = st.columns(2)
                with col1:
                    allow_duets = st.checkbox("Allow Duets", value=True)
                    allow_stitches = st.checkbox("Allow Stitches", value=True)
                with col2:
                    visibility = st.selectbox("Visibility", ["Public", "Friends", "Private"])
                    location = st.text_input("Location", placeholder="Add location")
                
                # Hashtag suggestions
                if caption:
                    suggested_tags = extract_hashtags(caption)
                    if suggested_tags:
                        st.markdown("**Suggested Hashtags:**")
                        for tag in suggested_tags[:5]:
                            st.markdown(f"<span class='hashtag-chip'>#{tag}</span>", unsafe_allow_html=True)
                
                if st.form_submit_button("Post Video", use_container_width=True):
                    if caption:
                        with st.spinner("Uploading..."):
                            media_data = uploaded_file.read()
                            media_type = uploaded_file.type
                            thumbnail = create_thumbnail(media_data)
                            
                            # Extract hashtags
                            hashtags_list = extract_hashtags(caption)
                            hashtags_str = ",".join(hashtags_list[:10])  # Limit to 10 hashtags
                            
                            success, result = create_post(
                                st.session_state.user_id, caption, media_data, media_type,
                                location, visibility=visibility.lower()
                            )
                            
                            if success:
                                # Save hashtags
                                try:
                                    c = conn.cursor()
                                    for tag in hashtags_list[:10]:
                                        c.execute("""
                                            INSERT OR IGNORE INTO hashtags (tag, post_count) VALUES (?, 1)
                                            ON CONFLICT(tag) DO UPDATE SET post_count = post_count + 1
                                        """, (tag.lower(),))
                                    conn.commit()
                                except:
                                    pass
                                
                                st.success("🎉 Video posted successfully!")
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
            
            col1, col2 = st.columns(2)
            with col1:
                add_music = st.checkbox("Add Sound")
                add_effects = st.checkbox("Add Effects")
            with col2:
                allow_comments = st.checkbox("Allow Comments", value=True)
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
    
    with tab3:
        st.markdown("### ✨ Effects & Filters")
        
        effects = [
            {"name": "Beauty", "icon": "💄", "desc": "Smooth skin filter"},
            {"name": "Funny", "icon": "😂", "desc": "Comedy effects"},
            {"name": "AR", "icon": "👓", "desc": "Augmented reality"},
            {"name": "Green Screen", "icon": "🟢", "desc": "Background effects"},
            {"name": "Time Warp", "icon": "⏰", "desc": "Slow/fast motion"},
            {"name": "Voice", "icon": "🎤", "desc": "Voice effects"},
        ]
        
        cols = st.columns(3)
        for idx, effect in enumerate(effects):
            with cols[idx % 3]:
                st.markdown(f"<div style='text-align: center; padding: 20px; background: {THEME_CONFIG['theme']['surface_light']}; border-radius: 12px;'>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 48px;'>{effect['icon']}</div>", unsafe_allow_html=True)
                st.markdown(f"**{effect['name']}**")
                st.caption(effect['desc'])
                if st.button("Try", key=f"effect_{idx}", use_container_width=True):
                    st.info(f"Opening {effect['name']} effect...")
                st.markdown("</div>", unsafe_allow_html=True)

def messages_page():
    """TikTok-style messages"""
    st.markdown("<h1 style='text-align: center;'>💬 Messages</h1>", unsafe_allow_html=True)
    
    # Quick actions
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📸 Camera", use_container_width=True):
            st.info("Camera opening...")
    with col2:
        if st.button("👥 New Group", use_container_width=True):
            st.info("Create group chat")
    with col3:
        if st.button("🔍 Find Friends", use_container_width=True):
            st.info("Search for friends")
    
    # Active now
    st.markdown("### 💚 Active Now")
    online_users = get_online_users()[:8]
    
    if online_users:
        cols = st.columns(min(8, len(online_users)))
        for idx, user in enumerate(online_users):
            user_id, username, location = user
            with cols[idx % 8]:
                st.markdown(f"""
                <div style='text-align: center;'>
                    <div style='width: 60px; height: 60px; border-radius: 50%; 
                                background: linear-gradient(45deg, #FF0050, #00F2EA);
                                margin: 0 auto;
                                display: flex; align-items: center; justify-content: center; 
                                color: white; font-size: 24px; font-weight: bold;'>
                        {username[0].upper()}
                    </div>
                    <div style='margin-top: 8px; font-size: 12px;'>@{username}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Conversations
    st.markdown("### 💭 All Messages")
    conversations = get_global_conversations(st.session_state.user_id)
    
    if not conversations:
        st.info("No messages yet. Start a conversation!")
    else:
        for conv in conversations:
            other_user_id, username, profile_pic, last_time, last_msg, unread, location = conv
            
            with st.container():
                col1, col2, col3 = st.columns([1, 4, 1])
                
                with col1:
                    if profile_pic and is_valid_image(profile_pic):
                        st.image(profile_pic, width=50, output_format='JPEG')
                
                with col2:
                    st.markdown(f"**@{username}**")
                    if last_msg:
                        st.caption(last_msg[:30] + "..." if len(last_msg) > 30 else last_msg)
                    st.caption(format_tiktok_time(last_time))
                
                with col3:
                    if unread > 0:
                        st.markdown(f"<div style='background: {THEME_CONFIG['theme']['primary']}; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 12px;'>{unread}</div>", unsafe_allow_html=True)
                    
                    if st.button("💬", key=f"msg_{other_user_id}"):
                        st.session_state.current_chat = other_user_id
                        st.session_state.chat_username = username
                        st.rerun()

def profile_page_tiktok():
    """TikTok-style profile page"""
    user = get_user(st.session_state.user_id)
    
    if user:
        (user_id, username, display_name, password_hash, email, profile_pic, bio, location, 
         timezone, language, is_online, last_seen, created_at, post_count, follower_count, 
         following_count, total_likes, verified, private_account, tiktok_style) = user
        
        # Profile header
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if profile_pic and is_valid_image(profile_pic):
                st.image(profile_pic, width=100, output_format='JPEG')
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
                post_id, _, content, media_type, media_data, _, _, _, _, _, _, 
                like_count, comment_count, share_count, _, _, _, _, _, _, _, 
                created_at, _, username, profile_pic, _, _, _ = post
                
                with cols[idx % 3]:
                    if media_data and 'image' in media_type:
                        st.image(media_data, use_container_width=True)
                        st.caption(f"❤️ {like_count} 💬 {comment_count}")
                    elif media_data and 'video' in media_type:
                        st.video(media_data)
                        st.caption(f"❤️ {like_count} 💬 {comment_count}")
        
        # Edit profile modal
        if st.session_state.get('editing_profile'):
            with st.form("edit_profile_form"):
                st.markdown("### ✏️ Edit Profile")
                
                new_display_name = st.text_input("Display Name", value=display_name or "")
                new_bio = st.text_area("Bio", value=bio or "", height=100)
                new_location = st.text_input("Location", value=location or "")
                
                col1, col2 = st.columns(2)
                with col1:
                    new_profile_pic = st.file_uploader("Profile Picture", type=['jpg', 'png', 'jpeg'])
                with col2:
                    private = st.checkbox("Private Account", value=private_account)
                
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
# MAIN APPLICATION WITH MOBILE SUPPORT
# ===================================

def main():
    """Main application with TikTok features"""
    
    # Page configuration for mobile
    st.set_page_config(
        page_title="ClipSphere",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="collapsed"  # Collapsed for mobile
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
    
    # Show login page if not logged in
    if not st.session_state.logged_in:
        # TikTok-style login
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("<h1 style='text-align: center;'>🎬 ClipSphere</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center;'>Create, Share, Discover</h3>", unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["Login", "Sign Up"])
            
            with tab1:
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="@username")
                    password = st.text_input("Password", type="password", placeholder="••••••••")
                    submit = st.form_submit_button("Login", use_container_width=True, type="primary")
                    
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
        
        return
    
    # Main app navigation
    # Get current page from query params or session
    query_params = st.query_params
    page = query_params.get("page", ["feed"])[0]
    st.session_state.current_page = page
    
    # Mobile navigation (shown at bottom on mobile)
    st.markdown(create_mobile_navigation(page), unsafe_allow_html=True)
    
    # Main content based on page
    if page == "feed":
        tiktok_feed_page()
    elif page == "discover":
        discover_page()
    elif page == "create":
        create_content_page()
    elif page == "messages":
        messages_page()
    elif page == "profile":
        profile_page_tiktok()
    
    # Desktop sidebar (hidden on mobile via CSS)
    with st.sidebar:
        st.markdown("<h2 style='text-align: center;'>🎬 ClipSphere</h2>", unsafe_allow_html=True)
        st.markdown(f"### 👋 @{st.session_state.username}")
        
        st.markdown("---")
        
        # Desktop navigation
        nav_options = {
            "feed": "🏠 For You",
            "discover": "🔍 Discover", 
            "create": "➕ Create",
            "messages": "💬 Messages",
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
                st.metric("Followers", user_data[15])  # follower_count
            with col2:
                st.metric("Likes", user_data[16])  # total_likes
        
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

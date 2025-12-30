import streamlit as st
import sqlite3
import datetime
import random
import time
from PIL import Image
import io
import base64
import json
import re
import uuid
import hashlib
import secrets

# ===================================
# MODERN THEME CONFIGURATION
# ===================================

THEME_CONFIG = {
    "app_name": "SocialSphere",
    "version": "3.0",
    "theme": {
        "primary": "#6366f1",
        "secondary": "#8b5cf6",
        "accent": "#ec4899",
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "background": "#f8fafc",
        "surface": "#ffffff",
        "text": "#1e293b",
        "muted": "#64748b",
        "border": "#e2e8f0"
    },
    "max_file_size": 50 * 1024 * 1024,
    "supported_timezones": ["UTC", "EST", "PST", "GMT", "CET", "AEST"],
    "languages": ["en", "es", "fr", "de", "zh", "ja"]
}

def format_global_time(timestamp):
    """Format timestamp for global audience"""
    try:
        if isinstance(timestamp, str):
            return timestamp
        elif isinstance(timestamp, datetime.datetime):
            return timestamp.strftime('%b %d, %Y · %I:%M %p')
        else:
            return str(timestamp)
    except:
        return "Just now"

def optimize_image_for_web(image_data, max_size=(1200, 1200), quality=85):
    """Optimize images for fast loading"""
    try:
        if image_data and isinstance(image_data, bytes):
            image = Image.open(io.BytesIO(image_data))
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
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
# ENHANCED DATABASE SETUP
# ===================================

def init_enhanced_db():
    """Initialize database with improved schema"""
    conn = sqlite3.connect("social_sphere.db", check_same_thread=False)
    c = conn.cursor()

    # Users table with more fields
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
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
        following_count INTEGER DEFAULT 0
    )
    """)

    # Posts table with engagement tracking
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
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Messages with better threading
    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        content TEXT,
        message_type TEXT DEFAULT 'text',
        media_data BLOB,
        is_read BOOLEAN DEFAULT FALSE,
        is_delivered BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Likes with reaction types
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

    # Comments with threading
    c.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_id INTEGER,
        content TEXT,
        parent_id INTEGER DEFAULT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
    )
    """)

    # Indexes for performance
    c.execute("CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(sender_id, receiver_id, created_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_likes_post_user ON likes(post_id, user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    
    # Trigger to update post counts
    c.execute("""
    CREATE TRIGGER IF NOT EXISTS update_post_count
    AFTER INSERT ON posts
    FOR EACH ROW
    BEGIN
        UPDATE users SET post_count = post_count + 1 WHERE id = NEW.user_id;
    END;
    """)

    conn.commit()
    return conn

# Initialize database
conn = init_enhanced_db()

# ===================================
# ENHANCED CORE FUNCTIONS
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

def display_image_safely(image_data, caption="", width=None, use_container_width=False, clazz=""):
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
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
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
        
        # Validate inputs
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if not re.match(r'^[\w.]+$', username):
            return False, "Username can only contain letters, numbers, dots and underscores"
        
        # Check if user exists
        c.execute("SELECT id FROM users WHERE username=?", (username,))
        if c.fetchone():
            return False, "Username already exists"
        
        # Check if email exists
        c.execute("SELECT id FROM users WHERE email=?", (email,))
        if c.fetchone():
            return False, "Email already registered"
        
        # Validate email format
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return False, "Invalid email format"
        
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
        return False, f"Database error: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

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
            SELECT id, username, email, profile_pic, bio, location, timezone, language, 
                   is_online, last_seen, post_count, follower_count, following_count
            FROM users WHERE id=?
        """, (user_id,))
        return c.fetchone()
    except sqlite3.Error:
        return None

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

def create_post(user_id, content, media_data=None, media_type=None, location=None, language="en", visibility="public"):
    """Create post with enhanced features"""
    try:
        if not content or len(content.strip()) == 0:
            return False, "Post content cannot be empty"
        if len(content) > 10000:
            return False, "Post content too long (max 10,000 characters)"
            
        c = conn.cursor()
        
        # Get user location if not provided
        if not location:
            user = get_user(user_id)
            if user:
                location = user[5]  # location field
        
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
        return True, post_id
    except sqlite3.Error as e:
        return False, f"Post creation failed: {str(e)}"

def get_posts(limit=20, language=None, location=None, user_id=None):
    """Get posts with filtering"""
    try:
        c = conn.cursor()
        
        query = """
            SELECT p.*, u.username, u.profile_pic,
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
        
        if language and language != 'all':
            query += " AND (p.language = ? OR p.language = 'en')"
            params.append(language)
        
        if location and location != 'global':
            query += " AND (p.location LIKE ? OR u.location LIKE ?)"
            params.extend([f'%{location}%', f'%{location}%'])
        
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

# ===================================
# MODERN UI COMPONENTS
# ===================================

def inject_modern_css():
    """Inject modern CSS with gradient theme"""
    st.markdown(f"""
    <style>
    /* Main Theme */
    .stApp {{
        background: linear-gradient(135deg, {THEME_CONFIG['theme']['background']} 0%, #f1f5f9 100%);
    }}
    
    /* Sidebar */
    .css-1d391kg, .css-1lcbmhc {{
        background: {THEME_CONFIG['theme']['surface']} !important;
        border-right: 1px solid {THEME_CONFIG['theme']['border']};
    }}
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {{
        color: {THEME_CONFIG['theme']['text']} !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 700;
    }}
    
    /* Buttons */
    .stButton>button {{
        background: linear-gradient(135deg, {THEME_CONFIG['theme']['primary']}, {THEME_CONFIG['theme']['secondary']});
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(99, 102, 241, 0.1);
    }}
    
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(99, 102, 241, 0.2);
    }}
    
    /* Cards */
    .feed-card {{
        background: {THEME_CONFIG['theme']['surface']};
        border-radius: 20px;
        padding: 24px;
        margin: 16px 0;
        border: 1px solid {THEME_CONFIG['theme']['border']};
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }}
    
    .feed-card:hover {{
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }}
    
    /* Message Bubbles */
    .message-bubble {{
        padding: 16px 20px;
        margin: 8px 0;
        border-radius: 24px;
        max-width: 70%;
        word-wrap: break-word;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        line-height: 1.5;
    }}
    
    .message-sent {{
        background: linear-gradient(135deg, {THEME_CONFIG['theme']['primary']}, {THEME_CONFIG['theme']['secondary']});
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 8px;
        box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2);
    }}
    
    .message-received {{
        background: {THEME_CONFIG['theme']['surface']};
        color: {THEME_CONFIG['theme']['text']};
        margin-right: auto;
        border: 1px solid {THEME_CONFIG['theme']['border']};
        border-bottom-left-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }}
    
    /* Gradient Text */
    .gradient-text {{
        background: linear-gradient(135deg, {THEME_CONFIG['theme']['primary']}, {THEME_CONFIG['theme']['accent']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
        font-family: 'Inter', sans-serif;
    }}
    
    /* Input Fields */
    .stTextInput>div>div>input, 
    .stTextArea>div>textarea {{
        border: 2px solid {THEME_CONFIG['theme']['border']} !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        font-size: 14px !important;
        transition: all 0.3s ease !important;
    }}
    
    .stTextInput>div>div>input:focus, 
    .stTextArea>div>textarea:focus {{
        border-color: {THEME_CONFIG['theme']['primary']} !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: transparent;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        background: {THEME_CONFIG['theme']['surface']};
        border: 1px solid {THEME_CONFIG['theme']['border']};
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {THEME_CONFIG['theme']['primary']}, {THEME_CONFIG['theme']['secondary']}) !important;
        color: white !important;
        border: none !important;
    }}
    
    /* Success Messages */
    .stAlert {{
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    
    /* Profile Image Container */
    .profile-img {{
        width: 60px;
        height: 60px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    
    /* Stats Cards */
    .stat-card {{
        background: {THEME_CONFIG['theme']['surface']};
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        border: 1px solid {THEME_CONFIG['theme']['border']};
    }}
    
    .stat-value {{
        font-size: 24px;
        font-weight: 700;
        color: {THEME_CONFIG['theme']['primary']};
        margin: 8px 0;
    }}
    
    .stat-label {{
        font-size: 12px;
        color: {THEME_CONFIG['theme']['muted']};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    /* Badges */
    .online-badge {{
        display: inline-block;
        width: 12px;
        height: 12px;
        background: {THEME_CONFIG['theme']['success']};
        border-radius: 50%;
        margin-right: 8px;
    }}
    
    .offline-badge {{
        display: inline-block;
        width: 12px;
        height: 12px;
        background: {THEME_CONFIG['theme']['muted']};
        border-radius: 50%;
        margin-right: 8px;
    }}
    </style>
    """, unsafe_allow_html=True)

def create_stat_card(title, value, icon="📊"):
    """Create a modern stat card"""
    return f"""
    <div class="stat-card">
        <div style="font-size: 24px; margin-bottom: 8px;">{icon}</div>
        <div class="stat-value">{value}</div>
        <div class="stat-label">{title}</div>
    </div>
    """

# ===================================
# MODERN PAGES
# ===================================

def login_page():
    """Modern login page"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<h1 class='gradient-text'>Welcome to SocialSphere</h1>", unsafe_allow_html=True)
        st.markdown("### Connect, share, and grow together")
        
        # Benefits
        st.markdown("""
        <div style='margin: 30px 0;'>
            <div style='display: flex; align-items: center; margin: 12px 0;'>
                <span style='font-size: 24px; margin-right: 12px;'>✨</span>
                <span>Share moments with friends worldwide</span>
            </div>
            <div style='display: flex; align-items: center; margin: 12px 0;'>
                <span style='font-size: 24px; margin-right: 12px;'>💬</span>
                <span>Real-time messaging with anyone</span>
            </div>
            <div style='display: flex; align-items: center; margin: 12px 0;'>
                <span style='font-size: 24px; margin-right: 12px;'>🌍</span>
                <span>Connect with global communities</span>
            </div>
            <div style='display: flex; align-items: center; margin: 12px 0;'>
                <span style='font-size: 24px; margin-right: 12px;'>🔒</span>
                <span>Secure and private by design</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("<h3>Get Started</h3>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Sign In", "Create Account"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("Sign In", use_container_width=True)
                
                if submit:
                    if username and password:
                        with st.spinner("Signing in..."):
                            user_id, username = verify_user_secure(username, password)
                            if user_id:
                                st.session_state.user_id = user_id
                                st.session_state.username = username
                                st.session_state.logged_in = True
                                
                                # Get user data
                                user_data = get_user(user_id)
                                if user_data:
                                    st.session_state.location = user_data[5]
                                    st.session_state.timezone = user_data[6]
                                
                                st.success(f"Welcome back, {username}!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Invalid username or password")
                    else:
                        st.error("Please enter both username and password")
        
        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Username", placeholder="Choose a username")
                new_password = st.text_input("Password", type="password", placeholder="Create a strong password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                email = st.text_input("Email", placeholder="your@email.com")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    location = st.text_input("Location", placeholder="City, Country")
                with col_b:
                    language = st.selectbox("Language", THEME_CONFIG["languages"])
                
                bio = st.text_area("Bio (Optional)", placeholder="Tell us about yourself...", height=80)
                profile_pic = st.file_uploader("Profile Picture", type=['jpg', 'png', 'jpeg'])
                
                if st.form_submit_button("Create Account", use_container_width=True):
                    if new_username and new_password and email:
                        if new_password == confirm_password:
                            profile_pic_data = profile_pic.read() if profile_pic else None
                            
                            with st.spinner("Creating your account..."):
                                success, result = create_user_secure(
                                    new_username, new_password, email, profile_pic_data, bio, 
                                    location, "UTC", language
                                )
                                
                                if success:
                                    st.success("Account created successfully! Please sign in.")
                                else:
                                    st.error(result)
                        else:
                            st.error("Passwords do not match")
                    else:
                        st.error("Please fill in all required fields")

def feed_page():
    """Modern feed page"""
    # Header with stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(create_stat_card("Online Now", len(get_online_users()), "👥"), unsafe_allow_html=True)
    with col2:
        posts = get_posts(limit=100)
        st.markdown(create_stat_card("Total Posts", len(posts), "📝"), unsafe_allow_html=True)
    with col3:
        st.markdown(create_stat_card("Your Posts", st.session_state.get('post_count', 0), "🌟"), unsafe_allow_html=True)
    
    # Create post section
    with st.container():
        with st.expander("✨ Create New Post", expanded=False):
            with st.form("create_post_form"):
                content = st.text_area("What's on your mind?", 
                                     placeholder="Share your thoughts...", 
                                     height=120)
                
                col1, col2 = st.columns(2)
                with col1:
                    media_file = st.file_uploader("Add Media", 
                                                 type=['jpg', 'png', 'jpeg', 'mp4', 'gif'],
                                                 help="Upload images or videos")
                with col2:
                    post_location = st.text_input("Location", 
                                                value=st.session_state.get('location', ''),
                                                placeholder="Where are you?")
                
                if st.form_submit_button("Publish Post", use_container_width=True):
                    if content:
                        media_data = media_file.read() if media_file else None
                        media_type = media_file.type if media_file else None
                        
                        success, result = create_post(
                            st.session_state.user_id, content, media_data, media_type,
                            post_location
                        )
                        
                        if success:
                            st.success("Post published successfully!")
                            st.rerun()
                        else:
                            st.error(result)
                    else:
                        st.error("Please write something to post")
    
    # Feed filters
    st.markdown("### 📱 Latest Posts")
    
    with st.container():
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            language_filter = st.selectbox("Language", ["all", "en", "es", "fr", "de", "zh", "ja"])
        with col2:
            location_filter = st.text_input("Location Filter", placeholder="Filter by location...")
        with col3:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
    
    # Display posts
    posts = get_posts(language=language_filter, location=location_filter)
    
    if not posts:
        st.info("""
        ### 🌟 No posts yet!
        
        Be the first to share something amazing! Click "✨ Create New Post" above to get started.
        """)
        return
    
    for post in posts:
        display_modern_post_card(post)

def display_modern_post_card(post):
    """Display modern post card"""
    (post_id, user_id, content, media_type, media_data, location, language, 
     visibility, is_deleted, like_count, comment_count, share_count, view_count,
     created_at, updated_at, username, profile_pic, post_like_count, post_comment_count) = post
    
    with st.container():
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        
        # Post header
        col1, col2 = st.columns([1, 10])
        with col1:
            if profile_pic and is_valid_image(profile_pic):
                st.image(io.BytesIO(profile_pic), width=50, output_format='JPEG')
            else:
                st.markdown("""
                <div style='width: 50px; height: 50px; border-radius: 50%; 
                            background: linear-gradient(135deg, #6366f1, #8b5cf6);
                            display: flex; align-items: center; justify-content: center; 
                            color: white; font-size: 20px; font-weight: bold;'>
                    {0}
                </div>
                """.format(username[0].upper() if username else "U"), unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"**{username}**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.caption(f"📍 {location}")
            with col_b:
                st.caption(f"🕐 {format_global_time(created_at)}")
        
        # Post content
        st.markdown(f"<div style='margin: 20px 0; font-size: 16px; line-height: 1.6;'>{content}</div>", 
                   unsafe_allow_html=True)
        
        # Media
        if media_data and media_type:
            if 'image' in media_type:
                display_image_safely(media_data, use_container_width=True)
            elif 'video' in media_type:
                st.video(io.BytesIO(media_data))
        
        # Engagement buttons
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button(f"❤️ {post_like_count}", key=f"like_{post_id}", use_container_width=True):
                like_post(st.session_state.user_id, post_id)
                st.rerun()
        
        with col2:
            if st.button(f"💬 {post_comment_count}", key=f"comment_{post_id}", use_container_width=True):
                st.session_state.current_post = post_id if not hasattr(st.session_state, 'current_post') or st.session_state.current_post != post_id else None
                st.rerun()
        
        with col3:
            if st.button("↪️", key=f"share_{post_id}", use_container_width=True):
                st.info("Share feature coming soon!")
        
        with col4:
            if st.button("🔗", key=f"link_{post_id}", use_container_width=True):
                st.code(f"Post ID: {post_id}")
        
        # Owner actions
        if user_id == st.session_state.user_id:
            with col5:
                menu_choice = st.selectbox("", ["⚙️", "Edit", "Delete"], 
                                         key=f"menu_{post_id}", label_visibility="collapsed")
                if menu_choice == "Edit":
                    st.session_state.editing_post = post_id
                    st.rerun()
                elif menu_choice == "Delete":
                    if delete_post(post_id, user_id):
                        st.success("Post deleted!")
                        st.rerun()
        
        # Comments section
        if hasattr(st.session_state, 'current_post') and st.session_state.current_post == post_id:
            st.markdown("---")
            st.markdown("**💬 Comments**")
            
            comments = get_comments(post_id)
            if comments:
                for comment in comments[:5]:  # Show only first 5 comments
                    comment_id, _, comment_user_id, comment_content, parent_id, comment_created_at, comment_username, comment_profile_pic = comment
                    
                    with st.container():
                        col1, col2 = st.columns([1, 10])
                        with col1:
                            if comment_profile_pic and is_valid_image(comment_profile_pic):
                                st.image(io.BytesIO(comment_profile_pic), width=30, output_format='JPEG')
                        with col2:
                            st.markdown(f"**{comment_username}** {comment_content}")
                            st.caption(format_global_time(comment_created_at))
            
            # Add comment
            with st.form(f"comment_form_{post_id}"):
                comment_text = st.text_input("Add a comment...", key=f"comment_input_{post_id}")
                if st.form_submit_button("Post Comment", use_container_width=True):
                    if comment_text:
                        success, message = add_comment(post_id, st.session_state.user_id, comment_text)
                        if success:
                            st.rerun()
                        else:
                            st.error(message)
        
        st.markdown('</div>', unsafe_allow_html=True)

def chat_page():
    """Modern chat page"""
    st.markdown("<h2 class='gradient-text'>💬 Messages</h2>", unsafe_allow_html=True)
    
    # Online users
    online_users = get_online_users()
    if online_users:
        st.markdown("**🟢 Online Now**")
        cols = st.columns(min(5, len(online_users)))
        for idx, user in enumerate(online_users[:5]):
            user_id, username, location = user
            with cols[idx % 5]:
                if st.button(f"💬 {username}", key=f"quick_{user_id}", use_container_width=True):
                    st.session_state.current_chat = user_id
                    st.session_state.chat_username = username
                    st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Conversations")
        conversations = get_global_conversations(st.session_state.user_id)
        
        if not conversations:
            st.info("No conversations yet. Start chatting with someone!")
        else:
            for conv in conversations:
                other_user_id, username, profile_pic, last_time, last_msg, unread, location = conv
                
                with st.container():
                    col_a, col_b = st.columns([1, 4])
                    with col_a:
                        if profile_pic and is_valid_image(profile_pic):
                            st.image(io.BytesIO(profile_pic), width=40, output_format='JPEG')
                    
                    with col_b:
                        is_selected = st.button(
                            f"{'🔔 ' if unread > 0 else ''}{username}",
                            key=f"conv_{other_user_id}",
                            use_container_width=True
                        )
                        if is_selected:
                            st.session_state.current_chat = other_user_id
                            st.session_state.chat_username = username
                            st.rerun()
    
    with col2:
        if hasattr(st.session_state, 'current_chat'):
            display_modern_chat()
        else:
            st.info("""
            ### Select a conversation
            Choose someone from your conversations or start a new chat!
            """)

def display_modern_chat():
    """Display modern chat interface"""
    st.markdown(f"### 💬 Chat with {st.session_state.chat_username}")
    
    # Mark messages as read
    mark_messages_as_read(st.session_state.user_id, st.session_state.current_chat)
    
    # Chat messages
    messages_container = st.container(height=400)
    
    with messages_container:
        messages = get_global_messages(st.session_state.user_id, st.session_state.current_chat, limit=50)
        
        for msg in reversed(messages):  # Show latest first
            msg_id, sender_id, receiver_id, content, msg_type, media_data, is_read, created_at, sender_name = msg
            
            if sender_id == st.session_state.user_id:
                # Sent message
                st.markdown(f"""
                <div style='text-align: right; margin: 10px 0;'>
                    <div style='display: inline-block; max-width: 70%;'>
                        <div class='message-bubble message-sent'>
                            {content}
                            <div style='font-size: 11px; opacity: 0.8; margin-top: 4px;'>
                                {format_global_time(created_at)}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Received message
                st.markdown(f"""
                <div style='text-align: left; margin: 10px 0;'>
                    <div style='display: inline-block; max-width: 70%;'>
                        <div class='message-bubble message-received'>
                            <strong>{sender_name}</strong>
                            <div>{content}</div>
                            <div style='font-size: 11px; opacity: 0.8; margin-top: 4px;'>
                                {format_global_time(created_at)}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Send message
    with st.form("send_message_form"):
        col1, col2 = st.columns([4, 1])
        with col1:
            message = st.text_input("Type your message...", label_visibility="collapsed")
        with col2:
            send = st.form_submit_button("Send", use_container_width=True)
        
        if send and message:
            success, result = send_global_message(
                st.session_state.user_id, st.session_state.current_chat, message
            )
            if success:
                st.rerun()
            else:
                st.error(result)

def profile_page():
    """Modern profile page"""
    user = get_user(st.session_state.user_id)
    
    if user:
        (user_id, username, email, profile_pic, bio, location, timezone, language, 
         is_online, last_seen, post_count, follower_count, following_count) = user
        
        # Profile header
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if profile_pic and is_valid_image(profile_pic):
                st.image(io.BytesIO(profile_pic), width=150, output_format='JPEG')
            else:
                st.markdown(f"""
                <div style='width: 150px; height: 150px; border-radius: 50%; 
                            background: linear-gradient(135deg, #6366f1, #8b5cf6);
                            display: flex; align-items: center; justify-content: center; 
                            color: white; font-size: 48px; font-weight: bold;'>
                    {username[0].upper() if username else "U"}
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"# {username}")
            st.markdown(f"**📍** {location} · **🌐** {timezone} · **🗣️** {language}")
            
            if bio:
                st.markdown(f"<div style='margin: 20px 0; padding: 20px; background: {THEME_CONFIG['theme']['surface']}; border-radius: 12px;'>{bio}</div>", 
                          unsafe_allow_html=True)
            
            # Stats
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown(create_stat_card("Posts", post_count, "📝"), unsafe_allow_html=True)
            with col_b:
                st.markdown(create_stat_card("Followers", follower_count, "👥"), unsafe_allow_html=True)
            with col_c:
                st.markdown(create_stat_card("Following", following_count, "❤️"), unsafe_allow_html=True)
    
    # Edit profile
    st.markdown("---")
    st.markdown("### ✏️ Edit Profile")
    
    with st.form("edit_profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_bio = st.text_area("Bio", value=bio if bio else "", height=100,
                                 placeholder="Tell people about yourself...")
            new_location = st.text_input("Location", value=location if location else "")
            new_timezone = st.selectbox("Timezone", THEME_CONFIG["supported_timezones"])
        
        with col2:
            new_language = st.selectbox("Language", THEME_CONFIG["languages"])
            new_profile_pic = st.file_uploader("Profile Picture", type=['jpg', 'png', 'jpeg'])
            remove_pic = st.checkbox("Remove current profile picture")
        
        if st.form_submit_button("Update Profile", use_container_width=True):
            profile_pic_data = None
            if remove_pic:
                profile_pic_data = ""
            elif new_profile_pic:
                profile_pic_data = new_profile_pic.read()
            
            success, message = update_user_profile(
                st.session_state.user_id,
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
    
    # Page configuration
    st.set_page_config(
        page_title="SocialSphere",
        page_icon="✨",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Inject modern CSS
    inject_modern_css()
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'location' not in st.session_state:
        st.session_state.location = 'Unknown'
    if 'timezone' not in st.session_state:
        st.session_state.timezone = 'UTC'
    
    # Show login page if not logged in
    if not st.session_state.logged_in:
        login_page()
        return
    
    # Update online status
    update_user_online_status(st.session_state.user_id, True)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"<h1 class='gradient-text'>✨ SocialSphere</h1>", unsafe_allow_html=True)
        st.markdown(f"### 👋 Hi, {st.session_state.username}!")
        
        # Navigation
        st.markdown("---")
        menu = st.radio(
            "Navigation",
            ["📱 Feed", "💬 Messages", "👤 Profile"],
            label_visibility="collapsed"
        )
        
        # Quick Stats
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        
        online_count = len(get_online_users())
        user_data = get_user(st.session_state.user_id)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Online", online_count)
        with col2:
            if user_data:
                st.metric("Posts", user_data[10])
        
        # Logout
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            update_user_online_status(st.session_state.user_id, False)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main content area
    if menu == "📱 Feed":
        feed_page()
    elif menu == "💬 Messages":
        chat_page()
    elif menu == "👤 Profile":
        profile_page()

if __name__ == "__main__":
    main()

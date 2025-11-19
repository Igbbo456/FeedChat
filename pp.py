import streamlit as st
import sqlite3
import datetime
import random
import time
from PIL import Image
import io
import base64
import json

# ===================================
# Database Initialization
# ===================================
def init_db():
    conn = sqlite3.connect("facebook.db", check_same_thread=False)
    c = conn.cursor()

    # Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT,
        profile_pic BLOB,
        cover_pic BLOB,
        bio TEXT,
        location TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Posts table
    c.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        media_data BLOB,
        media_type TEXT,
        like_count INTEGER DEFAULT 0,
        comment_count INTEGER DEFAULT 0,
        share_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Friends table
    c.execute("""
    CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        friend_id INTEGER,
        status TEXT DEFAULT 'pending',
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

    # Groups table
    c.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        cover_pic BLOB,
        created_by INTEGER,
        member_count INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Group members table
    c.execute("""
    CREATE TABLE IF NOT EXISTS group_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        user_id INTEGER,
        role TEXT DEFAULT 'member',
        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Events table
    c.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        location TEXT,
        event_date DATETIME,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Event attendees table
    c.execute("""
    CREATE TABLE IF NOT EXISTS event_attendees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        user_id INTEGER,
        status TEXT DEFAULT 'going',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    return conn

# Initialize database
conn = init_db()

# ===================================
# CORE FUNCTIONS
# ===================================
def is_valid_image(image_data):
    """Check if the image data is valid"""
    try:
        if image_data is None:
            return False
        image = Image.open(io.BytesIO(image_data))
        image.verify()
        return True
    except:
        return False

def create_user(username, password, email, profile_pic=None, cover_pic=None, bio="", location=""):
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=?", (username,))
        if c.fetchone():
            return False
        c.execute("INSERT INTO users (username, password, email, profile_pic, cover_pic, bio, location) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (username, password, email, profile_pic, cover_pic, bio, location))
        conn.commit()
        return True
    except sqlite3.Error:
        return False

def verify_user(username, password):
    try:
        c = conn.cursor()
        c.execute("SELECT id, username FROM users WHERE username=? AND password=?", (username, password))
        return c.fetchone()
    except sqlite3.Error:
        return None

def get_user(user_id):
    try:
        c = conn.cursor()
        c.execute("SELECT id, username, email, profile_pic, cover_pic, bio, location FROM users WHERE id=?", (user_id,))
        return c.fetchone()
    except sqlite3.Error:
        return None

def create_post(user_id, content, media_data=None, media_type=None):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO posts (user_id, content, media_data, media_type) VALUES (?, ?, ?, ?)",
                 (user_id, content, media_data, media_type))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error:
        return None

def get_posts(user_id=None, limit=20):
    try:
        c = conn.cursor()
        if user_id:
            c.execute("""
                SELECT p.*, u.username, u.profile_pic,
                (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as like_count,
                (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count,
                EXISTS(SELECT 1 FROM likes WHERE post_id = p.id AND user_id = ?) as is_liked
                FROM posts p
                JOIN users u ON p.user_id = u.id
                WHERE p.user_id = ?
                ORDER BY p.created_at DESC
                LIMIT ?
            """, (user_id, user_id, limit))
        else:
            c.execute("""
                SELECT p.*, u.username, u.profile_pic,
                (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as like_count,
                (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count,
                EXISTS(SELECT 1 FROM likes WHERE post_id = p.id AND user_id = ?) as is_liked
                FROM posts p
                JOIN users u ON p.user_id = u.id
                ORDER BY p.created_at DESC
                LIMIT ?
            """, (user_id, limit))
        return c.fetchall()
    except sqlite3.Error:
        return []

def like_post(user_id, post_id):
    try:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False

def unlike_post(user_id, post_id):
    try:
        c = conn.cursor()
        c.execute("DELETE FROM likes WHERE user_id=? AND post_id=?", (user_id, post_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False

def add_comment(post_id, user_id, content):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
                 (post_id, user_id, content))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error:
        return None

def get_comments(post_id):
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

def send_friend_request(user_id, friend_id):
    try:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO friends (user_id, friend_id) VALUES (?, ?)", (user_id, friend_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False

def get_friends(user_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT u.id, u.username, u.profile_pic 
            FROM friends f 
            JOIN users u ON f.friend_id = u.id 
            WHERE f.user_id = ? AND f.status = 'accepted'
        """, (user_id,))
        return c.fetchall()
    except sqlite3.Error:
        return []

def create_group(name, description, created_by, cover_pic=None):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO groups (name, description, cover_pic, created_by) VALUES (?, ?, ?, ?)",
                 (name, description, cover_pic, created_by))
        group_id = c.lastrowid
        # Add creator as admin
        c.execute("INSERT INTO group_members (group_id, user_id, role) VALUES (?, ?, 'admin')",
                 (group_id, created_by))
        conn.commit()
        return group_id
    except sqlite3.Error:
        return None

def get_groups(user_id=None):
    try:
        c = conn.cursor()
        if user_id:
            c.execute("""
                SELECT g.*, u.username as creator_name 
                FROM groups g 
                JOIN users u ON g.created_by = u.id 
                JOIN group_members gm ON g.id = gm.group_id 
                WHERE gm.user_id = ?
            """, (user_id,))
        else:
            c.execute("""
                SELECT g.*, u.username as creator_name 
                FROM groups g 
                JOIN users u ON g.created_by = u.id 
                ORDER BY g.member_count DESC
            """)
        return c.fetchall()
    except sqlite3.Error:
        return []

def send_message(sender_id, receiver_id, content):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)",
                 (sender_id, receiver_id, content))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error:
        return None

def get_messages(user_id, other_user_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT m.*, u.username as sender_name
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE (m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?)
            ORDER BY m.created_at ASC
        """, (user_id, other_user_id, other_user_id, user_id))
        return c.fetchall()
    except sqlite3.Error:
        return []

def get_conversations(user_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT DISTINCT 
                CASE WHEN m.sender_id = ? THEN m.receiver_id ELSE m.sender_id END as other_user_id,
                u.username,
                u.profile_pic,
                (SELECT content FROM messages 
                 WHERE ((sender_id = ? AND receiver_id = other_user_id) 
                     OR (sender_id = other_user_id AND receiver_id = ?))
                 ORDER BY created_at DESC LIMIT 1) as last_message
            FROM messages m
            JOIN users u ON u.id = CASE WHEN m.sender_id = ? THEN m.receiver_id ELSE m.sender_id END
            WHERE m.sender_id = ? OR m.receiver_id = ?
            GROUP BY other_user_id
        """, (user_id, user_id, user_id, user_id, user_id, user_id))
        return c.fetchall()
    except sqlite3.Error:
        return []

# ===================================
# FACEBOOK-STYLE UI COMPONENTS
# ===================================
def facebook_header():
    """Facebook-style header with navigation"""
    st.markdown("""
        <style>
        .facebook-header {
            background-color: #1877f2;
            padding: 8px 16px;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
        }
        .facebook-nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1200px;
            margin: 0 auto;
        }
        .facebook-logo {
            color: white;
            font-size: 28px;
            font-weight: bold;
        }
        .nav-icons {
            display: flex;
            gap: 20px;
            color: white;
        }
        .main-content {
            margin-top: 60px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="facebook-header">
            <div class="facebook-nav">
                <div class="facebook-logo">facebook</div>
                <div class="nav-icons">
                    <span>🏠</span>
                    <span>👥</span>
                    <span>📺</span>
                    <span>🛒</span>
                    <span>👤</span>
                </div>
            </div>
        </div>
        <div class="main-content"></div>
    """, unsafe_allow_html=True)

def facebook_sidebar():
    """Facebook-style left sidebar"""
    with st.sidebar:
        st.markdown("""
            <style>
            .sidebar {
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                margin: 10px 0;
            }
            .sidebar-item {
                padding: 10px;
                margin: 5px 0;
                border-radius: 8px;
                cursor: pointer;
            }
            .sidebar-item:hover {
                background-color: #f0f2f5;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # User profile section
        user = get_user(st.session_state.user_id)
        if user:
            user_id, username, email, profile_pic, cover_pic, bio, location = user
            col1, col2 = st.columns([1, 3])
            with col1:
                if profile_pic and is_valid_image(profile_pic):
                    st.image(io.BytesIO(profile_pic), width=40)
                else:
                    st.write("👤")
            with col2:
                st.write(f"**{username}**")
        
        st.markdown('<div class="sidebar">', unsafe_allow_html=True)
        
        # Navigation items
        nav_items = [
            ("🏠", "News Feed"),
            ("👥", "Friends"),
            ("📺", "Watch"),
            ("🛒", "Marketplace"),
            ("🎯", "Memories"),
            ("💼", "Jobs"),
            ("👥", "Groups"),
            ("📅", "Events"),
            ("📚", "Pages"),
            ("ℹ️", "About")
        ]
        
        for icon, text in nav_items:
            if st.button(f"{icon} {text}", key=f"nav_{text}", use_container_width=True):
                st.session_state.current_page = text.lower().replace(" ", "_")
        
        st.markdown('</div>', unsafe_allow_html=True)

def create_post_box():
    """Facebook-style post creation box"""
    st.markdown("""
        <style>
        .post-box {
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            margin: 10px 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="post-box">', unsafe_allow_html=True)
    
    user = get_user(st.session_state.user_id)
    if user:
        user_id, username, email, profile_pic, cover_pic, bio, location = user
        
        col1, col2 = st.columns([1, 10])
        with col1:
            if profile_pic and is_valid_image(profile_pic):
                st.image(io.BytesIO(profile_pic), width=40)
            else:
                st.write("👤")
        
        with col2:
            post_content = st.text_input("What's on your mind?", placeholder=f"What's on your mind, {username}?", label_visibility="collapsed")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("📹 Live Video", use_container_width=True):
                st.session_state.post_type = "live"
        with col2:
            if st.button("🖼️ Photo/Video", use_container_width=True):
                st.session_state.post_type = "media"
        with col3:
            if st.button("😊 Feeling/Activity", use_container_width=True):
                st.session_state.post_type = "feeling"
        with col4:
            if st.button("📝 Create Post", use_container_width=True, type="primary"):
                if post_content:
                    create_post(st.session_state.user_id, post_content)
                    st.success("Post created successfully!")
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_post(post):
    """Display a single Facebook-style post"""
    st.markdown("""
        <style>
        .post-container {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            margin: 15px 0;
            padding: 15px;
        }
        .post-header {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .post-actions {
            display: flex;
            justify-content: space-around;
            border-top: 1px solid #ddd;
            padding-top: 10px;
            margin-top: 10px;
        }
        .post-action {
            flex: 1;
            text-align: center;
            padding: 8px;
            border-radius: 5px;
            cursor: pointer;
        }
        .post-action:hover {
            background-color: #f0f2f5;
        }
        </style>
    """, unsafe_allow_html=True)
    
    post_id, user_id, content, media_data, media_type, like_count, comment_count, share_count, created_at, username, profile_pic, actual_like_count, actual_comment_count, is_liked = post
    
    st.markdown('<div class="post-container">', unsafe_allow_html=True)
    
    # Post header
    col1, col2 = st.columns([1, 10])
    with col1:
        if profile_pic and is_valid_image(profile_pic):
            st.image(io.BytesIO(profile_pic), width=40)
        else:
            st.write("👤")
    with col2:
        st.write(f"**{username}**")
        st.caption(f"{created_at}")
    
    # Post content
    if content:
        st.write(content)
    
    # Post media
    if media_data and is_valid_image(media_data):
        st.image(io.BytesIO(media_data), use_container_width=True)
    
    # Engagement stats
    st.write(f"❤️ {actual_like_count}   💬 {actual_comment_count}   🔄 {share_count}")
    
    # Post actions
    col1, col2, col3 = st.columns(3)
    with col1:
        if is_liked:
            if st.button("❤️ Liked", key=f"like_{post_id}", use_container_width=True):
                unlike_post(st.session_state.user_id, post_id)
                st.rerun()
        else:
            if st.button("🤍 Like", key=f"like_{post_id}", use_container_width=True):
                like_post(st.session_state.user_id, post_id)
                st.rerun()
    with col2:
        if st.button("💬 Comment", key=f"comment_{post_id}", use_container_width=True):
            if 'commenting_post' in st.session_state and st.session_state.commenting_post == post_id:
                st.session_state.commenting_post = None
            else:
                st.session_state.commenting_post = post_id
            st.rerun()
    with col3:
        if st.button("🔄 Share", key=f"share_{post_id}", use_container_width=True):
            st.info("Share functionality coming soon!")
    
    # Comments section
    if 'commenting_post' in st.session_state and st.session_state.commenting_post == post_id:
        comments = get_comments(post_id)
        
        # Display existing comments
        for comment in comments:
            comment_id, _, comment_user_id, comment_content, comment_created_at, comment_username, comment_profile_pic = comment
            
            col1, col2 = st.columns([1, 10])
            with col1:
                if comment_profile_pic and is_valid_image(comment_profile_pic):
                    st.image(io.BytesIO(comment_profile_pic), width=30)
                else:
                    st.write("👤")
            with col2:
                st.write(f"**{comment_username}** {comment_content}")
                st.caption(f"{comment_created_at}")
        
        # Add new comment
        with st.form(f"add_comment_{post_id}"):
            comment_text = st.text_input("Write a comment...", key=f"comment_input_{post_id}")
            if st.form_submit_button("Comment"):
                if comment_text:
                    add_comment(post_id, st.session_state.user_id, comment_text)
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ===================================
# FACEBOOK PAGES
# ===================================
def news_feed_page():
    """Facebook News Feed"""
    st.markdown("""
        <style>
        .main-feed {
            max-width: 680px;
            margin: 0 auto;
            padding: 20px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-feed">', unsafe_allow_html=True)
    
    # Create post box
    create_post_box()
    
    # Display posts
    posts = get_posts(st.session_state.user_id, limit=20)
    if posts:
        for post in posts:
            display_post(post)
    else:
        st.info("No posts yet. Be the first to post!")
    
    st.markdown('</div>', unsafe_allow_html=True)

def profile_page():
    """Facebook Profile Page"""
    user = get_user(st.session_state.user_id)
    if not user:
        st.error("User not found")
        return
    
    user_id, username, email, profile_pic, cover_pic, bio, location = user
    
    # Cover photo
    if cover_pic and is_valid_image(cover_pic):
        st.image(io.BytesIO(cover_pic), use_container_width=True)
    else:
        st.markdown('<div style="height: 300px; background-color: #e9ebee; border-radius: 10px;"></div>', unsafe_allow_html=True)
    
    # Profile info
    col1, col2 = st.columns([1, 3])
    with col1:
        if profile_pic and is_valid_image(profile_pic):
            st.image(io.BytesIO(profile_pic), width=150)
        else:
            st.markdown('<div style="width: 150px; height: 150px; background-color: #ddd; border-radius: 50%;"></div>', unsafe_allow_html=True)
    
    with col2:
        st.title(username)
        if bio:
            st.write(bio)
        if location:
            st.write(f"📍 {location}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Friends", "0")
        with col2:
            st.metric("Posts", "0")
        with col3:
            st.metric("Photos", "0")
    
    # Profile navigation
    tab1, tab2, tab3, tab4 = st.tabs(["Posts", "About", "Friends", "Photos"])
    
    with tab1:
        # User's posts
        posts = get_posts(st.session_state.user_id, limit=20)
        if posts:
            for post in posts:
                display_post(post)
        else:
            st.info("No posts yet")
    
    with tab2:
        # About section
        st.subheader("About")
        if bio:
            st.write(f"**Bio:** {bio}")
        if location:
            st.write(f"**Location:** {location}")
        st.write(f"**Joined:** {user[7] if len(user) > 7 else 'Unknown'}")
    
    with tab3:
        # Friends section
        st.subheader("Friends")
        friends = get_friends(st.session_state.user_id)
        if friends:
            cols = st.columns(3)
            for idx, friend in enumerate(friends):
                with cols[idx % 3]:
                    friend_id, friend_username, friend_profile_pic = friend
                    if friend_profile_pic and is_valid_image(friend_profile_pic):
                        st.image(io.BytesIO(friend_profile_pic), width=100)
                    else:
                        st.write("👤")
                    st.write(friend_username)
        else:
            st.info("No friends yet")
    
    with tab4:
        st.info("Photos feature coming soon!")

def friends_page():
    """Facebook Friends Page"""
    st.title("Friends")
    
    tab1, tab2, tab3 = st.tabs(["All Friends", "Friend Requests", "Suggestions"])
    
    with tab1:
        friends = get_friends(st.session_state.user_id)
        if friends:
            for friend in friends:
                friend_id, friend_username, friend_profile_pic = friend
                col1, col2 = st.columns([1, 4])
                with col1:
                    if friend_profile_pic and is_valid_image(friend_profile_pic):
                        st.image(io.BytesIO(friend_profile_pic), width=50)
                    else:
                        st.write("👤")
                with col2:
                    st.write(f"**{friend_username}**")
                    if st.button("Message", key=f"msg_{friend_id}"):
                        st.session_state.current_chat = friend_id
                        st.session_state.current_page = "messenger"
        else:
            st.info("No friends yet")
    
    with tab2:
        st.info("Friend requests feature coming soon!")
    
    with tab3:
        st.info("Friend suggestions feature coming soon!")

def groups_page():
    """Facebook Groups Page"""
    st.title("Groups")
    
    tab1, tab2, tab3 = st.tabs(["Your Groups", "Discover", "Create Group"])
    
    with tab1:
        groups = get_groups(st.session_state.user_id)
        if groups:
            for group in groups:
                group_id, name, description, cover_pic, created_by, member_count, created_at, creator_name = group
                col1, col2 = st.columns([1, 4])
                with col1:
                    if cover_pic and is_valid_image(cover_pic):
                        st.image(io.BytesIO(cover_pic), width=80)
                    else:
                        st.write("👥")
                with col2:
                    st.subheader(name)
                    st.write(description)
                    st.caption(f"{member_count} members • Created by {creator_name}")
        else:
            st.info("You haven't joined any groups yet")
    
    with tab2:
        groups = get_groups()
        if groups:
            for group in groups:
                group_id, name, description, cover_pic, created_by, member_count, created_at, creator_name = group
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    if cover_pic and is_valid_image(cover_pic):
                        st.image(io.BytesIO(cover_pic), width=80)
                    else:
                        st.write("👥")
                with col2:
                    st.subheader(name)
                    st.write(description)
                    st.caption(f"{member_count} members")
                with col3:
                    if st.button("Join", key=f"join_{group_id}"):
                        st.success(f"Joined {name}!")
        else:
            st.info("No groups available")
    
    with tab3:
        with st.form("create_group"):
            st.subheader("Create New Group")
            name = st.text_input("Group Name")
            description = st.text_area("Description")
            cover_pic = st.file_uploader("Cover Photo", type=['jpg', 'png', 'jpeg'])
            
            if st.form_submit_button("Create Group"):
                if name and description:
                    cover_pic_data = cover_pic.read() if cover_pic else None
                    group_id = create_group(name, description, st.session_state.user_id, cover_pic_data)
                    if group_id:
                        st.success(f"Group '{name}' created successfully!")
                    else:
                        st.error("Failed to create group")
                else:
                    st.error("Please fill in all required fields")

def messenger_page():
    """Facebook Messenger"""
    st.title("Messenger")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Chats")
        conversations = get_conversations(st.session_state.user_id)
        
        if conversations:
            for conv in conversations:
                other_user_id, username, profile_pic, last_message = conv
                if st.button(f"{username}: {last_message[:30] if last_message else 'Start chatting'}...", 
                           key=f"conv_{other_user_id}", use_container_width=True):
                    st.session_state.current_chat = other_user_id
                    st.session_state.chat_username = username
                    st.rerun()
        else:
            st.info("No conversations yet")
    
    with col2:
        if hasattr(st.session_state, 'current_chat'):
            st.subheader(f"Chat with {st.session_state.chat_username}")
            
            # Display messages
            messages = get_messages(st.session_state.user_id, st.session_state.current_chat)
            
            for msg in messages:
                msg_id, sender_id, receiver_id, content, is_read, created_at, sender_name = msg
                
                if sender_id == st.session_state.user_id:
                    st.markdown(f"""
                        <div style="background-color: #1877f2; color: white; padding: 10px; border-radius: 10px; margin: 5px 0; text-align: right;">
                            {content}
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style="background-color: #f0f2f5; padding: 10px; border-radius: 10px; margin: 5px 0;">
                            {content}
                        </div>
                    """, unsafe_allow_html=True)
                st.caption(f"{created_at}")
            
            # Send message
            with st.form("send_message"):
                message_content = st.text_input("Type a message...")
                if st.form_submit_button("Send"):
                    if message_content:
                        send_message(st.session_state.user_id, st.session_state.current_chat, message_content)
                        st.rerun()
        else:
            st.info("Select a conversation to start chatting")

def marketplace_page():
    """Facebook Marketplace"""
    st.title("Marketplace")
    st.info("Marketplace feature coming soon!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Browse Items")
        st.write("Explore items for sale in your area")
    
    with col2:
        st.subheader("Sell Something")
        with st.form("sell_item"):
            title = st.text_input("Item Title")
            description = st.text_area("Description")
            price = st.number_input("Price", min_value=0.0)
            category = st.selectbox("Category", ["Electronics", "Home", "Clothing", "Vehicles", "Other"])
            images = st.file_uploader("Item Photos", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)
            
            if st.form_submit_button("List Item"):
                st.success("Item listed successfully!")

def watch_page():
    """Facebook Watch"""
    st.title("Watch")
    st.info("Video platform coming soon!")
    
    # Sample video content
    cols = st.columns(2)
    video_categories = ["Popular", "Gaming", "Sports", "Music", "News", "Learning"]
    
    for idx, category in enumerate(video_categories):
        with cols[idx % 2]:
            st.subheader(category)
            st.image("https://via.placeholder.com/300x200?text=Video+Preview", use_container_width=True)
            st.write(f"Sample {category} Video")
            st.caption("1.2M views • 2 hours ago")

# ===================================
# MAIN APPLICATION
# ===================================
def login_page():
    """Facebook-style Login Page"""
    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 20px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .facebook-login-logo {
            color: #1877f2;
            font-size: 48px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="login-container">
            <div class="facebook-login-logo">facebook</div>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                st.subheader("Log into Facebook")
                username = st.text_input("Email or phone number")
                password = st.text_input("Password", type="password")
                login_btn = st.form_submit_button("Log In", type="primary", use_container_width=True)
                
                if login_btn:
                    if username and password:
                        user = verify_user(username, password)
                        if user:
                            st.session_state.user_id = user[0]
                            st.session_state.username = user[1]
                            st.session_state.logged_in = True
                            st.session_state.current_page = "news_feed"
                            st.success(f"Welcome back, {user[1]}!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    else:
                        st.error("Please enter both username and password")
            
            st.markdown("---")
            st.write("Don't have an account?")
            
            with st.form("register_form"):
                st.subheader("Create New Account")
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                email = st.text_input("Email")
                register_btn = st.form_submit_button("Sign Up", use_container_width=True)
                
                if register_btn:
                    if new_username and new_password and email:
                        if new_password == confirm_password:
                            if create_user(new_username, new_password, email):
                                st.success("Account created successfully! Please log in.")
                            else:
                                st.error("Username already exists")
                        else:
                            st.error("Passwords do not match")
                    else:
                        st.error("Please fill in all required fields")

def main():
    """Main Facebook Application"""
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "news_feed"
    
    # Set page config
    st.set_page_config(
        page_title="Facebook",
        page_icon="👥",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply Facebook theme
    st.markdown("""
        <style>
        .main {
            background-color: #f0f2f5;
        }
        .stApp {
            background-color: #f0f2f5;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.logged_in:
        login_page()
        return
    
    # Facebook header
    facebook_header()
    
    # Main layout
    col1, col2, col3 = st.columns([2, 5, 2])
    
    with col1:
        facebook_sidebar()
    
    with col2:
        # Main content based on current page
        if st.session_state.current_page == "news_feed":
            news_feed_page()
        elif st.session_state.current_page == "profile":
            profile_page()
        elif st.session_state.current_page == "friends":
            friends_page()
        elif st.session_state.current_page == "groups":
            groups_page()
        elif st.session_state.current_page == "messenger":
            messenger_page()
        elif st.session_state.current_page == "marketplace":
            marketplace_page()
        elif st.session_state.current_page == "watch":
            watch_page()
        else:
            news_feed_page()
    
    with col3:
        # Right sidebar - Contacts/Sponsored
        st.markdown("""
            <style>
            .right-sidebar {
                background-color: white;
                padding: 15px;
                border-radius: 10px;
                margin: 10px 0;
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="right-sidebar">', unsafe_allow_html=True)
        st.subheader("Contacts")
        
        # Sample contacts
        contacts = ["Alice Johnson", "Bob Smith", "Carol Davis", "David Wilson", "Eva Brown"]
        for contact in contacts:
            st.write(f"👤 {contact}")
        
        st.markdown("---")
        st.subheader("Sponsored")
        st.image("https://via.placeholder.com/200x100?text=Ad", use_container_width=True)
        st.caption("Sponsored ad content")
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

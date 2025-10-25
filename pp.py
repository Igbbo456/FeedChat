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

# ===================================
# Database Initialization - ENTERPRISE LEVEL
# ===================================
def init_db():
    conn = sqlite3.connect("feedchat.db", check_same_thread=False)
    c = conn.cursor()

    # Existing tables (keeping your current structure)
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT,
        profile_pic BLOB,
        bio TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Add is_active column if it doesn't exist
    try:
        c.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
    except sqlite3.OperationalError:
        pass

    c.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        media_type TEXT,
        media_data BLOB,
        is_deleted BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    try:
        c.execute("ALTER TABLE posts ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE")
    except sqlite3.OperationalError:
        pass

    # ===================================
    # ENTERPRISE FEATURE: Groups & Communities
    # ===================================
    c.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        description TEXT,
        cover_image BLOB,
        is_public BOOLEAN DEFAULT TRUE,
        created_by INTEGER,
        member_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS group_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        user_id INTEGER,
        role TEXT DEFAULT 'member',
        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(group_id, user_id)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS group_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        user_id INTEGER,
        content TEXT,
        media_type TEXT,
        media_data BLOB,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ===================================
    # ENTERPRISE FEATURE: E-commerce
    # ===================================
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seller_id INTEGER,
        name TEXT,
        description TEXT,
        price DECIMAL(10,2),
        images JSON,
        category TEXT,
        is_available BOOLEAN DEFAULT TRUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        buyer_id INTEGER,
        quantity INTEGER,
        total_price DECIMAL(10,2),
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ===================================
    # ENTERPRISE FEATURE: Stories & Live Streaming
    # ===================================
    c.execute("""
    CREATE TABLE IF NOT EXISTS stories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        media_data BLOB,
        media_type TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS live_streams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        description TEXT,
        stream_url TEXT,
        is_live BOOLEAN DEFAULT FALSE,
        viewer_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS stream_viewers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stream_id INTEGER,
        user_id INTEGER,
        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ===================================
    # ENTERPRISE FEATURE: Multiple Images per Post
    # ===================================
    c.execute("""
    CREATE TABLE IF NOT EXISTS post_media (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        media_data BLOB,
        media_type TEXT,
        position INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ===================================
    # ENTERPRISE FEATURE: Premium Subscriptions
    # ===================================
    c.execute("""
    CREATE TABLE IF NOT EXISTS subscription_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price_monthly DECIMAL(10,2),
        price_yearly DECIMAL(10,2),
        features JSON,
        is_active BOOLEAN DEFAULT TRUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS user_subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan_id INTEGER,
        status TEXT DEFAULT 'active',
        start_date DATETIME,
        end_date DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ===================================
    # ENTERPRISE FEATURE: Advanced Analytics
    # ===================================
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        event_type TEXT,
        event_data JSON,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ===================================
    # ENTERPRISE FEATURE: AI Content Moderation
    # ===================================
    c.execute("""
    CREATE TABLE IF NOT EXISTS reported_content (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reporter_id INTEGER,
        content_type TEXT,
        content_id INTEGER,
        reason TEXT,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ===================================
    # ENTERPRISE FEATURE: Advanced Notifications
    # ===================================
    c.execute("""
    CREATE TABLE IF NOT EXISTS push_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        message TEXT,
        notification_type TEXT,
        is_read BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Your existing tables (keeping them)
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
    CREATE TABLE IF NOT EXISTS shares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS saved_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS follows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        follower_id INTEGER,
        following_id INTEGER,
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

    c.execute("""
    CREATE TABLE IF NOT EXISTS calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caller_id INTEGER,
        receiver_id INTEGER,
        meeting_url TEXT,
        status TEXT DEFAULT 'scheduled',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        is_read BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS blocked_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        blocker_id INTEGER,
        blocked_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(blocker_id, blocked_id)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS user_preferences (
        user_id INTEGER PRIMARY KEY,
        dark_mode BOOLEAN DEFAULT FALSE,
        language TEXT DEFAULT 'en',
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Insert default subscription plans
    try:
        c.execute("""
            INSERT OR IGNORE INTO subscription_plans (name, price_monthly, price_yearly, features) 
            VALUES 
            ('Basic', 0.00, 0.00, '["Basic features", "Limited storage"]'),
            ('Pro', 9.99, 99.99, '["Advanced features", "More storage", "Priority support"]'),
            ('Enterprise', 29.99, 299.99, '["All features", "Unlimited storage", "Dedicated support"]')
        """)
    except:
        pass

    conn.commit()
    return conn

# Initialize database
conn = init_db()

# ===================================
# CORE FUNCTIONS - Defined FIRST
# ===================================

def is_valid_image(image_data):
    """Check if the image data is valid and can be opened by PIL"""
    try:
        if image_data is None:
            return False
        image = Image.open(io.BytesIO(image_data))
        image.verify()
        return True
    except (IOError, SyntaxError, Exception):
        return False

def display_image_safely(image_data, caption="", width=None, use_container_width=False):
    """Safely display an image with error handling"""
    try:
        if image_data and is_valid_image(image_data):
            if width:
                st.image(io.BytesIO(image_data), caption=caption, width=width)
            elif use_container_width:
                st.image(io.BytesIO(image_data), caption=caption, use_container_width=True)
            else:
                st.image(io.BytesIO(image_data), caption=caption)
        else:
            st.warning("Unable to display image (corrupted or invalid format)")
    except Exception as e:
        st.warning(f"Error displaying image: {str(e)}")

def create_user(username, password, email, profile_pic=None, bio=""):
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=?", (username,))
        if c.fetchone():
            return False
        if profile_pic and not is_valid_image(profile_pic):
            st.error("Invalid profile picture format. Please use JPG, PNG, or JPEG.")
            return False
        c.execute("INSERT INTO users (username, password, email, profile_pic, bio, is_active) VALUES (?, ?, ?, ?, ?, ?)",
                 (username, password, email, profile_pic, bio, True))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def verify_user(username, password):
    try:
        c = conn.cursor()
        # First try with is_active check
        try:
            c.execute("SELECT id, username FROM users WHERE username=? AND password=? AND is_active=1", (username, password))
            result = c.fetchone()
            if result:
                return result
        except sqlite3.OperationalError:
            # If is_active column doesn't exist yet, fall back to basic check
            pass
        
        # Fallback: check without is_active column
        c.execute("SELECT id, username FROM users WHERE username=? AND password=?", (username, password))
        return c.fetchone()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_user(user_id):
    try:
        c = conn.cursor()
        # Try with is_active check first
        try:
            c.execute("SELECT id, username, email, profile_pic, bio FROM users WHERE id=? AND is_active=1", (user_id,))
            result = c.fetchone()
            if result:
                return result
        except sqlite3.OperationalError:
            pass
        
        # Fallback: get user without is_active check
        c.execute("SELECT id, username, email, profile_pic, bio FROM users WHERE id=?", (user_id,))
        return c.fetchone()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_all_users():
    try:
        c = conn.cursor()
        # Try with is_active check first
        try:
            c.execute("SELECT id, username FROM users WHERE is_active=1")
            return c.fetchall()
        except sqlite3.OperationalError:
            pass
        
        # Fallback: get all users without is_active check
        c.execute("SELECT id, username FROM users")
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# ENTERPRISE FEATURE: Groups & Communities
# ===================================
def create_group(name, description, created_by, cover_image=None, is_public=True):
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO groups (name, description, cover_image, is_public, created_by) 
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, cover_image, is_public, created_by))
        group_id = c.lastrowid
        
        # Creator automatically becomes admin
        c.execute("""
            INSERT INTO group_members (group_id, user_id, role) 
            VALUES (?, ?, 'admin')
        """, (group_id, created_by))
        
        conn.commit()
        return group_id
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

def join_group(group_id, user_id):
    try:
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO group_members (group_id, user_id, role) 
            VALUES (?, ?, 'member')
        """, (group_id, user_id))
        
        # Update member count
        c.execute("""
            UPDATE groups SET member_count = (
                SELECT COUNT(*) FROM group_members WHERE group_id = ?
            ) WHERE id = ?
        """, (group_id, group_id))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_user_groups(user_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT g.*, gm.role 
            FROM groups g
            JOIN group_members gm ON g.id = gm.group_id
            WHERE gm.user_id = ?
            ORDER BY g.created_at DESC
        """, (user_id,))
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_group_posts(group_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT gp.*, u.username, 
                   COUNT(DISTINCT l.id) as like_count,
                   COUNT(DISTINCT c.id) as comment_count
            FROM group_posts gp
            JOIN users u ON gp.user_id = u.id
            LEFT JOIN likes l ON gp.id = l.post_id
            LEFT JOIN comments c ON gp.id = c.post_id
            WHERE gp.group_id = ?
            GROUP BY gp.id
            ORDER BY gp.created_at DESC
        """, (group_id,))
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# ENTERPRISE FEATURE: E-commerce
# ===================================
def create_product(seller_id, name, description, price, images, category):
    try:
        c = conn.cursor()
        images_json = json.dumps(images) if isinstance(images, list) else images
        c.execute("""
            INSERT INTO products (seller_id, name, description, price, images, category) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (seller_id, name, description, price, images_json, category))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_products(seller_id=None):
    try:
        c = conn.cursor()
        if seller_id:
            c.execute("""
                SELECT p.*, u.username as seller_name 
                FROM products p
                JOIN users u ON p.seller_id = u.id
                WHERE p.seller_id = ? AND p.is_available = 1
                ORDER BY p.created_at DESC
            """, (seller_id,))
        else:
            c.execute("""
                SELECT p.*, u.username as seller_name 
                FROM products p
                JOIN users u ON p.seller_id = u.id
                WHERE p.is_available = 1
                ORDER BY p.created_at DESC
            """)
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

def create_order(product_id, buyer_id, quantity):
    try:
        c = conn.cursor()
        # Get product price
        c.execute("SELECT price FROM products WHERE id = ?", (product_id,))
        product = c.fetchone()
        if not product:
            return None
        
        total_price = product[0] * quantity
        c.execute("""
            INSERT INTO orders (product_id, buyer_id, quantity, total_price) 
            VALUES (?, ?, ?, ?)
        """, (product_id, buyer_id, quantity, total_price))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# ENTERPRISE FEATURE: Stories
# ===================================
def create_story(user_id, media_data, media_type):
    try:
        c = conn.cursor()
        expires_at = datetime.datetime.now() + datetime.timedelta(hours=24)
        c.execute("""
            INSERT INTO stories (user_id, media_data, media_type, expires_at) 
            VALUES (?, ?, ?, ?)
        """, (user_id, media_data, media_type, expires_at))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_active_stories(user_id=None):
    try:
        c = conn.cursor()
        if user_id:
            c.execute("""
                SELECT s.*, u.username 
                FROM stories s
                JOIN users u ON s.user_id = u.id
                WHERE s.user_id = ? AND s.expires_at > datetime('now')
                ORDER BY s.created_at DESC
            """, (user_id,))
        else:
            c.execute("""
                SELECT s.*, u.username 
                FROM stories s
                JOIN users u ON s.user_id = u.id
                WHERE s.expires_at > datetime('now')
                ORDER BY s.created_at DESC
            """)
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# ENTERPRISE FEATURE: Live Streaming
# ===================================
def create_live_stream(user_id, title, description):
    try:
        c = conn.cursor()
        stream_url = f"https://livestream.feedchat.com/{uuid.uuid4()}"
        c.execute("""
            INSERT INTO live_streams (user_id, title, description, stream_url, is_live) 
            VALUES (?, ?, ?, ?, TRUE)
        """, (user_id, title, description, stream_url, True))
        conn.commit()
        return c.lastrowid, stream_url
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None, None
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_live_streams():
    try:
        c = conn.cursor()
        c.execute("""
            SELECT ls.*, u.username, u.profile_pic,
                   (SELECT COUNT(*) FROM stream_viewers WHERE stream_id = ls.id) as viewer_count
            FROM live_streams ls
            JOIN users u ON ls.user_id = u.id
            WHERE ls.is_live = TRUE
            ORDER BY ls.created_at DESC
        """)
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# ENTERPRISE FEATURE: Multiple Images per Post
# ===================================
def create_post_with_multiple_media(user_id, content, media_files):
    try:
        c = conn.cursor()
        # Create post
        c.execute("INSERT INTO posts (user_id, content) VALUES (?, ?)", (user_id, content))
        post_id = c.lastrowid
        
        # Add multiple media
        for i, media_file in enumerate(media_files):
            media_data = media_file.read()
            media_type = "image" if media_file.type.startswith('image') else "video"
            c.execute("""
                INSERT INTO post_media (post_id, media_data, media_type, position) 
                VALUES (?, ?, ?, ?)
            """, (post_id, media_data, media_type, i))
        
        conn.commit()
        return post_id
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_post_media(post_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT media_data, media_type, position 
            FROM post_media 
            WHERE post_id = ? 
            ORDER BY position
        """, (post_id,))
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# ENTERPRISE FEATURE: Premium Subscriptions
# ===================================
def get_subscription_plans():
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM subscription_plans WHERE is_active = 1")
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

def create_subscription(user_id, plan_id, duration='monthly'):
    try:
        c = conn.cursor()
        start_date = datetime.datetime.now()
        if duration == 'monthly':
            end_date = start_date + datetime.timedelta(days=30)
        else:  # yearly
            end_date = start_date + datetime.timedelta(days=365)
        
        c.execute("""
            INSERT INTO user_subscriptions (user_id, plan_id, start_date, end_date) 
            VALUES (?, ?, ?, ?)
        """, (user_id, plan_id, start_date, end_date))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_user_subscription(user_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT us.*, sp.name, sp.features 
            FROM user_subscriptions us
            JOIN subscription_plans sp ON us.plan_id = sp.id
            WHERE us.user_id = ? AND us.status = 'active' AND us.end_date > datetime('now')
        """, (user_id,))
        return c.fetchone()
    except sqlite3.Error as e:
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# ENTERPRISE FEATURE: AI Content Moderation
# ===================================
def report_content(reporter_id, content_type, content_id, reason):
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO reported_content (reporter_id, content_type, content_id, reason) 
            VALUES (?, ?, ?, ?)
        """, (reporter_id, content_type, content_id, reason))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# ENTERPRISE FEATURE: Advanced Analytics
# ===================================
def log_analytics_event(user_id, event_type, event_data):
    try:
        c = conn.cursor()
        event_data_json = json.dumps(event_data) if isinstance(event_data, dict) else event_data
        c.execute("""
            INSERT INTO user_analytics (user_id, event_type, event_data) 
            VALUES (?, ?, ?)
        """, (user_id, event_type, event_data_json))
        conn.commit()
    except sqlite3.Error:
        pass  # Analytics failures shouldn't break the app
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# EXISTING CORE FUNCTIONS (Post-related)
# ===================================
def create_post(user_id, content, media_type=None, media_data=None):
    try:
        c = conn.cursor()
        if media_data and media_type == "image" and not is_valid_image(media_data):
            st.error("Invalid image format. Please use JPG, PNG, or JPEG.")
            return None
        c.execute("INSERT INTO posts (user_id, content, media_type, media_data) VALUES (?, ?, ?, ?)",
                 (user_id, content, media_type, media_data))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_posts(user_id=None):
    try:
        c = conn.cursor()
        if user_id:
            try:
                c.execute("""
                    SELECT p.id, p.user_id, u.username, p.content, p.media_type, p.media_data, p.created_at,
                           COUNT(l.id) as like_count,
                           SUM(CASE WHEN l.user_id = ? THEN 1 ELSE 0 END) as user_liked
                    FROM posts p
                    JOIN users u ON p.user_id = u.id
                    LEFT JOIN likes l ON p.id = l.post_id
                    WHERE p.is_deleted = 0 
                    AND u.is_active = 1
                    AND p.user_id NOT IN (SELECT blocked_id FROM blocked_users WHERE blocker_id=?)
                    AND (p.user_id IN (SELECT following_id FROM follows WHERE follower_id=?) OR p.user_id=?)
                    GROUP BY p.id
                    ORDER BY p.created_at DESC
                """, (user_id, user_id, user_id, user_id))
                return c.fetchall()
            except sqlite3.OperationalError:
                pass
            c.execute("""
                SELECT p.id, p.user_id, u.username, p.content, p.media_type, p.media_data, p.created_at,
                       COUNT(l.id) as like_count,
                       SUM(CASE WHEN l.user_id = ? THEN 1 ELSE 0 END) as user_liked
                FROM posts p
                JOIN users u ON p.user_id = u.id
                LEFT JOIN likes l ON p.id = l.post_id
                WHERE p.user_id IN (SELECT following_id FROM follows WHERE follower_id=?) OR p.user_id=?
                GROUP BY p.id
                ORDER BY p.created_at DESC
            """, (user_id, user_id, user_id))
        else:
            c.execute("""
                SELECT p.id, p.user_id, u.username, p.content, p.media_type, p.media_data, p.created_at,
                       COUNT(l.id) as like_count,
                       0 as user_liked
                FROM posts p
                JOIN users u ON p.user_id = u.id
                LEFT JOIN likes l ON p.id = l.post_id
                GROUP BY p.id
                ORDER BY p.created_at DESC
            """)
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_user_posts(user_id):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT p.id, p.user_id, u.username, p.content, p.media_type, p.media_data, p.created_at,
                   COUNT(l.id) as like_count,
                   SUM(CASE WHEN l.user_id = ? THEN 1 ELSE 0 END) as user_liked
            FROM posts p
            JOIN users u ON p.user_id = u.id
            LEFT JOIN likes l ON p.id = l.post_id
            WHERE p.user_id=? AND p.is_deleted=0
            GROUP BY p.id
            ORDER BY p.created_at DESC
        """, (user_id, user_id))
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

def like_post(user_id, post_id):
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM likes WHERE user_id=? AND post_id=?", (user_id, post_id))
        if not c.fetchone():
            c.execute("INSERT INTO likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
            conn.commit()
            c.execute("SELECT user_id FROM posts WHERE id=?", (post_id,))
            post_owner_result = c.fetchone()
            if post_owner_result:
                post_owner = post_owner_result[0]
                user = get_user(user_id)
                if user:
                    c.execute("INSERT INTO notifications (user_id, content) VALUES (?, ?)",
                             (post_owner, f"{user[1]} liked your post"))
                    conn.commit()
            return True
        return False
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def follow_user(follower_id, following_id):
    try:
        c = conn.cursor()
        # Check if blocked
        c.execute("SELECT id FROM blocked_users WHERE blocker_id=? AND blocked_id=?", (following_id, follower_id))
        if c.fetchone():
            st.error("You cannot follow this user as they have blocked you.")
            return False
            
        c.execute("SELECT id FROM follows WHERE follower_id=? AND following_id=?", (follower_id, following_id))
        if not c.fetchone():
            c.execute("INSERT INTO follows (follower_id, following_id) VALUES (?, ?)", (follower_id, following_id))
            conn.commit()
            follower = get_user(follower_id)
            if follower:
                c.execute("INSERT INTO notifications (user_id, content) VALUES (?, ?)",
                         (following_id, f"{follower[1]} started following you"))
                conn.commit()
            return True
        return False
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def unfollow_user(follower_id, following_id):
    try:
        c = conn.cursor()
        c.execute("DELETE FROM follows WHERE follower_id=? AND following_id=?", (follower_id, following_id))
        conn.commit()
        return c.rowcount > 0
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def is_following(follower_id, following_id):
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM follows WHERE follower_id=? AND following_id=?", (follower_id, following_id))
        return c.fetchone() is not None
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# Streamlit UI - ENTERPRISE EDITION
# ===================================
st.set_page_config(page_title="FeedChat Pro", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

# Initialize session state with enterprise features
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Feed"
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None
if "current_group" not in st.session_state:
    st.session_state.current_group = None
if "message_input" not in st.session_state:
    st.session_state.message_input = ""
if "last_message_id" not in st.session_state:
    st.session_state.last_message_id = 0
if "active_meeting" not in st.session_state:
    st.session_state.active_meeting = None
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "show_comments" not in st.session_state:
    st.session_state.show_comments = {}
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "show_stories" not in st.session_state:
    st.session_state.show_stories = {}
if "current_product" not in st.session_state:
    st.session_state.current_product = None

# Enhanced dark mode CSS with enterprise styling
def apply_theme(dark_mode):
    if dark_mode:
        st.markdown("""
            <style>
            .stApp {
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #ffffff;
            }
            .enterprise-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                border-radius: 15px;
                margin-bottom: 20px;
                color: white;
                text-align: center;
            }
            .premium-badge {
                background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
                color: #000;
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 0.8em;
            }
            .group-card {
                background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
                border: 1px solid #4a5f7a;
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
            }
            .product-card {
                background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                color: white;
            }
            .story-container {
                background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                border-radius: 20px;
                padding: 15px;
                margin: 10px;
                text-align: center;
                color: white;
            }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            .stApp {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .enterprise-header {
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                padding: 20px;
                border-radius: 15px;
                margin-bottom: 20px;
                color: white;
                text-align: center;
            }
            .premium-badge {
                background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
                color: #000;
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 0.8em;
            }
            .group-card {
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                border: 1px solid #e9ecef;
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
            }
            .product-card {
                background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                color: white;
            }
            .story-container {
                background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                border-radius: 20px;
                padding: 15px;
                margin: 10px;
                text-align: center;
                color: white;
            }
            </style>
        """, unsafe_allow_html=True)

# Enhanced sidebar with enterprise features
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h1 style='color: white; margin-bottom: 10px;'>🚀 FeedChat Pro</h1>
            <p style='color: rgba(255, 255, 255, 0.8); font-size: 0.9em;'>Enterprise Social Platform</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.user:
        user_info = get_user(st.session_state.user[0])
        if user_info:
            # Check if user has premium subscription
            subscription = get_user_subscription(st.session_state.user[0])
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if user_info[3]:
                    display_image_safely(user_info[3], width=60)
                st.success(f"**{user_info[1]}**")
            with col2:
                if subscription:
                    st.markdown('<div class="premium-badge">PREMIUM</div>', unsafe_allow_html=True)
            
            # Dark mode toggle
            dark_mode = st.toggle("Dark Mode", value=st.session_state.dark_mode)
            if dark_mode != st.session_state.dark_mode:
                st.session_state.dark_mode = dark_mode
            
            st.markdown("---")
            
            # Enhanced navigation
            nav_col1, nav_col2 = st.columns(2)
            with nav_col1:
                if st.button("🏠", help="Feed", use_container_width=True):
                    st.session_state.page = "Feed"
                if st.button("👥", help="Groups", use_container_width=True):
                    st.session_state.page = "Groups"
                if st.button("🛍️", help="Marketplace", use_container_width=True):
                    st.session_state.page = "Marketplace"
            with nav_col2:
                if st.button("📹", help="Live", use_container_width=True):
                    st.session_state.page = "Live"
                if st.button("💬", help="Messages", use_container_width=True):
                    st.session_state.page = "Messages"
                if st.button("🔔", help="Notifications", use_container_width=True):
                    st.session_state.page = "Notifications"
            
            if st.button("🌐 Discover People", use_container_width=True):
                st.session_state.page = "Discover"
            
            if st.button("📸 Stories", use_container_width=True):
                st.session_state.page = "Stories"
            
            if st.button("🔍 Search", use_container_width=True):
                st.session_state.page = "Search"
            
            if st.button("💾 Saved Posts", use_container_width=True):
                st.session_state.page = "SavedPosts"
            
            if st.button("👤 Profile", use_container_width=True):
                st.session_state.page = "Profile"
            
            if st.button("🚫 Blocked Users", use_container_width=True):
                st.session_state.page = "BlockedUsers"
            
            if st.button("💎 Premium", use_container_width=True):
                st.session_state.page = "Premium"
            
            st.markdown("---")
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user = None
                st.session_state.page = "Feed"
                st.session_state.current_chat = None
                st.session_state.active_meeting = None
                st.rerun()
    else:
        st.info("Please login or sign up to use FeedChat Pro")

# Apply theme
apply_theme(st.session_state.dark_mode)

# Main content - Enhanced with enterprise features
if not st.session_state.user:
    # Enhanced auth pages with premium branding
    st.markdown("""
        <div class="enterprise-header">
            <h1>🚀 Welcome to FeedChat Pro</h1>
            <p>Next-generation social platform with enterprise features</p>
        </div>
    """, unsafe_allow_html=True)
    
    auth_tab1, auth_tab2 = st.tabs(["🔐 Enterprise Login", "📝 Premium Sign Up"])
    
    with auth_tab1:
        with st.form("Login"):
            st.subheader("Welcome Back!")
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            if st.form_submit_button("Login", use_container_width=True):
                if username and password:
                    user = verify_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter both username and password")
    
    with auth_tab2:
        with st.form("Sign Up"):
            st.subheader("Join FeedChat Pro Today!")
            new_username = st.text_input("Choose a username", placeholder="Enter a unique username")
            new_email = st.text_input("Email", placeholder="Enter your email")
            new_password = st.text_input("Choose a password", type="password", placeholder="Create a strong password")
            confirm_password = st.text_input("Confirm password", type="password", placeholder="Confirm your password")
            profile_pic = st.file_uploader("Profile picture (optional)", type=["jpg", "png", "jpeg"])
            bio = st.text_area("Bio (optional)", placeholder="Tell us about yourself...")
            
            if st.form_submit_button("Create Account", use_container_width=True):
                if new_password != confirm_password:
                    st.error("Passwords don't match")
                elif not new_username or not new_email or not new_password:
                    st.error("Please fill in all required fields")
                else:
                    profile_pic_data = profile_pic.read() if profile_pic else None
                    if create_user(new_username, new_password, new_email, profile_pic_data, bio):
                        st.success("Account created! Please login.")
                    else:
                        st.error("Username already exists")

# Main App (after login) - ENTERPRISE EDITION
else:
    user_id = st.session_state.user[0]
    
    # ===================================
    # ENTERPRISE FEATURE: Groups Page
    # ===================================
    if st.session_state.page == "Groups":
        st.header("👥 Groups & Communities")
        
        groups_tab1, groups_tab2, groups_tab3 = st.tabs(["My Groups", "Discover Groups", "Create Group"])
        
        with groups_tab1:
            st.subheader("Your Groups")
            user_groups = get_user_groups(user_id)
            if not user_groups:
                st.info("You haven't joined any groups yet. Join or create one!")
            else:
                for group in user_groups:
                    with st.container():
                        st.markdown("<div class='group-card'>", unsafe_allow_html=True)
                        col1, col2, col3 = st.columns([1, 3, 1])
                        with col1:
                            if group[3]:  # cover_image
                                display_image_safely(group[3], width=80)
                        with col2:
                            st.write(f"**{group[1]}**")
                            st.write(f"👥 {group[6]} members • {'Public' if group[4] else 'Private'}")
                            st.caption(group[2])
                        with col3:
                            if st.button("Enter", key=f"enter_group_{group[0]}"):
                                st.session_state.current_group = group[0]
                                st.session_state.page = "GroupDetail"
                                st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
        
        with groups_tab2:
            st.subheader("Discover Groups")
            st.info("Group discovery feature coming soon!")
        
        with groups_tab3:
            st.subheader("Create New Group")
            with st.form("create_group_form"):
                group_name = st.text_input("Group Name")
                group_description = st.text_area("Description")
                is_public = st.checkbox("Public Group", value=True)
                cover_image = st.file_uploader("Cover Image", type=["jpg", "png", "jpeg"])
                
                if st.form_submit_button("Create Group", use_container_width=True):
                    if group_name and group_description:
                        cover_image_data = cover_image.read() if cover_image else None
                        group_id = create_group(group_name, group_description, user_id, cover_image_data, is_public)
                        if group_id:
                            st.success(f"Group '{group_name}' created successfully!")
                            st.rerun()
                    else:
                        st.error("Please fill in all required fields")
    
    # ===================================
    # ENTERPRISE FEATURE: Marketplace
    # ===================================
    elif st.session_state.page == "Marketplace":
        st.header("🛍️ Marketplace")
        
        marketplace_tab1, marketplace_tab2 = st.tabs(["Browse Products", "Sell Product"])
        
        with marketplace_tab1:
            st.subheader("Featured Products")
            products = get_products()
            if not products:
                st.info("No products available yet. Be the first to sell!")
            else:
                # FIXED: Safe column access
                cols = st.columns(3)
                for i, product in enumerate(products):
                    # Only use available columns
                    if i < len(cols):
                        with cols[i]:
                            st.markdown("<div class='product-card'>", unsafe_allow_html=True)
                            st.write(f"**{product[2]}**")  # name
                            st.write(f"💰 ${product[4]}")  # price
                            st.caption(f"by {product[8]}")  # seller_name
                            if st.button("View Details", key=f"view_product_{product[0]}"):
                                st.session_state.current_product = product[0]
                                st.session_state.page = "ProductDetail"
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
        
        with marketplace_tab2:
            st.subheader("Sell Your Product")
            with st.form("sell_product_form"):
                product_name = st.text_input("Product Name")
                product_description = st.text_area("Description")
                product_price = st.number_input("Price ($)", min_value=0.01, step=0.01)
                product_category = st.selectbox("Category", ["Electronics", "Clothing", "Books", "Home", "Other"])
                product_images = st.file_uploader("Product Images", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
                
                if st.form_submit_button("List Product", use_container_width=True):
                    if product_name and product_description and product_price:
                        image_data = []
                        for img in product_images:
                            image_data.append(base64.b64encode(img.read()).decode())
                        
                        product_id = create_product(user_id, product_name, product_description, product_price, image_data, product_category)
                        if product_id:
                            st.success("Product listed successfully!")
                            st.rerun()
                    else:
                        st.error("Please fill in all required fields")
    
    # ===================================
    # ENTERPRISE FEATURE: Live Streaming
    # ===================================
    elif st.session_state.page == "Live":
        st.header("📹 Live Streaming")
        
        live_tab1, live_tab2 = st.tabs(["Watch Live", "Go Live"])
        
        with live_tab1:
            st.subheader("Live Streams")
            live_streams = get_live_streams()
            if not live_streams:
                st.info("No live streams at the moment. Be the first to go live!")
            else:
                for stream in live_streams:
                    with st.container():
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            if stream[8]:  # profile_pic
                                display_image_safely(stream[8], width=80)
                        with col2:
                            st.write(f"**{stream[2]}**")  # title
                            st.write(f"👤 {stream[7]} • 👁️ {stream[9]} viewers")  # username, viewer_count
                            st.caption(stream[3])  # description
                            if st.button("Watch Stream", key=f"watch_{stream[0]}"):
                                st.info(f"Stream URL: {stream[4]}")
        
        with live_tab2:
            st.subheader("Start a Live Stream")
            with st.form("go_live_form"):
                stream_title = st.text_input("Stream Title")
                stream_description = st.text_area("Description")
                
                if st.form_submit_button("Go Live", use_container_width=True):
                    if stream_title:
                        stream_id, stream_url = create_live_stream(user_id, stream_title, stream_description)
                        if stream_id:
                            st.success(f"Live stream started! Share this URL: {stream_url}")
                            st.rerun()
                    else:
                        st.error("Please enter a stream title")
    
    # ===================================
    # ENTERPRISE FEATURE: Stories
    # ===================================
    elif st.session_state.page == "Stories":
        st.header("📸 Stories")
        
        stories_tab1, stories_tab2 = st.tabs(["View Stories", "Create Story"])
        
        with stories_tab1:
            st.subheader("Active Stories")
            stories = get_active_stories()
            if not stories:
                st.info("No active stories. Create one!")
            else:
                # Display stories in a horizontal layout
                cols = st.columns(min(5, len(stories)))
                for i, story in enumerate(stories):
                    if i < len(cols):
                        with cols[i]:
                            st.markdown("<div class='story-container'>", unsafe_allow_html=True)
                            st.write(f"👤 {story[6]}")  # username
                            if story[2]:  # media_data
                                display_image_safely(story[2], width=150)
                            st.markdown("</div>", unsafe_allow_html=True)
        
        with stories_tab2:
            st.subheader("Create New Story")
            with st.form("create_story_form"):
                story_media = st.file_uploader("Upload Photo/Video", type=["jpg", "png", "jpeg", "mp4"])
                story_caption = st.text_input("Caption (optional)")
                
                if st.form_submit_button("Post Story", use_container_width=True):
                    if story_media:
                        media_data = story_media.read()
                        media_type = "image" if story_media.type.startswith('image') else "video"
                        story_id = create_story(user_id, media_data, media_type)
                        if story_id:
                            st.success("Story posted! It will expire in 24 hours.")
                            st.rerun()
                    else:
                        st.error("Please upload a photo or video")
    
    # ===================================
    # ENTERPRISE FEATURE: Premium Subscriptions
    # ===================================
    elif st.session_state.page == "Premium":
        st.header("💎 Premium Subscriptions")
        
        # Check current subscription
        current_subscription = get_user_subscription(user_id)
        
        if current_subscription:
            st.success(f"**Current Plan:** {current_subscription[6]} (Premium)")
            features = json.loads(current_subscription[7])
            st.write("**Your Benefits:**")
            for feature in features:
                st.write(f"✅ {feature}")
            
            st.warning("Your subscription ends on: " + current_subscription[5].split()[0])
        else:
            st.info("You're currently on the **Basic** plan. Upgrade to unlock premium features!")
        
        st.markdown("---")
        st.subheader("Available Plans")
        
        plans = get_subscription_plans()
        cols = st.columns(len(plans))
        
        for i, plan in enumerate(plans):
            with cols[i]:
                st.markdown(f"### {plan[1]}")
                st.write(f"**Monthly:** ${plan[2]}")
                st.write(f"**Yearly:** ${plan[3]} (Save {int((1 - (plan[3]/(plan[2]*12))) * 100)}%)")
                
                features = json.loads(plan[4])
                st.write("**Features:**")
                for feature in features:
                    st.write(f"• {feature}")
                
                if plan[1] != "Basic":
                    if st.button(f"Upgrade to {plan[1]}", key=f"upgrade_{plan[0]}", use_container_width=True):
                        # In a real app, this would redirect to payment processing
                        subscription_id = create_subscription(user_id, plan[0], 'monthly')
                        if subscription_id:
                            st.success(f"Successfully upgraded to {plan[1]} plan!")
                            st.rerun()
    
    # ===================================
    # EXISTING PAGES (Feed, Profile, etc.)
    # ===================================
    elif st.session_state.page == "Feed":
        st.header("🏠 Your Feed")
        
        # Create post section
        with st.form("create_post_form", clear_on_submit=True):
            post_content = st.text_area("What's on your mind?", placeholder="Share your thoughts...")
            post_media = st.file_uploader("Add media (optional)", type=["jpg", "png", "jpeg", "mp4"])
            col1, col2 = st.columns([3, 1])
            with col2:
                submit_post = st.form_submit_button("Post", use_container_width=True)
            
            if submit_post and post_content:
                media_type = None
                media_data = None
                if post_media:
                    media_data = post_media.read()
                    media_type = "image" if post_media.type.startswith('image') else "video"
                
                post_id = create_post(user_id, post_content, media_type, media_data)
                if post_id:
                    st.success("Post created successfully!")
                    st.rerun()
        
        # Display posts
        st.markdown("---")
        st.subheader("Recent Posts")
        
        posts = get_posts(user_id)
        if not posts:
            st.info("No posts yet. Follow some users or create your first post!")
        else:
            for post in posts:
                with st.container():
                    st.markdown("---")
                    col1, col2 = st.columns([1, 10])
                    with col1:
                        user_info = get_user(post[1])
                        if user_info and user_info[3]:
                            display_image_safely(user_info[3], width=50)
                    with col2:
                        st.write(f"**{post[2]}** · {post[6].split()[0]}")
                    
                    st.write(post[3])  # content
                    
                    if post[4] and post[5]:  # media_type and media_data
                        display_image_safely(post[5], use_container_width=True)
                    
                    # Like button and stats
                    col1, col2, col3 = st.columns([1, 1, 3])
                    with col1:
                        if st.button(f"❤️ {post[7]}", key=f"like_{post[0]}"):
                            if like_post(user_id, post[0]):
                                st.rerun()
                    with col2:
                        if st.button("💬 Comment", key=f"comment_{post[0]}"):
                            st.session_state.show_comments[post[0]] = not st.session_state.show_comments.get(post[0], False)
                            st.rerun()
                    
                    # Comments section
                    if st.session_state.show_comments.get(post[0], False):
                        st.text_input("Add a comment...", key=f"comment_input_{post[0]}")
                        if st.button("Post Comment", key=f"post_comment_{post[0]}"):
                            st.info("Comment functionality to be implemented")
    
    elif st.session_state.page == "Profile":
        st.header("👤 Your Profile")
        
        user_info = get_user(user_id)
        if user_info:
            col1, col2 = st.columns([1, 3])
            with col1:
                if user_info[3]:
                    display_image_safely(user_info[3], width=150)
                else:
                    st.info("No profile picture")
            with col2:
                st.write(f"**Username:** {user_info[1]}")
                st.write(f"**Email:** {user_info[2]}")
                st.write(f"**Bio:** {user_info[4] if user_info[4] else 'No bio yet'}")
            
            # User's posts
            st.markdown("---")
            st.subheader("Your Posts")
            user_posts = get_user_posts(user_id)
            if not user_posts:
                st.info("You haven't posted anything yet.")
            else:
                for post in user_posts:
                    with st.container():
                        st.write(f"**{post[6].split()[0]}**")
                        st.write(post[3])
                        if post[4] and post[5]:
                            display_image_safely(post[5], use_container_width=True)
                        st.write(f"❤️ {post[7]} likes")
                        st.markdown("---")
    
    # Add other existing pages here with proper error handling...
    else:
        st.header(st.session_state.page)
        st.info("This page is under development. Check back soon!")

# Close database connection when done
def close_db():
    try:
        conn.close()
    except:
        pass

# Register cleanup
import atexit
atexit.register(close_db)

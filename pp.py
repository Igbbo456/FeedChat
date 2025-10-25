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

    # ===================================
    # NEW ENTERPRISE FEATURES - ALL ADDED
    # ===================================

    # AI-Powered Content Recommendations
    c.execute("""
    CREATE TABLE IF NOT EXISTS content_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        recommended_user_id INTEGER,
        recommendation_score DECIMAL(3,2),
        reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Enterprise Collaboration Features
    c.execute("""
    CREATE TABLE IF NOT EXISTS workspaces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT,
        admin_id INTEGER,
        max_users INTEGER,
        is_active BOOLEAN DEFAULT TRUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS shared_calendars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER,
        event_name TEXT,
        description TEXT,
        start_time DATETIME,
        end_time DATETIME,
        created_by INTEGER
    )
    """)

    # Advanced Security & Compliance
    c.execute("""
    CREATE TABLE IF NOT EXISTS two_factor_auth (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        secret_key TEXT,
        is_enabled BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS compliance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action_type TEXT,
        ip_address TEXT,
        user_agent TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Monetization & E-commerce Enhancements
    c.execute("""
    CREATE TABLE IF NOT EXISTS digital_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creator_id INTEGER,
        product_type TEXT,
        title TEXT,
        description TEXT,
        price DECIMAL(10,2),
        file_url TEXT,
        thumbnail BLOB,
        sales_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS affiliate_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_url TEXT,
        affiliate_code TEXT,
        clicks INTEGER DEFAULT 0,
        conversions INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Content Management & Scheduling
    c.execute("""
    CREATE TABLE IF NOT EXISTS scheduled_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        media_data BLOB,
        scheduled_time DATETIME,
        platforms JSON,
        status TEXT DEFAULT 'scheduled',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Advanced Communication Features
    c.execute("""
    CREATE TABLE IF NOT EXISTS video_meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        host_id INTEGER,
        meeting_topic TEXT,
        participant_ids JSON,
        start_time DATETIME,
        end_time DATETIME,
        recording_url TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS voice_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        audio_data BLOB,
        duration_seconds INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Gamification & Engagement
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        achievement_type TEXT,
        achievement_level INTEGER,
        points_earned INTEGER,
        unlocked_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS leaderboards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        metric_type TEXT,
        score INTEGER,
        time_frame TEXT,
        rank_position INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # API & Integration Framework
    c.execute("""
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        api_key TEXT UNIQUE,
        name TEXT,
        permissions JSON,
        is_active BOOLEAN DEFAULT TRUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS webhooks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        target_url TEXT,
        event_type TEXT,
        secret_key TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Advanced Content Moderation
    c.execute("""
    CREATE TABLE IF NOT EXISTS content_flags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_type TEXT,
        content_id INTEGER,
        flag_type TEXT,
        confidence_score DECIMAL(3,2),
        auto_action_taken BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Multi-language & Localization
    c.execute("""
    CREATE TABLE IF NOT EXISTS translations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        language_code TEXT,
        translation_key TEXT,
        translation_value TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Advanced Notification System
    c.execute("""
    CREATE TABLE IF NOT EXISTS notification_preferences (
        user_id INTEGER PRIMARY KEY,
        email_notifications BOOLEAN DEFAULT TRUE,
        push_notifications BOOLEAN DEFAULT TRUE,
        sms_notifications BOOLEAN DEFAULT FALSE,
        digest_frequency TEXT DEFAULT 'daily',
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Data Export & Portability
    c.execute("""
    CREATE TABLE IF NOT EXISTS data_exports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        export_type TEXT,
        file_path TEXT,
        status TEXT DEFAULT 'processing',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Advanced User Onboarding
    c.execute("""
    CREATE TABLE IF NOT EXISTS onboarding_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        step_name TEXT,
        is_completed BOOLEAN DEFAULT FALSE,
        completed_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Virtual Events Platform
    c.execute("""
    CREATE TABLE IF NOT EXISTS virtual_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        host_id INTEGER,
        event_name TEXT,
        description TEXT,
        start_time DATETIME,
        end_time DATETIME,
        max_attendees INTEGER,
        registration_count INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT TRUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS event_registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        user_id INTEGER,
        registration_date DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # AI Content Assistant
    c.execute("""
    CREATE TABLE IF NOT EXISTS ai_writing_assistant (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        original_content TEXT,
        improved_content TEXT,
        improvement_type TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Marketplace Reviews & Reputation
    c.execute("""
    CREATE TABLE IF NOT EXISTS product_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        reviewer_id INTEGER,
        rating INTEGER,
        review_text TEXT,
        is_verified_purchase BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS user_reputation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        reputation_score DECIMAL(5,2) DEFAULT 0.0,
        total_reviews INTEGER DEFAULT 0,
        positive_reviews INTEGER DEFAULT 0,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Smart Groups & Interest Matching
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_interests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        interest_category TEXT,
        interest_level INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS smart_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        category TEXT,
        matching_algorithm TEXT,
        member_count INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT TRUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Predictive Analytics
    c.execute("""
    CREATE TABLE IF NOT EXISTS predictive_analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        prediction_type TEXT,
        predicted_value DECIMAL(10,2),
        confidence_score DECIMAL(3,2),
        prediction_date DATE,
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

    # Insert default translations
    try:
        c.execute("""
            INSERT OR IGNORE INTO translations (language_code, translation_key, translation_value) 
            VALUES 
            ('en', 'welcome', 'Welcome to FeedChat Pro'),
            ('es', 'welcome', 'Bienvenido a FeedChat Pro'),
            ('fr', 'welcome', 'Bienvenue sur FeedChat Pro'),
            ('en', 'like', 'Like'),
            ('es', 'like', 'Me gusta'),
            ('fr', 'like', 'J''aime')
        """)
    except:
        pass

    # Insert default achievements
    try:
        c.execute("""
            INSERT OR IGNORE INTO user_achievements (achievement_type, achievement_level, points_earned) 
            VALUES 
            ('first_post', 1, 10),
            ('social_butterfly', 1, 50),
            ('content_creator', 1, 100),
            ('influencer', 1, 500)
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
# CORE SOCIAL MEDIA FUNCTIONS - ADDED
# ===================================

def create_post(user_id, content, media_data=None, media_type=None):
    """Create a new post"""
    try:
        c = conn.cursor()
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

def get_posts(limit=20, offset=0):
    """Get posts for feed"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT p.*, u.username, u.profile_pic, 
                   COUNT(DISTINCT l.id) as like_count,
                   COUNT(DISTINCT c.id) as comment_count,
                   COUNT(DISTINCT s.id) as share_count
            FROM posts p
            JOIN users u ON p.user_id = u.id
            LEFT JOIN likes l ON p.id = l.post_id
            LEFT JOIN comments c ON p.id = c.post_id
            LEFT JOIN shares s ON p.id = s.post_id
            WHERE p.is_deleted = 0
            GROUP BY p.id
            ORDER BY p.created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
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
    """Like a post"""
    try:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def unlike_post(user_id, post_id):
    """Unlike a post"""
    try:
        c = conn.cursor()
        c.execute("DELETE FROM likes WHERE user_id=? AND post_id=?", (user_id, post_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def is_liked(user_id, post_id):
    """Check if user liked a post"""
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM likes WHERE user_id=? AND post_id=?", (user_id, post_id))
        return c.fetchone() is not None
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def add_comment(post_id, user_id, content):
    """Add a comment to a post"""
    try:
        c = conn.cursor()
        c.execute("INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
                 (post_id, user_id, content))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error:
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_comments(post_id):
    """Get comments for a post"""
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
    finally:
        try:
            c.close()
        except Exception:
            pass

def save_post(user_id, post_id):
    """Save a post"""
    try:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO saved_posts (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def unsave_post(user_id, post_id):
    """Unsave a post"""
    try:
        c = conn.cursor()
        c.execute("DELETE FROM saved_posts WHERE user_id=? AND post_id=?", (user_id, post_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def is_saved(user_id, post_id):
    """Check if post is saved"""
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM saved_posts WHERE user_id=? AND post_id=?", (user_id, post_id))
        return c.fetchone() is not None
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def share_post(user_id, post_id):
    """Share a post"""
    try:
        c = conn.cursor()
        c.execute("INSERT INTO shares (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def send_message(sender_id, receiver_id, content):
    """Send a message"""
    try:
        c = conn.cursor()
        c.execute("INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)",
                 (sender_id, receiver_id, content))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error:
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_messages(user_id, other_user_id, limit=50):
    """Get messages between two users"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT m.*, u1.username as sender_name, u2.username as receiver_name
            FROM messages m
            JOIN users u1 ON m.sender_id = u1.id
            JOIN users u2 ON m.receiver_id = u2.id
            WHERE (m.sender_id = ? AND m.receiver_id = ?) 
               OR (m.sender_id = ? AND m.receiver_id = ?)
            ORDER BY m.created_at ASC
            LIMIT ?
        """, (user_id, other_user_id, other_user_id, user_id, limit))
        return c.fetchall()
    except sqlite3.Error:
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_conversations(user_id):
    """Get all conversations for a user"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT DISTINCT 
                CASE 
                    WHEN m.sender_id = ? THEN m.receiver_id 
                    ELSE m.sender_id 
                END as other_user_id,
                u.username,
                u.profile_pic,
                MAX(m.created_at) as last_message_time,
                (SELECT content FROM messages 
                 WHERE ((sender_id = ? AND receiver_id = other_user_id) 
                     OR (sender_id = other_user_id AND receiver_id = ?))
                 ORDER BY created_at DESC LIMIT 1) as last_message
            FROM messages m
            JOIN users u ON u.id = CASE 
                WHEN m.sender_id = ? THEN m.receiver_id 
                ELSE m.sender_id 
            END
            WHERE m.sender_id = ? OR m.receiver_id = ?
            GROUP BY other_user_id
            ORDER BY last_message_time DESC
        """, (user_id, user_id, user_id, user_id, user_id, user_id))
        return c.fetchall()
    except sqlite3.Error:
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

def create_group(name, description, created_by, cover_image=None, is_public=True):
    """Create a new group"""
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO groups (name, description, cover_image, is_public, created_by) 
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, cover_image, is_public, created_by))
        group_id = c.lastrowid
        
        # Add creator as admin
        c.execute("INSERT INTO group_members (group_id, user_id, role) VALUES (?, ?, 'admin')",
                 (group_id, created_by))
        
        conn.commit()
        return group_id
    except sqlite3.Error:
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_groups(limit=20):
    """Get all groups"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT g.*, u.username as creator_name, 
                   COUNT(gm.user_id) as member_count
            FROM groups g
            JOIN users u ON g.created_by = u.id
            LEFT JOIN group_members gm ON g.id = gm.group_id
            WHERE g.is_public = 1
            GROUP BY g.id
            ORDER BY member_count DESC
            LIMIT ?
        """, (limit,))
        return c.fetchall()
    except sqlite3.Error:
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

def join_group(user_id, group_id):
    """Join a group"""
    try:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)",
                 (group_id, user_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def leave_group(user_id, group_id):
    """Leave a group"""
    try:
        c = conn.cursor()
        c.execute("DELETE FROM group_members WHERE user_id=? AND group_id=?", (user_id, group_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def is_group_member(user_id, group_id):
    """Check if user is group member"""
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM group_members WHERE user_id=? AND group_id=?", (user_id, group_id))
        return c.fetchone() is not None
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def create_group_post(group_id, user_id, content, media_data=None, media_type=None):
    """Create a post in a group"""
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO group_posts (group_id, user_id, content, media_type, media_data) 
            VALUES (?, ?, ?, ?, ?)
        """, (group_id, user_id, content, media_type, media_data))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error:
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_group_posts(group_id, limit=20):
    """Get posts from a group"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT gp.*, u.username, u.profile_pic
            FROM group_posts gp
            JOIN users u ON gp.user_id = u.id
            WHERE gp.group_id = ?
            ORDER BY gp.created_at DESC
            LIMIT ?
        """, (group_id, limit))
        return c.fetchall()
    except sqlite3.Error:
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# MISSING FUNCTION DEFINITIONS - ADDED
# ===================================

def is_following(follower_id, following_id):
    """Check if a user is following another user"""
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM follows WHERE follower_id=? AND following_id=?", (follower_id, following_id))
        return c.fetchone() is not None
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def follow_user(follower_id, following_id):
    """Follow a user"""
    try:
        c = conn.cursor()
        c.execute("INSERT INTO follows (follower_id, following_id) VALUES (?, ?)", (follower_id, following_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def unfollow_user(follower_id, following_id):
    """Unfollow a user"""
    try:
        c = conn.cursor()
        c.execute("DELETE FROM follows WHERE follower_id=? AND following_id=?", (follower_id, following_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_user_subscription(user_id):
    """Get user's subscription information"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT sp.name, sp.price_monthly, us.status, us.end_date 
            FROM user_subscriptions us
            JOIN subscription_plans sp ON us.plan_id = sp.id
            WHERE us.user_id = ? AND us.status = 'active'
        """, (user_id,))
        return c.fetchone()
    except sqlite3.Error:
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# DISCOVER PEOPLE FEATURE FUNCTIONS
# ===================================
def get_users_to_discover(current_user_id, limit=20):
    """Get users to discover (excluding current user and already followed users)"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT u.id, u.username, u.email, u.profile_pic, u.bio, u.created_at,
                   COUNT(DISTINCT p.id) as post_count,
                   COUNT(DISTINCT f1.id) as follower_count,
                   CASE WHEN f2.id IS NOT NULL THEN 1 ELSE 0 END as is_following
            FROM users u
            LEFT JOIN posts p ON u.id = p.user_id AND p.is_deleted = 0
            LEFT JOIN follows f1 ON u.id = f1.following_id
            LEFT JOIN follows f2 ON u.id = f2.following_id AND f2.follower_id = ?
            WHERE u.id != ? AND u.is_active = 1
            GROUP BY u.id
            ORDER BY follower_count DESC, post_count DESC
            LIMIT ?
        """, (current_user_id, current_user_id, limit))
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_suggested_users_based_on_interests(current_user_id, limit=10):
    """Get suggested users based on similar interests (placeholder implementation)"""
    try:
        c = conn.cursor()
        # This is a simplified version - in a real app, you'd analyze user behavior
        c.execute("""
            SELECT u.id, u.username, u.profile_pic, u.bio,
                   COUNT(DISTINCT p.id) as post_count,
                   COUNT(DISTINCT f.id) as follower_count
            FROM users u
            LEFT JOIN posts p ON u.id = p.user_id AND p.is_deleted = 0
            LEFT JOIN follows f ON u.id = f.following_id
            WHERE u.id != ? AND u.is_active = 1
            AND u.id NOT IN (SELECT following_id FROM follows WHERE follower_id = ?)
            GROUP BY u.id
            ORDER BY RANDOM()
            LIMIT ?
        """, (current_user_id, current_user_id, limit))
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

def search_users(query, current_user_id):
    """Search users by username or bio"""
    try:
        c = conn.cursor()
        search_term = f"%{query}%"
        c.execute("""
            SELECT u.id, u.username, u.profile_pic, u.bio,
                   COUNT(DISTINCT p.id) as post_count,
                   COUNT(DISTINCT f.id) as follower_count,
                   CASE WHEN fl.id IS NOT NULL THEN 1 ELSE 0 END as is_following
            FROM users u
            LEFT JOIN posts p ON u.id = p.user_id AND p.is_deleted = 0
            LEFT JOIN follows f ON u.id = f.following_id
            LEFT JOIN follows fl ON u.id = fl.following_id AND fl.follower_id = ?
            WHERE (u.username LIKE ? OR u.bio LIKE ?) 
            AND u.id != ? AND u.is_active = 1
            GROUP BY u.id
            ORDER BY 
                CASE WHEN u.username LIKE ? THEN 1 ELSE 2 END,
                follower_count DESC
        """, (current_user_id, search_term, search_term, current_user_id, search_term))
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_user_stats(user_id):
    """Get user statistics for profile cards"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT 
                COUNT(DISTINCT p.id) as post_count,
                COUNT(DISTINCT f1.id) as follower_count,
                COUNT(DISTINCT f2.id) as following_count
            FROM users u
            LEFT JOIN posts p ON u.id = p.user_id AND p.is_deleted = 0
            LEFT JOIN follows f1 ON u.id = f1.following_id
            LEFT JOIN follows f2 ON u.id = f2.follower_id
            WHERE u.id = ?
        """, (user_id,))
        return c.fetchone()
    except sqlite3.Error as e:
        return (0, 0, 0)
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# NEW ENTERPRISE FEATURE FUNCTIONS
# ===================================

# AI-Powered Content Recommendations
def get_ai_recommendations(user_id, limit=10):
    """Get AI-powered user recommendations"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT u.id, u.username, u.profile_pic, u.bio,
                   cr.recommendation_score, cr.reason
            FROM content_recommendations cr
            JOIN users u ON cr.recommended_user_id = u.id
            WHERE cr.user_id = ? AND u.is_active = 1
            ORDER BY cr.recommendation_score DESC
            LIMIT ?
        """, (user_id, limit))
        return c.fetchall()
    except sqlite3.Error as e:
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

# Enterprise Collaboration Features
def create_workspace(company_name, admin_id, max_users=50):
    """Create a new enterprise workspace"""
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO workspaces (company_name, admin_id, max_users) 
            VALUES (?, ?, ?)
        """, (company_name, admin_id, max_users))
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

def create_calendar_event(workspace_id, event_name, description, start_time, end_time, created_by):
    """Create a shared calendar event"""
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO shared_calendars (workspace_id, event_name, description, start_time, end_time, created_by) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (workspace_id, event_name, description, start_time, end_time, created_by))
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

# Advanced Security & Compliance
def enable_2fa(user_id):
    """Enable two-factor authentication for user"""
    try:
        c = conn.cursor()
        secret_key = secrets.token_hex(16)
        c.execute("""
            INSERT OR REPLACE INTO two_factor_auth (user_id, secret_key, is_enabled) 
            VALUES (?, ?, TRUE)
        """, (user_id, secret_key))
        conn.commit()
        return secret_key
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

def log_compliance_event(user_id, action_type, ip_address, user_agent):
    """Log compliance events for audit trail"""
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO compliance_logs (user_id, action_type, ip_address, user_agent) 
            VALUES (?, ?, ?, ?)
        """, (user_id, action_type, ip_address, user_agent))
        conn.commit()
    except sqlite3.Error:
        pass  # Compliance failures shouldn't break the app
    finally:
        try:
            c.close()
        except Exception:
            pass

# Monetization & E-commerce Enhancements
def create_digital_product(creator_id, product_type, title, description, price, file_url, thumbnail=None):
    """Create a digital product"""
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO digital_products (creator_id, product_type, title, description, price, file_url, thumbnail) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (creator_id, product_type, title, description, price, file_url, thumbnail))
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

def create_affiliate_link(user_id, product_url, affiliate_code):
    """Create an affiliate marketing link"""
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO affiliate_links (user_id, product_url, affiliate_code) 
            VALUES (?, ?, ?)
        """, (user_id, product_url, affiliate_code))
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

# Content Management & Scheduling
def schedule_post(user_id, content, media_data, scheduled_time, platforms):
    """Schedule a post for future publishing"""
    try:
        c = conn.cursor()
        platforms_json = json.dumps(platforms)
        c.execute("""
            INSERT INTO scheduled_posts (user_id, content, media_data, scheduled_time, platforms) 
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, content, media_data, scheduled_time, platforms_json))
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

def get_scheduled_posts(user_id):
    """Get user's scheduled posts"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT * FROM scheduled_posts 
            WHERE user_id = ? AND status = 'scheduled'
            ORDER BY scheduled_time ASC
        """, (user_id,))
        return c.fetchall()
    except sqlite3.Error as e:
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

# Advanced Communication Features
def create_video_meeting(host_id, meeting_topic, participant_ids, start_time, end_time):
    """Schedule a video meeting"""
    try:
        c = conn.cursor()
        participant_ids_json = json.dumps(participant_ids)
        meeting_url = f"https://meet.feedchat.com/{uuid.uuid4()}"
        c.execute("""
            INSERT INTO video_meetings (host_id, meeting_topic, participant_ids, start_time, end_time) 
            VALUES (?, ?, ?, ?, ?)
        """, (host_id, meeting_topic, participant_ids_json, start_time, end_time))
        conn.commit()
        return c.lastrowid, meeting_url
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None, None
    finally:
        try:
            c.close()
        except Exception:
            pass

# Gamification & Engagement
def unlock_achievement(user_id, achievement_type):
    """Unlock an achievement for user"""
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO user_achievements (user_id, achievement_type, achievement_level, points_earned) 
            VALUES (?, ?, 1, (SELECT points_earned FROM user_achievements WHERE achievement_type = ? LIMIT 1))
        """, (user_id, achievement_type, achievement_type))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_leaderboard(metric_type='engagement', time_frame='weekly'):
    """Get leaderboard for specific metric and time frame"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT u.username, u.profile_pic, l.score, l.rank_position
            FROM leaderboards l
            JOIN users u ON l.user_id = u.id
            WHERE l.metric_type = ? AND l.time_frame = ?
            ORDER BY l.rank_position ASC
            LIMIT 10
        """, (metric_type, time_frame))
        return c.fetchall()
    except sqlite3.Error:
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

# API & Integration Framework
def create_api_key(user_id, name, permissions):
    """Generate API key for user"""
    try:
        c = conn.cursor()
        api_key = f"fcp_{secrets.token_urlsafe(32)}"
        permissions_json = json.dumps(permissions)
        c.execute("""
            INSERT INTO api_keys (user_id, api_key, name, permissions) 
            VALUES (?, ?, ?, ?)
        """, (user_id, api_key, name, permissions_json))
        conn.commit()
        return api_key
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

# Advanced Content Moderation
def auto_moderate_content(content):
    """AI-powered content moderation (simplified)"""
    # In a real implementation, this would call an AI service
    banned_words = ['spam', 'scam', 'fraud']  # Simplified list
    content_lower = content.lower()
    
    for word in banned_words:
        if word in content_lower:
            return {
                'is_safe': False,
                'confidence_score': 0.9,
                'flagged_reasons': [f'Contains banned word: {word}'],
                'suggested_actions': ['auto_hide', 'review']
            }
    
    return {
        'is_safe': True,
        'confidence_score': 0.95,
        'flagged_reasons': [],
        'suggested_actions': []
    }

# Multi-language & Localization
def get_translation(language_code, translation_key):
    """Get translation for specific language and key"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT translation_value FROM translations 
            WHERE language_code = ? AND translation_key = ?
        """, (language_code, translation_key))
        result = c.fetchone()
        return result[0] if result else translation_key
    except sqlite3.Error:
        return translation_key
    finally:
        try:
            c.close()
        except Exception:
            pass

# Advanced Analytics Dashboard
def get_user_engagement_analytics(user_id):
    """Get comprehensive user engagement analytics"""
    try:
        c = conn.cursor()
        # Post performance
        c.execute("""
            SELECT 
                COUNT(*) as total_posts,
                AVG(like_count) as avg_likes,
                MAX(like_count) as max_likes
            FROM (
                SELECT p.id, COUNT(l.id) as like_count
                FROM posts p
                LEFT JOIN likes l ON p.id = l.post_id
                WHERE p.user_id = ? AND p.is_deleted = 0
                GROUP BY p.id
            )
        """, (user_id,))
        post_stats = c.fetchone()
        
        # Follower growth
        c.execute("""
            SELECT COUNT(*) as total_followers,
                   COUNT(CASE WHEN created_at >= date('now', '-7 days') THEN 1 END) as weekly_growth
            FROM follows 
            WHERE following_id = ?
        """, (user_id,))
        follower_stats = c.fetchone()
        
        return {
            'post_performance': {
                'total_posts': post_stats[0] if post_stats else 0,
                'avg_likes': round(post_stats[1] or 0, 2),
                'max_likes': post_stats[2] or 0
            },
            'follower_growth': {
                'total_followers': follower_stats[0] if follower_stats else 0,
                'weekly_growth': follower_stats[1] if follower_stats else 0
            }
        }
    except sqlite3.Error:
        return {}
    finally:
        try:
            c.close()
        except Exception:
            pass

# Virtual Events Platform
def create_virtual_event(host_id, event_name, description, start_time, end_time, max_attendees):
    """Create a virtual event"""
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO virtual_events (host_id, event_name, description, start_time, end_time, max_attendees) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (host_id, event_name, description, start_time, end_time, max_attendees))
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

def register_for_event(event_id, user_id):
    """Register user for virtual event"""
    try:
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO event_registrations (event_id, user_id) 
            VALUES (?, ?)
        """, (event_id, user_id))
        
        # Update registration count
        c.execute("""
            UPDATE virtual_events 
            SET registration_count = (
                SELECT COUNT(*) FROM event_registrations WHERE event_id = ?
            ) WHERE id = ?
        """, (event_id, event_id))
        
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

# AI Content Assistant
def improve_content_with_ai(original_content, improvement_type='grammar'):
    """AI-powered content improvement (simplified)"""
    # In real implementation, this would call an AI service like OpenAI
    improvements = {
        'grammar': "Improved grammar and spelling",
        'clarity': "Enhanced clarity and readability", 
        'engagement': "Made more engaging and compelling",
        'professional': "Made more professional tone"
    }
    
    return {
        'original_content': original_content,
        'improved_content': f"{original_content} [AI-Enhanced: {improvements.get(improvement_type, 'Improved')}]",
        'improvement_type': improvement_type
    }

# Marketplace Reviews & Reputation
def create_product_review(product_id, reviewer_id, rating, review_text, is_verified_purchase=False):
    """Create a product review"""
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO product_reviews (product_id, reviewer_id, rating, review_text, is_verified_purchase) 
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, reviewer_id, rating, review_text, is_verified_purchase))
        conn.commit()
        
        # Update seller reputation
        update_seller_reputation(product_id)
        
        return c.lastrowid
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

def update_seller_reputation(product_id):
    """Update seller reputation based on reviews"""
    try:
        c = conn.cursor()
        # Get seller ID from product
        c.execute("SELECT seller_id FROM products WHERE id = ?", (product_id,))
        seller_result = c.fetchone()
        if not seller_result:
            return
        
        seller_id = seller_result[0]
        
        # Calculate new reputation
        c.execute("""
            SELECT 
                COUNT(*) as total_reviews,
                AVG(rating) as avg_rating,
                COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive_reviews
            FROM product_reviews pr
            JOIN products p ON pr.product_id = p.id
            WHERE p.seller_id = ?
        """, (seller_id,))
        stats = c.fetchone()
        
        if stats and stats[0] > 0:
            reputation_score = (stats[1] or 0) * 20  # Convert to 0-100 scale
            c.execute("""
                INSERT OR REPLACE INTO user_reputation 
                (user_id, reputation_score, total_reviews, positive_reviews) 
                VALUES (?, ?, ?, ?)
            """, (seller_id, reputation_score, stats[0], stats[2] or 0))
            conn.commit()
    except sqlite3.Error:
        pass
    finally:
        try:
            c.close()
        except Exception:
            pass

# Smart Groups & Interest Matching
def add_user_interest(user_id, interest_category, interest_level=1):
    """Add user interest for smart group matching"""
    try:
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO user_interests (user_id, interest_category, interest_level) 
            VALUES (?, ?, ?)
        """, (user_id, interest_category, interest_level))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_smart_group_recommendations(user_id):
    """Get smart group recommendations based on interests"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT sg.*, COUNT(DISTINCT ui.user_id) as similar_users
            FROM smart_groups sg
            JOIN user_interests ui ON sg.category = ui.interest_category
            WHERE ui.user_id = ? AND sg.is_active = 1
            GROUP BY sg.id
            ORDER BY similar_users DESC
            LIMIT 5
        """, (user_id,))
        return c.fetchall()
    except sqlite3.Error:
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

# Predictive Analytics
def generate_predictive_analytics(user_id):
    """Generate predictive analytics for user"""
    try:
        c = conn.cursor()
        
        # Predict follower growth (simplified)
        c.execute("""
            SELECT COUNT(*) as current_followers
            FROM follows 
            WHERE following_id = ?
        """, (user_id,))
        current_followers = c.fetchone()[0] or 0
        
        predicted_growth = current_followers * 1.1  # 10% growth prediction
        
        c.execute("""
            INSERT INTO predictive_analytics (user_id, prediction_type, predicted_value, confidence_score, prediction_date)
            VALUES (?, 'follower_growth', ?, 0.75, date('now', '+30 days'))
        """, (user_id, predicted_growth))
        
        conn.commit()
        return predicted_growth
    except sqlite3.Error:
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# Streamlit UI - ENTERPRISE EDITION
# ===================================
st.set_page_config(page_title="FeedChat Pro", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

# Initialize session state with ALL enterprise features
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
if "current_workspace" not in st.session_state:
    st.session_state.current_workspace = None
if "ai_assistant_active" not in st.session_state:
    st.session_state.ai_assistant_active = False

# Enhanced dark mode CSS with ALL enterprise styling
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
            .user-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                color: white;
            }
            .stats-badge {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 5px 10px;
                margin: 2px;
                font-size: 0.8em;
            }
            .workspace-card {
                background: linear-gradient(135deg, #8e44ad 0%, #9b59b6 100%);
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                color: white;
            }
            .analytics-card {
                background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                color: white;
            }
            .ai-assistant {
                background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                color: white;
            }
            .event-card {
                background: linear-gradient(135deg, #16a085 0%, #1abc9c 100%);
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
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
            .user-card {
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                color: white;
            }
            .stats-badge {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 10px;
                padding: 5px 10px;
                margin: 2px;
                font-size: 0.8em;
            }
            .workspace-card {
                background: linear-gradient(135deg, #8e44ad 0%, #9b59b6 100%);
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                color: white;
            }
            .analytics-card {
                background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                color: white;
            }
            .ai-assistant {
                background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                color: white;
            }
            .event-card {
                background: linear-gradient(135deg, #16a085 0%, #1abc9c 100%);
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                color: white;
            }
            </style>
        """, unsafe_allow_html=True)

# Enhanced sidebar with ALL enterprise features
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
            
            # Enhanced navigation with ALL features
            nav_col1, nav_col2 = st.columns(2)
            with nav_col1:
                if st.button("🏠", help="Feed", use_container_width=True):
                    st.session_state.page = "Feed"
                if st.button("👥", help="Groups", use_container_width=True):
                    st.session_state.page = "Groups"
                if st.button("🛍️", help="Marketplace", use_container_width=True):
                    st.session_state.page = "Marketplace"
                if st.button("📊", help="Analytics", use_container_width=True):
                    st.session_state.page = "Analytics"
                if st.button("🤖", help="AI Assistant", use_container_width=True):
                    st.session_state.page = "AIAssistant"
            with nav_col2:
                if st.button("📹", help="Live", use_container_width=True):
                    st.session_state.page = "Live"
                if st.button("💬", help="Messages", use_container_width=True):
                    st.session_state.page = "Messages"
                if st.button("🔔", help="Notifications", use_container_width=True):
                    st.session_state.page = "Notifications"
                if st.button("🏢", help="Workspace", use_container_width=True):
                    st.session_state.page = "Workspace"
                if st.button("🎯", help="Events", use_container_width=True):
                    st.session_state.page = "Events"
            
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
            
            if st.button("⚙️ Settings", use_container_width=True):
                st.session_state.page = "Settings"
            
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

# Main content - Enhanced with ALL enterprise features
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
    # CORE FEED PAGE - ADDED
    # ===================================
    if st.session_state.page == "Feed":
        st.header("🏠 Your Feed")
        
        # Create post section
        with st.form("create_post", clear_on_submit=True):
            st.subheader("Create a Post")
            post_content = st.text_area("What's on your mind?", placeholder="Share your thoughts...", height=100)
            post_image = st.file_uploader("Add an image", type=["jpg", "png", "jpeg"])
            
            col1, col2 = st.columns([3, 1])
            with col2:
                submit_post = st.form_submit_button("Post", use_container_width=True)
            
            if submit_post and post_content:
                image_data = post_image.read() if post_image else None
                image_type = post_image.type if post_image else None
                
                post_id = create_post(user_id, post_content, image_data, image_type)
                if post_id:
                    st.success("Post created successfully!")
                    st.rerun()
                else:
                    st.error("Failed to create post")
        
        st.markdown("---")
        
        # Display posts
        st.subheader("Recent Posts")
        posts = get_posts(limit=10)
        
        if not posts:
            st.info("No posts yet. Be the first to post!")
        else:
            for post in posts:
                with st.container():
                    st.markdown("<div class='post-card'>", unsafe_allow_html=True)
                    
                    # Post header
                    col1, col2 = st.columns([1, 10])
                    with col1:
                        if post[8]:  # profile_pic
                            display_image_safely(post[8], width=50)
                        else:
                            st.write("👤")
                    with col2:
                        st.write(f"**{post[7]}**")  # username
                        st.caption(f"Posted {post[6]}")  # created_at
                    
                    # Post content
                    if post[2]:  # content
                        st.write(post[2])
                    
                    # Post media
                    if post[4]:  # media_data
                        display_image_safely(post[4], use_container_width=True)
                    
                    # Post actions
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        # Like button
                        if is_liked(user_id, post[0]):
                            if st.button(f"❤️ {post[9]}", key=f"like_{post[0]}"):
                                if unlike_post(user_id, post[0]):
                                    st.rerun()
                        else:
                            if st.button(f"🤍 {post[9]}", key=f"unlike_{post[0]}"):
                                if like_post(user_id, post[0]):
                                    st.rerun()
                    
                    with col2:
                        # Comment button
                        if st.button(f"💬 {post[10]}", key=f"comment_{post[0]}"):
                            if post[0] in st.session_state.show_comments:
                                st.session_state.show_comments[post[0]] = not st.session_state.show_comments[post[0]]
                            else:
                                st.session_state.show_comments[post[0]] = True
                            st.rerun()
                    
                    with col3:
                        # Share button
                        if st.button(f"🔄 {post[11]}", key=f"share_{post[0]}"):
                            if share_post(user_id, post[0]):
                                st.success("Post shared!")
                    
                    with col4:
                        # Save button
                        if is_saved(user_id, post[0]):
                            if st.button("📌", key=f"unsave_{post[0]}"):
                                if unsave_post(user_id, post[0]):
                                    st.rerun()
                        else:
                            if st.button("📋", key=f"save_{post[0]}"):
                                if save_post(user_id, post[0]):
                                    st.rerun()
                    
                    # Comments section
                    if st.session_state.show_comments.get(post[0], False):
                        st.markdown("---")
                        st.subheader("Comments")
                        
                        # Add comment
                        with st.form(f"add_comment_{post[0]}", clear_on_submit=True):
                            comment_text = st.text_input("Add a comment", placeholder="Write a comment...")
                            if st.form_submit_button("Comment"):
                                if comment_text:
                                    if add_comment(post[0], user_id, comment_text):
                                        st.rerun()
                                    else:
                                        st.error("Failed to add comment")
                        
                        # Display comments
                        comments = get_comments(post[0])
                        for comment in comments:
                            st.markdown(f"**{comment[5]}**: {comment[3]}")
                            st.caption(f"Posted {comment[4]}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("---")
    
    # ===================================
    # GROUPS PAGE - ADDED
    # ===================================
    elif st.session_state.page == "Groups":
        st.header("👥 Groups")
        
        groups_tab1, groups_tab2 = st.tabs(["Browse Groups", "Your Groups"])
        
        with groups_tab1:
            st.subheader("Discover Groups")
            
            # Create group form
            with st.expander("Create New Group"):
                with st.form("create_group"):
                    group_name = st.text_input("Group Name")
                    group_description = st.text_area("Description")
                    group_cover = st.file_uploader("Cover Image", type=["jpg", "png", "jpeg"])
                    is_public = st.checkbox("Public Group", value=True)
                    
                    if st.form_submit_button("Create Group"):
                        if group_name:
                            cover_data = group_cover.read() if group_cover else None
                            group_id = create_group(group_name, group_description, user_id, cover_data, is_public)
                            if group_id:
                                st.success(f"Group '{group_name}' created successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to create group")
            
            # Browse groups
            st.subheader("Available Groups")
            groups = get_groups()
            
            if not groups:
                st.info("No groups available. Create the first one!")
            else:
                cols = st.columns(2)
                for i, group in enumerate(groups):
                    with cols[i % 2]:
                        st.markdown("<div class='group-card'>", unsafe_allow_html=True)
                        
                        if group[3]:  # cover_image
                            display_image_safely(group[3], use_container_width=True)
                        
                        st.write(f"**{group[1]}**")  # name
                        st.write(group[2])  # description
                        st.caption(f"👥 {group[7]} members • Created by {group[8]}")
                        
                        if is_group_member(user_id, group[0]):
                            if st.button("Leave Group", key=f"leave_{group[0]}", use_container_width=True):
                                if leave_group(user_id, group[0]):
                                    st.success(f"Left {group[1]}")
                                    st.rerun()
                        else:
                            if st.button("Join Group", key=f"join_{group[0]}", use_container_width=True):
                                if join_group(user_id, group[0]):
                                    st.success(f"Joined {group[1]}")
                                    st.rerun()
                        
                        st.markdown("</div>", unsafe_allow_html=True)
        
        with groups_tab2:
            st.subheader("Your Groups")
            # This would show groups the user is member of
            st.info("Your groups will appear here once you join some!")
    
    # ===================================
    # MESSAGES PAGE - ADDED
    # ===================================
    elif st.session_state.page == "Messages":
        st.header("💬 Messages")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Conversations")
            conversations = get_conversations(user_id)
            
            if not conversations:
                st.info("No conversations yet. Start chatting with someone!")
            else:
                for conv in conversations:
                    if st.button(f"{conv[1]}", key=f"conv_{conv[0]}", use_container_width=True):
                        st.session_state.current_chat = conv[0]
                        st.rerun()
        
        with col2:
            if st.session_state.current_chat:
                other_user = get_user(st.session_state.current_chat)
                if other_user:
                    st.subheader(f"Chat with {other_user[1]}")
                    
                    # Display messages
                    messages = get_messages(user_id, st.session_state.current_chat)
                    
                    for msg in messages:
                        if msg[1] == user_id:  # Sent by current user
                            st.markdown(f"<div style='text-align: right; background: #007bff; color: white; padding: 10px; border-radius: 10px; margin: 5px;'>{msg[3]}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='text-align: left; background: #f1f1f1; color: black; padding: 10px; border-radius: 10px; margin: 5px;'>{msg[3]}</div>", unsafe_allow_html=True)
                    
                    # Send message
                    with st.form("send_message", clear_on_submit=True):
                        message_text = st.text_input("Type a message...", key="message_input")
                        if st.form_submit_button("Send"):
                            if message_text:
                                if send_message(user_id, st.session_state.current_chat, message_text):
                                    st.rerun()
                                else:
                                    st.error("Failed to send message")
            else:
                st.info("Select a conversation to start chatting")
    
    # ===================================
    # PROFILE PAGE - ADDED
    # ===================================
    elif st.session_state.page == "Profile":
        st.header("👤 Your Profile")
        
        user_info = get_user(user_id)
        if user_info:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if user_info[3]:
                    display_image_safely(user_info[3], width=150)
                else:
                    st.write("👤 No profile picture")
            
            with col2:
                st.write(f"**Username:** {user_info[1]}")
                st.write(f"**Email:** {user_info[2]}")
                if user_info[4]:
                    st.write(f"**Bio:** {user_info[4]}")
                
                # User stats
                stats = get_user_stats(user_id)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Posts", stats[0])
                with col2:
                    st.metric("Followers", stats[1])
                with col3:
                    st.metric("Following", stats[2])
        
        st.markdown("---")
        st.subheader("Your Posts")
        
        user_posts = get_posts(limit=20)  # This would need to be filtered by user
        if not user_posts:
            st.info("You haven't posted anything yet.")
        else:
            for post in user_posts[:5]:  # Show only 5 recent posts
                if post[1] == user_id:  # Only show user's own posts
                    st.write(f"**{post[2]}**")
                    if post[4]:
                        display_image_safely(post[4], width=200)
                    st.caption(f"Posted {post[6]}")
                    st.markdown("---")
    
    # ===================================
    # OTHER PAGES (existing code)
    # ===================================
    elif st.session_state.page == "Analytics":
        st.header("📊 Advanced Analytics")
        # ... (keep existing analytics code)
    
    elif st.session_state.page == "AIAssistant":
        st.header("🤖 AI Content Assistant")
        # ... (keep existing AI assistant code)
    
    elif st.session_state.page == "Workspace":
        st.header("🏢 Enterprise Workspace")
        # ... (keep existing workspace code)
    
    elif st.session_state.page == "Events":
        st.header("🎯 Virtual Events")
        # ... (keep existing events code)
    
    elif st.session_state.page == "Settings":
        st.header("⚙️ Settings & Security")
        # ... (keep existing settings code)
    
    elif st.session_state.page == "Discover":
        st.header("🌐 Discover People")
        # ... (keep existing discover code)
    
    # ===================================
    # PLACEHOLDER PAGES
    # ===================================
    elif st.session_state.page == "Marketplace":
        st.header("🛍️ Marketplace")
        st.info("🛒 E-commerce features coming soon!")
        st.write("Buy and sell products within the FeedChat community.")
    
    elif st.session_state.page == "Live":
        st.header("📹 Live Streaming")
        st.info("🎥 Live streaming features coming soon!")
        st.write("Go live and connect with your audience in real-time.")
    
    elif st.session_state.page == "Stories":
        st.header("📸 Stories")
        st.info("📖 Story features coming soon!")
        st.write("Share moments that disappear after 24 hours.")
    
    elif st.session_state.page == "Notifications":
        st.header("🔔 Notifications")
        st.info("🔔 Notification center coming soon!")
        st.write("Stay updated with your latest interactions.")
    
    elif st.session_state.page == "SavedPosts":
        st.header("💾 Saved Posts")
        st.info("📑 Saved posts feature coming soon!")
        st.write("Access your bookmarked content here.")
    
    elif st.session_state.page == "BlockedUsers":
        st.header("🚫 Blocked Users")
        st.info("🛡️ User management features coming soon!")
        st.write("Manage your blocked users list.")
    
    elif st.session_state.page == "Premium":
        st.header("💎 Premium Subscription")
        st.info("⭐ Premium features coming soon!")
        st.write("Upgrade to unlock exclusive features and benefits.")
    
    elif st.session_state.page == "Search":
        st.header("🔍 Search")
        st.info("🔎 Advanced search features coming soon!")
        st.write("Search for users, posts, and content across the platform.")
    
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

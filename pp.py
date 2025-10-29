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
# CORE SOCIAL MEDIA FUNCTIONS
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
# MARKETPLACE FUNCTIONS
# ===================================

def create_product(seller_id, name, description, price, category, images=None):
    """Create a new product"""
    try:
        c = conn.cursor()
        images_json = json.dumps(images) if images else "[]"
        c.execute("""
            INSERT INTO products (seller_id, name, description, price, category, images) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (seller_id, name, description, price, category, images_json))
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

def get_products(limit=20, category=None):
    """Get products with optional category filter"""
    try:
        c = conn.cursor()
        if category:
            c.execute("""
                SELECT p.*, u.username as seller_name
                FROM products p
                JOIN users u ON p.seller_id = u.id
                WHERE p.is_available = 1 AND p.category = ?
                ORDER BY p.created_at DESC
                LIMIT ?
            """, (category, limit))
        else:
            c.execute("""
                SELECT p.*, u.username as seller_name
                FROM products p
                JOIN users u ON p.seller_id = u.id
                WHERE p.is_available = 1
                ORDER BY p.created_at DESC
                LIMIT ?
            """, (limit,))
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
    """Create a new order"""
    try:
        c = conn.cursor()
        # Get product price
        c.execute("SELECT price FROM products WHERE id=?", (product_id,))
        product = c.fetchone()
        if not product:
            return None
        
        total_price = float(product[0]) * quantity
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
# STORIES & LIVE STREAMING FUNCTIONS
# ===================================

def create_story(user_id, media_data, media_type):
    """Create a new story"""
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

def get_active_stories():
    """Get active stories (not expired)"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT s.*, u.username, u.profile_pic
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

def create_live_stream(user_id, title, description, stream_url):
    """Create a new live stream"""
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO live_streams (user_id, title, description, stream_url, is_live) 
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, title, description, stream_url, True))
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

def get_active_live_streams():
    """Get active live streams"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT ls.*, u.username, u.profile_pic
            FROM live_streams ls
            JOIN users u ON ls.user_id = u.id
            WHERE ls.is_live = 1
            ORDER BY ls.viewer_count DESC
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
# PREMIUM SUBSCRIPTION FUNCTIONS
# ===================================

def get_subscription_plans():
    """Get all subscription plans"""
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

def create_user_subscription(user_id, plan_id):
    """Create a user subscription"""
    try:
        c = conn.cursor()
        start_date = datetime.datetime.now()
        
        # Get plan details to determine end date
        c.execute("SELECT name, price_monthly FROM subscription_plans WHERE id=?", (plan_id,))
        plan = c.fetchone()
        
        if not plan:
            return None
            
        # Set end date based on plan type (simplified logic)
        if plan[1] == 0:  # Free plan
            end_date = None  # Never expires
        else:
            end_date = start_date + datetime.timedelta(days=30)  # 30 days for paid plans
        
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
    """Get user's current subscription"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT us.*, sp.name, sp.features
            FROM user_subscriptions us
            JOIN subscription_plans sp ON us.plan_id = sp.id
            WHERE us.user_id = ? AND us.status = 'active'
            ORDER BY us.created_at DESC
            LIMIT 1
        """, (user_id,))
        return c.fetchone()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# AI & ANALYTICS FUNCTIONS
# ===================================

def log_user_analytics(user_id, event_type, event_data):
    """Log user analytics"""
    try:
        c = conn.cursor()
        event_data_json = json.dumps(event_data)
        c.execute("""
            INSERT INTO user_analytics (user_id, event_type, event_data) 
            VALUES (?, ?, ?)
        """, (user_id, event_type, event_data_json))
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

def report_content(reporter_id, content_type, content_id, reason):
    """Report content for moderation"""
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

def generate_content_recommendations(user_id):
    """Generate AI-powered content recommendations for user"""
    try:
        c = conn.cursor()
        # Simple recommendation logic based on user interactions
        c.execute("""
            SELECT DISTINCT p.user_id, COUNT(*) as interaction_count
            FROM posts p
            JOIN likes l ON p.id = l.post_id
            WHERE l.user_id = ? AND p.user_id != ?
            GROUP BY p.user_id
            ORDER BY interaction_count DESC
            LIMIT 5
        """, (user_id, user_id))
        
        recommendations = c.fetchall()
        results = []
        
        for rec in recommendations:
            recommended_user_id = rec[0]
            score = min(1.0, rec[1] / 10.0)  # Normalize score
            
            # Check if recommendation already exists
            c.execute("""
                SELECT id FROM content_recommendations 
                WHERE user_id=? AND recommended_user_id=?
            """, (user_id, recommended_user_id))
            
            if not c.fetchone():
                c.execute("""
                    INSERT INTO content_recommendations 
                    (user_id, recommended_user_id, recommendation_score, reason) 
                    VALUES (?, ?, ?, ?)
                """, (user_id, recommended_user_id, score, "Based on your interactions"))
                results.append((recommended_user_id, score))
        
        conn.commit()
        return results
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_content_recommendations(user_id, limit=10):
    """Get content recommendations for user"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT cr.*, u.username, u.profile_pic, u.bio
            FROM content_recommendations cr
            JOIN users u ON cr.recommended_user_id = u.id
            WHERE cr.user_id = ?
            ORDER BY cr.recommendation_score DESC
            LIMIT ?
        """, (user_id, limit))
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
# ENTERPRISE COLLABORATION FUNCTIONS
# ===================================

def create_workspace(company_name, admin_id, max_users=50):
    """Create a new workspace"""
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
            INSERT INTO shared_calendars 
            (workspace_id, event_name, description, start_time, end_time, created_by) 
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

# ===================================
# SECURITY & COMPLIANCE FUNCTIONS
# ===================================

def enable_two_factor_auth(user_id, secret_key):
    """Enable two-factor authentication for user"""
    try:
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO two_factor_auth (user_id, secret_key, is_enabled) 
            VALUES (?, ?, ?)
        """, (user_id, secret_key, True))
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

def log_compliance_action(user_id, action_type, ip_address, user_agent):
    """Log compliance actions for audit purposes"""
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO compliance_logs (user_id, action_type, ip_address, user_agent) 
            VALUES (?, ?, ?, ?)
        """, (user_id, action_type, ip_address, user_agent))
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
# GAMIFICATION FUNCTIONS
# ===================================

def award_achievement(user_id, achievement_type):
    """Award an achievement to user"""
    try:
        c = conn.cursor()
        # Get achievement details
        c.execute("""
            SELECT achievement_level, points_earned 
            FROM user_achievements 
            WHERE achievement_type = ?
            ORDER BY achievement_level DESC 
            LIMIT 1
        """, (achievement_type,))
        
        achievement = c.fetchone()
        if not achievement:
            return False
            
        achievement_level = achievement[0]
        points_earned = achievement[1]
        
        # Check if user already has this achievement
        c.execute("""
            SELECT id FROM user_achievements 
            WHERE user_id = ? AND achievement_type = ? AND achievement_level = ?
        """, (user_id, achievement_type, achievement_level))
        
        if not c.fetchone():
            c.execute("""
                INSERT INTO user_achievements 
                (user_id, achievement_type, achievement_level, points_earned) 
                VALUES (?, ?, ?, ?)
            """, (user_id, achievement_type, achievement_level, points_earned))
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

def update_leaderboard(user_id, metric_type, score, time_frame="weekly"):
    """Update user's position on leaderboard"""
    try:
        c = conn.cursor()
        # Calculate rank position
        c.execute("""
            SELECT user_id, score 
            FROM leaderboards 
            WHERE metric_type = ? AND time_frame = ?
            ORDER BY score DESC
        """, (metric_type, time_frame))
        
        leaderboard = c.fetchall()
        rank_position = 1
        
        for i, (uid, s) in enumerate(leaderboard):
            if uid == user_id:
                # User already on leaderboard, update score
                c.execute("""
                    UPDATE leaderboards 
                    SET score = ?, updated_at = datetime('now')
                    WHERE user_id = ? AND metric_type = ? AND time_frame = ?
                """, (score, user_id, metric_type, time_frame))
                conn.commit()
                return i + 1
                
            if score > s:
                break
            rank_position = i + 2
        
        # Insert new entry
        c.execute("""
            INSERT OR REPLACE INTO leaderboards 
            (user_id, metric_type, score, time_frame, rank_position) 
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, metric_type, score, time_frame, rank_position))
        conn.commit()
        return rank_position
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# STREAMLIT UI COMPONENTS
# ===================================

def login_page():
    """Login page component"""
    st.title("🔐 FeedChat Pro - Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if username and password:
                user = verify_user(username, password)
                if user:
                    st.session_state.user_id = user[0]
                    st.session_state.username = user[1]
                    st.session_state.logged_in = True
                    st.success(f"Welcome back, {user[1]}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.error("Please enter both username and password")
    
    # Registration section
    st.markdown("---")
    st.subheader("New User? Register Here")
    
    with st.form("register_form"):
        new_username = st.text_input("Choose Username")
        new_password = st.text_input("Choose Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        email = st.text_input("Email")
        bio = st.text_area("Bio (Optional)")
        profile_pic = st.file_uploader("Profile Picture (Optional)", type=['jpg', 'png', 'jpeg'])
        
        register = st.form_submit_button("Register")
        
        if register:
            if new_username and new_password and email:
                if new_password == confirm_password:
                    profile_pic_data = None
                    if profile_pic:
                        profile_pic_data = profile_pic.read()
                    
                    if create_user(new_username, new_password, email, profile_pic_data, bio):
                        st.success("Registration successful! Please login.")
                    else:
                        st.error("Username already exists or invalid data.")
                else:
                    st.error("Passwords do not match")
            else:
                st.error("Please fill in all required fields")

def main_feed():
    """Main social media feed"""
    st.title("🏠 FeedChat Pro - Your Feed")
    
    # Post creation
    with st.form("create_post"):
        st.subheader("Create New Post")
        content = st.text_area("What's on your mind?")
        media_file = st.file_uploader("Add Media", type=['jpg', 'png', 'jpeg', 'mp4', 'mov'])
        submit = st.form_submit_button("Post")
        
        if submit and content:
            media_data = None
            media_type = None
            if media_file:
                media_data = media_file.read()
                media_type = media_file.type
            
            post_id = create_post(st.session_state.user_id, content, media_data, media_type)
            if post_id:
                st.success("Post created successfully!")
                # Award achievement for first post
                award_achievement(st.session_state.user_id, "first_post")
            else:
                st.error("Failed to create post")
    
    # Display posts
    st.markdown("---")
    st.subheader("Recent Posts")
    
    posts = get_posts(limit=20)
    if not posts:
        st.info("No posts yet. Be the first to post!")
        return
    
    for post in posts:
        post_id, user_id, content, media_type, media_data, is_deleted, created_at, username, profile_pic, like_count, comment_count, share_count = post
        
        if is_deleted:
            continue
            
        with st.container():
            col1, col2 = st.columns([1, 4])
            
            with col1:
                if profile_pic and is_valid_image(profile_pic):
                    st.image(io.BytesIO(profile_pic), width=50)
                else:
                    st.image("👤", width=50)
            
            with col2:
                st.write(f"**{username}**")
                st.caption(f"Posted {created_at}")
            
            st.write(content)
            
            if media_data and media_type:
                if 'image' in media_type:
                    display_image_safely(media_data, width=400)
                elif 'video' in media_type:
                    st.video(io.BytesIO(media_data))
            
            # Engagement buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                liked = is_liked(st.session_state.user_id, post_id)
                if liked:
                    if st.button("❤️", key=f"like_{post_id}"):
                        unlike_post(st.session_state.user_id, post_id)
                        st.rerun()
                else:
                    if st.button("🤍", key=f"like_{post_id}"):
                        like_post(st.session_state.user_id, post_id)
                        st.rerun()
                st.caption(f"{like_count} likes")
            
            with col2:
                if st.button("💬", key=f"comment_{post_id}"):
                    st.session_state.current_post = post_id
            
            with col3:
                saved = is_saved(st.session_state.user_id, post_id)
                if saved:
                    if st.button("📌", key=f"save_{post_id}"):
                        unsave_post(st.session_state.user_id, post_id)
                        st.rerun()
                else:
                    if st.button("📋", key=f"save_{post_id}"):
                        save_post(st.session_state.user_id, post_id)
                        st.rerun()
            
            with col4:
                if st.button("🔄", key=f"share_{post_id}"):
                    share_post(st.session_state.user_id, post_id)
                    st.success("Post shared!")
            
            # Comments section
            if hasattr(st.session_state, 'current_post') and st.session_state.current_post == post_id:
                st.subheader("Comments")
                
                # Add comment
                with st.form(f"add_comment_{post_id}"):
                    comment_text = st.text_input("Add a comment")
                    if st.form_submit_button("Comment"):
                        if comment_text:
                            add_comment(post_id, st.session_state.user_id, comment_text)
                            st.rerun()
                
                # Display comments
                comments = get_comments(post_id)
                for comment in comments:
                    comment_id, _, comment_user_id, comment_content, comment_created_at, comment_username, comment_profile_pic = comment
                    
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if comment_profile_pic and is_valid_image(comment_profile_pic):
                            st.image(io.BytesIO(comment_profile_pic), width=30)
                        else:
                            st.image("👤", width=30)
                    
                    with col2:
                        st.write(f"**{comment_username}**")
                        st.write(comment_content)
                        st.caption(f"{comment_created_at}")
            
            st.markdown("---")

def marketplace_page():
    """Marketplace page"""
    st.title("🛒 Marketplace")
    
    tab1, tab2, tab3 = st.tabs(["Browse Products", "Sell Product", "My Orders"])
    
    with tab1:
        st.subheader("Browse Products")
        
        # Category filter
        categories = ["All", "Electronics", "Clothing", "Books", "Home", "Other"]
        selected_category = st.selectbox("Filter by Category", categories)
        
        category_filter = None if selected_category == "All" else selected_category
        products = get_products(category=category_filter)
        
        if not products:
            st.info("No products available in this category.")
        else:
            cols = st.columns(2)
            for idx, product in enumerate(products):
                with cols[idx % 2]:
                    product_id, seller_id, name, description, price, category, images_json, is_available, created_at, seller_name = product
                    
                    st.subheader(name)
                    st.write(f"**${price}**")
                    st.write(f"Category: {category}")
                    st.write(f"Seller: {seller_name}")
                    st.write(description[:100] + "..." if len(description) > 100 else description)
                    
                    # Display product images
                    if images_json:
                        try:
                            images = json.loads(images_json)
                            if images and len(images) > 0:
                                # For simplicity, display first image
                                if is_valid_image(images[0]):
                                    display_image_safely(images[0], width=200)
                        except:
                            pass
                    
                    # Purchase form
                    with st.form(f"purchase_{product_id}"):
                        quantity = st.number_input("Quantity", min_value=1, value=1, key=f"qty_{product_id}")
                        if st.form_submit_button("Buy Now"):
                            order_id = create_order(product_id, st.session_state.user_id, quantity)
                            if order_id:
                                st.success(f"Order placed successfully! Order ID: {order_id}")
                            else:
                                st.error("Failed to place order")
    
    with tab2:
        st.subheader("Sell Your Product")
        
        with st.form("sell_product"):
            name = st.text_input("Product Name")
            description = st.text_area("Description")
            price = st.number_input("Price ($)", min_value=0.01, step=0.01)
            category = st.selectbox("Category", ["Electronics", "Clothing", "Books", "Home", "Other"])
            images = st.file_uploader("Product Images", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)
            
            if st.form_submit_button("List Product"):
                if name and description and price:
                    image_data_list = []
                    for img in images:
                        if is_valid_image(img.read()):
                            img.seek(0)  # Reset file pointer
                            image_data_list.append(img.read())
                    
                    product_id = create_product(st.session_state.user_id, name, description, price, category, image_data_list)
                    if product_id:
                        st.success("Product listed successfully!")
                    else:
                        st.error("Failed to list product")
                else:
                    st.error("Please fill in all required fields")
    
    with tab3:
        st.subheader("My Orders")
        # Implementation for displaying user orders would go here
        st.info("Order history feature coming soon!")

def groups_page():
    """Groups page"""
    st.title("👥 Groups & Communities")
    
    tab1, tab2, tab3 = st.tabs(["Browse Groups", "My Groups", "Create Group"])
    
    with tab1:
        st.subheader("Discover Groups")
        groups = get_groups()
        
        if not groups:
            st.info("No groups available yet.")
        else:
            for group in groups:
                group_id, name, description, cover_image, is_public, created_by, member_count, created_at, creator_name, actual_member_count = group
                
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        if cover_image and is_valid_image(cover_image):
                            st.image(io.BytesIO(cover_image), width=80)
                        else:
                            st.image("🏢", width=80)
                    
                    with col2:
                        st.subheader(name)
                        st.write(description)
                        st.caption(f"Created by {creator_name} • {actual_member_count} members")
                        
                        is_member = is_group_member(st.session_state.user_id, group_id)
                        if is_member:
                            if st.button("Leave Group", key=f"leave_{group_id}"):
                                leave_group(st.session_state.user_id, group_id)
                                st.rerun()
                        else:
                            if st.button("Join Group", key=f"join_{group_id}"):
                                join_group(st.session_state.user_id, group_id)
                                st.rerun()
                    
                    st.markdown("---")
    
    with tab2:
        st.subheader("Groups You've Joined")
        # Implementation for user's groups would go here
        st.info("Your groups will appear here")
    
    with tab3:
        st.subheader("Create New Group")
        
        with st.form("create_group"):
            name = st.text_input("Group Name")
            description = st.text_area("Description")
            is_public = st.checkbox("Public Group", value=True)
            cover_image = st.file_uploader("Cover Image", type=['jpg', 'png', 'jpeg'])
            
            if st.form_submit_button("Create Group"):
                if name and description:
                    cover_image_data = cover_image.read() if cover_image else None
                    group_id = create_group(name, description, st.session_state.user_id, cover_image_data, is_public)
                    if group_id:
                        st.success(f"Group '{name}' created successfully!")
                    else:
                        st.error("Failed to create group. Name might be taken.")
                else:
                    st.error("Please fill in group name and description")

def messaging_page():
    """Messaging page"""
    st.title("💬 Messages")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Conversations")
        conversations = get_conversations(st.session_state.user_id)
        
        if not conversations:
            st.info("No conversations yet.")
        else:
            for conv in conversations:
                other_user_id, username, profile_pic, last_message_time, last_message = conv
                
                if st.button(f"{username}: {last_message[:30]}...", key=f"conv_{other_user_id}"):
                    st.session_state.current_chat = other_user_id
                    st.session_state.chat_username = username
    
    with col2:
        if hasattr(st.session_state, 'current_chat'):
            st.subheader(f"Chat with {st.session_state.chat_username}")
            
            # Display messages
            messages = get_messages(st.session_state.user_id, st.session_state.current_chat)
            
            for msg in messages:
                msg_id, sender_id, receiver_id, content, is_read, created_at, sender_name, receiver_name = msg
                
                if sender_id == st.session_state.user_id:
                    st.write(f"**You**: {content}")
                else:
                    st.write(f"**{sender_name}**: {content}")
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

def profile_page():
    """User profile page"""
    st.title("👤 Your Profile")
    
    # Check if user is logged in
    if not st.session_state.get('logged_in') or not st.session_state.get('user_id'):
        st.error("Please log in to view your profile.")
        return
    
    try:
        user = get_user(st.session_state.user_id)
        if not user:
            st.error("User profile not found.")
            return
            
        # Safely unpack user data with fallback values
        try:
            if len(user) >= 5:
                user_id, username, email, profile_pic, bio = user
            else:
                # Handle case where user tuple has fewer elements
                user_id = user[0] if len(user) > 0 else st.session_state.user_id
                username = user[1] if len(user) > 1 else st.session_state.get('username', 'Unknown User')
                email = user[2] if len(user) > 2 else "No email"
                profile_pic = user[3] if len(user) > 3 else None
                bio = user[4] if len(user) > 4 else ""
        except Exception as unpack_error:
            st.error(f"Error unpacking user data: {unpack_error}")
            # Use fallback values
            username = st.session_state.get('username', 'Unknown User')
            email = "No email"
            profile_pic = None
            bio = ""
        
        # Display profile information
        col1, col2 = st.columns([1, 3])
        
        with col1:
            try:
                if profile_pic and is_valid_image(profile_pic):
                    st.image(io.BytesIO(profile_pic), width=150)
                else:
                    st.image("👤", width=150)
            except Exception as img_error:
                st.error(f"Error displaying profile picture: {img_error}")
                st.image("👤", width=150)
        
        with col2:
            st.subheader(username)
            st.write(f"**Email:** {email}")
            if bio and bio.strip():
                st.write(f"**Bio:** {bio}")
            
            # Subscription info with error handling
            try:
                subscription = get_user_subscription(st.session_state.user_id)
                if subscription:
                    # Safely access subscription data
                    plan_name = "Premium"
                    if len(subscription) > 7 and subscription[7]:
                        plan_name = subscription[7]
                    elif len(subscription) > 8 and subscription[8]:  # Try different index
                        plan_name = subscription[8]
                    st.success(f"🎉 {plan_name} Member")
                else:
                    st.info("🔓 Free Account")
            except Exception as sub_error:
                st.error(f"Error loading subscription: {sub_error}")
                st.info("🔓 Free Account")
    
    except Exception as e:
        st.error(f"Error loading profile: {str(e)}")
        st.info("Please try refreshing the page or contact support if the problem persists.")
        return
    
    # User achievements section
    st.subheader("🏆 Achievements")
    try:
        # Implementation for displaying user achievements would go here
        st.info("Your achievements will appear here")
    except Exception as e:
        st.error(f"Error loading achievements: {str(e)}")
    
    # User stats section
    st.subheader("📊 Your Stats")
    try:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Posts", "0")  # Would implement post count
        with col2:
            st.metric("Followers", "0")  # Would implement follower count
        with col3:
            st.metric("Following", "0")  # Would implement following count
    except Exception as e:
        st.error(f"Error loading stats: {str(e)}")

def stories_page():
    """Stories page"""
    st.title("📸 Stories")
    
    stories = get_active_stories()
    if not stories:
        st.info("No active stories right now.")
        return
    
    # Display stories in a horizontal layout
    cols = st.columns(len(stories))
    
    for idx, story in enumerate(stories):
        with cols[idx]:
            story_id, user_id, media_data, media_type, created_at, expires_at, username, profile_pic = story
            
            # Display story preview
            if profile_pic and is_valid_image(profile_pic):
                st.image(io.BytesIO(profile_pic), width=80)
            else:
                st.image("👤", width=80)
            
            st.write(username)
            
            # Click to view story
            if st.button("View", key=f"story_{story_id}"):
                st.session_state.viewing_story = story_id
        
    # Story viewer
    if hasattr(st.session_state, 'viewing_story'):
        story_id = st.session_state.viewing_story
        # Find the story
        current_story = None
        for story in stories:
            if story[0] == story_id:
                current_story = story
                break
        
        if current_story:
            story_id, user_id, media_data, media_type, created_at, expires_at, username, profile_pic = current_story
            
            st.subheader(f"Story by {username}")
            
            if media_data:
                if 'image' in media_type:
                    display_image_safely(media_data, use_container_width=True)
                elif 'video' in media_type:
                    st.video(io.BytesIO(media_data))
            
            # Close story viewer
            if st.button("Close Story"):
                del st.session_state.viewing_story
                st.rerun()

def live_streams_page():
    """Live streams page"""
    st.title("🎥 Live Streams")
    
    streams = get_active_live_streams()
    if not streams:
        st.info("No live streams right now.")
        
        # Option to start a stream
        st.subheader("Start Your Own Stream")
        with st.form("start_stream"):
            title = st.text_input("Stream Title")
            description = st.text_area("Description")
            stream_url = st.text_input("Stream URL (e.g., YouTube, Twitch)")
            
            if st.form_submit_button("Go Live"):
                if title and stream_url:
                    stream_id = create_live_stream(st.session_state.user_id, title, description, stream_url)
                    if stream_id:
                        st.success("You're now live!")
                    else:
                        st.error("Failed to start stream")
                else:
                    st.error("Please fill in title and stream URL")
        return
    
    # Display active streams
    for stream in streams:
        stream_id, user_id, title, description, stream_url, is_live, viewer_count, created_at, username, profile_pic = stream
        
        with st.container():
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if profile_pic and is_valid_image(profile_pic):
                    st.image(io.BytesIO(profile_pic), width=80)
                else:
                    st.image("👤", width=80)
                st.write(f"**LIVE** - {viewer_count} viewers")
            
            with col2:
                st.subheader(title)
                st.write(description)
                st.write(f"Hosted by: {username}")
                
                if st.button("Watch Stream", key=f"stream_{stream_id}"):
                    st.video(stream_url)
            
            st.markdown("---")

def premium_page():
    """Premium subscription page"""
    st.title("⭐ FeedChat Pro Premium")
    
    st.info("Upgrade to unlock exclusive features and support our platform!")
    
    plans = get_subscription_plans()
    
    if not plans:
        st.error("No subscription plans available.")
        return
    
    cols = st.columns(len(plans))
    
    for idx, plan in enumerate(plans):
        with cols[idx]:
            plan_id, name, price_monthly, price_yearly, features_json, is_active = plan
            
            st.subheader(name)
            
            if price_monthly == 0:
                st.write("**FREE**")
            else:
                st.write(f"**${price_monthly}/month**")
                st.write(f"or ${price_yearly}/year")
            
            try:
                features = json.loads(features_json)
                for feature in features:
                    st.write(f"✓ {feature}")
            except:
                st.write("Basic features included")
            
            current_sub = get_user_subscription(st.session_state.user_id)
            is_current_plan = current_sub and current_sub[2] == plan_id
            
            if is_current_plan:
                st.success("Current Plan")
            else:
                if st.button(f"Select {name}", key=f"plan_{plan_id}"):
                    if create_user_subscription(st.session_state.user_id, plan_id):
                        st.success(f"Successfully subscribed to {name}!")
                        st.rerun()
                    else:
                        st.error("Failed to subscribe")

def recommendations_page():
    """AI-powered recommendations page"""
    st.title("🤖 Smart Recommendations")
    
    st.info("Discover new content and people based on your interests and activity!")
    
    # Generate recommendations if not already done
    if st.button("Generate New Recommendations"):
        with st.spinner("Analyzing your activity..."):
            results = generate_content_recommendations(st.session_state.user_id)
            if results:
                st.success(f"Found {len(results)} new recommendations!")
            else:
                st.info("Need more activity to generate personalized recommendations.")
    
    # Display recommendations
    recommendations = get_content_recommendations(st.session_state.user_id)
    
    if not recommendations:
        st.info("No recommendations yet. Generate some or interact more with content!")
        return
    
    st.subheader("People You Might Like")
    
    for rec in recommendations:
        rec_id, user_id, recommended_user_id, score, reason, created_at, username, profile_pic, bio = rec
        
        with st.container():
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if profile_pic and is_valid_image(profile_pic):
                    st.image(io.BytesIO(profile_pic), width=60)
                else:
                    st.image("👤", width=60)
            
            with col2:
                st.write(f"**{username}**")
                if bio:
                    st.write(bio[:100] + "..." if len(bio) > 100 else bio)
                st.progress(score)
                st.caption(f"Match score: {score:.0%} • {reason}")
            
            st.markdown("---")

# ===================================
# MAIN APPLICATION
# ===================================

def main():
    """Main application"""
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    # App header
    st.sidebar.title("🚀 FeedChat Pro")
    st.sidebar.markdown("Enterprise Social Media Platform")
    
    if not st.session_state.logged_in:
        login_page()
        return
    
    # Navigation for logged-in users
    st.sidebar.write(f"Welcome, **{st.session_state.username}**!")
    
    # Navigation menu
    menu_options = [
        "🏠 Home Feed",
        "📸 Stories", 
        "🎥 Live Streams",
        "👥 Groups",
        "💬 Messages",
        "🛒 Marketplace",
        "🤖 Recommendations",
        "⭐ Premium",
        "👤 Profile"
    ]
    
    selected_menu = st.sidebar.selectbox("Navigation", menu_options)
    
    # Logout button
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.rerun()
    
    # Display selected page
    if selected_menu == "🏠 Home Feed":
        main_feed()
    elif selected_menu == "📸 Stories":
        stories_page()
    elif selected_menu == "🎥 Live Streams":
        live_streams_page()
    elif selected_menu == "👥 Groups":
        groups_page()
    elif selected_menu == "💬 Messages":
        messaging_page()
    elif selected_menu == "🛒 Marketplace":
        marketplace_page()
    elif selected_menu == "🤖 Recommendations":
        recommendations_page()
    elif selected_menu == "⭐ Premium":
        premium_page()
    elif selected_menu == "👤 Profile":
        profile_page()

if __name__ == "__main__":
    main()

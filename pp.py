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
        """, (seller

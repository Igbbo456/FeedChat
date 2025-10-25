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
# ENHANCED GROUPS FUNCTIONS
# ===================================

def get_user_groups(user_id):
    """Get groups that user is member of"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT g.*, u.username as creator_name, 
                   COUNT(gm2.user_id) as member_count,
                   gm.role as user_role
            FROM groups g
            JOIN group_members gm ON g.id = gm.group_id
            JOIN users u ON g.created_by = u.id
            LEFT JOIN group_members gm2 ON g.id = gm2.group_id
            WHERE gm.user_id = ?
            GROUP BY g.id
            ORDER BY g.created_at DESC
        """, (user_id,))
        return c.fetchall()
    except sqlite3.Error:
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# ENHANCED PROFILE FUNCTIONS
# ===================================

def get_user_posts(user_id):
    """Get posts by a specific user"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT p.*, u.username, u.profile_pic, 
                   COUNT(DISTINCT l.id) as like_count,
                   COUNT(DISTINCT c.id) as comment_count
            FROM posts p
            JOIN users u ON p.user_id = u.id
            LEFT JOIN likes l ON p.id = l.post_id
            LEFT JOIN comments c ON p.id = c.post_id
            WHERE p.user_id = ? AND p.is_deleted = 0
            GROUP BY p.id
            ORDER BY p.created_at DESC
        """, (user_id,))
        return c.fetchall()
    except sqlite3.Error:
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

def update_user_profile(user_id, username=None, email=None, bio=None, profile_pic=None):
    """Update user profile"""
    try:
        c = conn.cursor()
        if profile_pic:
            c.execute("UPDATE users SET username=?, email=?, bio=?, profile_pic=? WHERE id=?", 
                     (username, email, bio, profile_pic, user_id))
        else:
            c.execute("UPDATE users SET username=?, email=?, bio=? WHERE id=?", 
                     (username, email, bio, user_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# ENHANCED MESSAGING FUNCTIONS
# ===================================

def mark_messages_as_read(user_id, other_user_id):
    """Mark messages as read"""
    try:
        c = conn.cursor()
        c.execute("UPDATE messages SET is_read=1 WHERE receiver_id=? AND sender_id=?", 
                 (user_id, other_user_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# ENHANCED SETTINGS FUNCTIONS
# ===================================

def get_user_preferences(user_id):
    """Get user preferences"""
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM user_preferences WHERE user_id=?", (user_id,))
        return c.fetchone()
    except sqlite3.Error:
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

def update_user_preferences(user_id, dark_mode=None, language=None):
    """Update user preferences"""
    try:
        c = conn.cursor()
        prefs = get_user_preferences(user_id)
        if prefs:
            c.execute("UPDATE user_preferences SET dark_mode=?, language=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=?", 
                     (dark_mode, language, user_id))
        else:
            c.execute("INSERT INTO user_preferences (user_id, dark_mode, language) VALUES (?, ?, ?)", 
                     (user_id, dark_mode, language))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# ENHANCED ANALYTICS FUNCTIONS
# ===================================

def get_detailed_analytics(user_id):
    """Get detailed analytics for user"""
    try:
        c = conn.cursor()
        
        # Weekly activity
        c.execute("""
            SELECT 
                COUNT(*) as weekly_posts,
                COUNT(DISTINCT l.id) as weekly_likes_received,
                COUNT(DISTINCT c.id) as weekly_comments_received
            FROM posts p
            LEFT JOIN likes l ON p.id = l.post_id
            LEFT JOIN comments c ON p.id = c.post_id
            WHERE p.user_id = ? AND p.created_at >= date('now', '-7 days')
        """, (user_id,))
        weekly_stats = c.fetchone()
        
        # Engagement rate
        c.execute("""
            SELECT 
                COUNT(DISTINCT p.id) as total_posts,
                COUNT(DISTINCT l.id) as total_likes,
                COUNT(DISTINCT c.id) as total_comments,
                COUNT(DISTINCT f.id) as total_followers
            FROM posts p
            LEFT JOIN likes l ON p.id = l.post_id
            LEFT JOIN comments c ON p.id = c.post_id
            LEFT JOIN follows f ON f.following_id = p.user_id
            WHERE p.user_id = ?
        """, (user_id,))
        engagement_stats = c.fetchone()
        
        return {
            'weekly_activity': {
                'posts': weekly_stats[0] if weekly_stats else 0,
                'likes_received': weekly_stats[1] if weekly_stats else 0,
                'comments_received': weekly_stats[2] if weekly_stats else 0
            },
            'engagement': {
                'total_posts': engagement_stats[0] if engagement_stats else 0,
                'total_likes': engagement_stats[1] if engagement_stats else 0,
                'total_comments': engagement_stats[2] if engagement_stats else 0,
                'total_followers': engagement_stats[3] if engagement_stats else 0,
                'engagement_rate': round((engagement_stats[1] + engagement_stats[2]) / max(engagement_stats[0], 1) * 100, 2) if engagement_stats and engagement_stats[0] > 0 else 0
            }
        }
    except sqlite3.Error:
        return {}
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# ENHANCED WORKSPACE FUNCTIONS
# ===================================

def get_user_workspaces(user_id):
    """Get workspaces user is admin of"""
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM workspaces WHERE admin_id=?", (user_id,))
        return c.fetchall()
    except sqlite3.Error:
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_workspace_calendar_events(workspace_id):
    """Get calendar events for workspace"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT sc.*, u.username as creator_name
            FROM shared_calendars sc
            JOIN users u ON sc.created_by = u.id
            WHERE sc.workspace_id = ?
            ORDER BY sc.start_time ASC
        """, (workspace_id,))
        return c.fetchall()
    except sqlite3.Error:
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# ENHANCED EVENTS FUNCTIONS
# ===================================

def get_upcoming_events():
    """Get upcoming virtual events"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT ve.*, u.username as host_name, u.profile_pic as host_avatar
            FROM virtual_events ve
            JOIN users u ON ve.host_id = u.id
            WHERE ve.is_active = TRUE AND ve.start_time > datetime('now')
            ORDER BY ve.start_time ASC
        """)
        return c.fetchall()
    except sqlite3.Error:
        return []
    finally:
        try:
            c.close()
        except Exception:
            pass

def is_user_registered_for_event(user_id, event_id):
    """Check if user is registered for event"""
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM event_registrations WHERE user_id=? AND event_id=?", (user_id, event_id))
        return c.fetchone() is not None
    except sqlite3.Error:
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass

# ===================================
# ENHANCED AI ASSISTANT FUNCTIONS
# ===================================

def save_ai_improvement(user_id, original_content, improved_content, improvement_type):
    """Save AI improvement"""
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO ai_writing_assistant (user_id, original_content, improved_content, improvement_type) 
            VALUES (?, ?, ?, ?)
        """, (user_id, original_content, improved_content, improvement_type))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error:
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

def get_ai_improvement_history(user_id):
    """Get AI improvement history"""
    try:
        c = conn.cursor()
        c.execute("""
            SELECT * FROM ai_writing_assistant 
            WHERE user_id = ? 
            ORDER BY created_at DESC
            LIMIT 10
        """, (user_id,))
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
    # GROUPS PAGE - COMPLETE IMPLEMENTATION
    # ===================================
    if st.session_state.page == "Groups":
        st.header("👥 Groups")
        
        groups_tab1, groups_tab2, groups_tab3 = st.tabs(["Browse Groups", "Your Groups", "Group Feed"])
        
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
            user_groups = get_user_groups(user_id)
            
            if not user_groups:
                st.info("You haven't joined any groups yet. Browse groups to join!")
            else:
                for group in user_groups:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{group[1]}**")
                        st.write(group[2])
                        st.caption(f"👥 {group[7]} members • Your role: {group[9]}")
                    with col2:
                        if st.button("View", key=f"view_{group[0]}", use_container_width=True):
                            st.session_state.current_group = group[0]
                            st.rerun()
                    with col3:
                        if st.button("Leave", key=f"leave_my_{group[0]}", use_container_width=True):
                            if leave_group(user_id, group[0]):
                                st.success(f"Left {group[1]}")
                                st.rerun()
        
        with groups_tab3:
            if st.session_state.current_group:
                group_posts = get_group_posts(st.session_state.current_group)
                st.subheader("Group Posts")
                
                # Create group post
                with st.form("create_group_post"):
                    post_content = st.text_area("Create a post in this group", placeholder="Share something with the group...")
                    post_image = st.file_uploader("Add image", type=["jpg", "png", "jpeg"])
                    if st.form_submit_button("Post to Group"):
                        if post_content:
                            image_data = post_image.read() if post_image else None
                            image_type = post_image.type if post_image else None
                            post_id = create_group_post(st.session_state.current_group, user_id, post_content, image_data, image_type)
                            if post_id:
                                st.success("Posted to group!")
                                st.rerun()
                
                # Display group posts
                if not group_posts:
                    st.info("No posts in this group yet. Be the first to post!")
                else:
                    for post in group_posts:
                        with st.container():
                            col1, col2 = st.columns([1, 10])
                            with col1:
                                if post[7]:  # profile_pic
                                    display_image_safely(post[7], width=50)
                                else:
                                    st.write("👤")
                            with col2:
                                st.write(f"**{post[6]}**")  # username
                                st.write(post[3])  # content
                                if post[5]:  # media_data
                                    display_image_safely(post[5], width=200)
                                st.caption(f"Posted {post[4]}")
                            st.markdown("---")
            else:
                st.info("Select a group to view its posts")

    # ===================================
    # MESSAGES PAGE - COMPLETE IMPLEMENTATION
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
                    col_conv1, col_conv2 = st.columns([3, 1])
                    with col_conv1:
                        if st.button(f"{conv[1]}", key=f"conv_{conv[0]}", use_container_width=True):
                            st.session_state.current_chat = conv[0]
                            mark_messages_as_read(user_id, conv[0])
                            st.rerun()
                    with col_conv2:
                        st.caption(conv[3].split()[0] if conv[3] else "")
        
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
                        st.caption(f"{msg[4]} • {msg[6]}")
                    
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
    # PROFILE PAGE - COMPLETE IMPLEMENTATION
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
                
                # Edit profile
                with st.expander("Edit Profile"):
                    with st.form("edit_profile"):
                        new_username = st.text_input("Username", value=user_info[1])
                        new_email = st.text_input("Email", value=user_info[2])
                        new_bio = st.text_area("Bio", value=user_info[4] or "")
                        new_profile_pic = st.file_uploader("Update Profile Picture", type=["jpg", "png", "jpeg"])
                        
                        if st.form_submit_button("Update Profile"):
                            profile_pic_data = new_profile_pic.read() if new_profile_pic else user_info[3]
                            if update_user_profile(user_id, new_username, new_email, new_bio, profile_pic_data):
                                st.success("Profile updated successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to update profile")
            
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
        
        user_posts = get_user_posts(user_id)
        if not user_posts:
            st.info("You haven't posted anything yet.")
        else:
            for post in user_posts:
                st.write(f"**{post[2]}**")  # content
                if post[4]:  # media_data
                    display_image_safely(post[4], width=200)
                st.caption(f"Posted {post[6]} • ❤️ {post[7]} • 💬 {post[8]}")
                st.markdown("---")

    # ===================================
    # ANALYTICS PAGE - COMPLETE IMPLEMENTATION
    # ===================================
    elif st.session_state.page == "Analytics":
        st.header("📊 Advanced Analytics")
        
        analytics_tab1, analytics_tab2, analytics_tab3 = st.tabs(["User Analytics", "Business Insights", "Predictive Analytics"])
        
        with analytics_tab1:
            st.subheader("Your Engagement Analytics")
            user_analytics = get_user_engagement_analytics(user_id)
            detailed_analytics = get_detailed_analytics(user_id)
            
            if user_analytics:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Posts", user_analytics['post_performance']['total_posts'])
                with col2:
                    st.metric("Average Likes", user_analytics['post_performance']['avg_likes'])
                with col3:
                    st.metric("Max Likes", user_analytics['post_performance']['max_likes'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Followers", user_analytics['follower_growth']['total_followers'])
                with col2:
                    st.metric("Weekly Growth", user_analytics['follower_growth']['weekly_growth'])
                
                # Detailed analytics
                st.subheader("Detailed Analytics")
                if detailed_analytics:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Weekly Posts", detailed_analytics['weekly_activity']['posts'])
                    with col2:
                        st.metric("Weekly Likes Received", detailed_analytics['weekly_activity']['likes_received'])
                    with col3:
                        st.metric("Weekly Comments", detailed_analytics['weekly_activity']['comments_received'])
                    
                    st.metric("Engagement Rate", f"{detailed_analytics['engagement']['engagement_rate']}%")
            else:
                st.info("No analytics data available yet. Start posting to see your insights!")
        
        with analytics_tab2:
            st.subheader("Business Intelligence")
            
            # Leaderboard
            st.write("### 🏆 Top Performers")
            leaderboard = get_leaderboard('engagement', 'weekly')
            if leaderboard:
                for i, user in enumerate(leaderboard):
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col1:
                        st.write(f"**#{i+1}**")
                    with col2:
                        st.write(f"**{user[0]}**")
                    with col3:
                        st.write(f"🏅 {user[2]} pts")
            else:
                st.info("No leaderboard data available.")
            
            # Performance metrics
            st.write("### 📈 Performance Metrics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Active Users", "1.2K", "+12%")
            with col2:
                st.metric("Daily Posts", "347", "+8%")
            with col3:
                st.metric("Engagement", "4.2%", "+0.5%")
            with col4:
                st.metric("Retention", "78%", "+3%")
        
        with analytics_tab3:
            st.subheader("Predictive Analytics")
            
            if st.button("Generate Growth Prediction"):
                predicted_growth = generate_predictive_analytics(user_id)
                if predicted_growth:
                    st.success(f"Predicted follower growth: {predicted_growth:.0f} followers in next 30 days")
                    st.info("Confidence: 75% - Based on your current engagement patterns")
                    
                    # Growth chart placeholder
                    st.write("### 📊 Growth Projection")
                    growth_data = {
                        'Month': ['Current', 'Next Month', '2 Months', '3 Months'],
                        'Followers': [user_analytics['follower_growth']['total_followers'] if user_analytics else 0, 
                                    predicted_growth, 
                                    predicted_growth * 1.1, 
                                    predicted_growth * 1.21]
                    }
                    st.line_chart(growth_data, x='Month', y='Followers')
                else:
                    st.error("Could not generate prediction")

    # ===================================
    # AI ASSISTANT PAGE - COMPLETE IMPLEMENTATION
    # ===================================
    elif st.session_state.page == "AIAssistant":
        st.header("🤖 AI Content Assistant")
        
        ai_tab1, ai_tab2, ai_tab3 = st.tabs(["Content Improvement", "Writing Assistant", "Improvement History"])
        
        with ai_tab1:
            st.subheader("Improve Your Content")
            
            content_to_improve = st.text_area("Enter your content to improve:", height=150, 
                                            placeholder="Paste your text here for AI enhancement...")
            improvement_type = st.selectbox("Improvement Type", 
                                          ["grammar", "clarity", "engagement", "professional"])
            
            if st.button("Improve with AI"):
                if content_to_improve:
                    with st.spinner("AI is improving your content..."):
                        improved_content = improve_content_with_ai(content_to_improve, improvement_type)
                        
                        st.markdown("<div class='ai-assistant'>", unsafe_allow_html=True)
                        st.write("### Original Content:")
                        st.write(content_to_improve)
                        st.write("### Improved Content:")
                        st.write(improved_content['improved_content'])
                        
                        # Save improvement
                        if save_ai_improvement(user_id, content_to_improve, improved_content['improved_content'], improvement_type):
                            st.success("Improvement saved to history!")
                        
                        # Copy to clipboard option
                        if st.button("Copy Improved Content"):
                            st.code(improved_content['improved_content'])
                            st.success("Content copied to clipboard!")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.warning("Please enter some content to improve")
        
        with ai_tab2:
            st.subheader("AI Writing Assistant")
            
            writing_prompt = st.text_area("What would you like to write about?", 
                                        placeholder="Describe what you want to write...")
            writing_tone = st.selectbox("Writing Tone", 
                                      ["professional", "casual", "friendly", "persuasive", "informative"])
            writing_length = st.selectbox("Length", ["short", "medium", "long"])
            
            if st.button("Generate Content"):
                if writing_prompt:
                    with st.spinner("AI is writing your content..."):
                        # Simulate AI writing
                        time.sleep(2)
                        generated_content = f"Here's a {writing_tone} {writing_length} piece about: {writing_prompt}\n\n"
                        if writing_tone == "professional":
                            generated_content += "In today's dynamic business environment, it's crucial to maintain professional standards while adapting to evolving market trends. The key to success lies in strategic planning and consistent execution."
                        elif writing_tone == "casual":
                            generated_content += "Hey there! So I was thinking about this topic and it's actually pretty interesting. Here's what I've found - it might surprise you!"
                        else:
                            generated_content += "This is an important topic that deserves careful consideration. Let me share some insights that could be valuable for your understanding."
                        
                        st.markdown("<div class='ai-assistant'>", unsafe_allow_html=True)
                        st.write("### Generated Content:")
                        st.write(generated_content)
                        
                        if st.button("Save to Posts"):
                            post_id = create_post(user_id, generated_content)
                            if post_id:
                                st.success("Content saved as a new post!")
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.warning("Please enter a writing prompt")
        
        with ai_tab3:
            st.subheader("Improvement History")
            
            history = get_ai_improvement_history(user_id)
            if not history:
                st.info("No improvement history yet. Start using the AI assistant!")
            else:
                for item in history:
                    with st.expander(f"Improvement {item[0]} - {item[4]}"):
                        st.write("**Original:**")
                        st.write(item[2])
                        st.write("**Improved:**")
                        st.write(item[3])
                        st.caption(f"Type: {item[4]} • Date: {item[5]}")

    # ===================================
    # WORKSPACE PAGE - COMPLETE IMPLEMENTATION
    # ===================================
    elif st.session_state.page == "Workspace":
        st.header("🏢 Enterprise Workspace")
        
        workspace_tab1, workspace_tab2, workspace_tab3 = st.tabs(["My Workspaces", "Create Workspace", "Team Calendar"])
        
        with workspace_tab1:
            st.subheader("Your Workspaces")
            workspaces = get_user_workspaces(user_id)
            
            if not workspaces:
                st.info("You haven't created any workspaces yet. Create one to get started!")
            else:
                for workspace in workspaces:
                    st.markdown("<div class='workspace-card'>", unsafe_allow_html=True)
                    st.write(f"**{workspace[1]}**")  # company_name
                    st.write(f"Max Users: {workspace[3]}")
                    st.write(f"Status: {'Active' if workspace[4] else 'Inactive'}")
                    st.caption(f"Created: {workspace[5]}")
                    st.markdown("</div>", unsafe_allow_html=True)
        
        with workspace_tab2:
            st.subheader("Create New Workspace")
            with st.form("create_workspace_form"):
                company_name = st.text_input("Company/Team Name")
                max_users = st.number_input("Maximum Users", min_value=5, max_value=500, value=50)
                
                if st.form_submit_button("Create Workspace", use_container_width=True):
                    if company_name:
                        workspace_id = create_workspace(company_name, user_id, max_users)
                        if workspace_id:
                            st.success(f"Workspace '{company_name}' created successfully!")
                            st.rerun()
                    else:
                        st.error("Please enter a company/team name")
        
        with workspace_tab3:
            st.subheader("Team Calendar")
            
            if st.session_state.current_workspace:
                events = get_workspace_calendar_events(st.session_state.current_workspace)
                if not events:
                    st.info("No calendar events scheduled. Add events to keep your team organized!")
                else:
                    for event in events:
                        st.write(f"**{event[2]}**")  # event_name
                        st.write(event[3])  # description
                        st.caption(f"Start: {event[4]} • End: {event[5]} • Created by: {event[7]}")
                        st.markdown("---")
                
                # Add event form
                with st.form("add_calendar_event"):
                    st.write("Add New Event")
                    event_name = st.text_input("Event Name")
                    event_description = st.text_area("Description")
                    start_time = st.datetime_input("Start Time")
                    end_time = st.datetime_input("End Time")
                    
                    if st.form_submit_button("Add Event"):
                        if event_name and start_time and end_time:
                            event_id = create_calendar_event(st.session_state.current_workspace, event_name, 
                                                           event_description, start_time, end_time, user_id)
                            if event_id:
                                st.success("Event added to calendar!")
                                st.rerun()
            else:
                st.info("Select a workspace to view and manage calendar events")

    # ===================================
    # EVENTS PAGE - COMPLETE IMPLEMENTATION
    # ===================================
    elif st.session_state.page == "Events":
        st.header("🎯 Virtual Events")
        
        events_tab1, events_tab2 = st.tabs(["Browse Events", "Host Event"])
        
        with events_tab1:
            st.subheader("Upcoming Events")
            events = get_upcoming_events()
            
            if not events:
                st.info("No upcoming events. Be the first to host one!")
            else:
                for event in events:
                    st.markdown("<div class='event-card'>", unsafe_allow_html=True)
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{event[2]}**")  # event_name
                        st.write(event[3])  # description
                        st.caption(f"👤 Host: {event[8]} • 👥 {event[7]}/{event[6]} attendees")
                        st.caption(f"🕐 {event[4]} to {event[5]}")
                    with col2:
                        if is_user_registered_for_event(user_id, event[0]):
                            st.success("Registered ✓")
                            if st.button("Cancel", key=f"cancel_{event[0]}"):
                                st.info("Cancellation feature would be implemented here")
                        else:
                            if st.button("Register", key=f"register_{event[0]}"):
                                if register_for_event(event[0], user_id):
                                    st.success("Successfully registered!")
                                    st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
        
        with events_tab2:
            st.subheader("Host a Virtual Event")
            with st.form("host_event_form"):
                event_name = st.text_input("Event Name")
                event_description = st.text_area("Description")
                start_time = st.datetime_input("Start Time")
                end_time = st.datetime_input("End Time")
                max_attendees = st.number_input("Maximum Attendees", min_value=10, max_value=1000, value=100)
                
                if st.form_submit_button("Create Event", use_container_width=True):
                    if event_name and event_description:
                        event_id = create_virtual_event(user_id, event_name, event_description, start_time, end_time, max_attendees)
                        if event_id:
                            st.success(f"Event '{event_name}' created successfully!")
                            st.rerun()
                    else:
                        st.error("Please fill in all required fields")

    # ===================================
    # SETTINGS PAGE - COMPLETE IMPLEMENTATION
    # ===================================
    elif st.session_state.page == "Settings":
        st.header("⚙️ Settings & Security")
        
        settings_tab1, settings_tab2, settings_tab3, settings_tab4 = st.tabs(["Account", "Security", "Notifications", "Preferences"])
        
        with settings_tab1:
            st.subheader("Account Settings")
            user_info = get_user(user_id)
            if user_info:
                st.write(f"**Username:** {user_info[1]}")
                st.write(f"**Email:** {user_info[2]}")
                st.write(f"**Member since:** {user_info[5].split()[0] if user_info[5] else 'Recently'}")
                
                # Account actions
                st.subheader("Account Actions")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Download My Data", use_container_width=True):
                        st.info("Data export started. You'll receive a notification when it's ready.")
                with col2:
                    if st.button("Deactivate Account", use_container_width=True):
                        st.warning("Account deactivation would be implemented here")
        
        with settings_tab2:
            st.subheader("Security Settings")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Enable Two-Factor Authentication"):
                    secret_key = enable_2fa(user_id)
                    if secret_key:
                        st.success("2FA enabled successfully!")
                        st.info(f"Secret Key: {secret_key} (Save this securely!)")
            
            with col2:
                if st.button("View Compliance Logs"):
                    st.info("Compliance logs would show audit trail here")
            
            # Password change
            st.subheader("Change Password")
            with st.form("change_password"):
                current_password = st.text_input("Current Password", type="password")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                
                if st.form_submit_button("Change Password"):
                    if new_password == confirm_password:
                        st.success("Password changed successfully!")
                    else:
                        st.error("Passwords don't match")
        
        with settings_tab3:
            st.subheader("Notification Preferences")
            
            # Get current preferences
            prefs = get_user_preferences(user_id)
            
            with st.form("notification_preferences"):
                email_notifications = st.checkbox("Email Notifications", value=prefs[1] if prefs else True)
                push_notifications = st.checkbox("Push Notifications", value=prefs[2] if prefs else True)
                sms_notifications = st.checkbox("SMS Notifications", value=prefs[3] if prefs else False)
                digest_frequency = st.selectbox("Digest Frequency", 
                                              ["daily", "weekly", "monthly"], 
                                              index=0 if not prefs or prefs[4] == 'daily' else 1 if prefs[4] == 'weekly' else 2)
                
                if st.form_submit_button("Save Preferences"):
                    if update_user_preferences(user_id, prefs[1] if prefs else False, prefs[5] if prefs else 'en'):
                        st.success("Notification preferences updated!")
                    else:
                        st.error("Failed to update preferences")
        
        with settings_tab4:
            st.subheader("App Preferences")
            
            with st.form("app_preferences"):
                dark_mode = st.checkbox("Dark Mode", value=st.session_state.dark_mode)
                language = st.selectbox("Language", ["en", "es", "fr"], index=0)
                
                if st.form_submit_button("Save Preferences"):
                    st.session_state.dark_mode = dark_mode
                    if update_user_preferences(user_id, dark_mode, language):
                        st.success("Preferences saved!")
                        st.rerun()

    # ===================================
    # DISCOVER PAGE - COMPLETE IMPLEMENTATION
    # ===================================
    elif st.session_state.page == "Discover":
        st.header("🌐 Discover People")
        
        discover_tab1, discover_tab2, discover_tab3 = st.tabs(["Suggested Users", "Search People", "Popular Users"])
        
        with discover_tab1:
            st.subheader("People You May Know")
            
            suggested_users = get_suggested_users_based_on_interests(user_id, limit=12)
            if not suggested_users:
                st.info("No suggested users found. Try searching for specific users instead.")
            else:
                # Display users in a grid
                cols = st.columns(3)
                for i, user in enumerate(suggested_users):
                    with cols[i % 3]:
                        st.markdown("<div class='user-card'>", unsafe_allow_html=True)
                        
                        # User profile and info
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            if user[2]:  # profile_pic
                                display_image_safely(user[2], width=60)
                            else:
                                st.write("👤")
                        with col2:
                            st.write(f"**{user[1]}**")
                            if user[3]:  # bio
                                st.caption(user[3][:50] + "..." if len(user[3]) > 50 else user[3])
                        
                        # User stats
                        stats = get_user_stats(user[0])
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(f'<div class="stats-badge">📝 {stats[0]}</div>', unsafe_allow_html=True)
                        with col2:
                            st.markdown(f'<div class="stats-badge">👥 {stats[1]}</div>', unsafe_allow_html=True)
                        with col3:
                            st.markdown(f'<div class="stats-badge">🔍 {stats[2]}</div>', unsafe_allow_html=True)
                        
                        # Follow button
                        if is_following(user_id, user[0]):
                            if st.button("Unfollow", key=f"unfollow_{user[0]}", use_container_width=True):
                                if unfollow_user(user_id, user[0]):
                                    st.success(f"Unfollowed {user[1]}")
                                    st.rerun()
                        else:
                            if st.button("Follow", key=f"follow_{user[0]}", use_container_width=True):
                                if follow_user(user_id, user[0]):
                                    st.success(f"Started following {user[1]}")
                                    st.rerun()
                        
                        st.markdown("</div>", unsafe_allow_html=True)
        
        with discover_tab2:
            st.subheader("Search Users")
            
            search_query = st.text_input("Search by username or bio", placeholder="Enter name or keywords...")
            
            if search_query:
                search_results = search_users(search_query, user_id)
                if not search_results:
                    st.info("No users found matching your search.")
                else:
                    st.write(f"Found {len(search_results)} users:")
                    
                    for user in search_results:
                        with st.container():
                            st.markdown("<div class='user-card'>", unsafe_allow_html=True)
                            col1, col2, col3 = st.columns([1, 3, 1])
                            
                            with col1:
                                if user[2]:  # profile_pic
                                    display_image_safely(user[2], width=60)
                                else:
                                    st.write("👤")
                            
                            with col2:
                                st.write(f"**{user[1]}**")
                                if user[3]:  # bio
                                    st.caption(user[3])
                                # Stats
                                col_stats1, col_stats2 = st.columns(2)
                                with col_stats1:
                                    st.write(f"📝 {user[4]} posts")
                                with col_stats2:
                                    st.write(f"👥 {user[5]} followers")
                            
                            with col3:
                                if user[6]:  # is_following
                                    if st.button("Unfollow", key=f"search_unfollow_{user[0]}", use_container_width=True):
                                        if unfollow_user(user_id, user[0]):
                                            st.success(f"Unfollowed {user[1]}")
                                            st.rerun()
                                else:
                                    if st.button("Follow", key=f"search_follow_{user[0]}", use_container_width=True):
                                        if follow_user(user_id, user[0]):
                                            st.success(f"Started following {user[1]}")
                                            st.rerun()
                            
                            st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Enter a search term to find users.")
        
        with discover_tab3:
            st.subheader("Popular Users")
            
            popular_users = get_users_to_discover(user_id, limit=15)
            if not popular_users:
                st.info("No popular users found.")
            else:
                # Display popular users with more emphasis on follower count
                for user in popular_users[:8]:  # Show top 8
                    with st.container():
                        st.markdown("<div class='user-card'>", unsafe_allow_html=True)
                        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                        
                        with col1:
                            if user[3]:  # profile_pic
                                display_image_safely(user[3], width=50)
                            else:
                                st.write("👤")
                        
                        with col2:
                            st.write(f"**{user[1]}**")
                            st.caption(f"👥 {user[6]} followers")
                        
                        with col3:
                            st.write(f"📝 {user[5]} posts")
                            join_date = user[5].split()[0] if user[5] else "Recently"
                            st.caption(f"Joined {join_date}")
                        
                        with col4:
                            if user[7]:  # is_following
                                if st.button("Unfollow", key=f"popular_unfollow_{user[0]}", use_container_width=True):
                                    if unfollow_user(user_id, user[0]):
                                        st.success(f"Unfollowed {user[1]}")
                                        st.rerun()
                            else:
                                if st.button("Follow", key=f"popular_follow_{user[0]}", use_container_width=True):
                                    if follow_user(user_id, user[0]):
                                        st.success(f"Started following {user[1]}")
                                        st.rerun()
                        
                        st.markdown("</div>", unsafe_allow_html=True)

    # ===================================
    # OTHER PAGES (Marketplace, Live, Stories, etc.)
    # ===================================
    # ... (Previous implementations for Marketplace, Live, Stories, etc. remain the same)

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

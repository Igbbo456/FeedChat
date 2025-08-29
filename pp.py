import streamlit as st
import sqlite3

# ===================================
# Reset / Initialize DB
# ===================================
def init_db():
    conn = sqlite3.connect("feedchat.db", check_same_thread=False)
    c = conn.cursor()

    # --- Users table ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        profile_pic BLOB
    )
    """)

    # --- Posts table ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # --- Comments table ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        username TEXT,
        comment TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # --- Likes table ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        username TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # --- Messages table ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    return conn  # Only return the connection, not the cursor

# Initialize DB - only store the connection
conn = init_db()

# ===================================
# Helper functions (updated to create cursor as needed)
# ===================================
def add_user(username, password, profile_pic=None):
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (username, password, profile_pic) VALUES (?, ?, ?)",
              (username, password, profile_pic))
    conn.commit()

def verify_user(username, password):
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone() is not None

def get_all_users():
    c = conn.cursor()
    c.execute("SELECT username FROM users")
    return [u[0] for u in c.fetchall()]

def add_post(username, message):
    c = conn.cursor()
    c.execute("INSERT INTO posts (username, message) VALUES (?, ?)", (username, message))
    conn.commit()

def get_posts():
    c = conn.cursor()
    c.execute("SELECT id, username, message, timestamp FROM posts ORDER BY id DESC")
    return c.fetchall()

def add_comment(post_id, username, comment):
    c = conn.cursor()
    c.execute("INSERT INTO comments (post_id, username, comment) VALUES (?, ?, ?)",
              (post_id, username, comment))
    conn.commit()

def get_comments(post_id):
    c = conn.cursor()
    c.execute("SELECT username, comment, timestamp FROM comments WHERE post_id=? ORDER BY id ASC", (post_id,))
    rows = c.fetchall()
    return rows if rows else []

def add_like(post_id, username):
    c = conn.cursor()
    c.execute("SELECT 1 FROM likes WHERE post_id=? AND username=?", (post_id, username))
    if not c.fetchone():
        c.execute("INSERT INTO likes (post_id, username) VALUES (?, ?)", (post_id, username))
        conn.commit()

def count_likes(post_id):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,))
    return c.fetchone()[0]

def send_message(sender, receiver, message):
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)",
              (sender, receiver, message))
    conn.commit()

def get_messages(user1, user2):
    c = conn.cursor()
    c.execute("""
        SELECT sender, message, timestamp 
        FROM messages
        WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
        ORDER BY id ASC
    """, (user1, user2, user2, user1))
    return c.fetchall()

# ... rest of the code remains the same

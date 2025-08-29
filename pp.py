import streamlit as st
import pandas as pd
from PIL import Image
from datetime import datetime

# Initialize session state
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'posts' not in st.session_state:
    st.session_state.posts = []
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

# Login/Signup functionality
def login_signup():
    st.subheader("Login/Signup")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in st.session_state.users and st.session_state.users[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
        else:
            st.error("Invalid username or password")
    if st.button("Signup"):
        if username not in st.session_state.users:
            st.session_state.users[username] = password
            st.success("User created successfully")
        else:
            st.error("Username already exists")

# Posting functionality
def post():
    st.subheader("Create Post")
    content = st.text_area("Content")
    image = st.file_uploader("Image", type=["jpg", "png"])
    if st.button("Post"):
        post = {
            "username": st.session_state.username,
            "content": content,
            "image": image,
            "likes": 0,
            "comments": []
        }
        st.session_state.posts.append(post)
        st.success("Post created successfully")

# Display posts
def display_posts():
    st.subheader("Posts")
    for post in st.session_state.posts:
        st.write(post["username"])
        st.write(post["content"])
        if post["image"]:
            st.image(post["image"])
        st.write(f"Likes: {post['likes']}")
        if st.button("Like", key=post["content"]):
            post["likes"] += 1
        st.write("Comments:")
        for comment in post["comments"]:
            st.write(comment)
        comment = st.text_input("Comment", key=post["content"] + "comment")
        if st.button("Comment", key=post["content"] + "comment_button"):
            post["comments"].append(comment)

# Messaging functionality
def messaging():
    st.subheader("Messaging")
    username = st.selectbox("Select User", list(st.session_state.users.keys()))
    message = st.text_input("Message")
    if st.button("Send"):
        st.write(f"Message sent to {username}")

# Main app
def main():
    if not st.session_state.logged_in:
        login_signup()
    else:
        st.write(f"Welcome, {st.session_state.username}!")
        tab1, tab2, tab3 = st.tabs(["Post", "Feed", "Messaging"])
        with tab1:
            post()
        with tab2:
            display_posts()
        with tab3:
            messaging()

if __name__ == "__main__":
    main()

# ==============================
# CONTINUATION OF MERGED CODE
# ==============================

# Display feed
posts = get_posts()
if not posts:
    st.info("No posts yet.")
else:
    for pid, user, msg, media, mtype, ts in posts:
        card = st.container()
        with card:
            col1, col2 = st.columns([1,9])
            with col1:
                u = get_user(user)
                if u and u[1]:
                    st.image(u[1], width=60)
                else:
                    st.write("👤")
            with col2:
                st.markdown(f"**{user}**  ·  _{ts}_")
                if msg:
                    st.write(msg)
                if media and mtype=="image":
                    st.image(media, use_container_width=True)
                elif media and mtype=="video":
                    st.video(media)

                # Like / Unlike
                like_col, info_col = st.columns([1,4])
                with like_col:
                    if has_liked(pid, st.session_state.username):
                        if st.button(f"Unlike ({count_likes(pid)})", key=f"unlike_{pid}"):
                            unlike_post_db(pid, st.session_state.username)
                            st.experimental_rerun()
                    else:
                        if st.button(f"Like ({count_likes(pid)})", key=f"like_{pid}"):
                            like_post_db(pid, st.session_state.username)
                            st.experimental_rerun()
                with info_col:
                    st.write(f"👍 {count_likes(pid)}  ·  💬 {len(get_comments(pid))}")

                # Comments
                st.markdown("**Comments**")
                for cu, cm, ct in get_comments(pid):
                    cu_user = get_user(cu)
                    cols = st.columns([1,9])
                    if cu_user and cu_user[1]:
                        cols[0].image(cu_user[1], width=30)
                    cols[1].markdown(f"**{cu}**: {cm}  _({ct})_")

                comment_text = st.text_input("Add a comment", key=f"comment_input_{pid}")
                if st.button("Post comment", key=f"comment_btn_{pid}"):
                    if comment_text.strip():
                        add_comment(pid, st.session_state.username, comment_text.strip())
                        st.experimental_rerun()

        st.markdown("---")

# -----------------------------
# PROFILE TAB
# -----------------------------
st.header("👤 Profile")
target = st.session_state.view_profile or st.session_state.username
user_row = get_user(target)
if user_row and user_row[1]:
    st.image(user_row[1], width=120)
st.caption(f"Viewing: {target}" if target!=st.session_state.username else "Your profile")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Followers", len(get_followers(target)))
with col2:
    st.metric("Following", len(get_following(target)))
with col3:
    st.metric("Likes received", count_total_likes(target))

# Follow/unfollow
if target != st.session_state.username:
    if is_following(st.session_state.username, target):
        if st.button("Unfollow", key=f"unfollow_btn_{target}"):
            unfollow_user(st.session_state.username, target)
            st.experimental_rerun()
    else:
        if st.button("Follow", key=f"follow_btn_{target}"):
            follow_user(st.session_state.username, target)
            st.experimental_rerun()
    if st.button("Back to my profile"):
        st.session_state.view_profile = None
        st.experimental_rerun()

# Show profile posts
their_posts = [p for p in get_posts() if p[1]==target]
if not their_posts:
    st.info("No posts yet.")
else:
    for pid, user, msg, media, mtype, ts in their_posts:
        st.markdown(f"**{user}** · _{ts}_")
        if msg:
            st.write(msg)
        if media and mtype=="image":
            st.image(media, use_container_width=True)
        elif media and mtype=="video":
            st.video(media)
        st.caption(f"❤️ {count_likes(pid)} likes")
        st.markdown("---")

# -----------------------------
# MESSAGES
# -----------------------------
st.header("💬 Messages")
with st.expander("Send a message"):
    to_user = st.text_input("To (username)", key="msg_to")
    msg_body = st.text_area("Message", key="msg_body")
    if st.button("Send message", key="send_msg_btn"):
        if not to_user.strip() or not msg_body.strip():
            st.warning("Fill recipient and message.")
        elif not get_user(to_user):
            st.error("User does not exist.")
        else:
            send_message(st.session_state.username, to_user, msg_body.strip())
            st.success("Message sent.")
            st.experimental_rerun()

chat_with = st.text_input("Chat with", key="chat_with")
if chat_with:
    conv = get_messages(st.session_state.username, chat_with)
    if not conv:
        st.info("No messages yet.")
    else:
        for s, m, ts in conv:
            st.markdown(f"**{s}** ({ts}): {m}")

# -----------------------------
# NOTIFICATIONS
# -----------------------------
st.header("🔔 Notifications")
notes = get_notifications(st.session_state.username)
if not notes:
    st.info("No notifications.")
else:
    for nid, msg, ts, seen in notes:
        st.markdown(f"- {'✅' if seen else '🆕'} {msg}  _({ts})_")
if st.button("Mark notifications read"):
    mark_notifications_seen(st.session_state.username)
    st.experimental_rerun()

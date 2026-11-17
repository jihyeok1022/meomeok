"""Application entry point: python -m streamlit run app.py."""
import streamlit as st

st.set_page_config(page_title='머먹', page_icon='🍚', layout='centered')

# Register the team's existing page files; each owner implements their own page.
# Custom in-page controls provide navigation instead of Streamlit's sidebar.
page = st.navigation(
    [
        st.Page('pages/1_feed.py', title='모집 글', default=True),
        st.Page('pages/2_write_post.py', title='글쓰기', url_path='write'),
        st.Page('pages/3_post_detail.py', title='모집 글 상세', url_path='post_detail'),
        st.Page('pages/4_profile.py', title='내 프로필', url_path='profile'),
        st.Page('pages/5_participation.py', title='내 신청', url_path='participation'),
        st.Page('pages/6_chat.py', title='톡방', url_path='chat'),
    ],
    position='hidden',
)
page.run()

"""Application entry point: python -m streamlit run app.py."""
import streamlit as st
import pymysql

import auth
from ui_common import CSS

st.set_page_config(page_title='머먹', page_icon='🍚', layout='centered')

LOGIN_CSS = """
[data-testid="stMainBlockContainer"]{background:#fff;padding:0!important;}
.st-key-login_shell{padding:32px 28px 28px;box-sizing:border-box;min-height:100dvh;}
.login-brand-row{display:flex;align-items:center;justify-content:space-between;}
.login-wordmark{font-size:25px;font-weight:900;letter-spacing:-1.4px;color:#ff7a3d;}
.login-campus{font-size:11px;font-weight:600;line-height:24px;border-radius:20px;
 padding:0 10px;color:#8b7467;background:#f7f6f4;}
.login-hero{padding:48px 0 26px;}
.login-illustration{height:92px;position:relative;margin-bottom:25px;}
.login-orbit{position:absolute;left:0;top:0;width:92px;height:92px;border-radius:50%;background:#fff1e9;}
.login-bowl{position:absolute;left:19px;top:43px;width:55px;height:30px;background:#ff7a3d;
 border-radius:5px 5px 34px 34px;transform:rotate(-8deg);}
.login-bowl:before{content:"";position:absolute;width:55px;height:12px;left:0;top:-5px;
 background:#fff;border:3px solid #ff7a3d;border-radius:50%;box-sizing:border-box;}
.login-bowl:after{content:"";position:absolute;width:19px;height:5px;left:18px;bottom:-3px;
 background:#ff7a3d;border-radius:3px;}
.login-chopsticks{position:absolute;left:57px;top:14px;width:4px;height:43px;background:#7e5945;
 border-radius:4px;transform:rotate(28deg);box-shadow:8px 0 0 #7e5945;}
.login-spark{position:absolute;left:106px;top:21px;color:#ff7a3d;font-size:19px;}
.login-eyebrow{font-size:11px;font-weight:700;color:#be7450;letter-spacing:1.4px;margin-bottom:10px;}
.login-heading{font-size:29px;line-height:1.4;letter-spacing:-1.3px;font-weight:800;color:#1f1f1f;}
.login-description{font-size:14px;line-height:23px;color:#777;margin-top:12px;letter-spacing:-.3px;}
.st-key-login_shell [data-testid="stForm"]{border:0;padding:0;}
.st-key-login_shell [data-testid="stTextInput"]{margin-bottom:17px;}
.st-key-login_shell label p{color:#333!important;font-size:13px!important;font-weight:600;}
.st-key-login_shell [data-baseweb="input"]{min-height:50px;border:1px solid #e4e2df;
 border-radius:12px;background:#fff!important;box-shadow:none;}
.st-key-login_shell [data-baseweb="input"]:focus-within{border-color:#ff7a3d;box-shadow:0 0 0 3px #fff1e9;}
/* Base Web paints the inner input wrapper independently of its outer border. */
.st-key-login_shell [data-baseweb="base-input"]{
 background:#fff!important;color:#1f1f1f!important;}
.st-key-login_shell input:-webkit-autofill{
 -webkit-box-shadow:0 0 0 1000px #fff inset!important;
 -webkit-text-fill-color:#1f1f1f!important;caret-color:#1f1f1f;}
.st-key-login_shell input{background:transparent!important;color:#1f1f1f!important;
 -webkit-text-fill-color:#1f1f1f!important;font-size:14px;padding:13px 14px;}
.st-key-login_shell input::placeholder{color:#aaa!important;-webkit-text-fill-color:#aaa!important;}
.st-key-login_shell [data-baseweb="input"] button{color:#777!important;background:transparent!important;}
.st-key-login_shell [data-baseweb="input"] svg{fill:#777;}
.st-key-login_shell [data-testid="stFormSubmitButton"] button{width:100%;min-height:52px;
 margin-top:5px;border:0;border-radius:12px;background:#ff7a3d!important;color:#fff!important;
 box-shadow:0 5px 12px #ff7a3d1a;}
.st-key-login_shell [data-testid="stFormSubmitButton"] button:hover{background:#ed6c30!important;}
.st-key-login_shell [data-testid="stFormSubmitButton"] button p{font-size:15px;font-weight:700;}
.st-key-login_shell [data-testid="stAlert"]{margin-top:14px;font-size:13px;}
.st-key-login_shell [data-testid="stExpander"]{border:0;margin-top:20px;color:#777;}
.st-key-login_shell [data-testid="stExpander"] summary{padding:8px 0;}
.st-key-login_shell [data-testid="stExpander"] summary p{font-size:12px;color:#777;}
.st-key-login_shell [data-testid="stExpander"] p{color:#666;font-size:12px;line-height:20px;}
.login-footer{border-top:1px solid #f0eeeb;padding-top:21px;margin-top:26px;
 font-size:11px;color:#aaa;line-height:19px;text-align:center;}
@media(max-width:350px){.st-key-login_shell{padding:24px 22px;}.login-hero{padding-top:30px;}
 .login-heading{font-size:26px;}}
"""


def submit_login():
    """Form callback: authenticate before rendering and always clear the password."""
    login_id = st.session_state.get('login_id', '').strip()
    password = st.session_state.get('login_password', '')
    st.session_state.pop('login_error', None)
    try:
        if not login_id or not password:
            st.session_state['login_error'] = '아이디와 비밀번호를 모두 입력해 주세요.'
            return
        user = auth.login(login_id, password)
        if user is None:
            st.session_state['login_error'] = '아이디 또는 비밀번호가 일치하지 않아요.'
            return
        st.session_state['user'] = {'user_id': user['user_id'], 'nickname': user['nickname']}
        st.session_state['_login_success'] = True
    except (pymysql.MySQLError, OSError):
        st.session_state['login_error'] = '로그인 서버에 연결하지 못했어요. 잠시 후 다시 시도해 주세요.'
    finally:
        # Password widget state is changed in a callback, before its next render.
        st.session_state['login_password'] = ''


def render_login():
    st.markdown(f'<style>{CSS}{LOGIN_CSS}</style>', unsafe_allow_html=True)
    with st.container(key='login_shell'):
        st.markdown('''<div class="login-brand-row"><span class="login-wordmark">머먹</span>
            <span class="login-campus">가천대학교</span></div>
            <div class="login-hero">
            <div class="login-illustration" aria-hidden="true"><div class="login-orbit"></div>
            <div class="login-chopsticks"></div><div class="login-bowl"></div><span class="login-spark">✦</span></div>
            <div class="login-eyebrow">함께하는 한 끼</div>
            <div class="login-heading">오늘의 한 끼,<br>함께 먹으면 더 맛있으니까.</div>
            <div class="login-description">가천대 근처에서 만나는 밥 친구.<br>로그인하고 오늘의 밥 모임을 찾아보세요.</div></div>''', unsafe_allow_html=True)
        with st.form('login_form', border=False):
            st.text_input('아이디 또는 가천 이메일', key='login_id', max_chars=100,
                          placeholder='아이디 또는 @gachon.ac.kr', autocomplete='username')
            st.text_input('비밀번호', type='password', key='login_password',
                          placeholder='비밀번호를 입력해 주세요', autocomplete='current-password')
            st.form_submit_button('로그인', on_click=submit_login, use_container_width=True)
        if error := st.session_state.get('login_error'):
            st.error(error)
        with st.expander('로그인이 안 되나요?'):
            st.write('가입한 아이디 또는 가천 이메일로 로그인할 수 있어요. '
                     '계정이 없다면 팀의 계정·DB 담당자에게 문의해 주세요.')
        st.markdown('<div class="login-footer">가까운 곳에서, 가볍게 한 끼.<br>머먹 · 가천대학교 밥 친구</div>', unsafe_allow_html=True)


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

# Check at the app boundary so direct URLs to any registered page also require login.
if auth.get_current_user() is None:
    render_login()
    st.stop()

if st.session_state.pop('_login_success', False):
    # Preserve a shared post link, but do not carry arbitrary query parameters.
    target_query = {'post': st.query_params['post']} if 'post' in st.query_params else None
    st.switch_page('pages/1_feed.py', query_params=target_query)

page.run()

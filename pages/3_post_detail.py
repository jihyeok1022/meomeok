"""머먹 게시물 상세 화면. 실행은 1_feed.py에서 카드를 선택한다.

게시물·댓글·좋아요·팔로우는 실제 서비스를 호출한다.
참여 기능은 3번 담당자의 서비스가 준비되었을 때 연결한다.
"""
from urllib.parse import urlsplit, urlunsplit, urlencode

import streamlit as st
import pymysql
import auth

from services import post_service, social_service, participation_service
import ui_common as ui


def join_presentation(post, user_id, state):
    """Return label, disabled, hint, action without changing any data."""
    if user_id == post['user_id']:
        return '내가 작성한 글', True, '본인이 작성한 모임이에요', None
    if state == 'ACCEPTED':
        return '참여 확정', True, '방장이 참여를 승인했어요', None
    if state == 'PENDING' and post['status'] in ('OPEN', 'CLOSED'):
        return '신청 취소', False, '승인 대기 중이에요 · 신청을 취소할 수 있어요', 'cancel'
    if state == 'REJECTED':
        return '신청 거절', True, '방장이 신청을 거절했어요', None
    if post['status'] != 'OPEN':
        return ui.STATUS_LABELS.get(post['status'], '모집 종료'), True, '신청할 수 없는 모임이에요', None
    remaining = post['capacity'] - post['current_count']
    if remaining <= 0:
        return '정원 마감', True, '모든 자리가 찼어요', None
    return '참가 신청', False, f'방장이 승인하면 참여 확정 · {remaining}자리 남음', 'apply'


@st.dialog('게시물 공유')
def share_post(post_id):
    url = st.context.url
    if url:
        parts = urlsplit(url)
        st.code(urlunsplit((parts.scheme, parts.netloc, parts.path,
                           urlencode({'post': post_id}), '')), language=None)
        st.caption('복사 버튼을 눌러 게시물 링크를 복사하세요. 로그인 후 같은 글을 볼 수 있어요.')
    else:
        st.info('앱 주소를 확인한 뒤 공유할 수 있어요.')


DETAIL_CSS = """

/* Compact native-button hit area; the visible HTML retains the existing design. */
.st-key-detail_profile_avatar{position:relative!important;isolation:isolate;gap:0!important;}
.st-key-detail_profile_avatar > :is([data-testid="stElementContainer"],[data-testid="stLayoutWrapper"]):has([data-testid="stButton"]){position:absolute!important;inset:0!important;width:100%!important;height:100%!important;z-index:2;margin:0!important;padding:0!important;}
.st-key-detail_profile_avatar [data-testid="stButton"]{width:100%!important;height:100%!important;}
.st-key-detail_profile_avatar button{display:block!important;width:100%!important;height:100%!important;min-height:0!important;min-width:0!important;padding:0!important;border:0!important;border-radius:6px!important;background:transparent!important;box-shadow:none!important;cursor:pointer!important;}
.st-key-detail_profile_avatar button p{opacity:0!important;}
.st-key-detail_profile_avatar button:focus-visible{outline:2px solid var(--orange)!important;outline-offset:1px;}
.st-key-detail_profile_avatar button:hover{background:rgba(255,122,61,.06)!important;}

/* Compact native-button hit area; the visible HTML retains the existing design. */
.st-key-detail_profile_nickname{position:relative!important;isolation:isolate;gap:0!important;}
.st-key-detail_profile_nickname > :is([data-testid="stElementContainer"],[data-testid="stLayoutWrapper"]):has([data-testid="stButton"]){position:absolute!important;inset:0!important;width:100%!important;height:100%!important;z-index:2;margin:0!important;padding:0!important;}
.st-key-detail_profile_nickname [data-testid="stButton"]{width:100%!important;height:100%!important;}
.st-key-detail_profile_nickname button{display:block!important;width:100%!important;height:100%!important;min-height:0!important;min-width:0!important;padding:0!important;border:0!important;border-radius:6px!important;background:transparent!important;box-shadow:none!important;cursor:pointer!important;}
.st-key-detail_profile_nickname button p{opacity:0!important;}
.st-key-detail_profile_nickname button:focus-visible{outline:2px solid var(--orange)!important;outline-offset:1px;}
.st-key-detail_profile_nickname button:hover{background:rgba(255,122,61,.06)!important;}

.st-key-detail_profile_avatar{width:36px!important;height:36px!important;}
.st-key-detail_profile_nickname{width:fit-content!important;min-width:0;max-width:100%;}
.st-key-detail_author_line > [data-testid="stLayoutWrapper"]:has(> .st-key-detail_author_identity){width:auto!important;min-width:0;}
.st-key-detail_author_identity{display:flex!important;gap:0!important;align-items:center!important;min-width:0;overflow:visible!important;}
.st-key-detail_author_identity > [data-testid="stLayoutWrapper"]:has(> .st-key-detail_profile_nickname){width:auto!important;min-width:0;}
.st-key-detail_author_identity .detail-author-name{font-size:14px;line-height:18px;height:18px;}
.detail-author-rating{white-space:nowrap;font-size:14px;line-height:18px;font-weight:700;color:#24201d;margin-left:3px;}
[data-testid="stMainBlockContainer"]{background:white!important;padding-bottom:136px!important;}
[data-testid="stMain"]{overflow-anchor:none;}
.st-key-detail_header{height:42px;min-height:42px;box-sizing:border-box;padding:6px 20px 10px 12px;}
.st-key-detail_header [data-testid="stHorizontalBlock"]{gap:10px;align-items:center;flex-wrap:nowrap!important;height:26px;}
.st-key-detail_header [data-testid="stColumn"]{min-width:0!important;}
.st-key-detail_header [data-testid="stColumn"]:first-child{flex:0 0 26px;}
.st-key-detail_header [data-testid="stColumn"]:nth-child(2){flex:1 1 auto;}
.st-key-detail_header [data-testid="stColumn"]:last-child{flex:0 0 22px;}
.detail-page-title{text-align:center;font-size:16px;line-height:23px;font-weight:700;color:#1f1f1f;}
.st-key-detail_header [data-testid="stButton"]{height:26px;line-height:0;}
.st-key-detail_header button{display:block;width:26px!important;height:26px!important;min-height:26px!important;
 padding:0;border:0;background-color:transparent!important;background-repeat:no-repeat;background-position:center;}
.st-key-detail_header [data-testid="stColumn"]:last-child button{width:22px!important;height:22px!important;min-height:22px!important;}
.st-key-detail_header button p{font-size:0!important;line-height:0!important;}
.st-key-detail_content{padding:8px 20px 16px;}
[data-testid="stMainBlockContainer"] .st-key-detail_author[data-testid="stHorizontalBlock"]{
 display:grid;grid-template-columns:36px minmax(0,1fr) max-content;gap:10px!important;
 align-items:center;justify-content:stretch;min-height:46px;margin-bottom:14px;padding-block:2px;overflow:visible;}
.st-key-detail_author > [data-testid="stLayoutWrapper"]:has(> .st-key-detail_author_copy){width:auto!important;min-width:0;}
[data-testid="stMainBlockContainer"] .st-key-detail_author_copy[data-testid="stVerticalBlock"]{
 display:grid;grid-template-columns:minmax(0,1fr);grid-template-rows:20px 14px;row-gap:5px!important;min-width:0;}
.st-key-detail_author_copy > [data-testid="stLayoutWrapper"]{min-width:0;}
.st-key-detail_author_line[data-testid="stHorizontalBlock"]{
 display:grid;grid-template-columns:minmax(0,max-content) max-content;grid-template-rows:20px;
 gap:7px!important;align-items:end!important;justify-content:start;min-width:0;padding-block:0;overflow:visible;}
.st-key-detail_author_line > [data-testid="stElementContainer"]:has(.detail-author-name){
 min-width:0;width:auto!important;align-self:end!important;margin:0!important;}
.st-key-detail_author_identity[data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;}
.st-key-detail_author :is(.stHtml,[data-testid="stHtml"]){margin:0!important;padding:0!important;}
.detail-author-name{height:18px;color:#24201d;font-size:14px;line-height:18px;font-weight:700;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.detail-created{height:14px;font-size:11px;line-height:14px;color:#766e68;white-space:nowrap;}
.detail-status{display:inline-block;font-size:11px;font-weight:700;line-height:16px;padding:3px 8px;border-radius:6px;
 white-space:nowrap;background:#ff7a3d;color:white;}
.detail-status.closed{background:#f3f0ed;color:#655d57;}
.st-key-detail_author_line > :is(.st-key-detail_follow,[data-testid="stLayoutWrapper"]:has(> .st-key-detail_follow)){
 width:48px!important;height:18px!important;align-self:end!important;margin:0 0 2px!important;}
.st-key-detail_follow{width:48px!important;height:18px!important;}
.st-key-detail_follow [data-testid="stElementContainer"],.st-key-detail_follow [data-testid="stButton"]{height:18px;line-height:0;}
.st-key-detail_follow button{display:flex;align-items:center;justify-content:center;box-sizing:border-box;
 width:48px!important;min-height:18px!important;height:18px!important;padding:0 4px;
 border:1px solid #e5e1dd;border-radius:5px;background:#fff!important;color:#6b625c!important;}
.st-key-detail_follow button p{margin:0;font-size:10px!important;line-height:12px!important;white-space:nowrap;color:inherit!important;}
.detail-title{font-size:21px;line-height:30px;font-weight:700;color:#1f1f1f;overflow-wrap:anywhere;margin:0 0 16px;}
.detail-body{font-size:15px;line-height:22px;color:#3a3a3a;white-space:pre-wrap;overflow-wrap:anywhere;margin-bottom:16px;}
.detail-info{display:flex;flex-direction:column;gap:12px;padding:14px 16px;border-radius:12px;background:#f7f6f4;margin-bottom:16px;}
.detail-info-row{display:flex;gap:10px;align-items:center;min-height:20px;}
.detail-info-label{flex:0 0 64px;font-size:13px;line-height:19px;color:#6b6b6b;}
.detail-info-value{font-size:14px;line-height:20px;color:#1f1f1f;overflow-wrap:anywhere;min-width:0;}
.detail-member-title{font-size:15px;font-weight:700;line-height:22px;color:#1f1f1f;margin-bottom:10px;}
.detail-member-title span{color:#ff7a3d;margin-left:6px;}
.detail-members{display:flex;gap:14px;align-items:flex-start;overflow-x:auto;padding-bottom:0;margin-bottom:16px;scrollbar-width:thin;}
.detail-member{display:flex;flex:0 0 auto;flex-direction:column;align-items:center;gap:4px;min-width:44px;max-width:70px;}
.detail-member-label{max-width:70px;font-size:11px;line-height:16px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#6b6b6b;}
.detail-member.vacant .detail-member-label{color:#a0a0a0;}
.detail-divider{height:1px;background:#ececec;margin:0 0 16px;}
.detail-reactions{display:flex;align-items:center;gap:16px;color:#6b6b6b;font-size:13px;line-height:19px;margin-bottom:16px;}
.detail-reaction{display:flex;align-items:center;gap:4px;}
.detail-comment{display:flex;gap:8px;align-items:flex-start;margin-bottom:16px;}
.detail-comment-copy{min-width:0;flex:1;}
.detail-comment-name{font-size:12px;font-weight:700;line-height:17px;color:#1f1f1f;}
.detail-comment-body{font-size:13px;line-height:19px;color:#3a3a3a;white-space:pre-wrap;overflow-wrap:anywhere;margin-top:1px;}
.detail-demo-note{font-size:11px;line-height:16px;color:#a0a0a0;margin:8px 0 16px;}
.st-key-detail_content img{display:block;flex-shrink:0;max-width:none;}
.st-key-detail_content [data-testid="stMarkdownContainer"] p{color:#1f1f1f;}
.st-key-detail_content [data-testid="stWidgetLabel"] p{font-size:13px;color:#1f1f1f!important;}
.st-key-detail_content [data-baseweb="textarea"]{background:white!important;border:1px solid #dcdcdc!important;border-radius:10px;}
.st-key-detail_content textarea{background:white!important;color:#1f1f1f!important;-webkit-text-fill-color:#1f1f1f!important;box-sizing:border-box;font-size:13px;line-height:20px;padding:12px 14px!important;resize:none!important;}
.st-key-detail_content textarea::placeholder{-webkit-text-fill-color:#a0a0a0!important;}
.st-key-detail_content [data-testid="stForm"] [data-testid="stTextArea"] [data-testid="InputInstructions"]{display:none!important;}
.st-key-detail_content [data-testid="stFormSubmitButton"] button{background:#fff1e9!important;color:#ff7a3d!important;border:0;border-radius:8px;margin-top:8px;}
.st-key-detail_content [data-testid="stFormSubmitButton"] button p{font-size:13px!important;color:#ff7a3d!important;}
.st-key-detail_actions{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:min(390px,100vw)!important;
 height:110px;box-sizing:border-box;background:white;border-top:1px solid #ececec;padding:10px 16px 24px;z-index:30;}
.detail-join-hint{text-align:center;font-size:11px;line-height:16px;color:#a0a0a0;margin-bottom:8px;white-space:nowrap;}
.st-key-detail_actions [data-testid="stHorizontalBlock"]{gap:10px;align-items:center;flex-wrap:nowrap!important;height:51px;}
.st-key-detail_actions [data-testid="stColumn"]{min-width:0!important;}
.st-key-detail_actions [data-testid="stColumn"]:first-child{flex:0 0 48px;}
.st-key-detail_actions [data-testid="stColumn"]:last-child{flex:1 1 auto;}
.st-key-detail_actions [data-testid="stElementContainer"],.st-key-detail_actions [data-testid="stButton"]{width:100%!important;line-height:0;}
.st-key-detail_actions button{display:flex;align-items:center;justify-content:center;width:100%!important;height:51px!important;min-height:51px!important;
 border:0;border-radius:12px;background-color:#ff7a3d!important;color:white!important;padding:14px!important;}
.st-key-detail_actions button p{font-size:16px!important;line-height:23px!important;font-weight:700;}
.st-key-detail_actions [data-testid="stColumn"]:first-child button{height:48px!important;min-height:48px!important;
 padding:12px!important;border:1px solid #ddd;background-color:white!important;background-repeat:no-repeat;background-position:center;}
.st-key-detail_actions [data-testid="stColumn"]:first-child button p{font-size:0!important;line-height:0!important;}
.st-key-detail_actions button:disabled{background:#ececec!important;color:#888!important;opacity:1;}
.st-key-detail_actions button:disabled p{color:#888!important;}
@media(max-width:350px){.detail-created{font-size:10px;}.detail-info-label{flex-basis:56px;}
 .detail-info-row{gap:8px;}.detail-info-value{font-size:12px;}.detail-join-hint{font-size:10px;}}
"""


def go_back():
    from_search = st.query_params.get('from') == 'search'
    st.query_params.pop('post', None)
    st.switch_page('pages/7_search.py' if from_search else 'pages/1_feed.py')


def perform_action(function, *args):
    """Callbacks finish before the page re-queries the latest counts and states."""
    st.session_state.pop('_detail_action_error', None)
    try:
        function(*args)
    except (ValueError, LookupError, PermissionError) as exc:
        st.session_state['_detail_action_error'] = str(exc)
    except (pymysql.MySQLError, OSError):
        st.session_state['_detail_action_error'] = '변경 내용을 저장하지 못했어요. 연결을 확인하고 다시 시도해 주세요.'


def open_author_profile(author_id, post_id):
    params = {'user': int(author_id), 'back_post': int(post_id)}
    if st.query_params.get('from') == 'search':
        params['back_from'] = 'search'
    st.switch_page('pages/4_profile.py', query_params=params)


def render_detail_page():
    user = auth.require_login()
    post_id = st.session_state.get('selected_post_id')
    new_view = st.session_state.pop('detail_scroll_to_top', False) or st.session_state.get('_detail_last_post') != post_id
    st.session_state['_detail_last_post'] = post_id
    load_error = None
    try:
        post = post_service.get_post(post_id, viewer_id=user['user_id'])
    except ValueError:
        post = None
    except (pymysql.MySQLError, OSError):
        post = None
        load_error = '게시물을 불러오지 못했어요. DB 연결을 확인한 후 다시 시도해 주세요.'
    liked = bool(post and post['is_liked'])
    css = ui.CSS + DETAIL_CSS
    css += f'.st-key-detail_header [data-testid="stColumn"]:first-child button{{background-image:url("{ui.asset("write_back")}");}}'
    css += f'.st-key-detail_header [data-testid="stColumn"]:last-child button{{background-image:url("{ui.asset("detail_share")}");}}'
    like_icon = ui.asset('detail_like')
    css += f'.st-key-detail_actions [data-testid="stColumn"]:first-child button{{background-image:url("{like_icon}")!important;}}'
    if liked:
        css += '.st-key-detail_actions [data-testid="stColumn"]:first-child button{background-color:#ffe5d5!important;border-color:#eea884;}'
    if post and post['is_following_author']:
        css += '.st-key-detail_follow button{background:#fff0e6!important;border-color:#f1cfbb;color:#a94d27!important;}'
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    with st.container(key='detail_header'):
        back, title, share = st.columns([26, 1, 22])
        with back:
            if st.button('뒤로', key='detail_back'):
                go_back()
        with title:
            st.markdown('<div class="detail-page-title">모집 글</div>', unsafe_allow_html=True)
        with share:
            if st.button('공유', key='detail_share', disabled=post is None):
                share_post(post_id)
    if load_error:
        st.error(load_error)
        if st.button('다시 불러오기', key='detail_retry'):
            st.rerun()
        return
    if post is None:
        st.warning('게시물을 찾을 수 없어요. 뒤로 돌아가 다른 글을 선택해 주세요.')
        return
    if st.session_state.pop('_post_created', False):
        st.toast('모집 글을 등록했어요.')
    if action_error := st.session_state.pop('_detail_action_error', None):
        st.error(action_error)
    followed = post['is_following_author']
    members = None
    state = None
    participation_ready = all(callable(getattr(participation_service, name, None)) for name in
                              ('get_application_status', 'apply_to_post', 'cancel_application'))
    try:
        if callable(getattr(participation_service, 'get_members', None)):
            members = participation_service.get_members(post_id)
        if participation_ready:
            state = participation_service.get_application_status(post_id, user['user_id'])
    except (pymysql.MySQLError, OSError, ValueError, LookupError, PermissionError):
        participation_ready = False
        st.warning('참여 정보를 확인하지 못했어요. 잠시 후 다시 시도해 주세요.')
    with st.container(key='detail_content'):
        with st.container(key='detail_author', horizontal=True, vertical_alignment='center'):
            rating = '평가 없음' if post['rating'] is None else f"평점 {post['rating']:.1f}"
            closed = '' if post['status'] == 'OPEN' else ' closed'
            with st.container(key='detail_profile_avatar', width=36, gap=None):
                st.html(ui.user_avatar(post["user_id"], 36), width=36)
                if st.button(f'{post["nickname"]} 프로필 사진 보기', key='detail_author_avatar_open'):
                    open_author_profile(post['user_id'], post_id)
            with st.container(key='detail_author_copy', gap=None):
                with st.container(key='detail_author_line', horizontal=True,
                                  vertical_alignment='bottom'):
                    with st.container(key='detail_author_identity', horizontal=True,
                                      vertical_alignment='center', width='content', gap=None):
                        with st.container(key='detail_profile_nickname', width='content', gap=None):
                            st.html(f'<div class="detail-author-name">{ui.e(post["nickname"])}</div>', width='content')
                            if st.button(f'{post["nickname"]} 프로필 보기', key='detail_author_name_open'):
                                open_author_profile(post['user_id'], post_id)
                        st.html(f'<span class="detail-author-rating">· {ui.e(rating)}</span>', width='content')
                    if user['user_id'] != post['user_id']:
                        with st.container(key='detail_follow', width=48):
                            st.button('팔로잉' if followed else '팔로우', key='detail_follow_button',
                                      on_click=perform_action,
                                      args=(social_service.set_follow, user['user_id'], post['user_id'], not followed))
                st.html(f'<div class="detail-created">{post["created_at"]:%m월 %d일 %H:%M} 작성</div>')
            st.html(f'<span class="detail-status{closed}">{ui.STATUS_LABELS[post["status"]]}</span>',
                    width='content')
        st.markdown(f'<div class="detail-title">{ui.e(post["title"])}</div>'
                    f'<div class="detail-body">{ui.e(post["body"])}</div>', unsafe_allow_html=True)
        info = [('detail_clock', '식사 시간', post['meal_time'].strftime('%m월 %d일 %H:%M')),
                ('detail_pin', '지역', post['region']), ('detail_bowl', '음식 종류', post['food_category']),
                ('detail_users', '정원', f'{post["current_count"]} / {post["capacity"]}명 (작성자 포함)')]
        st.markdown('<div class="detail-info">' + ''.join(
            f'<div class="detail-info-row">{ui.icon(icon)}<span class="detail-info-label">{label}</span>'
            f'<span class="detail-info-value">{ui.e(value)}</span></div>' for icon, label, value in info) + '</div>', unsafe_allow_html=True)
        slots = []
        for member in members or []:
            name = member['nickname'] + ('(방장)' if member['is_host'] else '')
            slots.append(f'<div class="detail-member">{ui.user_avatar(member["user_id"], 44)}'
                         f'<span class="detail-member-label">{ui.e(name)}</span></div>')
        for _ in range(max(0, post['capacity'] - len(members)) if members is not None else 0):
            slots.append(f'<div class="detail-member vacant">{ui.icon("detail_empty")}<span class="detail-member-label">빈자리</span></div>')
        if members is None:
            slots.append('<div class="detail-demo-note">멤버 목록은 참여 서비스 연결 후 표시돼요.</div>')
        st.markdown(f'<div class="detail-member-title">참여 멤버<span>{post["current_count"]}/{post["capacity"]}</span></div>'
                    '<div class="detail-members">' + ''.join(slots) + '</div><div class="detail-divider"></div>'
                    f'<div class="detail-reactions"><span class="detail-reaction">{ui.icon("detail_heart")}좋아요 {post["like_count"]}</span>'
                    f'<span class="detail-reaction">{ui.icon("detail_comment")}댓글 {post["comment_count"]}</span></div>', unsafe_allow_html=True)
        comments_failed = False
        try:
            comments = social_service.list_comments(post_id)
        except (pymysql.MySQLError, OSError):
            comments, comments_failed = [], True
            st.error('댓글을 불러오지 못했어요. 잠시 후 다시 시도해 주세요.')
        for comment in comments:
            st.markdown(f'<div class="detail-comment">{ui.user_avatar(comment["user_id"], 28)}<div class="detail-comment-copy">'
                        f'<div class="detail-comment-name">{ui.e(comment["nickname"])}</div>'
                        f'<div class="detail-comment-body">{ui.e(comment["content"])}</div></div></div>', unsafe_allow_html=True)
        if not comments and not comments_failed:
            st.caption('아직 댓글이 없어요. 첫 댓글을 남겨보세요.')
        if st.session_state.pop(f'_clear_comment_{post_id}', False):
            st.session_state[f'detail_comment_input_{post_id}'] = ''
        with st.form(f'detail_comment_form_{post_id}', clear_on_submit=False, border=False):
            content = st.text_area('댓글 작성', placeholder='함께 먹을 사람에게 댓글을 남겨보세요', height=80,
                                   key=f'detail_comment_input_{post_id}')
            if st.form_submit_button('댓글 등록'):
                try:
                    social_service.create_comment(post_id, user['user_id'], content)
                except (ValueError, LookupError, PermissionError) as exc:
                    st.error(str(exc))
                except (pymysql.MySQLError, OSError):
                    st.error('댓글을 등록하지 못했어요. 입력한 내용은 유지돼요. 다시 시도해 주세요.')
                else:
                    st.session_state[f'_clear_comment_{post_id}'] = True
                    st.rerun()

    if new_view:
        # Only trusted, fixed code: never insert titles, comments or URL values here.
        st.html('''<script>
        (() => {
        const resetDetailScroll = () => {
            const main = document.querySelector('[data-testid="stMain"]');
            if (main) main.scrollTo({top: 0, behavior: 'instant'});
        };
        requestAnimationFrame(resetDetailScroll);
        setTimeout(resetDetailScroll, 150);
        setTimeout(resetDetailScroll, 400);
        })();
        </script>''', unsafe_allow_javascript=True)
    label, disabled, hint, action = join_presentation(post, user['user_id'], state)
    if not participation_ready and user['user_id'] != post['user_id'] and not disabled:
        label, disabled, hint, action = '참여 신청 준비 중', True, '참여 서비스가 연결되면 신청할 수 있어요', None
    with st.container(key='detail_actions'):
        st.markdown(f'<div class="detail-join-hint">{ui.e(hint)}</div>', unsafe_allow_html=True)
        like_column, apply_column = st.columns([48, 300])
        with like_column:
            st.button('좋아요 취소' if liked else '좋아요', key='detail_like_button',
                      on_click=perform_action,
                      args=(social_service.set_like, post_id, user['user_id'], not liked))
        with apply_column:
            if st.button(label, key='detail_apply', disabled=disabled):
                try:
                    if action == 'cancel':
                        participation_service.cancel_application(post_id, user['user_id'])
                    else:
                        participation_service.apply_to_post(post_id, user['user_id'])
                except (ValueError, LookupError, PermissionError) as exc:
                    st.toast(str(exc))
                except (pymysql.MySQLError, OSError):
                    st.toast('신청을 처리하지 못했어요. 잠시 후 다시 시도해 주세요.')
                else:
                    st.rerun()


def main():
    st.set_page_config(page_title='머먹 · 모집 글 상세', page_icon='🍚', layout='centered')
    if 'post' in st.query_params:
        try:
            st.session_state['selected_post_id'] = int(st.query_params['post'])
        except (ValueError, TypeError):
            st.session_state['selected_post_id'] = None
    render_detail_page()


if __name__ == '__main__':
    main()

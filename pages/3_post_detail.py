"""머먹 게시물 상세 화면. 실행은 1_feed.py에서 카드를 선택한다.

DB 연결 전 UI 체험용이다. 모든 변경은 demo_data의 브라우저 세션에만 남는다.
실제 서비스 연결 시 조회·댓글·좋아요·팔로우는 2번 담당자,
신청·취소는 3번 담당자 함수를 호출하고 권한을 백엔드에서 재검사한다.
"""
from urllib.parse import urlsplit, urlunsplit, urlencode

import streamlit as st

import demo_data as data
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
        st.caption('복사 버튼을 눌러 링크를 복사하세요. 예시 게시물 링크입니다.')
    else:
        st.info('앱 주소를 확인한 뒤 공유할 수 있어요.')


DETAIL_CSS = """
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
.st-key-detail_author{position:relative;height:40px;min-height:40px;margin-bottom:16px;}
.detail-author{display:flex;gap:10px;align-items:center;height:40px;color:#1f1f1f;}
.detail-author-copy{flex:1;min-width:0;padding-right:64px;}
.detail-author-name{font-size:14px;line-height:20px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.detail-created{font-size:12px;line-height:17px;color:#a0a0a0;white-space:nowrap;}
.detail-status{font-size:12px;font-weight:700;line-height:17px;padding:4px 10px;border-radius:6px;
 white-space:nowrap;background:#ff7a3d;color:white;}
.detail-status.closed{background:#bdbdbd;}
.st-key-detail_follow{position:absolute;right:70px;top:0;width:60px!important;height:24px;}
.st-key-detail_follow [data-testid="stButton"]{height:24px;line-height:0;}
.st-key-detail_follow button{display:block;width:60px!important;min-height:24px!important;height:24px!important;
 padding:3px 6px;border:0;border-radius:6px;background:#fff1e9!important;color:#ff7a3d!important;}
.st-key-detail_follow button p{font-size:11px!important;line-height:16px!important;white-space:nowrap;color:#ff7a3d!important;}
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
.st-key-detail_content textarea{background:white!important;color:#1f1f1f!important;-webkit-text-fill-color:#1f1f1f!important;font-size:13px;padding:12px;}
.st-key-detail_content textarea::placeholder{-webkit-text-fill-color:#a0a0a0!important;}
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
@media(max-width:350px){.detail-author-copy{padding-right:42px;}.st-key-detail_follow{width:48px!important;right:64px;}
 .st-key-detail_follow button{width:48px!important;}.detail-created{font-size:10px;}.detail-info-label{flex-basis:56px;}
 .detail-info-row{gap:8px;}.detail-info-value{font-size:12px;}.detail-join-hint{font-size:10px;}}
"""


def go_back():
    st.query_params.pop('post', None)
    st.switch_page('pages/1_feed.py')


def render_detail_page():
    user = data.current_user()
    post_id = st.session_state.get('selected_post_id')
    new_view = st.session_state.pop('detail_scroll_to_top', False) or st.session_state.get('_detail_last_post') != post_id
    st.session_state['_detail_last_post'] = post_id
    post = data.get_post(post_id)
    liked = (user['user_id'], post_id) in data.get_store()['likes']
    css = ui.CSS + DETAIL_CSS
    css += f'.st-key-detail_header [data-testid="stColumn"]:first-child button{{background-image:url("{ui.asset("write_back")}");}}'
    css += f'.st-key-detail_header [data-testid="stColumn"]:last-child button{{background-image:url("{ui.asset("detail_share")}");}}'
    css += f'.st-key-detail_actions [data-testid="stColumn"]:first-child button{{background-image:url("{ui.asset("detail_like")}")!important;}}'
    if liked:
        css += '.st-key-detail_actions [data-testid="stColumn"]:first-child button{background-color:#fff1e9!important;border-color:#ff7a3d;}'
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
    if post is None:
        st.warning('게시물을 찾을 수 없어요. 뒤로 돌아가 다른 글을 선택해 주세요.')
        return
    followed = (user['user_id'], post['user_id']) in data.get_store()['follows']
    with st.container(key='detail_content'):
        with st.container(key='detail_author'):
            rating = '평가 없음' if post['rating'] is None else f"평점 {post['rating']:.1f}"
            closed = '' if post['status'] == 'OPEN' else ' closed'
            st.markdown('<div class="detail-author">' + ui.icon('detail_author') +
                        f'<div class="detail-author-copy"><div class="detail-author-name">{ui.e(post["nickname"])} · {ui.e(rating)}</div>'
                        f'<div class="detail-created">{post["created_at"]:%m월 %d일 %H:%M} 작성</div></div>'
                        f'<span class="detail-status{closed}">{ui.STATUS_LABELS[post["status"]]}</span></div>', unsafe_allow_html=True)
            if user['user_id'] != post['user_id']:
                with st.container(key='detail_follow'):
                    st.button('팔로잉' if followed else '팔로우', key='detail_follow_button',
                              on_click=data.toggle_follow, args=(user['user_id'], post['user_id']))
        st.markdown(f'<div class="detail-title">{ui.e(post["title"])}</div>'
                    f'<div class="detail-body">{ui.e(post["body"])}</div>', unsafe_allow_html=True)
        info = [('detail_clock', '식사 시간', post['meal_time'].strftime('%m월 %d일 %H:%M')),
                ('detail_pin', '지역', post['region']), ('detail_bowl', '음식 종류', post['food_category']),
                ('detail_users', '정원', f'{post["current_count"]} / {post["capacity"]}명 (작성자 포함)')]
        st.markdown('<div class="detail-info">' + ''.join(
            f'<div class="detail-info-row">{ui.icon(icon)}<span class="detail-info-label">{label}</span>'
            f'<span class="detail-info-value">{ui.e(value)}</span></div>' for icon, label, value in info) + '</div>', unsafe_allow_html=True)
        members = data.get_members(post_id)
        slots = []
        for member in members:
            name = member['nickname'] + ('(방장)' if member['is_host'] else '')
            slots.append(f'<div class="detail-member">{ui.icon("detail_host" if member["is_host"] else "detail_guest")}'
                         f'<span class="detail-member-label">{ui.e(name)}</span></div>')
        for _ in range(max(0, post['capacity'] - len(members))):
            slots.append(f'<div class="detail-member vacant">{ui.icon("detail_empty")}<span class="detail-member-label">빈자리</span></div>')
        st.markdown(f'<div class="detail-member-title">참여 멤버<span>{post["current_count"]}/{post["capacity"]}</span></div>'
                    '<div class="detail-members">' + ''.join(slots) + '</div><div class="detail-divider"></div>'
                    f'<div class="detail-reactions"><span class="detail-reaction">{ui.icon("detail_heart")}좋아요 {post["like_count"]}</span>'
                    f'<span class="detail-reaction">{ui.icon("detail_comment")}댓글 {post["comment_count"]}</span></div>', unsafe_allow_html=True)
        for comment in data.get_comments(post_id):
            st.markdown(f'<div class="detail-comment">{ui.icon("detail_comment_avatar")}<div class="detail-comment-copy">'
                        f'<div class="detail-comment-name">{ui.e(comment["nickname"])}</div>'
                        f'<div class="detail-comment-body">{ui.e(comment["content"])}</div></div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="detail-demo-note">예시 화면 · {ui.e(user["nickname"])}으로 체험 중<br>'
                    '댓글·좋아요·팔로우·신청은 현재 브라우저에서만 반영돼요.</div>', unsafe_allow_html=True)
        with st.form(f'detail_comment_form_{post_id}', clear_on_submit=True, border=False):
            content = st.text_area('댓글 작성', placeholder='함께 먹을 사람에게 댓글을 남겨보세요', height=80,
                                   key=f'detail_comment_input_{post_id}')
            if st.form_submit_button('댓글 등록'):
                try:
                    data.add_comment(post_id, user, content)
                except ValueError as exc:
                    st.error(str(exc))
                else:
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
    label, disabled, hint, action = join_presentation(post, user['user_id'], data.application_state(post_id, user['user_id']))
    with st.container(key='detail_actions'):
        st.markdown(f'<div class="detail-join-hint">{ui.e(hint)} · 체험</div>', unsafe_allow_html=True)
        like_column, apply_column = st.columns([48, 300])
        with like_column:
            st.button('좋아요 취소' if liked else '좋아요', key='detail_like_button',
                      on_click=data.toggle_like, args=(post_id, user['user_id']))
        with apply_column:
            if st.button(label, key='detail_apply', disabled=disabled):
                try:
                    if action == 'cancel':
                        data.cancel_application(post_id, user['user_id'])
                    else:
                        data.apply_to_post(post_id, user['user_id'])
                except ValueError as exc:
                    st.toast(str(exc))
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

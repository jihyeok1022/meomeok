"""Feed page. Run the application with: streamlit run app.py."""

from datetime import datetime
from pathlib import Path

import streamlit as st
import pymysql
import auth
from services import post_service

from ui_common import CSS, FOOD_CATEGORIES, REGIONS, STATUS_LABELS, FEED_STATUSES, asset, icon, e


# DB CHECK 제약조건. '전체'는 검색 UI에서만 사용하는 값이다.
# 홈 피드는 모집 진행 중인 글과 마감된 글만 표시한다.





PAGE_SIZE = 20


def load_posts(**filters):
    """Request one extra row to decide whether there is another page."""
    return post_service.list_posts(**filters, limit=PAGE_SIZE + 1,
                                   offset=st.session_state.get('db_feed_page', 0) * PAGE_SIZE)


def time_label(value):
    days = (value.date() - datetime.now().date()).days
    day = {0: '오늘', 1: '내일'}.get(days, value.strftime('%m/%d'))
    return f'{day} {value:%H:%M}'




def page_path(filename):
    root = Path(__file__).resolve().parent
    if root.name == 'pages':
        root = root.parent
    target = root / 'pages' / filename
    return target if target.is_file() and target.read_text(encoding='utf-8-sig').strip() else None


@st.dialog('안내')
def notice(message):
    st.write(message)


def navigate(filename):
    if page_path(filename):
        st.switch_page(f'pages/{filename}')
    else:
        notice('해당 화면은 아직 구현되지 않았어요.')


def open_detail(post_id):
    st.session_state['selected_post_id'] = post_id
    st.session_state['detail_scroll_to_top'] = True
    st.switch_page('pages/3_post_detail.py', query_params={'post': post_id})


def sign_out():
    import auth
    auth.logout()
    # Clear per-user drafts and temporary interactions before another account logs in.
    st.session_state.clear()
    st.query_params.clear()
    st.switch_page('pages/1_feed.py')


def main():
    st.set_page_config(page_title='머먹 · 모집 글', page_icon='🍚', layout='centered')
    user = auth.require_login()
    if 'post' in st.query_params:
        st.switch_page('pages/3_post_detail.py',
                       query_params={'post': st.query_params['post']})
    st.markdown(f'<style>{CSS}</style>', unsafe_allow_html=True)
    nickname = f"{e(user['nickname'])}님, " if user.get('nickname') else ''
    st.session_state.setdefault('db_feed_show_search', False)
    st.session_state.setdefault('db_feed_sort', '최신순')
    st.markdown('<div class="status-bar" aria-hidden="true"><strong>9:41</strong><span>LTE 100%</span></div>', unsafe_allow_html=True)
    with st.container(key='header'):
        brand, search, bell = st.columns([254, 32, 32])
        with brand:
            st.markdown('<div class="brand">머먹</div>', unsafe_allow_html=True)
        with search:
            if st.button('검색', key='search_button'):
                st.session_state.db_feed_show_search = not st.session_state.db_feed_show_search
        with bell:
            if st.button('알림', key='bell_button'):
                notice('알림 기능은 아직 연결되지 않았어요.')
    st.markdown(f'<div class="intro-block"><div class="intro">{nickname}오늘 누구랑 밥 먹을까요?</div>'
                '<div class="sub">가천대 근처에서 함께할 밥 모임을 찾아보세요</div></div>', unsafe_allow_html=True)
    with st.container(key='categories'):
        category = st.pills('음식 종류', ['전체', *FOOD_CATEGORIES], default='전체',
                            key='db_feed_category', label_visibility='collapsed') or '전체'
    if st.session_state.db_feed_show_search:
        with st.container(key='tools'):
            st.text_input('제목·본문 검색', key='db_feed_query', placeholder='제목이나 본문으로 찾아보세요')
            st.selectbox('지역', ['전체', *REGIONS], key='db_feed_region')
            st.selectbox('모집 상태', ['전체', *FEED_STATUSES],
                                  format_func=lambda value: STATUS_LABELS.get(value, value), key='db_feed_status')
            # 팔로우 관계는 Follow 조회가 필요하다. 임의 사용자 ID로 필터링하지 않는다.
    with st.container(key='section'):
        heading, sorting = st.columns([240, 110])
        with heading:
            st.markdown('<div class="section-title">밥 모임 둘러보기</div>', unsafe_allow_html=True)
        with sorting:
            if st.button(st.session_state.db_feed_sort, key='sort'):
                st.session_state.db_feed_sort = '식사 시간순' if st.session_state.db_feed_sort == '최신순' else '최신순'
                st.rerun()
    sort = st.session_state.db_feed_sort
    query = st.session_state.get('db_feed_query', '').strip()
    region = st.session_state.get('db_feed_region', '전체')
    status = st.session_state.get('db_feed_status', '전체')
    filters = dict(region=None if region == '전체' else region,
                   food_category=None if category == '전체' else category,
                   status=None if status == '전체' else status, keyword=query,
                   sort='latest' if sort == '최신순' else 'meal_time')
    fingerprint = tuple(filters.items())
    if st.session_state.get('_feed_filters') != fingerprint:
        st.session_state['db_feed_page'] = 0
        st.session_state['_feed_filters'] = fingerprint
    failed = False
    try:
        posts = [p for p in load_posts(**filters) if p['status'] in FEED_STATUSES]
    except (pymysql.MySQLError, OSError):
        posts, failed = [], True
        st.error('모임을 불러오지 못했어요. DB 연결을 확인한 후 다시 시도해 주세요.')
        if st.button('다시 불러오기', key='feed_retry'):
            st.rerun()
    except ValueError as exc:
        posts, failed = [], True
        st.error(str(exc))
    has_next = len(posts) > PAGE_SIZE
    filtered = posts[:PAGE_SIZE]
    if not filtered and not failed:
        st.markdown('<div class="empty">조건에 맞는 모임이 없어요.<br>검색 조건을 바꿔보세요.</div>', unsafe_allow_html=True)
    styles = {'OPEN': '', 'CLOSED': 'closed', 'COMPLETED': 'completed', 'CANCELED': 'canceled'}
    for post in filtered:
        rating = '평가 없음' if post['rating'] is None else f"평점 {post['rating']:.1f}"
        card = (
            '<article class="meetup-card"><div class="card-top"><div class="tags">'
            f'<span class="badge {styles[post["status"]]}">{STATUS_LABELS[post["status"]]}</span>'
            f'<span class="food">{e(post["food_category"])}</span></div>'
            f'<span class="time">{icon("clock")}{e(time_label(post["meal_time"]))}</span></div>'
            f'<div class="card-title">{e(post["title"])}</div>'
            f'<div class="region">{icon("pin")}{e(post["region"])}</div><div class="card-rule"></div><div class="card-bottom">'
            f'<div class="host">{icon("avatar")}<span>{e(post["nickname"])} · {e(rating)}</span></div>'
            f'<div class="stats"><span class="stat members" title="작성자 포함">{icon("users")}{post["current_count"]}/{post["capacity"]}명</span>'
            f'<span class="stat">{icon("heart")}{post["like_count"]}</span>'
            f'<span class="stat">{icon("comment")}{post["comment_count"]}</span></div></div></article>'
        )
        with st.container(key=f'card_{post["post_id"]}'):
            st.markdown(card, unsafe_allow_html=True)
            if st.button(f'{post["title"]} 상세 보기', key=f'db_open_{post["post_id"]}'):
                open_detail(post['post_id'])
    if not failed and (st.session_state.get('db_feed_page', 0) or has_next):
        with st.container(key='feed_pagination'):
            previous, counter, following = st.columns([1, 1, 1])
            page_number = st.session_state.get('db_feed_page', 0)
            with previous:
                if st.button('이전', key='feed_previous', disabled=page_number == 0):
                    st.session_state['db_feed_page'] = page_number - 1
                    st.rerun()
            with counter:
                st.caption(f'{page_number + 1}페이지')
            with following:
                if st.button('다음', key='feed_next', disabled=not has_next):
                    st.session_state['db_feed_page'] = page_number + 1
                    st.rerun()
    with st.container(key='feed_account'):
        if st.button('로그아웃', key='feed_logout'):
            sign_out()
    with st.container(key='fab'):
        if st.button('글쓰기', key='db_write_post'):
            navigate('2_write_post.py')
    with st.container(key='bottom_nav'):
        for column, label, filename, key in zip(st.columns(4), ['모집 글', '내 신청', '톡방', '내 프로필'],
                                           [None, '5_participation.py', '6_chat.py', '4_profile.py'],
                                           ['nav_home', 'nav_apply', 'nav_chat', 'nav_profile']):
            with column, st.container(key=key):
                if st.button(label, key=f'db_nav_{label}', use_container_width=True):
                    if filename:
                        navigate(filename)
                    else:
                        st.rerun()


if __name__ == '__main__':
    main()

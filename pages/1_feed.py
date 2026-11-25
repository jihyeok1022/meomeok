"""Feed page. Run the application with: streamlit run app.py."""

from datetime import datetime
from pathlib import Path

import streamlit as st
import pymysql
import auth
from services import post_service

from ui_common import CSS, FOOD_CATEGORIES, REGIONS, STATUS_LABELS, FEED_STATUSES, asset, icon, e, user_avatar


# DB CHECK 제약조건. '전체'는 검색 UI에서만 사용하는 값이다.
# 홈 피드는 모집 진행 중인 글과 마감된 글만 표시한다.





PAGE_SIZE = 20


def load_posts(page_number, **filters):
    """Request one extra row to decide whether there is another page."""
    return post_service.list_posts(**filters, limit=PAGE_SIZE + 1,
                                   offset=page_number * PAGE_SIZE)


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


def open_detail(post_id, *, from_search=False):
    st.session_state['selected_post_id'] = post_id
    st.session_state['detail_scroll_to_top'] = True
    params = {'post': post_id}
    if from_search:
        params['from'] = 'search'
    st.switch_page('pages/3_post_detail.py', query_params=params)


def render_home_header(user):
    nickname = f"{e(user['nickname'])}님, " if user.get('nickname') else ''
    st.markdown('<div class="status-bar" aria-hidden="true"><strong>9:41</strong><span>LTE 100%</span></div>', unsafe_allow_html=True)
    with st.container(key='header'):
        brand, search, bell = st.columns([254, 32, 32])
        with brand:
            st.markdown('<div class="brand">머먹</div>', unsafe_allow_html=True)
        with search:
            if st.button('검색', key='search_button'):
                st.switch_page('pages/7_search.py')
        with bell:
            if st.button('알림', key='bell_button'):
                notice('알림 기능은 아직 연결되지 않았어요.')
    st.markdown(f'<div class="intro-block"><div class="intro">{nickname}오늘 누구랑 밥 먹을까요?</div>'
                '<div class="sub">가천대 근처에서 함께할 밥 모임을 찾아보세요</div></div>', unsafe_allow_html=True)


def main(*, search_mode=False):
    page_title = '모집 글 검색' if search_mode else '모집 글'
    st.set_page_config(page_title=f'머먹 · {page_title}', page_icon='🍚', layout='centered')
    user = auth.require_login()
    if 'post' in st.query_params and not search_mode:
        st.switch_page('pages/3_post_detail.py',
                       query_params={'post': st.query_params['post']})
    st.markdown(f'<style>{CSS}</style>', unsafe_allow_html=True)
    scope = 'search' if search_mode else 'feed'
    sort_key = f'db_{scope}_sort'
    page_key = f'db_{scope}_page'
    fingerprint_key = f'_{scope}_filters'
    category_key = f'db_{scope}_category'
    st.session_state.setdefault(sort_key, '최신순')

    query, region, status = '', '전체', '전체'
    if search_mode:
        search_values = st.session_state.get('db_search_values', {})
        regions = ['전체', *REGIONS]
        statuses = ['전체', *FEED_STATUSES]
        with st.container(key='search_controls'):
            with st.container(key='search_back_slot', width=34):
                if st.button('뒤로', key='search_back', icon=':material/arrow_back:'):
                    st.switch_page('pages/1_feed.py')
            with st.form('search_form', border=False):
                with st.container(key='search_bar', horizontal=True, gap=None,
                                  vertical_alignment='center'):
                    query = st.text_input('제목·본문 검색', value=search_values.get('query', ''),
                                          key='db_search_query', placeholder='제목이나 본문으로 검색',
                                          label_visibility='collapsed')
                    with st.container(key='search_submit_slot', width=40):
                        submitted = st.form_submit_button('검색', key='search_submit',
                                                          icon=':material/search:')
                region_col, status_col = st.columns(2)
                with region_col:
                    region = st.selectbox('지역', regions, index=regions.index(search_values.get('region', '전체')),
                                          key='db_search_region')
                with status_col:
                    status = st.selectbox('모집 상태', statuses, index=statuses.index(search_values.get('status', '전체')),
                                          format_func=lambda value: STATUS_LABELS.get(value, value), key='db_search_status')
                with st.container(key='categories'):
                    category = st.pills('음식 종류', ['전체', *FOOD_CATEGORIES],
                                        default=search_values.get('category', '전체'),
                                        key=category_key, label_visibility='collapsed') or '전체'
        if submitted:
            search_values = dict(query=query, region=region, status=status, category=category)
            st.session_state['db_search_values'] = search_values
        if not search_values:
            return
        query, region, status, category = (search_values[key] for key in ('query', 'region', 'status', 'category'))
    else:
        render_home_header(user)
        with st.container(key='categories'):
            category = st.pills('음식 종류', ['전체', *FOOD_CATEGORIES], default='전체',
                                key=category_key, label_visibility='collapsed') or '전체'
    with st.container(key='section'):
        heading, sorting = st.columns([240, 110])
        with heading:
            section_title = '검색 결과' if search_mode else '밥 모임 둘러보기'
            st.markdown(f'<div class="section-title">{section_title}</div>', unsafe_allow_html=True)
        with sorting:
            if st.button(st.session_state[sort_key], key='sort'):
                st.session_state[sort_key] = '식사 시간순' if st.session_state[sort_key] == '최신순' else '최신순'
                st.rerun()
    sort = st.session_state[sort_key]
    filters = dict(region=None if region == '전체' else region,
                   food_category=None if category == '전체' else category,
                   status=None if status == '전체' else status, keyword=query.strip(),
                   sort='latest' if sort == '최신순' else 'meal_time')
    fingerprint = tuple(filters.items())
    if st.session_state.get(fingerprint_key) != fingerprint:
        st.session_state[page_key] = 0
        st.session_state[fingerprint_key] = fingerprint
    page_number = st.session_state.get(page_key, 0)
    failed = False
    try:
        posts = [p for p in load_posts(page_number, **filters) if p['status'] in FEED_STATUSES]
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
            f'<div class="host">{user_avatar(post["user_id"], 24)}<span>{e(post["nickname"])} · {e(rating)}</span></div>'
            f'<div class="stats"><span class="stat members" title="작성자 포함">{icon("users")}{post["current_count"]}/{post["capacity"]}명</span>'
            f'<span class="stat">{icon("heart")}{post["like_count"]}</span>'
            f'<span class="stat">{icon("comment")}{post["comment_count"]}</span></div></div></article>'
        )
        with st.container(key=f'card_{post["post_id"]}'):
            st.markdown(card, unsafe_allow_html=True)
            if st.button(f'{post["title"]} 상세 보기', key=f'db_open_{post["post_id"]}'):
                open_detail(post['post_id'], from_search=search_mode)
    if not failed and (page_number or has_next):
        with st.container(key='feed_pagination'):
            previous, counter, following = st.columns([1, 1, 1])
            with previous:
                if st.button('이전', key='feed_previous', disabled=page_number == 0):
                    st.session_state[page_key] = page_number - 1
                    st.rerun()
            with counter:
                st.caption(f'{page_number + 1}페이지')
            with following:
                if st.button('다음', key='feed_next', disabled=not has_next):
                    st.session_state[page_key] = page_number + 1
                    st.rerun()
    if search_mode:
        return

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

"""Feed page. Run the application with: streamlit run app.py."""

from datetime import datetime
from pathlib import Path

import streamlit as st

from ui_common import CSS, FOOD_CATEGORIES, REGIONS, STATUS_LABELS, FEED_STATUSES, asset, icon, e


# DB CHECK 제약조건. '전체'는 검색 UI에서만 사용하는 값이다.
# 홈 피드는 모집 진행 중인 글과 마감된 글만 표시한다.





def load_posts():
    """서비스 연결 전까지 상세 화면과 같은 예시 데이터를 사용한다."""
    from demo_data import get_posts
    return get_posts()


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


def main():
    st.set_page_config(page_title='머먹 · 모집 글', page_icon='🍚', layout='centered')
    if 'post' in st.query_params:
        st.switch_page('pages/3_post_detail.py',
                       query_params={'post': st.query_params['post']})
    st.markdown(f'<style>{CSS}</style>', unsafe_allow_html=True)
    posts = [post for post in load_posts() if post['status'] in FEED_STATUSES]
    user = st.session_state.get('user') or {}
    nickname = f"{e(user['nickname'])}님, " if user.get('nickname') else ''
    open_count = sum(p['status'] == 'OPEN' for p in posts)
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
                f'<div class="sub">가천대 근처에서 모집 중인 밥 모임 {open_count}개</div></div>', unsafe_allow_html=True)
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
    query = st.session_state.get('db_feed_query', '').strip().casefold()
    region = st.session_state.get('db_feed_region', '전체')
    status = st.session_state.get('db_feed_status', '전체')
    filtered = [p for p in posts
                if (category == '전체' or p['food_category'] == category)
                and (region == '전체' or p['region'] == region)
                and (status == '전체' or p['status'] == status)
                and (not query or query in (p['title'] + ' ' + p['body']).casefold())]
    filtered.sort(key=lambda p: p['created_at'] if sort == '최신순' else p['meal_time'], reverse=sort == '최신순')
    if not filtered:
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
    st.markdown('<div class="demo-note">예시 데이터로 만든 화면입니다.</div>', unsafe_allow_html=True)
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

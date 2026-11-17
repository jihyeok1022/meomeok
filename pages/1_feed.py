"""머먹 피드 — DB 스키마 기준 독립 실행 화면.

실행: python -m streamlit run feed_db.py
필요 패키지: streamlit>=1.45

Figma는 색상과 레이아웃 참고용이다. 필드와 선택값은
01_create_tables.sql 기준이다. 현재는 DB 연결 없이 예시 데이터를 표시한다.
백엔드가 완성되면 load_posts()의 반환값을 서비스 조회 결과로 교체한다.
화면에서 SQL이나 DB 저장 작업을 수행하지 않는다.
"""

import base64
from datetime import datetime, timedelta
from html import escape
from pathlib import Path

import streamlit as st


# DB CHECK 제약조건. '전체'는 검색 UI에서만 사용하는 값이다.
FOOD_CATEGORIES = ('한식', '중식', '양식', '일식', '기타', '미정')
REGIONS = ('교내', '복정동', '태평동', '기타')
STATUS_LABELS = {
    'OPEN': '모집중', 'CLOSED': '마감',
    'COMPLETED': '식사 완료', 'CANCELED': '취소',
}
# 홈 피드는 모집 진행 중인 글과 마감된 글만 표시한다.
FEED_STATUSES = ('OPEN', 'CLOSED')

st.set_page_config(page_title='머먹 · 모집 글', page_icon='🍚', layout='centered')


@st.cache_data
def asset(name):
    path = Path(__file__).resolve().parent / 'assets' / f'{name}.svg'
    return 'data:image/svg+xml;base64,' + base64.b64encode(path.read_bytes()).decode('ascii')


def icon(name):
    return f'<img src="{asset(name)}" alt="" aria-hidden="true">'


def load_posts():
    """서비스 연결 지점. 아래 반환 형식은 화면용 제안이며 확정 API가 아니다.

    Post + Content + User를 합쳐 표시한다.
    current_count = ACCEPTED 참여자 수 + 작성자 1명.
    rating = 작성자가 받은 Review.rating의 평균 (평가 없으면 None).
    like_count / comment_count = 해당 게시물의 좋아요 / 댓글 수.
    위 네 값은 저장 컬럼이 아닌 조회 집계값이다.
    """
    now = datetime.now().replace(second=0, microsecond=0)
    rows = [
        (1, 1, '도윤', '수업 끝나고 김치찌개 먹을 사람', '교내', '한식',
         now + timedelta(hours=2), 4, 'OPEN', '수업 끝나고 같이 저녁 먹어요.', 2, 4.8, 5, 3),
        (2, 5, '민지', '내일 점심 돈가스 먹으러 갈 분', '복정동', '일식',
         (now + timedelta(days=1)).replace(hour=12, minute=0), 3, 'OPEN',
         '복정동에서 점심 먹을 분 구해요. 가게는 같이 정해요!', 1, None, 8, 2),
        (3, 4, '수민', '오늘 같이 식사하실 분', '태평동', '기타',
         now + timedelta(hours=1), 4, 'CLOSED', '인원이 모두 모여 모집을 마감했어요.', 4, 4.5, 12, 6),
        (4, 2, '지우', '다음 모임 메뉴는 같이 정해요', '기타', '미정',
         now - timedelta(days=1), 2, 'COMPLETED', '함께 식사해 주셔서 감사합니다.', 2, 5.0, 2, 1),
        (5, 3, '현우', '저녁 모임 취소 안내', '교내', '양식',
         now + timedelta(days=1), 3, 'CANCELED', '개인 사정으로 모임을 취소했습니다.', 1, None, 0, 0),
    ]
    keys = ('post_id', 'user_id', 'nickname', 'title', 'region', 'food_category',
            'meal_time', 'capacity', 'status', 'body', 'current_count',
            'rating', 'like_count', 'comment_count')
    posts = [dict(zip(keys, row)) for row in rows]
    for index, post in enumerate(posts):
        post['created_at'] = now - timedelta(minutes=10 * (index + 1))
    return posts


def time_label(value):
    days = (value.date() - datetime.now().date()).days
    day = {0: '오늘', 1: '내일'}.get(days, value.strftime('%m/%d'))
    return f'{day} {value:%H:%M}'


def e(value):
    return escape(str(value))


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
    # 이 파일을 독립 실행할 때는 pages/ 파일이 라우터에 등록되지 않는다.
    if Path(__file__).name != '1_feed.py':
        notice('독립 실행 미리보기입니다. 페이지 이동은 기존 앱에 통합한 뒤 사용할 수 있어요.')
        return
    target = page_path(filename)
    if target:
        st.switch_page(str(target))
    else:
        notice('해당 화면은 아직 구현되지 않았어요.')


@st.dialog('모집 글')
def preview(post):
    st.subheader(post['title'])
    rating = '아직 평가 없음' if post['rating'] is None else f"평균 평점 {post['rating']:.1f}"
    st.caption(f"{post['nickname']} · {rating}")
    st.write(post['body'])
    st.write(f"지역: {post['region']} · 음식 종류: {post['food_category']}")
    st.write(f"식사 시간: {time_label(post['meal_time'])}")
    st.write(f"인원: {post['current_count']}/{post['capacity']}명 (작성자 포함)")
    st.write(f"상태: {STATUS_LABELS[post['status']]}")
    st.caption(f"작성: {post['created_at']:%Y-%m-%d %H:%M}")
    st.info('예시 데이터입니다. 댓글·좋아요·팔로우·참여 신청은 백엔드 연결 후 사용할 수 있어요.')


CSS = """
/* Reference: Figma 2:40. All dimensions below are CSS pixels. */
:root{--orange:#ff7a3d;--paper:#f7f6f4;--line:#ececec;--ink:#1f1f1f;--muted:#6b6b6b;}
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"]{
 background:#efeeec!important;color:var(--ink)!important;color-scheme:light;}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stSidebar"],
[data-testid="stDecoration"],#MainMenu,footer{display:none!important;}
[data-testid="stMain"]{scrollbar-width:none;}
[data-testid="stMain"]::-webkit-scrollbar{display:none;}
[data-testid="stMainBlockContainer"]{--text-color:#1f1f1f;--background-color:#fff;
 --secondary-background-color:#f7f6f4;width:100%!important;max-width:390px!important;
 height:auto!important;min-height:100dvh;flex:0 0 auto!important;
 padding:0 0 94px!important;margin:0 auto!important;
 background:var(--paper);font-family:'Noto Sans KR','Malgun Gothic',sans-serif;}
[data-testid="stMainBlockContainer"] p,[data-testid="stMainBlockContainer"] button{
 font-family:'Noto Sans KR','Malgun Gothic',sans-serif;}
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"]{gap:0!important;}
/* Streamlit 1.56 gives MarkdownContainer a -16px bottom margin.
   Raw HTML has no paragraph margin to offset, so remove it explicitly. */
[data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"]{margin-bottom:0!important;}
[data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"] p{margin:0;}
[data-testid="stElementContainer"]:has(>.stMarkdown style){display:none;}
.status-bar{height:40px;box-sizing:border-box;padding:14px 24px 6px;display:flex;
 align-items:center;justify-content:space-between;background:white;color:var(--ink);font-size:12px;line-height:20px;}
.status-bar strong{font-size:14px;font-weight:700;}
.st-key-header{background:white;height:51px!important;min-height:51px!important;max-height:51px!important;
 padding:8px 20px 12px!important;box-sizing:border-box;}
.st-key-header [data-testid="stHorizontalBlock"]{height:31px;gap:16px;align-items:center;flex-wrap:nowrap!important;}
.st-key-header [data-testid="stColumn"]{min-width:0!important;}
.st-key-header [data-testid="stColumn"]:first-child{flex:1 1 auto;}
.st-key-header [data-testid="stColumn"]:not(:first-child){flex:0 0 24px;}
.brand{font-size:22px;font-weight:800;line-height:31px;color:var(--orange);}
.st-key-header [data-testid="stButton"]{height:24px;line-height:0;}
.st-key-header button{display:flex;width:24px!important;min-width:24px!important;height:24px!important;
 min-height:24px!important;padding:0!important;border:0;border-radius:0;box-shadow:none;
 background-color:transparent!important;background-repeat:no-repeat;background-position:center;}
.st-key-header button p{font-size:0!important;line-height:0!important;}
.st-key-header button:hover{background-color:#fff1e9!important;border-radius:4px;}
.intro-block{height:49px;box-sizing:border-box;background:white;padding:4px 20px 0;}
.intro{font-size:18px;line-height:25px;font-weight:700;letter-spacing:-.6px;color:var(--ink);white-space:nowrap;}
.sub{font-size:13px;line-height:18px;color:var(--muted);margin-top:2px;}
.st-key-categories{height:62px;min-height:62px;box-sizing:border-box;background:white;
 padding:12px 8px 16px 20px!important;}
.st-key-categories [data-testid="stPills"]{overflow:hidden;}
.st-key-categories [role="radiogroup"]{display:flex;align-items:center;gap:8px!important;flex-wrap:nowrap!important;
 overflow-x:auto;scrollbar-width:none;max-width:100%;padding:0;}
.st-key-categories [role="radiogroup"]::-webkit-scrollbar{display:none;}
.st-key-categories button{height:34px!important;min-height:34px!important;min-width:54px;
 flex-shrink:0;border:1px solid var(--line)!important;border-radius:999px;background:white!important;
 color:var(--muted)!important;padding:7px 14px!important;white-space:nowrap;box-shadow:none!important;}
.st-key-categories button p{font-size:13px;line-height:18px;font-weight:500;}
.st-key-categories button[data-testid="stBaseButton-pillsActive"]{
 min-width:52px;height:32px!important;min-height:32px!important;border:0!important;
 background:var(--orange)!important;color:white!important;}
.st-key-categories button[data-testid="stBaseButton-pillsActive"] p{font-weight:700;}
.st-key-tools{background:white;padding:0 20px 16px!important;color:var(--ink);}
.st-key-tools [data-testid="stVerticalBlock"]{gap:8px!important;}
.st-key-tools label,.st-key-tools label p{color:var(--ink)!important;}
.st-key-tools [data-baseweb="select"]>div,.st-key-tools [data-baseweb="input"]{
 background:white!important;color:var(--ink)!important;border-color:#ddd!important;}
.st-key-tools input{background:white!important;color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important;}
.st-key-tools svg{fill:var(--muted)!important;}
.st-key-section{height:50px!important;min-height:50px!important;max-height:50px!important;
 padding:18px 20px 10px!important;box-sizing:border-box;}
.st-key-section [data-testid="stHorizontalBlock"]{height:22px;gap:0;align-items:center;flex-wrap:nowrap!important;}
.st-key-section [data-testid="stColumn"]{min-width:0!important;}
.st-key-section [data-testid="stColumn"]:first-child{flex:1 1 auto;}
.st-key-section [data-testid="stColumn"]:last-child{flex:0 0 84px;}
.section-title{font-size:16px;line-height:22px;font-weight:700;color:var(--ink);white-space:nowrap;}
.st-key-section [data-testid="stElementContainer"],.st-key-section [data-testid="stButton"]{width:100%!important;}
.st-key-section button{display:flex;width:100%!important;height:22px!important;min-height:22px!important;
 padding:0!important;border:0;border-radius:0;box-shadow:none;background:transparent!important;
 color:var(--muted)!important;justify-content:flex-end;align-items:center;}
.st-key-section button p{font-size:13px!important;line-height:18px!important;font-weight:500;}
.st-key-section button>div{justify-content:flex-end!important;}
[class*="st-key-card_"]{position:relative;height:160px!important;min-height:160px!important;
 max-height:160px!important;width:calc(100% - 40px)!important;margin:0 20px 12px!important;flex-shrink:0;}
.meetup-card{height:160px;width:100%;box-sizing:border-box;padding:16px;border:1px solid var(--line);
 border-radius:16px;background:white;box-shadow:0 2px 4px #0000000d;color:var(--ink);
 display:flex;flex-direction:column;gap:10px;}
.card-top,.card-bottom{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-shrink:0;}
.tags{display:flex;align-items:center;gap:6px;}
.badge,.food{border-radius:6px;padding:3px 8px;font-size:11px;line-height:15px;white-space:nowrap;}
.badge{background:var(--orange);color:white;font-weight:700;}
.badge.closed{background:#bdbdbd;}
.badge.completed{background:#e5f3ea;color:#277245;}
.badge.canceled{background:#fce8e6;color:#ae3930;}
.food{background:#fff1e9;color:var(--orange);font-weight:500;}
.time{display:flex;align-items:center;gap:4px;font-size:12px;line-height:17px;color:var(--muted);white-space:nowrap;}
.card-title{font-size:16px;font-weight:700;line-height:22px;letter-spacing:-.5px;
 margin:0;padding:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex-shrink:0;}
.region{display:flex;align-items:center;gap:4px;font-size:13px;line-height:18px;color:var(--muted);}
.card-rule{height:1px;background:var(--line);flex-shrink:0;}
.host{display:flex;align-items:center;gap:6px;font-size:12px;line-height:17px;white-space:nowrap;min-width:0;}
.host span{overflow:hidden;text-overflow:ellipsis;}
.stats{display:flex;align-items:center;gap:10px;white-space:nowrap;flex-shrink:0;}
.stat{display:flex;align-items:center;gap:3px;font-size:12px;line-height:17px;color:#a0a0a0;}
.stat.members{color:var(--orange);font-weight:700;}
.meetup-card img{display:block;flex-shrink:0;max-width:none;}
/* Keep the native button for keyboard interaction without adding layout height. */
[class*="st-key-card_"] [data-testid="stElementContainer"]:has(>[data-testid="stButton"]){
 position:absolute!important;inset:0;z-index:2;}
[class*="st-key-card_"] [data-testid="stButton"]{position:absolute;inset:0;width:100%!important;height:160px;}
[class*="st-key-card_"] button{display:block;width:100%!important;height:160px!important;
 min-height:160px!important;padding:0;border:0;border-radius:16px;background:transparent!important;box-shadow:none;}
[class*="st-key-card_"] button p{font-size:0!important;line-height:0!important;}
[class*="st-key-card_"] button:hover{box-shadow:inset 0 0 0 1px #ff7a3d88;}
[class*="st-key-card_"] button:focus-visible{outline:3px solid var(--orange);outline-offset:3px;}
.st-key-fab{position:fixed;bottom:100px;left:calc(50% + 76px);width:99px!important;z-index:20;}
.st-key-fab button{display:flex;align-items:center;height:44px!important;min-height:44px!important;width:99px!important;
 padding:12px 20px 12px 40px!important;border:0;border-radius:999px;background-color:var(--orange)!important;
 background-repeat:no-repeat;background-position:16px center;color:white!important;box-shadow:0 4px 12px #ff7a3d59;}
.st-key-fab button p{font-size:14px!important;font-weight:700;line-height:20px;white-space:nowrap;}
.st-key-fab button:hover{background-color:#ed682b!important;}
.st-key-bottom_nav{position:fixed;bottom:0;left:50%;transform:translateX(-50%);z-index:30;
 width:min(390px,100vw)!important;height:70px!important;min-height:70px!important;box-sizing:border-box;
 padding:8px 0 20px!important;border-top:1px solid var(--line);background:white;}
.st-key-bottom_nav [data-testid="stHorizontalBlock"]{height:41px;gap:0;flex-wrap:nowrap!important;}
.st-key-bottom_nav [data-testid="stColumn"]{min-width:0!important;flex:1 1 0;}
.st-key-bottom_nav [data-testid="stElementContainer"],.st-key-bottom_nav [data-testid="stButton"]{width:100%!important;height:41px;}
.st-key-bottom_nav button{display:flex;align-items:flex-start;justify-content:center;height:41px!important;
 min-height:41px!important;width:100%!important;padding:26px 0 0!important;border:0;border-radius:0;
 background-color:transparent!important;background-repeat:no-repeat;background-position:center top;color:#a0a0a0!important;}
.st-key-bottom_nav button p{font-size:11px!important;line-height:15px!important;white-space:nowrap;}
.st-key-nav_home button{color:var(--orange)!important;font-weight:700;}
.demo-note{font-size:11px;line-height:16px;text-align:center;color:#777;padding:8px 20px 18px;}
.empty{margin:0 20px 16px;padding:28px 16px;background:white;border:1px solid var(--line);
 border-radius:16px;text-align:center;font-size:13px;color:var(--muted);}
[data-testid="stDialog"] [role="dialog"]{background:white!important;color:var(--ink)!important;}
@media(max-width:390px){.st-key-fab{left:auto;right:20px;}}
@media(max-width:350px){.intro{font-size:17px;letter-spacing:-.8px;}.host{font-size:11px;}.stats{gap:6px;}}
"""
for key, name in {'search_button': 'search', 'bell_button': 'bell', 'fab': 'plus',
                  'nav_home': 'home', 'nav_apply': 'calendar', 'nav_chat': 'groups', 'nav_profile': 'user'}.items():
    CSS += f'.st-key-{key} button{{background-image:url("{asset(name)}");}}\n'


def main():
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
                st.session_state['selected_post_id'] = post['post_id']
                if Path(__file__).name == '1_feed.py' and page_path('3_post_detail.py'):
                    navigate('3_post_detail.py')
                else:
                    preview(post)
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

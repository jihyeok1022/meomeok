"""머먹 홈 — Figma 2:40 기반. 실행: python -m streamlit run 1_feed_figma.py
assets/ 폴더를 이 파일과 함께 두세요. DB 연결 전 예시 화면입니다.
"""
import base64
from datetime import datetime, timedelta
from html import escape
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="머먹 · 모집 글", page_icon="🍚", layout="centered")
ROOT = Path(__file__).resolve().parent

@st.cache_data
def asset(name):
    return "data:image/svg+xml;base64," + base64.b64encode((ROOT / "assets" / f"{name}.svg").read_bytes()).decode("ascii")

def icon(name):
    return f'<img src="{asset(name)}" alt="" aria-hidden="true">'

def load_posts():
    """백엔드 연동 지점. place/budget은 DB에 없는 시안용 정보입니다.
    분식도 현재 DB 허용값에 없으므로 연동 전 팀과 분류를 맞춰야 합니다.
    """
    today = datetime.now().replace(second=0, microsecond=0)
    rows = [
        (1, 1, "도윤", 4.8, "학식 말고 김치찌개 먹을 사람", "정문 앞 · 김치찌개", "1만원 이하", "교내", "한식", today.replace(hour=18, minute=30), 2, 4, "OPEN", 5, 3,
         "6시 수업 끝나고 저녁 먹으려고요. 친구랑 둘이 가는데 같이 먹을 분 있나요? 6시 20분쯤 정문에서 만나면 될 것 같아요. 밥 먹고 바로 가셔도 괜찮아요 ㅋㅋ"),
        (2, 5, "민지", 4.6, "내일 점심 돈가스 먹으러 갈 분", "복정동 · 돈가스집", "1~2만원", "복정동", "일식", (today + timedelta(days=1)).replace(hour=12, minute=0), 1, 3, "OPEN", 8, 2,
         "내일 12시부터 공강인데 돈가스가 먹고 싶어서요. 복정동 쪽 가려고 하는데 가게는 같이 정해도 돼요! 1시 수업이라 그전엔 돌아올 예정이에요."),
        (3, 4, "수민", 4.9, "공강인데 떡볶이 먹을 사람?", "후문 · 떡볶이집", "1만원 이하", "교내", "분식", today.replace(hour=13, minute=0), 4, 4, "CLOSED", 12, 6,
         "다음 수업까지 두 시간 남아서 후문에 떡볶이 먹으러 가려고요. 저 매운 거 잘 못 먹어서 순한 맛으로 먹을 분 구해요.\n\n추가) 인원 다 모였어요! 신청해 주신 분들 감사합니다."),
    ]
    keys = "post_id user_id nickname rating title place budget region food_category meal_time current_count capacity status like_count comment_count body".split()
    posts = [dict(zip(keys, row)) for row in rows]
    for index, post in enumerate(posts):
        post["created_at"] = today - timedelta(minutes=10 * (index + 1))
    return posts

def time_label(value):
    days = (value.date() - datetime.now().date()).days
    return f"{ {0: '오늘', 1: '내일'}.get(days, value.strftime('%m/%d'))} {value:%H:%M}"

@st.dialog("알림")
def notice(message):
    st.write(message)

@st.dialog("모집 글 미리보기")
def preview(post):
    st.subheader(post["title"])
    st.caption(f"{post['nickname']} · 매너 {post['rating']:.1f}")
    st.write(post["body"])
    st.write(f"식사 시간: {time_label(post['meal_time'])}")
    st.write(f"장소: {post['place']}")
    st.write(f"인원: {post['current_count']}/{post['capacity']}명 (작성자 포함)")
    st.caption("예시 게시글입니다. 참여 신청과 댓글은 백엔드 연결 후 사용할 수 있어요.")

def page_path(filename):
    project = ROOT.parent if ROOT.name == "pages" else ROOT
    target = project / "pages" / filename
    return target if target.is_file() and target.read_text(encoding="utf-8-sig").strip() else None

def navigate(filename, message):
    target = page_path(filename)
    if target:
        st.switch_page(str(target))
    else:
        notice(message)

CSS = """
:root{--orange:#ff7a3d;--paper:#f7f6f4;--line:#ececec;--ink:#1f1f1f;}
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"]{background:#efeeec;}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stSidebar"],
[data-testid="stDecoration"],#MainMenu,footer{display:none;}
[data-testid="stMainBlockContainer"]{max-width:390px;min-height:100dvh;padding:0 0 94px;
 background:var(--paper);box-shadow:0 0 40px #00000006;font-family:'Noto Sans KR','Malgun Gothic',sans-serif;}
[data-testid="stVerticalBlock"]{gap:0;}
[data-testid="stMain"]{scrollbar-width:none;}
[data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"],
[data-testid="stMainBlockContainer"] p{font-family:'Noto Sans KR','Malgun Gothic',sans-serif;}
[data-testid="stMarkdownContainer"] p{margin:0;}
[data-testid="stMainBlockContainer"] button{font-family:inherit;}
.status-bar{height:40px;padding:14px 24px 6px;display:flex;align-items:center;justify-content:space-between;
 background:white;color:var(--ink);font-size:12px;box-sizing:border-box;}
.status-bar strong{font-size:14px;}
.st-key-header{background:white;padding:8px 20px 12px;height:51px;min-height:51px;box-sizing:border-box;}
.st-key-header [data-testid="stHorizontalBlock"]{gap:16px;align-items:center;}
.st-key-header [data-testid="stHorizontalBlock"],.st-key-section [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;}
.st-key-header [data-testid="stColumn"],.st-key-section [data-testid="stColumn"]{min-width:0!important;}
.st-key-header [data-testid="stColumn"]:first-child{flex:1 1 auto;}
.st-key-header [data-testid="stColumn"]:not(:first-child){flex:0 0 24px;}
.st-key-section [data-testid="stColumn"]:first-child{flex:1 1 auto;}
.st-key-section [data-testid="stColumn"]:last-child{flex:0 0 100px;}
.stMarkdown,.stMarkdown>div{height:auto!important;}
[data-testid="stElementContainer"]:has(>.stMarkdown .status-bar){height:40px!important;}
.brand{color:var(--orange);font-weight:800;font-size:22px;line-height:31px;}
.st-key-header button{width:24px!important;min-width:24px!important;height:24px;min-height:24px;padding:0;border:0;
 background-color:transparent;border-radius:0;background-repeat:no-repeat;}
.st-key-header button:hover{background-color:#fff1e9;}
.st-key-header button p{font-size:0;}
.intro{background:white;padding:4px 20px 0;}
.intro h1{font-family:inherit;font-size:18px;line-height:25px;font-weight:750;letter-spacing:-.6px;
 margin:0;padding:0;color:var(--ink);}
.intro p{font-size:13px;color:#6b6b6b;line-height:18px;margin-top:2px;}
.st-key-categories{background:white;padding:28px 8px 16px 20px;}
.st-key-categories [role="radiogroup"]{gap:8px!important;flex-wrap:nowrap!important;overflow-x:auto;scrollbar-width:none;max-width:100%;}
.st-key-categories button{border:1px solid var(--line);border-radius:999px;background:white;color:#6b6b6b;
 padding:7px 14px;min-height:34px;min-width:52px;flex-shrink:0;white-space:nowrap;box-shadow:none;}
.st-key-categories button p{font-size:13px;line-height:18px;}
.st-key-categories button[aria-checked="true"]{background:var(--orange)!important;color:white!important;border-color:var(--orange)!important;}
.st-key-search_panel{background:white;padding:0 20px 16px;}
.st-key-search_panel [data-testid="stVerticalBlock"]{gap:8px;}
.st-key-section{padding:18px 20px 10px;}
.st-key-section [data-testid="stHorizontalBlock"]{align-items:center;gap:0;}
.section-title{font-size:16px;font-weight:750;line-height:22px;color:var(--ink);}
.st-key-sort button{border:none;background:transparent;min-height:22px;padding:0;color:#6b6b6b;float:right;}
.st-key-sort button p{font-size:13px;line-height:18px;}
.st-key-sort{width:100%!important;}
.st-key-sort button{width:100%;justify-content:flex-end;}
[class*="st-key-card_"]{margin:0 20px 12px;width:calc(100% - 40px)!important;position:relative;min-height:160px;flex-shrink:0;}
.meetup-card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:16px;height:160px;
 box-sizing:border-box;box-shadow:0 2px 4px #0000000d;display:flex;flex-direction:column;gap:10px;color:var(--ink);}
.card-top,.card-bottom{display:flex;align-items:center;justify-content:space-between;}
.tags{display:flex;gap:6px;}
.badge,.food-tag{font-size:11px;font-weight:700;border-radius:6px;padding:3px 8px;line-height:15px;white-space:nowrap;}
.badge{background:var(--orange);color:white;}.badge.closed{background:#bdbdbd;}
.food-tag{background:#fff1e9;color:var(--orange);font-weight:500;}
.time,.place,.host,.stat{display:flex;align-items:center;gap:4px;}
.time{font-size:12px;color:#6b6b6b;white-space:nowrap;}
.card-title{font-size:16px!important;font-weight:750!important;line-height:22px!important;margin:0!important;
 padding:0!important;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;letter-spacing:-.5px;}
.place{color:#6b6b6b;font-size:13px;line-height:18px;white-space:nowrap;}
.place span{overflow:hidden;text-overflow:ellipsis;}
.card-rule{height:1px;background:var(--line);flex-shrink:0;}
.card-bottom{gap:8px;}.host{font-size:12px;gap:6px;white-space:nowrap;}
.stats{display:flex;align-items:center;gap:10px;}
.stat{gap:3px;color:#a0a0a0;font-size:12px;white-space:nowrap;}
.stat.members{color:var(--orange);font-weight:700;}
.meetup-card img{display:block;flex-shrink:0;}
[class*="st-key-card_"] [data-testid="stButton"]{position:absolute;inset:0;z-index:2;}
[class*="st-key-card_"] button{width:100%;height:160px;border:0;padding:0;
 background:transparent!important;border-radius:16px;box-shadow:none;}
[class*="st-key-card_"] button p{font-size:0;}
[class*="st-key-card_"] button:hover{box-shadow:inset 0 0 0 1px #ff7a3d88;}
[class*="st-key-card_"] button:focus-visible{outline:3px solid #ff7a3d;outline-offset:3px;}
.st-key-fab{position:fixed;bottom:100px;left:calc(50% + 76px);z-index:20;width:99px;}
.st-key-fab button{border:0;border-radius:999px;background-color:var(--orange);height:44px;
 padding:12px 20px 12px 40px;color:white;box-shadow:0 4px 12px #ff7a3d59;
 background-repeat:no-repeat;background-position:16px center;}
.st-key-fab button p{font-size:14px;line-height:20px;font-weight:700;white-space:nowrap;}
.st-key-fab button:hover{background-color:#ed682b;color:white;}
.st-key-bottom_nav{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:390px;max-width:100%;
 height:70px;background:white;border-top:1px solid var(--line);padding:8px 0 20px;z-index:30;box-sizing:border-box;}
.st-key-bottom_nav [data-testid="stHorizontalBlock"]{gap:0;flex-wrap:nowrap;}
.st-key-bottom_nav [data-testid="stColumn"]{min-width:0!important;flex:1 1 0;}
.st-key-bottom_nav [data-testid="stElementContainer"],.st-key-bottom_nav [data-testid="stButton"]{width:100%!important;}
.st-key-bottom_nav button{width:100%;height:41px;min-height:41px;padding:26px 0 0;border:0;
 background-color:transparent;background-repeat:no-repeat;background-position:center top;border-radius:0;color:#a0a0a0;}
.st-key-bottom_nav button p{font-size:11px;line-height:15px;white-space:nowrap;}
.st-key-nav_home button{color:var(--orange);font-weight:700;}
.demo-note{font-size:11px;color:#777;text-align:center;padding:3px 20px 20px;}
.empty{margin:0 20px 16px;padding:36px 20px;border:1px solid var(--line);border-radius:16px;
 background:white;text-align:center;color:#6b6b6b;font-size:14px;}
@media(max-width:390px){.st-key-fab{left:auto;right:20px;}.host{font-size:11px;}.stats{gap:6px;}}
"""
for key, name in {"search_button":"search", "bell_button":"bell", "fab":"plus", "nav_home":"home",
                  "nav_apply":"calendar", "nav_chat":"groups", "nav_profile":"user"}.items():
    CSS += f'.st-key-{key} button{{background-image:url("{asset(name)}");}}\n'
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

st.session_state.setdefault("feed_sort", "최신순")
st.session_state.setdefault("feed_show_search", False)
posts = load_posts()
user = st.session_state.get("user") or {}
greeting = f'{escape(str(user["nickname"]))}님, 오늘 누구랑 밥 먹을까요?' if user.get("nickname") else "오늘 누구랑 밥 먹을까요?"
open_count = sum(p["status"] == "OPEN" for p in posts)
st.markdown('<div class="status-bar" aria-hidden="true"><strong>9:41</strong><span>LTE 100%</span></div>', unsafe_allow_html=True)
with st.container(key="header"):
    brand, search, bell = st.columns([254,32,32])
    with brand:
        st.markdown('<div class="brand">머먹</div>', unsafe_allow_html=True)
    with search:
        if st.button("검색", key="search_button", help="검색 및 필터 열기"):
            st.session_state.feed_show_search = not st.session_state.feed_show_search
    with bell:
        if st.button("알림", key="bell_button", help="알림"):
            notice("현재 예시 화면입니다. 알림 기능은 아직 연결되지 않았어요.")
st.markdown(f'<div class="intro"><h1>{greeting}</h1><p>가천대 근처에서 모집 중인 밥 모임 {open_count}개</p></div>', unsafe_allow_html=True)
with st.container(key="categories"):
    category = st.pills("음식 종류", ["전체","한식","일식","중식","분식","양식"], default="전체",
                        key="feed_category", label_visibility="collapsed") or "전체"
if st.session_state.feed_show_search:
    with st.container(key="search_panel"):
        st.text_input("게시글 검색", placeholder="제목이나 본문 검색", key="feed_search")
        st.selectbox("지역", ["전체","교내","복정동","태평동","기타"], key="feed_region")
        st.checkbox("모집 중인 글만 보기", key="feed_open_only")
        st.checkbox("팔로우한 사람만 보기 (예시: 민지·수민)", key="feed_follow_only")
with st.container(key="section"):
    title, sort = st.columns([240,110])
    with title:
        st.markdown('<div class="section-title">지금 모집 중인 밥 모임</div>', unsafe_allow_html=True)
    with sort:
        if st.button(st.session_state.feed_sort, key="sort", help="최신순 / 식사 시간순 전환"):
            st.session_state.feed_sort = "식사 시간순" if st.session_state.feed_sort == "최신순" else "최신순"
            st.rerun()
query = st.session_state.get("feed_search", "").strip().casefold()
region = st.session_state.get("feed_region", "전체")
filtered = [p for p in posts if (category == "전체" or p["food_category"] == category)
            and (region == "전체" or p["region"] == region)
            and (not query or query in (p["title"] + " " + p["body"]).casefold())
            and (not st.session_state.get("feed_open_only") or p["status"] == "OPEN")
            and (not st.session_state.get("feed_follow_only") or p["user_id"] in {4,5})]
filtered.sort(key=lambda p: p["created_at"] if st.session_state.feed_sort == "최신순" else p["meal_time"],
              reverse=st.session_state.feed_sort == "최신순")
if not filtered:
    st.markdown('<div class="empty">조건에 맞는 모임이 없어요.<br>다른 메뉴나 검색어로 찾아보세요.</div>', unsafe_allow_html=True)
for post in filtered:
    e = lambda value: escape(str(value))
    badge = "모집중" if post["status"] == "OPEN" else "마감"
    closed = "" if post["status"] == "OPEN" else " closed"
    card = ('<article class="meetup-card"><div class="card-top"><div class="tags">'
        f'<span class="badge{closed}">{badge}</span><span class="food-tag">{e(post["food_category"])}</span></div>'
        f'<div class="time">{icon("clock")}{e(time_label(post["meal_time"]))}</div></div>'
        f'<h2 class="card-title">{e(post["title"])}</h2>'
        f'<div class="place">{icon("pin")}<span>{e(post["place"])} · {e(post["budget"])}</span></div>'
        '<div class="card-rule"></div><div class="card-bottom">'
        f'<div class="host">{icon("avatar")}{e(post["nickname"])} · 매너 {post["rating"]:.1f}</div>'
        f'<div class="stats"><span class="stat members">{icon("users")}{post["current_count"]}/{post["capacity"]}명</span>'
        f'<span class="stat">{icon("heart")}{post["like_count"]}</span>'
        f'<span class="stat">{icon("comment")}{post["comment_count"]}</span></div></div></article>')
    with st.container(key=f"card_{post['post_id']}"):
        st.markdown(card, unsafe_allow_html=True)
        if st.button(f"{post['title']} 상세 보기", key=f"open_{post['post_id']}"):
            st.session_state["selected_post_id"] = post["post_id"]
            if page_path("3_post_detail.py"):
                st.switch_page(str(page_path("3_post_detail.py")))
            else:
                preview(post)
st.markdown('<div class="demo-note">예시 데이터로 만든 화면입니다.</div>', unsafe_allow_html=True)
with st.container(key="fab"):
    if st.button("글쓰기", key="write_post", help="모집 글 작성"):
        navigate("2_write_post.py", "글쓰기 화면은 다음 단계에서 연결할 예정이에요.")
with st.container(key="bottom_nav"):
    home, apply, chat, profile = st.columns(4)
    with home, st.container(key="nav_home"):
        if st.button("모집 글", key="bottom_home"):
            st.rerun()
    with apply, st.container(key="nav_apply"):
        if st.button("내 신청", key="bottom_apply"):
            navigate("5_participation.py", "내 신청 화면은 담당자가 구현한 뒤 연결할 예정이에요.")
    with chat, st.container(key="nav_chat"):
        if st.button("톡방", key="bottom_chat"):
            navigate("6_chat.py", "톡방 화면은 담당자가 구현한 뒤 연결할 예정이에요.")
    with profile, st.container(key="nav_profile"):
        if st.button("내 프로필", key="bottom_profile"):
            navigate("4_profile.py", "프로필 화면은 담당자가 구현한 뒤 연결할 예정이에요.")

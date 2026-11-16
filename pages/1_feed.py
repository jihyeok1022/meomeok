"""머먹 게시글 목록 화면. DB 연결 전에는 아래 예시 데이터를 사용합니다."""

from datetime import datetime, timedelta

import streamlit as st


st.set_page_config(page_title="머먹", page_icon="여기에 페이지 아이콘", layout="centered")


def load_posts():
    """백엔드 연결 시 이 함수의 예시 데이터를 실제 조회 결과로 교체."""
    tomorrow = (datetime.now() + timedelta(days=1)).replace(
        hour=12, minute=30, second=0, microsecond=0
    )
    return [
        {
            "post_id": 1,
            "user_id": 2,
            "nickname": "도윤",
            "title": "학식 ㄱㄱ?",
            "body": "학생식당 입구에서 만나요. 편하게 이야기하면서 먹어요!",
            "region": "교내",
            "food_category": "한식",
            "meal_time": tomorrow,
            "current_count": 2,
            "capacity": 4,
            "status": "OPEN",
        },
        {
            "post_id": 2,
            "user_id": 3,
            "nickname": "수민",
            "title": "태평동 돈가스 야르",
            "body": "같이 갈 사람?",
            "region": "태평동",
            "food_category": "일식",
            "meal_time": tomorrow.replace(hour=18, minute=0),
            "current_count": 1,
            "capacity": 2,
            "status": "OPEN",
        },
        {
            "post_id": 3,
            "user_id": 4,
            "nickname": "서연",
            "title": "수업 끝나고 마라탕 한사발 하실 분",
            "body": "복정역 근처에서 먹을 생각인데 ㄱㄴ하신 분 있나요",
            "region": "복정동",
            "food_category": "중식",
            "meal_time": tomorrow.replace(hour=19, minute=0),
            "current_count": 3,
            "capacity": 3,
            "status": "CLOSED",
        },
        {
            "post_id": 4,
            "user_id": 5,
            "nickname": "민지",
            "title": "파스타 좋아하는 사람?",
            "body": "메뉴는 만나서 함께 골라요. 처음 오시는 분도 환영해요.",
            "region": "기타",
            "food_category": "양식",
            "meal_time": tomorrow + timedelta(days=1),
            "current_count": 2,
            "capacity": 4,
            "status": "OPEN",
        },
    ]


STATUS_LABELS = {
    "OPEN": "모집 중",
    "CLOSED": "모집 마감",
    "COMPLETED": "식사 완료",
    "CANCELED": "취소된 모임",
}

st.title("머먹")
st.subheader("오늘의 밥친구를 찾아봐요")
st.caption("같이 먹고 싶은 메뉴와 장소로 모임을 찾아보세요.")
st.info("화면 개발용 예시입니다. 실제 게시글·로그인·팔로우 정보는 연결 전입니다.")

search = st.text_input("게시글 검색", placeholder="제목이나 본문을 검색해 보세요")
region_col, food_col = st.columns(2)
with region_col:
    region = st.selectbox("지역", ["전체", "교내", "복정동", "태평동", "기타"])
with food_col:
    food = st.selectbox("음식 종류", ["전체", "한식", "중식", "양식", "일식", "기타", "미정"])

only_open = st.checkbox("모집 중인 글만 보기", value=True)
followed_only = st.checkbox("팔로우한 사람만 보기 (예시: 도윤·민지)")

posts = load_posts()
sample_following_ids = {2, 5}
keyword = search.strip().casefold()
filtered_posts = [
    post
    for post in posts
    if (region == "전체" or post["region"] == region)
    and (food == "전체" or post["food_category"] == food)
    and (
        not only_open
        or (
            post["status"] == "OPEN"
            and post["meal_time"] > datetime.now()
            and post["current_count"] < post["capacity"]
        )
    )
    and (not followed_only or post["user_id"] in sample_following_ids)
    and (not keyword or keyword in (post["title"] + " " + post["body"]).casefold())
]

st.divider()
st.caption(f"검색 결과 {len(filtered_posts)}개 · 가까운 식사 시간순")

if not filtered_posts:
    st.info("조건에 맞는 모임이 없어요. 검색어나 필터를 바꿔보세요.")

for post in sorted(filtered_posts, key=lambda item: (item["meal_time"], item["post_id"])):
    with st.container(border=True):
        st.caption(f"{STATUS_LABELS[post['status']]} · {post['region']} · {post['food_category']}")
        st.subheader(post["title"])
        st.write(
            f"📅 {post['meal_time']:%m/%d %H:%M}  |  "
            f"👥 {post['current_count']}/{post['capacity']}명 (작성자 포함)"
        )
        st.caption(f"작성자 {post['nickname']}")
        # 상세 화면이 완성되기 전까지 본문을 이 자리에서 미리 보여줍니다.
        with st.expander("본문 미리보기"):
            st.write(post["body"])

st.caption("머먹 · 가천대학교 밥친구 모집")

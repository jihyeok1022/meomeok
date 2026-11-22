"""
services/post_service.py - 모집 글 목록·상세 조회와 등록
게시물 규칙
- 피드(list_posts)는 항상 모집 중(OPEN)과 모집 마감(CLOSED) 글만 반환한다.
- 완료(COMPLETED)·취소(CANCELED) 글은 피드 검색에서도 노출하지 않는다.
- 제목(title)과 본문(body)은 Content 테이블에 분리 저장하므로 Post와 한 트랜잭션으로 처리한다.
- current_count(작성자 1명 + ACCEPTED 참여자 수), rating, like_count, comment_count는 조회 시 집계한다.
- 작성한 글 목록(get_user_posts)은 user_service(1번)가 담당한다.
"""

from datetime import datetime

from db import query, query_one, transaction

ALLOWED_REGIONS = {"교내", "복정동", "태평동", "기타"}
ALLOWED_FOOD_CATEGORIES = {"한식", "중식", "양식", "일식", "기타", "미정"}
ALLOWED_FEED_STATUSES = {"OPEN", "CLOSED"}
ALLOWED_SORTS = {"latest", "meal_time"}


def _validate_positive_int(value, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"유효하지 않은 {name}입니다.")
    return value


def _to_float_or_none(value):
    if value is None:
        return None
    return float(value)


def _format_post_row(row: dict) -> dict:
    return {
        "post_id": int(row["post_id"]),
        "user_id": int(row["user_id"]),
        "nickname": row["nickname"],
        "title": row["title"],
        "body": row["body"],
        "region": row["region"],
        "food_category": row["food_category"],
        "meal_time": row["meal_time"],
        "capacity": int(row["capacity"]),
        "status": row["status"],
        "created_at": row["created_at"],
        "current_count": int(row["current_count"]),
        "rating": _to_float_or_none(row["rating"]),
        "like_count": int(row["like_count"]),
        "comment_count": int(row["comment_count"]),
    }


def list_posts(
    *,
    region=None,
    food_category=None,
    status=None,
    keyword="",
    sort="latest",
    limit=50,
    offset=0,
) -> list[dict]:
    """피드용 모집 글 목록 조회 (항상 OPEN, CLOSED만 반환).
    정렬: sort='latest'(작성 최신순) 또는 'meal_time'(식사 시각 빠른순), 동률 시 post_id 내림차순.
    잘못된 필터·정렬·페이지 값은 ValueError.
    반환 키: post_id, user_id, nickname, title, body, region, food_category,
            meal_time, capacity, status, created_at, current_count, rating,
            like_count, comment_count"""
    if region is not None and region not in ALLOWED_REGIONS:
        raise ValueError(f"잘못된 지역 값입니다: {region}")

    if food_category is not None and food_category not in ALLOWED_FOOD_CATEGORIES:
        raise ValueError(f"잘못된 음식 종류 값입니다: {food_category}")

    if status is not None and status not in ALLOWED_FEED_STATUSES:
        raise ValueError(f"피드에서 허용되지 않는 상태 값입니다: {status}")

    if sort not in ALLOWED_SORTS:
        raise ValueError(f"잘못된 정렬 기준입니다: {sort}")

    if isinstance(limit, bool) or not isinstance(limit, int) or not (1 <= limit <= 100):
        raise ValueError("limit은 1~100 사이의 정수여야 합니다.")

    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset은 0 이상의 정수여야 합니다.")

    where_clauses = ["p.status IN ('OPEN', 'CLOSED')"]
    params: list = []

    if region is not None:
        where_clauses.append("p.region = %s")
        params.append(region)

    if food_category is not None:
        where_clauses.append("p.food_category = %s")
        params.append(food_category)

    if status is not None:
        where_clauses.append("p.status = %s")
        params.append(status)

    clean_keyword = (keyword or "").strip()
    if clean_keyword:
        where_clauses.append("(c.title LIKE %s OR c.body LIKE %s)")
        like_pattern = f"%{clean_keyword}%"
        params.extend([like_pattern, like_pattern])

    order_by = (
        "p.meal_time ASC, p.post_id DESC"
        if sort == "meal_time"
        else "p.created_at DESC, p.post_id DESC"
    )

    sql = f"""
        SELECT
            p.post_id,
            p.user_id,
            u.nickname,
            c.title,
            c.body,
            p.region,
            p.food_category,
            p.meal_time,
            p.capacity,
            p.status,
            p.created_at,
            (
                SELECT COUNT(*)
                FROM Participation pa
                WHERE pa.post_id = p.post_id AND pa.status = 'ACCEPTED'
            ) + 1 AS current_count,
            (
                SELECT AVG(r.rating)
                FROM Review r
                WHERE r.reviewee_id = p.user_id
            ) AS rating,
            (
                SELECT COUNT(*)
                FROM `Like` l
                WHERE l.post_id = p.post_id
            ) AS like_count,
            (
                SELECT COUNT(*)
                FROM Comment cm
                WHERE cm.post_id = p.post_id
            ) AS comment_count
        FROM Post p
        JOIN Content c ON c.post_id = p.post_id
        JOIN `User` u ON u.user_id = p.user_id
        WHERE {" AND ".join(where_clauses)}
        ORDER BY {order_by}
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])

    rows = query(sql, tuple(params))
    return [_format_post_row(row) for row in rows]


def get_post(post_id: int, viewer_id: int | None = None) -> dict | None:
    """게시물 상세 조회. 글이 없으면 None.
    viewer_id는 현재 로그인 사용자 ID(비로그인 조회면 None -> 두 bool 값은 False).
    반환 키: list_posts 기본 키 + is_liked, is_following_author"""
    valid_post_id = _validate_positive_int(post_id, "post_id")

    valid_viewer_id = None
    if viewer_id is not None:
        valid_viewer_id = _validate_positive_int(viewer_id, "viewer_id")

    sql = """
        SELECT
            p.post_id,
            p.user_id,
            u.nickname,
            c.title,
            c.body,
            p.region,
            p.food_category,
            p.meal_time,
            p.capacity,
            p.status,
            p.created_at,
            (
                SELECT COUNT(*)
                FROM Participation pa
                WHERE pa.post_id = p.post_id AND pa.status = 'ACCEPTED'
            ) + 1 AS current_count,
            (
                SELECT AVG(r.rating)
                FROM Review r
                WHERE r.reviewee_id = p.user_id
            ) AS rating,
            (
                SELECT COUNT(*)
                FROM `Like` l
                WHERE l.post_id = p.post_id
            ) AS like_count,
            (
                SELECT COUNT(*)
                FROM Comment cm
                WHERE cm.post_id = p.post_id
            ) AS comment_count
        FROM Post p
        JOIN Content c ON c.post_id = p.post_id
        JOIN `User` u ON u.user_id = p.user_id
        WHERE p.post_id = %s
    """
    row = query_one(sql, (valid_post_id,))
    if row is None:
        return None

    post = _format_post_row(row)

    is_liked = False
    is_following_author = False

    if valid_viewer_id is not None:
        liked_row = query_one(
            "SELECT 1 AS ok FROM `Like` WHERE post_id = %s AND user_id = %s",
            (valid_post_id, valid_viewer_id),
        )
        is_liked = liked_row is not None

        follow_row = query_one(
            "SELECT 1 AS ok FROM Follow WHERE follower_id = %s AND followee_id = %s",
            (valid_viewer_id, post["user_id"]),
        )
        is_following_author = follow_row is not None

    post["is_liked"] = is_liked
    post["is_following_author"] = is_following_author
    return post


def create_post(user_id: int, payload: dict) -> int:
    """새 모집 글을 Post와 Content에 한 트랜잭션으로 저장하고 생성된 post_id(int)를 반환한다.
    초기 상태는 OPEN이며 작성자는 Participation에 별도 행을 만들지 않는다.
    입력값 오류는 ValueError, 존재하지 않는 회원이면 LookupError."""
    valid_user_id = _validate_positive_int(user_id, "user_id")

    if not isinstance(payload, dict):
        raise ValueError("게시물 입력 형식이 올바르지 않습니다.")

    title = (payload.get("title") or "").strip()
    body = (payload.get("body") or "").strip()
    capacity = payload.get("capacity")
    meal_time = payload.get("meal_time")
    region = payload.get("region")
    food_category = payload.get("food_category")

    if not title or len(title) > 100:
        raise ValueError("제목은 공백 제외 1자 이상 100자 이하여야 합니다.")

    if not body or len(body.encode("utf-8")) > 65535:
        raise ValueError("본문은 공백 제외 필수이며 UTF-8 기준 65,535바이트 이하여야 합니다.")

    if isinstance(capacity, bool) or not isinstance(capacity, int) or not (2 <= capacity <= 20):
        raise ValueError("정원(capacity)은 2~20 사이의 정수여야 합니다.")

    if not isinstance(meal_time, datetime):
        raise ValueError("meal_time은 datetime 객체여야 합니다.")

    if meal_time <= datetime.now():
        raise ValueError("식사 시간(meal_time)은 현재 시각보다 미래여야 합니다.")

    if region not in ALLOWED_REGIONS:
        raise ValueError(f"허용되지 않는 지역입니다: {region}")

    if food_category not in ALLOWED_FOOD_CATEGORIES:
        raise ValueError(f"허용되지 않는 음식 종류입니다: {food_category}")

    user_row = query_one("SELECT user_id FROM `User` WHERE user_id = %s", (valid_user_id,))
    if user_row is None:
        raise LookupError(f"존재하지 않는 회원입니다: user_id={valid_user_id}")

    with transaction() as cur:
        cur.execute(
            """
            INSERT INTO Post (user_id, capacity, region, meal_time, food_category, status)
            VALUES (%s, %s, %s, %s, %s, 'OPEN')
            """,
            (valid_user_id, capacity, region, meal_time, food_category),
        )
        post_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO Content (post_id, title, body)
            VALUES (%s, %s, %s)
            """,
            (post_id, title, body),
        )

    return int(post_id)

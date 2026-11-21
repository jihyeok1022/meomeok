"""
services/social_service.py - 댓글, 좋아요, 팔로우
소셜 규칙
- 댓글은 작성 시각 오름차순(created_at ASC, comment_id ASC)으로 조회한다.
- 좋아요와 팔로우는 토글이 아니라 목표 상태(liked / following: bool)를 받아 멱등하게 처리한다.
- Like는 MySQL 예약어이므로 SQL에서 항상 백틱(`Like`)으로 감싼다.
- 자기 자신은 팔로우할 수 없다(ValueError).
- 팔로워·팔로잉 목록 조회(get_followers, get_followings)는 user_service(1번)가 담당한다.
"""

from db import execute, query, query_one


def _validate_positive_int(value, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"유효하지 않은 {name}입니다.")
    return value


def _format_comment_row(row: dict) -> dict:
    return {
        "comment_id": int(row["comment_id"]),
        "post_id": int(row["post_id"]),
        "user_id": int(row["user_id"]),
        "nickname": row["nickname"],
        "content": row["content"],
        "created_at": row["created_at"],
    }


def list_comments(post_id: int) -> list[dict]:
    """특정 게시글의 댓글 목록 (작성 순: created_at ASC, comment_id ASC).
    댓글이나 게시물이 없으면 []을 반환한다.
    반환 키: comment_id, post_id, user_id, nickname, content, created_at"""
    valid_post_id = _validate_positive_int(post_id, "post_id")

    sql = """
        SELECT
            cm.comment_id,
            cm.post_id,
            cm.user_id,
            u.nickname,
            cm.content,
            cm.created_at
        FROM Comment cm
        JOIN `User` u ON u.user_id = cm.user_id
        WHERE cm.post_id = %s
        ORDER BY cm.created_at ASC, cm.comment_id ASC
    """
    rows = query(sql, (valid_post_id,))
    return [_format_comment_row(row) for row in rows]


def create_comment(post_id: int, user_id: int, content: str) -> dict:
    """댓글을 저장하고 생성된 CommentView 딕셔너리를 반환한다.
    내용 오류는 ValueError, 게시글이나 회원이 없으면 LookupError.
    반환 키: comment_id, post_id, user_id, nickname, content, created_at"""
    valid_post_id = _validate_positive_int(post_id, "post_id")
    valid_user_id = _validate_positive_int(user_id, "user_id")

    clean_content = (content or "").strip()
    if not clean_content or len(clean_content.encode("utf-8")) > 65535:
        raise ValueError("댓글 내용은 공백 제외 필수이며 UTF-8 기준 65,535바이트 이하여야 합니다.")

    post_row = query_one("SELECT post_id FROM Post WHERE post_id = %s", (valid_post_id,))
    if post_row is None:
        raise LookupError(f"존재하지 않는 게시글입니다: post_id={valid_post_id}")

    user_row = query_one("SELECT user_id FROM `User` WHERE user_id = %s", (valid_user_id,))
    if user_row is None:
        raise LookupError(f"존재하지 않는 회원입니다: user_id={valid_user_id}")

    comment_id = execute(
        """
        INSERT INTO Comment (user_id, post_id, content)
        VALUES (%s, %s, %s)
        """,
        (valid_user_id, valid_post_id, clean_content),
    )

    created = query_one(
        """
        SELECT
            cm.comment_id,
            cm.post_id,
            cm.user_id,
            u.nickname,
            cm.content,
            cm.created_at
        FROM Comment cm
        JOIN `User` u ON u.user_id = cm.user_id
        WHERE cm.comment_id = %s
        """,
        (comment_id,),
    )
    if created is None:
        raise RuntimeError("등록된 댓글을 조회할 수 없습니다.")

    return _format_comment_row(created)


def set_like(post_id: int, user_id: int, liked: bool) -> dict:
    """좋아요 추가(liked=True) 또는 해제(liked=False).
    이미 원하는 상태여도 중복 에러 없이 성공 처리한다.
    게시글이나 회원이 없으면 LookupError.
    반환 키: is_liked, like_count"""
    valid_post_id = _validate_positive_int(post_id, "post_id")
    valid_user_id = _validate_positive_int(user_id, "user_id")

    if not isinstance(liked, bool):
        raise ValueError("liked 값은 bool(True/False)이어야 합니다.")

    post_row = query_one("SELECT post_id FROM Post WHERE post_id = %s", (valid_post_id,))
    if post_row is None:
        raise LookupError(f"존재하지 않는 게시글입니다: post_id={valid_post_id}")

    user_row = query_one("SELECT user_id FROM `User` WHERE user_id = %s", (valid_user_id,))
    if user_row is None:
        raise LookupError(f"존재하지 않는 회원입니다: user_id={valid_user_id}")

    if liked:
        execute(
            """
            INSERT IGNORE INTO `Like` (user_id, post_id)
            VALUES (%s, %s)
            """,
            (valid_user_id, valid_post_id),
        )
    else:
        execute(
            """
            DELETE FROM `Like`
            WHERE user_id = %s AND post_id = %s
            """,
            (valid_user_id, valid_post_id),
        )

    count_row = query_one(
        "SELECT COUNT(*) AS cnt FROM `Like` WHERE post_id = %s",
        (valid_post_id,),
    )
    is_liked_row = query_one(
        "SELECT 1 AS ok FROM `Like` WHERE post_id = %s AND user_id = %s",
        (valid_post_id, valid_user_id),
    )

    return {
        "is_liked": is_liked_row is not None,
        "like_count": int(count_row["cnt"]) if count_row else 0,
    }


def set_follow(follower_id: int, followee_id: int, following: bool) -> dict:
    """팔로우 추가(following=True) 또는 해제(following=False).
    이미 원하는 상태여도 중복 에러 없이 성공 처리한다.
    자기 자신 팔로우는 ValueError, 대상 회원이 없으면 LookupError.
    반환 키: is_following"""
    valid_follower_id = _validate_positive_int(follower_id, "follower_id")
    valid_followee_id = _validate_positive_int(followee_id, "followee_id")

    if not isinstance(following, bool):
        raise ValueError("following 값은 bool(True/False)이어야 합니다.")

    if valid_follower_id == valid_followee_id:
        raise ValueError("자기 자신은 팔로우할 수 없습니다.")

    follower_row = query_one("SELECT user_id FROM `User` WHERE user_id = %s", (valid_follower_id,))
    if follower_row is None:
        raise LookupError(f"존재하지 않는 팔로워입니다: user_id={valid_follower_id}")

    followee_row = query_one("SELECT user_id FROM `User` WHERE user_id = %s", (valid_followee_id,))
    if followee_row is None:
        raise LookupError(f"존재하지 않는 팔로우 대상 회원입니다: user_id={valid_followee_id}")

    if following:
        execute(
            """
            INSERT IGNORE INTO Follow (follower_id, followee_id)
            VALUES (%s, %s)
            """,
            (valid_follower_id, valid_followee_id),
        )
    else:
        execute(
            """
            DELETE FROM Follow
            WHERE follower_id = %s AND followee_id = %s
            """,
            (valid_follower_id, valid_followee_id),
        )

    is_following_row = query_one(
        "SELECT 1 AS ok FROM Follow WHERE follower_id = %s AND followee_id = %s",
        (valid_follower_id, valid_followee_id),
    )
    return {"is_following": is_following_row is not None}

"""
services/review_service.py - 리뷰 작성과 조회

리뷰 규칙
- 식사 완료(COMPLETED)된 모집 글에서만 쓸 수 있다.
- 작성자와 평가 대상 모두 그 모임 멤버(작성자 또는 ACCEPTED 참여자)여야 한다.
- 자기 자신은 평가할 수 없고, 같은 모임에서 같은 사람은 한 번만 평가한다.
- 별점은 1~5.
평균 별점(매너 점수)은 stats_service(4번)가 담당한다.
"""

import pymysql

from db import query, query_one, execute


class ReviewError(Exception):
    """화면에 그대로 보여줄 수 있는 오류 메시지를 담는다."""


def _is_member(post_id, user_id):
    """해당 모임의 작성자이거나 승인된 참여자인지 확인한다."""
    row = query_one(
        """SELECT 1 AS ok FROM Post WHERE post_id = %s AND user_id = %s
           UNION
           SELECT 1 FROM Participation
           WHERE post_id = %s AND user_id = %s AND status = 'ACCEPTED'""",
        (post_id, user_id, post_id, user_id),
    )
    return row is not None


def can_review(post_id, reviewer_id, reviewee_id):
    """리뷰를 쓸 수 있으면 (True, ""), 없으면 (False, 이유)를 반환한다."""
    post = query_one("SELECT status FROM Post WHERE post_id = %s", (post_id,))
    if post is None:
        return False, "존재하지 않는 모집 글입니다."
    if post["status"] != "COMPLETED":
        return False, "식사가 완료된 모임에서만 리뷰를 쓸 수 있습니다."
    if reviewer_id == reviewee_id:
        return False, "자기 자신은 평가할 수 없습니다."
    if not _is_member(post_id, reviewer_id) or not _is_member(post_id, reviewee_id):
        return False, "함께 식사한 멤버끼리만 리뷰를 쓸 수 있습니다."
    already = query_one(
        """SELECT 1 AS ok FROM Review
           WHERE post_id = %s AND reviewer_id = %s AND reviewee_id = %s""",
        (post_id, reviewer_id, reviewee_id),
    )
    if already:
        return False, "이미 이 모임에서 리뷰를 남겼습니다."
    return True, ""


def write_review(post_id, reviewer_id, reviewee_id, rating, content=""):
    """리뷰를 저장하고 review_id를 반환한다. 조건에 맞지 않으면 ReviewError."""
    rating = int(rating)
    if not 1 <= rating <= 5:
        raise ReviewError("별점은 1~5 사이로 선택해 주세요.")
    ok, reason = can_review(post_id, reviewer_id, reviewee_id)
    if not ok:
        raise ReviewError(reason)
    try:
        return execute(
            """INSERT INTO Review (reviewer_id, reviewee_id, post_id, rating, content)
               VALUES (%s, %s, %s, %s, %s)""",
            (reviewer_id, reviewee_id, post_id, rating, content.strip() or None),
        )
    except pymysql.IntegrityError as err:
        # 두 번 눌러서 동시에 저장된 경우 등
        raise ReviewError("이미 이 모임에서 리뷰를 남겼습니다.") from err


def get_received_reviews(user_id):
    """프로필의 '받은 리뷰' 목록 (최신순).
    반환 키: review_id, post_id, post_title, reviewer_id, reviewer_nickname,
            rating, content, created_at"""
    return query(
        """SELECT r.review_id, r.post_id, c.title AS post_title,
                  r.reviewer_id, u.nickname AS reviewer_nickname,
                  r.rating, r.content, r.created_at
           FROM Review r
           JOIN `User` u  ON u.user_id = r.reviewer_id
           JOIN Content c ON c.post_id = r.post_id
           WHERE r.reviewee_id = %s
           ORDER BY r.created_at DESC""",
        (user_id,),
    )


def get_written_reviews(user_id):
    """내가 쓴 리뷰 목록 (최신순).
    반환 키: review_id, post_id, post_title, reviewee_id, reviewee_nickname,
            rating, content, created_at"""
    return query(
        """SELECT r.review_id, r.post_id, c.title AS post_title,
                  r.reviewee_id, u.nickname AS reviewee_nickname,
                  r.rating, r.content, r.created_at
           FROM Review r
           JOIN `User` u  ON u.user_id = r.reviewee_id
           JOIN Content c ON c.post_id = r.post_id
           WHERE r.reviewer_id = %s
           ORDER BY r.created_at DESC""",
        (user_id,),
    )


def get_reviewable_mates(user_id):
    """아직 리뷰하지 않은 식사 메이트 (리뷰 쓰기 화면용).
    내가 멤버인 COMPLETED 모임에서, 나를 제외한 멤버 중 아직 평가하지 않은 사람.
    반환 키: post_id, post_title, meal_time, mate_id, mate_nickname"""
    return query(
        """SELECT p.post_id, c.title AS post_title, p.meal_time,
                  u.user_id AS mate_id, u.nickname AS mate_nickname
           FROM Post p
           JOIN Content c ON c.post_id = p.post_id
           JOIN (SELECT post_id, user_id FROM Post
                 UNION
                 SELECT post_id, user_id FROM Participation WHERE status = 'ACCEPTED') mate
             ON mate.post_id = p.post_id
           JOIN `User` u ON u.user_id = mate.user_id
           WHERE p.status = 'COMPLETED'
             AND mate.user_id <> %s
             AND (p.user_id = %s
                  OR EXISTS (SELECT 1 FROM Participation me
                              WHERE me.post_id = p.post_id AND me.user_id = %s
                                AND me.status = 'ACCEPTED'))
             AND NOT EXISTS (SELECT 1 FROM Review r
                              WHERE r.post_id = p.post_id
                                AND r.reviewer_id = %s
                                AND r.reviewee_id = mate.user_id)
           ORDER BY p.meal_time DESC, u.nickname""",
        (user_id, user_id, user_id, user_id),
    )

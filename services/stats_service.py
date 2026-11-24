"""머먹 통계 서비스: 인기 게시글 및 회원 평점 조회."""
from db import query, query_one


def get_popular_posts(limit=3):
    """좋아요가 있는 게시글을 좋아요 수 내림차순으로 조회한다."""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError('limit은 양의 정수여야 합니다.')
    return query("""
        SELECT p.post_id, c.title, p.user_id, u.nickname,
               p.created_at, COUNT(l.user_id) AS like_count
        FROM Post p
        JOIN Content c ON c.post_id = p.post_id
        JOIN `User` u ON u.user_id = p.user_id
        JOIN `Like` l ON l.post_id = p.post_id
        GROUP BY p.post_id, c.title, p.user_id, u.nickname, p.created_at
        ORDER BY like_count DESC, p.created_at ASC, p.post_id ASC
        LIMIT %s
    """, (limit,))


def get_user_average_rating(user_id):
    """받은 리뷰의 평균 별점을 float로 반환한다. 리뷰가 없으면 None."""
    row = query_one("""
        SELECT AVG(rating) AS avg_rating
        FROM Review
        WHERE reviewee_id = %s
    """, (user_id,))
    if row is None or row['avg_rating'] is None:
        return None
    return float(row['avg_rating'])


def get_user_rating_stats(user_id):
    """회원의 평균 별점과 리뷰 수를 조회한다. 없는 회원은 None."""
    row = query_one("""
        SELECT u.user_id, u.nickname, AVG(r.rating) AS avg_rating,
               COUNT(r.review_id) AS review_count
        FROM `User` u
        LEFT JOIN Review r ON r.reviewee_id = u.user_id
        WHERE u.user_id = %s
        GROUP BY u.user_id, u.nickname
    """, (user_id,))
    if row is not None and row['avg_rating'] is not None:
        row['avg_rating'] = float(row['avg_rating'])
    return row

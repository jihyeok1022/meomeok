"""
services/user_service.py - 프로필 조회와 수정

반환 형식: 딕셔너리 (목록은 딕셔너리 리스트)
평균 별점은 stats_service(4번), 팔로우 추가·취소는 social_service(2번)가 담당한다.
"""

import pymysql

from db import query, query_one, execute, transaction


def get_profile(user_id):
    """프로필 화면 상단 정보. 회원이 없으면 None.
    반환 키: user_id, login_id, gachon_email, name, nickname, birth_year, neighborhood,
            food_preference, favorite_food, bio, follower_count, following_count, post_count"""
    return query_one(
        """SELECT u.user_id, u.login_id, u.gachon_email, u.name, u.nickname,
                  u.birth_year, u.neighborhood,
                  p.food_preference, p.favorite_food, p.bio,
                  (SELECT COUNT(*) FROM Follow f WHERE f.followee_id = u.user_id) AS follower_count,
                  (SELECT COUNT(*) FROM Follow f WHERE f.follower_id = u.user_id) AS following_count,
                  (SELECT COUNT(*) FROM Post po WHERE po.user_id = u.user_id)     AS post_count
           FROM `User` u
           LEFT JOIN Profile p ON p.user_id = u.user_id
           WHERE u.user_id = %s""",
        (user_id,),
    )


def update_profile(user_id, neighborhood, food_preference, favorite_food, bio):
    """동네(User)와 음식 취향·선호 음식·자기소개(Profile)를 수정한다."""
    with transaction() as cur:
        cur.execute("UPDATE `User` SET neighborhood = %s WHERE user_id = %s",
                    (neighborhood.strip(), user_id))
        # 프로필 행이 없던 회원도 처리 (있으면 수정, 없으면 생성)
        cur.execute(
            """INSERT INTO Profile (user_id, food_preference, favorite_food, bio)
               VALUES (%s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
                 food_preference = VALUES(food_preference),
                 favorite_food   = VALUES(favorite_food),
                 bio             = VALUES(bio)""",
            (user_id, food_preference or None, favorite_food or None, bio or None),
        )


def update_nickname(user_id, nickname):
    """닉네임 변경. 이미 쓰는 닉네임이면 ValueError."""
    try:
        execute("UPDATE `User` SET nickname = %s WHERE user_id = %s", (nickname.strip(), user_id))
    except pymysql.IntegrityError as err:
        raise ValueError("이미 사용 중인 닉네임입니다.") from err


def get_user_posts(user_id):
    """프로필의 '작성한 포스트' 목록 (최신순).
    반환 키: post_id, title, body, region, meal_time, food_category, status, capacity,
            current_count, like_count, comment_count, created_at"""
    return query(
        """SELECT p.post_id, c.title, c.body, p.region, p.meal_time, p.food_category,
                  p.status, p.capacity, p.created_at,
                  (SELECT COUNT(*) FROM Participation pa
                    WHERE pa.post_id = p.post_id AND pa.status = 'ACCEPTED') + 1 AS current_count,
                  (SELECT COUNT(*) FROM `Like` l   WHERE l.post_id = p.post_id)  AS like_count,
                  (SELECT COUNT(*) FROM Comment cm WHERE cm.post_id = p.post_id) AS comment_count
           FROM Post p
           JOIN Content c ON c.post_id = p.post_id
           WHERE p.user_id = %s
           ORDER BY p.created_at DESC""",
        (user_id,),
    )


def get_followers(user_id):
    """나를 팔로우하는 회원 목록. 반환 키: user_id, nickname, neighborhood, followed_at"""
    return query(
        """SELECT u.user_id, u.nickname, u.neighborhood, f.created_at AS followed_at
           FROM Follow f
           JOIN `User` u ON u.user_id = f.follower_id
           WHERE f.followee_id = %s
           ORDER BY f.created_at DESC""",
        (user_id,),
    )


def get_followings(user_id):
    """내가 팔로우하는 회원 목록. 반환 키: user_id, nickname, neighborhood, followed_at"""
    return query(
        """SELECT u.user_id, u.nickname, u.neighborhood, f.created_at AS followed_at
           FROM Follow f
           JOIN `User` u ON u.user_id = f.followee_id
           WHERE f.follower_id = %s
           ORDER BY f.created_at DESC""",
        (user_id,),
    )

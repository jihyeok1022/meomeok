-- =========================================================
-- 머먹 (Meal Mate) - 03. 조회 쿼리
-- 아래 @변수는 데모용이다. 앱에서는 같은 자리에 ? 플레이스홀더를 쓰고
-- 파라미터로 값을 넘긴다 (문자열 연결 금지: SQL injection 방지).
-- 집계가 여러 개인 쿼리는 서브쿼리로 따로 계산해 JOIN 시 행이 곱해지지 않게 한다.
-- =========================================================
USE meal_mate;
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

SET @me   = 1;   -- 로그인한 회원 (지혁)
SET @post = 2;   -- 상세 보기 중인 게시글

-- ---------------------------------------------------------
-- [필수 1] 전체 게시글 목록 (최신순)
-- ---------------------------------------------------------
SELECT p.post_id,
       c.title,
       u.nickname                          AS author,
       p.region, p.food_category, p.meal_time,
       (SELECT COUNT(*) FROM Participation pa
         WHERE pa.post_id = p.post_id AND pa.status = 'ACCEPTED') + 1 AS current_count,
       p.capacity,
       p.status,
       p.created_at
FROM Post p
JOIN Content c ON c.post_id = p.post_id
JOIN `User` u  ON u.user_id = p.user_id
ORDER BY p.created_at DESC;

-- ---------------------------------------------------------
-- [필수 2] 게시글별 좋아요 수 (좋아요 0개인 글도 포함)
-- ---------------------------------------------------------
SELECT p.post_id,
       c.title,
       COUNT(l.user_id) AS like_count
FROM Post p
JOIN Content c     ON c.post_id = p.post_id
LEFT JOIN `Like` l ON l.post_id = p.post_id
GROUP BY p.post_id, c.title
ORDER BY like_count DESC, p.post_id;

-- ---------------------------------------------------------
-- [필수 3] 특정 게시글의 댓글 목록 (작성 순)
-- ---------------------------------------------------------
SELECT cm.comment_id,
       u.nickname AS writer,
       cm.content,
       cm.created_at
FROM Comment cm
JOIN `User` u ON u.user_id = cm.user_id
WHERE cm.post_id = @post
ORDER BY cm.created_at;

-- ---------------------------------------------------------
-- [필수 4] 특정 회원이 좋아요한 게시글
-- ---------------------------------------------------------
SELECT p.post_id,
       c.title,
       u.nickname   AS author,
       l.created_at AS liked_at
FROM `Like` l
JOIN Post p    ON p.post_id = l.post_id
JOIN Content c ON c.post_id = p.post_id
JOIN `User` u  ON u.user_id = p.user_id
WHERE l.user_id = @me
ORDER BY l.created_at DESC;

-- ---------------------------------------------------------
-- [필수 5] 내가 팔로우한 회원들의 게시글 피드 (최신순)
-- ---------------------------------------------------------
SELECT p.post_id,
       u.nickname AS author,
       c.title,
       p.meal_time,
       p.status,
       p.created_at
FROM Follow f
JOIN Post p    ON p.user_id = f.followee_id
JOIN Content c ON c.post_id = p.post_id
JOIN `User` u  ON u.user_id = p.user_id
WHERE f.follower_id = @me
ORDER BY p.created_at DESC;

-- ---------------------------------------------------------
-- [필수 6] 좋아요가 가장 많은 게시글 Top 3
--          (동점이면 먼저 작성된 글 우선)
-- ---------------------------------------------------------
SELECT p.post_id,
       c.title,
       COUNT(l.user_id) AS like_count
FROM Post p
JOIN Content c ON c.post_id = p.post_id
JOIN `Like` l  ON l.post_id = p.post_id
GROUP BY p.post_id, c.title, p.created_at
ORDER BY like_count DESC, p.created_at
LIMIT 3;

-- =========================================================
-- 팀 주제(밥친구 모집) 전용 쿼리
-- =========================================================

-- ---------------------------------------------------------
-- [주제 1] 지역별 모집 중인 글과 남은 자리
--          남은 자리 = 정원 - 작성자 1명 - 승인 인원
-- ---------------------------------------------------------
SET @region = '교내';

SELECT p.post_id,
       c.title,
       u.nickname AS host,
       p.meal_time,
       p.food_category,
       p.capacity - 1 - COALESCE(a.accepted, 0) AS seats_left
FROM Post p
JOIN Content c ON c.post_id = p.post_id
JOIN `User` u  ON u.user_id = p.user_id
LEFT JOIN (SELECT post_id, COUNT(*) AS accepted
           FROM Participation
           WHERE status = 'ACCEPTED'
           GROUP BY post_id) a ON a.post_id = p.post_id
WHERE p.status = 'OPEN'
  AND p.region = @region
  AND p.meal_time > NOW()
  AND p.capacity - 1 - COALESCE(a.accepted, 0) > 0
ORDER BY p.meal_time;

-- ---------------------------------------------------------
-- [주제 2] 회원별 매너 점수 (받은 리뷰 평균 별점, 리뷰 수)
-- ---------------------------------------------------------
SELECT u.user_id,
       u.nickname,
       ROUND(AVG(r.rating), 1) AS avg_rating,
       COUNT(r.review_id)      AS review_count
FROM `User` u
LEFT JOIN Review r ON r.reviewee_id = u.user_id
GROUP BY u.user_id, u.nickname
ORDER BY avg_rating DESC, review_count DESC;

-- ---------------------------------------------------------
-- [주제 3] 내가 모집한 글에 들어온 대기 중 신청자 (승인/거절 화면)
--          신청자의 매너 점수를 함께 보여준다.
-- ---------------------------------------------------------
SET @host = 5;   -- 민지

SELECT p.post_id,
       c.title,
       u.nickname AS applicant,
       (SELECT ROUND(AVG(r.rating), 1) FROM Review r
         WHERE r.reviewee_id = u.user_id) AS applicant_rating,
       pa.applied_at
FROM Post p
JOIN Content c        ON c.post_id = p.post_id
JOIN Participation pa ON pa.post_id = p.post_id
JOIN `User` u         ON u.user_id = pa.user_id
WHERE p.user_id = @host
  AND pa.status = 'PENDING'
ORDER BY pa.applied_at;

-- ---------------------------------------------------------
-- [주제 4] 내 신청 · 참여 목록과 화면 버튼 상태
-- ---------------------------------------------------------
SELECT p.post_id,
       c.title,
       p.meal_time,
       pa.status AS my_status,
       p.status  AS post_status,
       CASE
         WHEN pa.status = 'PENDING'                               THEN '신청 취소'
         WHEN pa.status = 'ACCEPTED' AND p.status = 'COMPLETED'  THEN '리뷰 쓰기'
         WHEN pa.status = 'ACCEPTED' AND cr.room_id IS NOT NULL  THEN '톡방 가기'
         ELSE '보기만'
       END AS action
FROM Participation pa
JOIN Post p          ON p.post_id = pa.post_id
JOIN Content c       ON c.post_id = p.post_id
LEFT JOIN ChatRoom cr ON cr.post_id = p.post_id
WHERE pa.user_id = @me
ORDER BY p.meal_time DESC;

-- ---------------------------------------------------------
-- [주제 5] 내 톡방 목록과 마지막 메시지
-- ---------------------------------------------------------
SELECT cr.room_id,
       c.title,
       p.status,
       lm.content    AS last_message,
       lm.created_at AS last_message_at
FROM ChatMember m
JOIN ChatRoom cr ON cr.room_id = m.room_id
JOIN Post p      ON p.post_id = cr.post_id
JOIN Content c   ON c.post_id = p.post_id
LEFT JOIN Message lm
       ON lm.message_id = (SELECT m2.message_id FROM Message m2
                            WHERE m2.room_id = cr.room_id
                            ORDER BY m2.created_at DESC, m2.message_id DESC
                            LIMIT 1)
WHERE m.user_id = @me
ORDER BY last_message_at DESC;

-- ---------------------------------------------------------
-- [주제 6] 리뷰를 아직 남기지 않은 식사 메이트 (리뷰 쓰기 알림)
--          같은 COMPLETED 톡방 멤버 중 내가 평가하지 않은 사람
-- ---------------------------------------------------------
SELECT p.post_id,
       c.title,
       u.nickname AS mate
FROM ChatMember me
JOIN ChatRoom cr   ON cr.room_id = me.room_id
JOIN Post p        ON p.post_id = cr.post_id AND p.status = 'COMPLETED'
JOIN Content c     ON c.post_id = p.post_id
JOIN ChatMember mt ON mt.room_id = me.room_id AND mt.user_id <> me.user_id
JOIN `User` u      ON u.user_id = mt.user_id
WHERE me.user_id = @me
  AND NOT EXISTS (SELECT 1 FROM Review r
                   WHERE r.post_id = p.post_id
                     AND r.reviewer_id = me.user_id
                     AND r.reviewee_id = mt.user_id)
ORDER BY p.meal_time DESC;
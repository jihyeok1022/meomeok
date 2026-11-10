-- =========================================================
-- 머먹 (Meal Mate) - 01. 스키마
-- MySQL 8.0.16 이상 (CHECK 제약조건 적용)
-- 테이블 12개: User, Profile, Post, Content, Comment, `Like`,
--             Follow, Participation, Review, ChatRoom, ChatMember, Message
-- =========================================================

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

DROP DATABASE IF EXISTS meal_mate;
CREATE DATABASE meal_mate
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
USE meal_mate;

-- 1. User: 회원 -------------------------------------------
CREATE TABLE `User` (
  user_id        BIGINT UNSIGNED   NOT NULL AUTO_INCREMENT,
  login_id       VARCHAR(30)       NOT NULL,
  gachon_email   VARCHAR(100)      NOT NULL,
  password_hash  VARCHAR(255)      NOT NULL,
  name           VARCHAR(30)       NOT NULL,
  nickname       VARCHAR(30)       NOT NULL,
  birth_year     SMALLINT UNSIGNED NOT NULL,
  neighborhood   VARCHAR(30)       NOT NULL,
  PRIMARY KEY (user_id),
  CONSTRAINT uq_user_login_id UNIQUE (login_id),
  CONSTRAINT uq_user_email    UNIQUE (gachon_email),
  CONSTRAINT uq_user_nickname UNIQUE (nickname),
  CONSTRAINT chk_user_email      CHECK (gachon_email LIKE '%@gachon.ac.kr'),
  CONSTRAINT chk_user_birth_year CHECK (birth_year BETWEEN 1950 AND 2010)
);

-- 2. Profile: 프로필 (User와 1:1, user_id가 공유 PK 겸 FK) --
CREATE TABLE Profile (
  user_id          BIGINT UNSIGNED NOT NULL,
  food_preference  VARCHAR(100)    NULL,
  favorite_food    VARCHAR(50)     NULL,
  bio              VARCHAR(200)    NULL,
  PRIMARY KEY (user_id),
  CONSTRAINT fk_profile_user FOREIGN KEY (user_id)
    REFERENCES `User` (user_id) ON DELETE CASCADE
);

-- 3. Post: 모집 글 -----------------------------------------
--    capacity: 작성자 포함 정원
--    현재 인원 = 승인(ACCEPTED)된 Participation 수 + 작성자 1명
CREATE TABLE Post (
  post_id        BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
  user_id        BIGINT UNSIGNED  NOT NULL,
  capacity       TINYINT UNSIGNED NOT NULL,
  region         VARCHAR(10)      NOT NULL,
  meal_time      DATETIME         NOT NULL,
  food_category  VARCHAR(10)      NOT NULL,
  status         VARCHAR(10)      NOT NULL DEFAULT 'OPEN',
  created_at     DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (post_id),
  CONSTRAINT fk_post_user FOREIGN KEY (user_id)
    REFERENCES `User` (user_id) ON DELETE CASCADE,
  CONSTRAINT chk_post_capacity CHECK (capacity BETWEEN 2 AND 20),
  CONSTRAINT chk_post_region   CHECK (region IN ('교내', '복정동', '태평동', '기타')),
  CONSTRAINT chk_post_food     CHECK (food_category IN ('한식', '중식', '양식', '일식', '기타', '미정')),
  CONSTRAINT chk_post_status   CHECK (status IN ('OPEN', 'CLOSED', 'COMPLETED', 'CANCELED'))
);

-- 4. Content: 글 제목과 본문 (Post와 1:1) ------------------
CREATE TABLE Content (
  content_id  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  post_id     BIGINT UNSIGNED NOT NULL,
  title       VARCHAR(100)    NOT NULL,
  body        TEXT            NOT NULL,
  PRIMARY KEY (content_id),
  CONSTRAINT uq_content_post UNIQUE (post_id),
  CONSTRAINT fk_content_post FOREIGN KEY (post_id)
    REFERENCES Post (post_id) ON DELETE CASCADE
);

-- 5. Comment: 댓글 (Post 1:N, User 1:N) -------------------
CREATE TABLE Comment (
  comment_id  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id     BIGINT UNSIGNED NOT NULL,
  post_id     BIGINT UNSIGNED NOT NULL,
  content     TEXT            NOT NULL,
  created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (comment_id),
  CONSTRAINT fk_comment_user FOREIGN KEY (user_id)
    REFERENCES `User` (user_id) ON DELETE CASCADE,
  CONSTRAINT fk_comment_post FOREIGN KEY (post_id)
    REFERENCES Post (post_id) ON DELETE CASCADE
);

-- 6. Like: 좋아요 (User-Post N:M 연결 테이블) -------------
--    LIKE는 MySQL 예약어이므로 테이블명을 항상 백틱으로 감싼다.
CREATE TABLE `Like` (
  user_id     BIGINT UNSIGNED NOT NULL,
  post_id     BIGINT UNSIGNED NOT NULL,
  created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, post_id),                -- 한 사람이 한 글에 한 번만
  CONSTRAINT fk_like_user FOREIGN KEY (user_id)
    REFERENCES `User` (user_id) ON DELETE CASCADE,
  CONSTRAINT fk_like_post FOREIGN KEY (post_id)
    REFERENCES Post (post_id) ON DELETE CASCADE
);

-- 7. Follow: 팔로우 (User-User 자기참조 N:M) --------------
--    MySQL은 CHECK에 쓰인 컬럼의 FK에 CASCADE를 허용하지 않아 기본값(RESTRICT)을 사용한다.
CREATE TABLE Follow (
  follower_id  BIGINT UNSIGNED NOT NULL,
  followee_id  BIGINT UNSIGNED NOT NULL,
  created_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (follower_id, followee_id),
  CONSTRAINT fk_follow_follower FOREIGN KEY (follower_id)
    REFERENCES `User` (user_id),
  CONSTRAINT fk_follow_followee FOREIGN KEY (followee_id)
    REFERENCES `User` (user_id),
  CONSTRAINT chk_follow_self CHECK (follower_id <> followee_id)
);

-- 8. Participation: 참여 신청 (작성자는 포함하지 않음) -----
CREATE TABLE Participation (
  post_id     BIGINT UNSIGNED NOT NULL,
  user_id     BIGINT UNSIGNED NOT NULL,
  status      VARCHAR(10)     NOT NULL DEFAULT 'PENDING',
  applied_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (post_id, user_id),                -- 중복 신청 방지
  CONSTRAINT fk_part_post FOREIGN KEY (post_id)
    REFERENCES Post (post_id) ON DELETE CASCADE,
  CONSTRAINT fk_part_user FOREIGN KEY (user_id)
    REFERENCES `User` (user_id) ON DELETE CASCADE,
  CONSTRAINT chk_part_status CHECK (status IN ('PENDING', 'ACCEPTED', 'REJECTED', 'CANCELED'))
);

-- 9. Review: 함께 식사한 회원 평가 -------------------------
CREATE TABLE Review (
  review_id    BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
  reviewer_id  BIGINT UNSIGNED  NOT NULL,
  reviewee_id  BIGINT UNSIGNED  NOT NULL,
  post_id      BIGINT UNSIGNED  NOT NULL,
  rating       TINYINT UNSIGNED NOT NULL,
  content      TEXT             NULL,
  created_at   DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (review_id),
  CONSTRAINT uq_review_once UNIQUE (post_id, reviewer_id, reviewee_id),
  CONSTRAINT fk_review_reviewer FOREIGN KEY (reviewer_id)
    REFERENCES `User` (user_id),
  CONSTRAINT fk_review_reviewee FOREIGN KEY (reviewee_id)
    REFERENCES `User` (user_id),
  CONSTRAINT fk_review_post FOREIGN KEY (post_id)
    REFERENCES Post (post_id) ON DELETE CASCADE,
  CONSTRAINT chk_review_rating CHECK (rating BETWEEN 1 AND 5),
  CONSTRAINT chk_review_self   CHECK (reviewer_id <> reviewee_id)
);

-- 10. ChatRoom: 모임 톡방 (Post와 1:0..1) -----------------
CREATE TABLE ChatRoom (
  room_id     BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  post_id     BIGINT UNSIGNED NOT NULL,
  created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (room_id),
  CONSTRAINT uq_room_post UNIQUE (post_id),      -- 게시글당 톡방 1개
  CONSTRAINT fk_room_post FOREIGN KEY (post_id)
    REFERENCES Post (post_id) ON DELETE CASCADE
);

-- 11. ChatMember: 톡방 멤버 (작성자 + 승인된 참여자) -------
CREATE TABLE ChatMember (
  room_id    BIGINT UNSIGNED NOT NULL,
  user_id    BIGINT UNSIGNED NOT NULL,
  joined_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (room_id, user_id),
  CONSTRAINT fk_member_room FOREIGN KEY (room_id)
    REFERENCES ChatRoom (room_id) ON DELETE CASCADE,
  CONSTRAINT fk_member_user FOREIGN KEY (user_id)
    REFERENCES `User` (user_id) ON DELETE CASCADE
);

-- 12. Message: 톡방 메시지 --------------------------------
--    (room_id, user_id) 복합 FK로 톡방 멤버만 메시지를 저장할 수 있다.
CREATE TABLE Message (
  message_id  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  room_id     BIGINT UNSIGNED NOT NULL,
  user_id     BIGINT UNSIGNED NOT NULL,
  content     TEXT            NOT NULL,
  created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (message_id),
  CONSTRAINT fk_message_member FOREIGN KEY (room_id, user_id)
    REFERENCES ChatMember (room_id, user_id) ON DELETE CASCADE
);

-- 조회 경로용 인덱스 (보고서 6절) -------------------------
CREATE INDEX idx_post_user_created     ON Post (user_id, created_at);
CREATE INDEX idx_post_status_region    ON Post (status, region, meal_time);
CREATE INDEX idx_comment_post_created  ON Comment (post_id, created_at);
CREATE INDEX idx_review_reviewee       ON Review (reviewee_id, created_at);
CREATE INDEX idx_message_room_created  ON Message (room_id, created_at, message_id);
-- =========================================================
-- 머먹 (Meal Mate) - 04. 참여 승인 트랜잭션 (보고서 6절)
-- Post 행을 잠근 뒤 정원을 확인하고 승인한다.
-- 이번 승인으로 정원이 차면 모집 마감, 톡방 생성, 멤버 추가,
-- 남은 대기 신청 거절을 한 트랜잭션에서 처리한다.
-- =========================================================
USE meal_mate;
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

DROP PROCEDURE IF EXISTS accept_participation;

DELIMITER //
CREATE PROCEDURE accept_participation(IN p_host_id BIGINT UNSIGNED,
                                      IN p_post_id BIGINT UNSIGNED,
                                      IN p_user_id BIGINT UNSIGNED)
BEGIN
  DECLARE v_host     BIGINT UNSIGNED;
  DECLARE v_capacity TINYINT UNSIGNED;
  DECLARE v_status   VARCHAR(10);
  DECLARE v_accepted INT;
  DECLARE v_room_id  BIGINT UNSIGNED;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  START TRANSACTION;

  -- 1) 게시글 행 잠금: 동시에 마지막 자리를 승인해도 정원을 넘지 않는다.
  SELECT user_id, capacity, status
    INTO v_host, v_capacity, v_status
  FROM Post
  WHERE post_id = p_post_id
  FOR UPDATE;

  IF v_host IS NULL OR v_host <> p_host_id THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '작성자만 승인할 수 있습니다.';
  END IF;

  IF v_status <> 'OPEN' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '모집 중인 글이 아닙니다.';
  END IF;

  -- 2) 현재 승인 인원과 정원 확인 (작성자 1명 포함)
  SELECT COUNT(*) INTO v_accepted
  FROM Participation
  WHERE post_id = p_post_id AND status = 'ACCEPTED';

  IF v_accepted + 1 >= v_capacity THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '정원이 가득 찼습니다.';
  END IF;

  -- 3) 대기 중인 신청만 승인
  UPDATE Participation
  SET status = 'ACCEPTED'
  WHERE post_id = p_post_id AND user_id = p_user_id AND status = 'PENDING';

  IF ROW_COUNT() = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '대기 중인 신청이 없습니다.';
  END IF;

  -- 4) 이번 승인으로 정원이 찼으면 마감 처리
  IF v_accepted + 2 = v_capacity THEN
    UPDATE Post SET status = 'CLOSED' WHERE post_id = p_post_id;

    INSERT INTO ChatRoom (post_id) VALUES (p_post_id);
    SET v_room_id = LAST_INSERT_ID();

    INSERT INTO ChatMember (room_id, user_id) VALUES (v_room_id, v_host);
    INSERT INTO ChatMember (room_id, user_id)
      SELECT v_room_id, user_id
      FROM Participation
      WHERE post_id = p_post_id AND status = 'ACCEPTED';

    UPDATE Participation
    SET status = 'REJECTED'
    WHERE post_id = p_post_id AND status = 'PENDING';
  END IF;

  COMMIT;
END //
DELIMITER ;

-- ---------------------------------------------------------
-- 시연 예시 (실행하면 데이터가 바뀌므로 필요할 때만 주석 해제)
-- 3번 글(지혁, 정원 3, 승인 1명)에서 민지(5)를 승인하면
-- 정원이 차서 CLOSED가 되고 톡방이 생성된다.
-- ---------------------------------------------------------
-- CALL accept_participation(1, 3, 5);
-- SELECT post_id, status FROM Post WHERE post_id = 3;
-- SELECT cr.room_id, m.user_id FROM ChatRoom cr
--   JOIN ChatMember m ON m.room_id = cr.room_id WHERE cr.post_id = 3;

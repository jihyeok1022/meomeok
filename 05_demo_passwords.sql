-- =========================================================
-- 머먹 (Meal Mate) - 05. 시연용 비밀번호 설정
-- 02의 샘플 회원 해시는 데모 문자열이라 실제 로그인이 안 된다.
-- 이 파일을 실행하면 샘플 회원 5명 모두 비밀번호 pass1234로 로그인할 수 있다.
-- (아래 값은 bcrypt로 만든 'pass1234'의 해시)
-- =========================================================
USE meal_mate;

UPDATE `User`
SET password_hash = '$2b$12$4k/JznOswbNxy/BSVC0AWOXJnCPw7VRgQR8S0cmKLDPcDFtYbkS3O'
WHERE user_id BETWEEN 1 AND 5;

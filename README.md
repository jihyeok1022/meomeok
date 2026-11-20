# meomeok
데이터베이스 프로젝트 E조

1번 2번 3번 순차적으로 실행

서관우 — 백엔드: DB 연결·로그인·프로필·리뷰
파일: db.py, auth.py, services/user_service.py, services/review_service.py, requirements.txt, .gitignore, .streamlit/secrets.toml.example, README.md

이서준 — 백엔드: 게시물·댓글·좋아요·팔로우
파일: services/post_service.py, services/social_service.py

박준혁 — 백엔드: 참여 신청·승인·마감·톡방·메시지
파일: services/participation_service.py, services/chat_service.py

황윤탁 — 백엔드: 인기 글·평균 평점 조회 + PPT 제작·발표
파일: services/stats_service.py, docs/발표자료.pptx

차지혁 — 프론트: 로그인·게시물·댓글·좋아요·팔로우 화면
파일: app.py, pages/1_feed.py, pages/2_write_post.py, pages/3_post_detail.py

권지은 — 프론트: 프로필·리뷰·참여 관리·채팅 화면
파일: pages/4_profile.py, pages/5_participation.py, pages/6_chat.py

## 공통 개발 규칙

각 기능의 세부 함수는 담당자가 구현하면서 정하고, 다른 담당자가 사용할 함수는 README에 이름·입력값·반환값을 추가해 주세요.

### 공통 함수

| 위치 | 함수 | 설명 | 반환값 |
|---|---|---|---|
| `db.py` | `get_connection()` | MySQL 연결 생성 | DB 연결 객체 |
| `auth.py` | `login(login_id, password)` | 아이디·비밀번호 확인 | 성공 시 사용자 정보, 실패 시 `None` |
| `auth.py` | `get_current_user()` | 현재 로그인한 사용자 조회 | 사용자 정보 또는 `None` |
| `auth.py` | `require_login()` | 로그인 여부 확인 | 로그인 상태면 사용자 정보 반환, 아니면 안내 후 화면 실행 중단 |
| `auth.py` | `logout()` | 로그인 정보 삭제 | 없음 |

로그인 성공 시 사용자 정보는 아래 형식으로 통일합니다.

```python
{"user_id": 1, "nickname": "철수"}
```

- 로그인 정보는 `st.session_state["user"]`에 저장합니다.
- `login()`은 인증 결과만 반환하고, 로그인 화면에서 세션에 저장합니다.
- `get_current_user()`, `require_login()`, `logout()`은 같은 세션 값을 사용합니다.

### 기본 약속

- 여러 건 조회는 `list[dict]`, 한 건 조회는 `dict`로 반환합니다.
- 조회 결과가 없으면 여러 건은 `[]`, 한 건은 `None`을 반환합니다.
- DB 날짜·시간은 Python `datetime`으로 전달하고, 화면에서 표시 형식을 정합니다.
- DB 연결을 연 쪽에서 연결을 닫고, 저장 작업을 수행하는 백엔드 함수에서 `commit`·`rollback`을 처리합니다.
- 권한·중복·정원 등 업무 규칙은 백엔드에서 검사합니다.
- 공통 인증 함수를 제외한 백엔드 함수에서는 `st.*`를 사용하지 않습니다.
- 함수 이름이나 반환 형식을 바꾸면 사용하는 담당자에게 먼저 공유합니다.

※ 참여 서비스 파일 위치는 `services/participation_service.py`로 통일합니다.

## 프론트엔드 실행 방법

프로젝트의 `meomeok` 폴더에서 다음 명령어를 실행합니다.

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

- 앱은 `app.py`로 실행합니다. `pages/` 안의 화면 파일은 개별 실행하지 않습니다.
- 공통 화면 스타일과 아이콘 로딩은 `ui_common.py`, 아이콘 파일은 `assets/`에서 관리합니다.
- 백엔드 연결 전까지 `demo_data.py`의 예시 데이터를 사용합니다.
- 피드·상세 화면의 댓글·좋아요·팔로우·참여 신청은 현재 세션에만 반영됩니다.
- 글쓰기 화면은 입력 검사와 미리보기까지 지원하며, 실제 DB에 글을 저장하지 않습니다.
- 실제 인증과 프로필·참여 관리·채팅 기능은 각 담당자의 구현과 연결이 필요합니다.

## API 명세서

[프론트엔드 연동 API 명세서](README_API.md)

화면에서 사용하는 데이터 형식, 서비스 함수의 입력·반환값, 검증 규칙과 담당자를 정리했습니다. 아직 합의되지 않은 서비스 함수는 연동 제안으로 표시했습니다.

## DB 준비와 전체 실행 방법

### 1) 데이터베이스 만들기

MySQL Workbench 등에서 아래 순서대로 실행합니다.

| 순서 | 파일 | 내용 |
|---|---|---|
| 1 | `01_create_tables.sql` | DB와 12개 테이블 생성 (기존 `meal_mate` DB는 삭제됨) |
| 2 | `02_insert_sample_data.sql` | 샘플 데이터 (회원 5, 게시글 10, 댓글 15, 좋아요 10, 팔로우 10) |
| 3 | `04_accept_transaction.sql` | 참여 승인 프로시저 `accept_participation` |
| 4 | `05_demo_passwords.sql` | 샘플 회원 비밀번호를 `pass1234`로 설정 (시연 로그인용) |

`03_select_queries.sql`은 제출용 조회 쿼리 모음이라 앱 실행에는 필요 없습니다.
데이터를 처음 상태로 되돌리려면 `01`부터 다시 실행합니다.

### 2) DB 접속 정보 설정

`.streamlit/secrets.toml.example`을 같은 폴더에 `secrets.toml`로 복사한 뒤, 내 MySQL 사용자와 비밀번호로 바꿉니다.

```powershell
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
```

`secrets.toml`은 `.gitignore`에 들어 있어 GitHub에 올라가지 않습니다. **절대 커밋하지 마세요.**

### 3) 시연용 계정

`05_demo_passwords.sql` 실행 후 비밀번호는 모두 `pass1234`입니다. 아이디 대신 가천 이메일로도 로그인됩니다.

| user_id | 아이디 | 이메일 | 닉네임 |
|---|---|---|---|
| 1 | jihyeok03 | jihyeok@gachon.ac.kr | 지혁 |
| 2 | doyun02 | doyun@gachon.ac.kr | 도윤 |
| 3 | sumin04 | sumin@gachon.ac.kr | 수민 |
| 4 | seoyeon03 | seoyeon@gachon.ac.kr | 서연 |
| 5 | minji05 | minji@gachon.ac.kr | 민지 |

## DB 작업 시 추가 규칙

1. **값은 항상 `%s` + 튜플로 넘깁니다.** f-string이나 `+`로 SQL에 값을 붙이지 않습니다 (SQL injection 방지, 프로젝트 필수 조건).
   ```python
   query("SELECT * FROM Post WHERE user_id = %s", (user_id,))   # O
   query(f"SELECT * FROM Post WHERE user_id = {user_id}")       # X
   ```
2. **`Like`와 `User`는 SQL에서 백틱으로 감쌉니다.** 예) `` `Like` ``, `` `User` ``
3. **여러 테이블을 함께 바꾸면 하나의 트랜잭션**으로 묶습니다. 예) 글 작성 = `Post` + `Content`
4. **저장 프로시저는 `call_procedure()`로 따로 호출합니다.** `accept_participation`은 내부에서 `START TRANSACTION`을 하므로, 같은 연결에서 먼저 실행한 문장이 자동으로 커밋됩니다.
5. **현재 인원 = ACCEPTED 참여자 수 + 1(작성자)** 입니다. 작성자는 `Participation`에 넣지 않습니다.
6. DB 연결 라이브러리는 `pymysql` 하나로 통일합니다. 결과는 처음부터 딕셔너리로 나옵니다.

## 1번 함수 목록 (서관우 · DB 연결·로그인·프로필·리뷰)

### db.py

| 함수 | 입력값 | 설명 | 반환값 |
|---|---|---|---|
| `get_connection()` | 없음 | MySQL 연결 생성 (DictCursor, autocommit 꺼짐). 연 쪽에서 commit/rollback·close | 연결 객체 |
| `query(sql, params=None)` | SQL, 튜플 | SELECT 여러 건 | `list[dict]` (없으면 `[]`) |
| `query_one(sql, params=None)` | SQL, 튜플 | SELECT 한 건 | `dict` 또는 `None` |
| `execute(sql, params=None)` | SQL, 튜플 | INSERT/UPDATE/DELETE 한 문장 + commit (오류 시 rollback) | INSERT면 새 AUTO_INCREMENT id, 그 외 바뀐 행 수 |
| `transaction()` | 없음 | `with transaction() as cur:` 블록을 한 트랜잭션으로 처리 | 커서 |
| `call_procedure(name, args=())` | 프로시저 이름, 튜플 | 저장 프로시저 단독 호출 + commit | `list[dict]` |
| `mysql_error_message(err)` | MySQL 예외 | 예외에서 메시지만 꺼냄 (예: '정원이 가득 찼습니다.') | `str` |

`query`, `execute`, `transaction`, `call_procedure`는 연결 열기·commit/rollback·닫기를 함수 안에서 처리합니다.

```python
from db import transaction

with transaction() as cur:                     # 글 작성 예시 (Post + Content)
    cur.execute("INSERT INTO Post (user_id, capacity, region, meal_time, food_category) "
                "VALUES (%s, %s, %s, %s, %s)", (user_id, 3, "교내", meal_time, "한식"))
    post_id = cur.lastrowid
    cur.execute("INSERT INTO Content (post_id, title, body) VALUES (%s, %s, %s)",
                (post_id, title, body))
```

### auth.py

| 함수 | 입력값 | 설명 | 반환값 |
|---|---|---|---|
| `login(login_id, password)` | 아이디(또는 가천 이메일), 비밀번호 | 비밀번호 확인 (세션 저장은 하지 않음) | `{"user_id", "nickname"}` 또는 `None` |
| `get_current_user()` | 없음 | `st.session_state["user"]` 조회 | `{"user_id", "nickname"}` 또는 `None` |
| `require_login()` | 없음 | 로그인 안 했으면 안내 후 실행 중단 | `{"user_id", "nickname"}` |
| `logout()` | 없음 | 세션의 로그인 정보 삭제 | 없음 |
| `signup(login_id, gachon_email, password, name, nickname, birth_year, neighborhood)` | 회원 정보 | 회원가입 + 빈 프로필 생성. 가천 메일·비밀번호 8자 이상·중복 검사 | 새 `user_id`, 실패 시 `AuthError` |
| `change_password(user_id, current_password, new_password)` | 회원 번호, 현재·새 비밀번호 | 현재 비밀번호 확인 후 변경 | 없음, 실패 시 `AuthError` |

```python
# pages/*.py 맨 위
me = auth.require_login()
st.write(f"{me['nickname']}님 안녕하세요")
```

### services/user_service.py

| 함수 | 입력값 | 설명 | 반환값 |
|---|---|---|---|
| `get_profile(user_id)` | 회원 번호 | 회원·프로필 정보 + 팔로워·팔로잉·작성 글 수 | `dict` 또는 `None` |
| `update_profile(user_id, neighborhood, food_preference, favorite_food, bio)` | 회원 번호, 수정 값 | 동네·음식 취향·선호 음식·자기소개 수정 (빈 값은 NULL) | 없음 |
| `update_nickname(user_id, nickname)` | 회원 번호, 닉네임 | 닉네임 변경 | 없음, 중복이면 `ValueError` |
| `get_user_posts(user_id)` | 회원 번호 | 작성한 글 (최신순) + 현재 인원·좋아요 수·댓글 수 | `list[dict]` |
| `get_followers(user_id)` | 회원 번호 | 나를 팔로우하는 회원 | `list[dict]` |
| `get_followings(user_id)` | 회원 번호 | 내가 팔로우하는 회원 | `list[dict]` |

- `get_profile` 키: `user_id, login_id, gachon_email, name, nickname, birth_year, neighborhood, food_preference, favorite_food, bio, follower_count, following_count, post_count`
- `get_user_posts` 키: `post_id, title, body, region, meal_time, food_category, status, capacity, current_count, like_count, comment_count, created_at`
- `get_followers` / `get_followings` 키: `user_id, nickname, neighborhood, followed_at`

### services/review_service.py

| 함수 | 입력값 | 설명 | 반환값 |
|---|---|---|---|
| `can_review(post_id, reviewer_id, reviewee_id)` | 글 번호, 작성자, 대상 | 리뷰 가능 여부 확인 | `(True, "")` 또는 `(False, 이유)` |
| `write_review(post_id, reviewer_id, reviewee_id, rating, content="")` | 글 번호, 작성자, 대상, 별점, 내용 | 리뷰 저장 | 새 `review_id`, 실패 시 `ReviewError` |
| `get_received_reviews(user_id)` | 회원 번호 | 받은 리뷰 (최신순) | `list[dict]` |
| `get_written_reviews(user_id)` | 회원 번호 | 내가 쓴 리뷰 (최신순) | `list[dict]` |
| `get_reviewable_mates(user_id)` | 회원 번호 | 아직 리뷰하지 않은 식사 메이트 | `list[dict]` |

- 리뷰 조건: 식사 완료(`COMPLETED`) 모임 · 작성자와 대상 모두 그 모임 멤버(작성자 또는 승인된 참여자) · 자기 평가 금지 · 같은 모임에서 같은 사람 1회 · 별점 1~5
- `get_received_reviews` 키: `review_id, post_id, post_title, reviewer_id, reviewer_nickname, rating, content, created_at`
- `get_written_reviews` 키: `review_id, post_id, post_title, reviewee_id, reviewee_nickname, rating, content, created_at`
- `get_reviewable_mates` 키: `post_id, post_title, meal_time, mate_id, mate_nickname`
- 평균 별점(매너 점수)은 4번 `stats_service.get_user_average_rating()`에서 제공합니다.

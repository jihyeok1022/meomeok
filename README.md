# meomeok
데이터베이스 프로젝트 E조

1번 2번 3번 순차적으로 실행

name1 — 백엔드: DB 연결·로그인·프로필·리뷰
파일: db.py, auth.py, services/user_service.py, services/review_service.py, requirements.txt, .gitignore, .streamlit/secrets.toml.example, README.md

name2 — 백엔드: 게시물·댓글·좋아요·팔로우
파일: services/post_service.py, services/social_service.py

name3 — 백엔드: 참여 신청·승인·마감·톡방·메시지
파일: services/participation_service.py, services/chat_service.py

name4 — 백엔드: 인기 글·평균 평점 조회 + PPT 제작·발표
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

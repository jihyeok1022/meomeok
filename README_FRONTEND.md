# 프론트엔드 연동 명세 (6번 담당)

대상: `pages/4_profile.py`, `pages/5_participation.py`, `pages/6_chat.py`.
이 문서는 기존 `README.md`, `README_API.md`를 보완한다. 기존 합의와 충돌하는 신규 함수는 구현 전에 담당자 간 합의한다.

## 1. 현재 작업 범위

- `4_profile.py`: 프로필·리뷰 화면 1차 코드 작성. 기존 서비스 호출 연결. 로컬 MySQL/브라우저 검증 필요.
- `5_participation.py`, `6_chat.py`: 다음 개발 단계. 아래 채팅 연결 계약은 제안이며 해당 화면 구현 완료를 뜻하지 않는다.
- `stats_service.py`, `chat_service.py`의 미구현 함수는 연동 준비 중으로 표시한다. 예시 데이터를 실제 화면에 넣지 않는다.

## 2. 공통 약속

- `app.py`에서 실행. 각 화면은 `auth.require_login()`으로 로그인 사용자를 확인하고 `st.session_state['user']`의 user_id를 사용한다.
- Streamlit이 Python 서비스 함수를 직접 호출한다. 별도 HTTP API를 전제하지 않는다.
- UI에서 SQL을 직접 실행하지 않는다. 권한·업무 규칙·트랜잭션·DB 연결 종료는 백엔드 담당이다.
- 여러 건 `list[dict]` (없으면 `[]`), 한 건 `dict` (없으면 `None`), 날짜·시간 `datetime`.
- DB 장애와 정상 빈 목록을 구분한다. DB 장애는 예외를 전달하고 화면에서 오류를 안내한다.
- HTML에 넣는 DB 문자열은 `ui_common.e()`로 이스케이프한다.
- UI는 `ui_common.CSS`와 `assets`를 재사용한다. 추가 CSS는 각 화면 파일에 둔다.

## 3. 프로필·리뷰: 기존 서비스 계약 사용

| 모듈 | 함수 | 화면에서 사용하는 반환값 / 동작 |
|---|---|---|
| user_service | get_profile(user_id) | user_id, nickname, neighborhood, birth_year, gachon_email, food_preference, favorite_food, bio, follower_count, following_count |
| user_service | update_profile(user_id, neighborhood, food_preference, favorite_food, bio) | None, 성공 후 재조회 |
| user_service | update_nickname(user_id, nickname) | None, 중복 ValueError, 성공 후 로그인 세션 nickname 갱신 |
| user_service | get_followers(user_id), get_followings(user_id) | 목록의 user_id, nickname, neighborhood |
| user_service | get_user_posts(user_id) | post_id, title, body, region, meal_time, food_category, status, capacity, current_count, like_count, comment_count |
| review_service | get_received_reviews(user_id) | review_id, post_id, post_title, reviewer_id, reviewer_nickname, rating, content, created_at |
| review_service | get_written_reviews(user_id) | review_id, post_id, post_title, reviewee_id, reviewee_nickname, rating, content, created_at |
| review_service | get_reviewable_mates(user_id) | post_id, post_title, meal_time, mate_id, mate_nickname |
| review_service | write_review(post_id, reviewer_id, reviewee_id, rating, content='') | 새 review_id, 실패 ReviewError |

프로필과 닉네임은 기존 서비스가 별도 트랜잭션이므로 별도 저장 버튼으로 제공한다. 리뷰 대상은 (post_id, mate_id)로 식별한다. 리뷰 중복·식사 완료·멤버 여부·자기 평가 방지는 기존 review_service의 검사에 맡긴다.

## 4. 추가 연동 필요

### 4.1 평균 평점 — stats_service.py (4번 담당)

기존 `README_API.md` 9절의 계약을 그대로 사용한다.

```python
get_user_average_rating(user_id: int) -> float | None
```

- 받은 리뷰의 평균 평점. 평가가 없으면 None.
- 화면은 소수점 한 자리 표시.
- `4_profile.py`에 함수 존재 여부 확인과 호출부가 작성되어 있다. 계약에 맞춰 구현되면 사용한다.

### 4.2 참여 중인 톡방 — chat_service.py (3번 담당)

아래는 **연동 제안**이다. 다른 명세가 이미 있다면 협의 후 일치시킨다.

```python
get_chat_rooms(user_id: int) -> list[dict]
```

반환 필드 제안:

| 키 | 타입 | 의미 |
|---|---|---|
| room_id | int | ChatRoom의 PK |
| post_id | int | 연결된 모집 글 ID |
| title | str | Content.title |
| member_count | int | ChatMember 수 |
| last_message | str 또는 None | 마지막 메시지 내용 |
| last_message_at | datetime 또는 None | 마지막 메시지 시각 |

- 로그인 사용자가 ChatMember에 포함된 방만 반환한다. 메시지가 없는 방도 포함한다.
- 마지막 메시지 기준 최신순, 메시지 없는 방은 생성 시각 기준으로 정렬하는 방안을 제안한다.
- `4_profile.py`는 `room_id`, `title`, `last_message`를 사용한다. 방에 들어갈 때 `pages/6_chat.py`에 `room` 쿼리 파라미터로 room_id를 전달한다.
- 함수가 없으면 연동 준비 중으로 표시한다. `6_chat.py`가 비어 있으면 이동하지 않고 안내한다.
- 채팅방 조회·메시지 작성 권한은 백엔드에서 재검사해야 한다. URL의 room ID만 신뢰하면 안 된다.

## 5. 페이지 이동 규칙

- 피드: `pages/1_feed.py`
- 상세: `pages/3_post_detail.py`, `post` 쿼리 파라미터 및 기존 `selected_post_id`, `detail_scroll_to_top` 세션 키 사용.
- 프로필: `pages/4_profile.py`. 참여 화면에서 리뷰 작성 요청 시 `review_post` 쿼리 파라미터로 post_id를 전달하면 리뷰 쓰기 메뉴를 기본으로 열고 해당 모임의 평가 대상을 우선 표시한다.
- 참여: `pages/5_participation.py`
- 채팅: `pages/6_chat.py`, 방 이동은 `room` 쿼리 파라미터 사용 제안.

## 6. 검증 체크리스트

- [x] Python 문법 검사 (4_profile.py)
- [ ] 로그인 후 하단 내 프로필 메뉴로 이동, 새로고침 및 다른 탭 이동
- [ ] 프로필 데이터·팔로워·팔로잉·작성 글 실제 DB 결과와 일치
- [ ] 수정 저장 후 재조회 및 새 로그인에서도 저장값 확인
- [ ] 중복 닉네임/빈 닉네임 및 빈 동네 오류 안내
- [ ] 받은 리뷰·작성한 리뷰·작성 대상 조회
- [ ] 리뷰 저장 및 중복 등록 방지, 저장 실패 시 오류 안내
- [ ] 통계/톡방 서비스 미구현 시 정상 화면 유지
- [ ] 평균 평점/톡방 서비스 연결 후 정상 조회
- [ ] 로그아웃 후 다른 사용자로 로그인 시 이전 계정 상태 제거
- [ ] 기존 자동 테스트 실행 및 실제 MySQL/브라우저 레이아웃 검수

검증 범위: 배포한 1차 코드의 Python 문법만 확인했으며, 작성 환경에는 Streamlit 및 실제 MySQL 서버가 없어 실행·저장·레이아웃 검증은 완료하지 않았다.

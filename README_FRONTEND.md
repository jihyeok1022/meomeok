# 프론트엔드 연동 명세 (6번 담당)

대상: `pages/4_profile.py`, `pages/5_participation.py`, `pages/6_chat.py`.
이 문서는 기존 `README.md`, `README_API.md`를 보완한다. 기존 합의와 충돌하는 신규 함수는 구현 전에 담당자 간 합의한다.

## 1. 현재 작업 범위

- `4_profile.py`: 프로필·리뷰 화면 1차 코드 작성. 기존 서비스 호출 연결. 프로필 조회·받은 리뷰·평균 평점 표시는 로컬 확인, 수정/리뷰 저장 검증 필요.
- `5_participation.py`: 참여 관리 UI 및 서비스 호출부 작성. 내 모집 글은 기존 서비스로 조회, 나머지 기능은 아래 제안 계약에 따라 연동 대기.
- `6_chat.py`: 톡방 목록·대화·멤버·메시지 전송 UI와 호출부 작성. 실제 채팅 서비스 연동 대기. 채팅 연결 계약은 제안이다.
- `stats_service.get_user_average_rating()` 연동 및 실제 화면 4.5점 표시를 로컬에서 확인했다. `participation_service.py`, `chat_service.py`의 미구현 함수는 연동 준비 중으로 표시한다. 예시 데이터를 실제 화면에 넣지 않는다.

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

### 3.1 리뷰 공개 범위 (팀 회의 방향, 사용자 전달 기준)

- 내 프로필은 로그인한 본인만 조회하며 받은 리뷰와 작성한 리뷰를 상세 표시한다.
- 다른 사람의 공개 프로필에서는 리뷰 관련 정보 중 평균 평점만 표시한다. 개별 별점, 리뷰 내용, 작성자, 작성한 리뷰 목록은 공개하지 않는다. 평점이 없으면 평가 없음으로 표시한다.
- 현재 `4_profile.py`는 로그인 사용자 ID만 사용한다. 다른 회원의 프로필 조회는 아직 구현하지 않았다. 공개 프로필이 추가되면 별도의 공개용 조회 계약을 두고 비공개 리뷰 정보를 응답에 포함하지 않는다. 사용자 ID를 바꿔 다른 회원의 비공개 리뷰를 조회할 수 없도록 백엔드에서도 권한을 검사하도록 협의한다. 로그인 본인용 이메일·채팅방 등 비공개 정보도 공개 화면에 재사용하지 않는다.

## 4. 추가 연동 필요

### 4.1 평균 평점 — stats_service.py (4번 담당, 연동 확인 완료)

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

### 4.3 참여 관리 — participation_service.py (3번 담당)

기존 README_API.md의 `cancel_application(post_id, user_id)`는 그대로 호출한다. 다음 다섯 함수는 **새 연동 제안**이며 `5_participation.py`가 사용하는 정확한 이름·인자 순서다. 이미 다른 명세가 있으면 합의 후 호출부와 문서를 함께 수정한다.

| 함수 | 반환 / 동작 |
|---|---|
| `get_my_applications(user_id)` | 신청자 본인의 참여 내역 `list[dict]` |
| `get_post_applications(post_id, host_id)` | 모집자가 자신의 글에 신청한 회원을 조회, `list[dict]` |
| `accept_application(post_id, host_id, applicant_id)` | 승인 성공 시 dict 또는 None, 실패는 예외 |
| `reject_application(post_id, host_id, applicant_id)` | 거절 성공 시 dict 또는 None, 실패는 예외 |
| `complete_meal(post_id, host_id)` | 식사 완료 성공 시 dict 또는 None, 실패는 예외 |

`get_my_applications` 반환 키: `post_id:int`, `title:str`, `status:str` (Participation.status), `post_status:str` (Post.status), `meal_time:datetime`, `region:str`. 최신 신청순, 취소·거절 이력 포함. `status`와 `post_status`를 구분한다.

`get_post_applications` 반환 키: `user_id:int` (신청자), `nickname:str`, `status:str`; `applied_at:datetime` 추가 권장. 대기 신청 우선 및 신청순, 동일 시각에는 user_id로 정렬. 작성자 자신은 참여 행에 포함하지 않는다.

내 모집 글 목록은 기존 `user_service.get_user_posts(user_id)`를 사용한다. 채팅방 ID는 `chat_service.get_chat_rooms(user_id)`의 `post_id`와 `room_id`를 매칭하여 사용한다. 방이 없으면 진입을 막는다. `post_id`를 방 ID로 간주하지 않는다.

| 화면 조건 | 동작 |
|---|---|
| 내 신청 PENDING + 글 OPEN/CLOSED | 기존 cancel_application 호출 |
| 내 신청 ACCEPTED + 글 OPEN/CLOSED | 방이 존재하고 채팅 화면 준비 완료 시 톡방 이동 |
| 내 신청 ACCEPTED + 글 COMPLETED | 프로필의 리뷰 쓰기 메뉴 이동 |
| 내 신청 REJECTED/CANCELED 또는 글 CANCELED | 상태 및 게시글 보기만 제공 |
| 내 모집 OPEN + 신청자 PENDING | 승인/거절, 정원이 찼다면 승인 비활성화 |
| 내 모집 CLOSED | 톡방, 식사 완료 확인 후 complete_meal 호출 |
| 내 모집 COMPLETED | 리뷰 쓰기 메뉴 이동 |

백엔드 필수 검증: 로그인 사용자가 신청자/모집자와 일치하는지, 모집자가 해당 글의 작성자인지, PENDING 여부와 글 상태/정원/중복을 처리 시점에 재검사한다. 승인 시 기존 `accept_participation` 저장 프로시저를 `db.call_procedure()`로 사용한다(프로시저 인자 순서: host_id, post_id, applicant_id). 정원이 채워지면 모집 마감 및 톡방·멤버 생성과 남은 대기 신청 거절은 프로시저 트랜잭션에 맡긴다. 임의 모집 마감이나 승인된 참여 탈퇴, 모집 글 취소는 아직 별도 계약을 합의하지 않았으므로 이 버전의 UI에 넣지 않는다. `complete_meal`은 모집자만 CLOSED에서 COMPLETED로 전환하며 식사 시각 및 완료 조건은 백엔드 담당자와 합의한다. 성공은 DB commit 후 반환하고 실패는 예외로 알린다(실패를 False나 빈 dict로 반환하지 않는다). 프론트는 성공 이후 재조회하며 상태나 인원 수를 미리 변경하지 않는다.

백엔드가 없는 경우: 신청한 모임은 연동 준비 중으로 표시하며, 내 모집 글은 실제 DB 데이터를 표시한다. 조회 API는 있지만 결과가 없으면 빈 목록 안내를 표시한다. 조회 실패는 오류로 표시한다. 신청·승인 테스트를 위한 가짜 데이터를 서비스 대신 사용하지 않는다.

### 4.4 톡방 대화·멤버·메시지 전송 — chat_service.py (3번 담당)

`get_chat_rooms(user_id)`는 4.2절을 그대로 사용한다. 아래 추가 함수는 **연동 제안**이며 `6_chat.py`의 호출 인자 순서와 일치한다.

| 함수 | 반환 / 동작 |
|---|---|
| `get_chat_members(room_id, user_id)` | `list[dict]`, 해당 톡방의 멤버 목록 |
| `get_messages(room_id, user_id, limit=100)` | `list[dict]`, 최근 최대 limit개 메시지를 오래된 순서로 반환 |
| `send_message(room_id, user_id, content)` | 저장된 메시지 ID(int) 또는 메시지 dict, 실패는 예외 |

`get_chat_members` 반환 키: `user_id:int`, `nickname:str`, `is_host:bool` (선택). `is_host`는 모집 글 작성자 여부이며 작성자 우선, 나머지는 안정적인 순서로 반환한다.

`get_messages` 반환 키: `message_id:int`, `user_id:int` (보낸 사람), `nickname:str`, `content:str`, `created_at:datetime`. 최근 limit개를 먼저 선택한 뒤 created_at 및 message_id 오름차순으로 반환한다. 동일 시각은 message_id로 순서를 고정한다. 메시지가 없으면 `[]`를 반환한다. limit는 1~100의 정수로 검증한다.

**권한 및 저장 규칙:**
- 모든 방 조회·멤버 조회·메시지 조회·전송에서 ChatMember를 기준으로 요청자의 권한을 확인한다. 다른 사람의 방 ID를 전달해도 읽거나 쓸 수 없어야 한다. 프론트는 로그인 세션의 user_id만 전달하고, 사용자의 방 목록에 없는 room ID로는 상세 호출을 수행하지 않는다.
- 방 없음은 LookupError, 멤버 아님은 PermissionError, 잘못된 입력/상태는 ValueError를 제안한다. DB 오류는 예외로 전달한다. 권한 검사 실패는 정상 빈 목록으로 위장하지 않는다.
- 메시지는 앞뒤 공백 제거 후 1~2,000자(이 버전 UI의 제안 제한), UTF-8 65,535바이트 이하. 서버에서도 검증한다. 원문을 저장하며 HTML 이스케이프는 화면에서 수행한다.
- Message INSERT 성공 후 commit하고 반환한다. 실패는 rollback 및 예외 처리. 메시지 전송 후 화면은 DB를 다시 조회한다. 전송 실패 시 입력은 남긴다. 통신 장애로 commit 여부가 불명확하면 새로 조회 후 재시도하도록 안내한다.
- 톡방 생성과 멤버 추가는 참여 승인 프로시저의 기존 트랜잭션을 사용한다. 프론트는 방/멤버를 임의 생성하지 않는다. 식사 완료·취소 후 전송 가능 여부는 팀에서 협의하고 백엔드에서 검증한다.
- 모임 정보는 기존 `post_service.get_post(post_id, viewer_id)`를 사용한다. 약속 장소는 별도 컬럼이 없으므로 본문과 지역·식사 시각을 표시한다.
- 화면은 최근 100개 메시지, 수동 새로고침, 본인/상대 메시지 구분, 멤버 목록, 전송 폼을 제공한다. 실시간 푸시·첨부파일·읽음 표시·이전 메시지 페이지네이션은 범위 밖이다. 수동 새로고침 전에 전송하지 않은 폼 입력은 사라질 수 있다.
- 서비스가 비어 있으면 톡방 목록 준비 중, 목록 조회 가능하나 개별 기능이 없으면 해당 기능만 준비 중으로 표시한다. 예시 데이터를 실제 화면에 표시하지 않는다.

## 5. 페이지 이동 규칙

- 피드: `pages/1_feed.py`
- 상세: `pages/3_post_detail.py`, `post` 쿼리 파라미터 및 기존 `selected_post_id`, `detail_scroll_to_top` 세션 키 사용.
- 프로필: `pages/4_profile.py`. 참여 화면에서 리뷰 작성 요청 시 `review_post` 쿼리 파라미터로 post_id를 전달하면 리뷰 쓰기 메뉴를 기본으로 열고 해당 모임의 평가 대상을 우선 표시한다.
- 참여: `pages/5_participation.py`
- 채팅: `pages/6_chat.py`, 방 이동은 `room` 쿼리 파라미터 사용 제안.

## 6. 검증 체크리스트

- [x] Python 문법 검사 (6_chat.py)
- [ ] 톡방 목록 및 미연동 안내 로컬 확인
- [ ] 프로필/참여 화면의 `room` 파라미터를 통한 방 이동
- [ ] 방 목록과 메시지 조회, 멤버 조회 및 권한 없는 room ID 차단
- [ ] 메시지 전송 후 재조회, 공백 및 저장 실패 처리, 다른 계정에서 수동 새로고침으로 확인

- [x] Python 문법 검사 (4_profile.py)
- [ ] 로그인 후 하단 내 프로필 메뉴로 이동, 새로고침 및 다른 탭 이동
- [ ] 프로필 데이터·팔로워·팔로잉·작성 글 실제 DB 결과와 일치 (화면 조회 확인, DB 원본 대조 필요)
- [ ] 수정 저장 후 재조회 및 새 로그인에서도 저장값 확인
- [ ] 중복 닉네임/빈 닉네임 및 빈 동네 오류 안내
- [ ] 받은 리뷰·작성한 리뷰·작성 대상 조회
- [ ] 리뷰 저장 및 중복 등록 방지, 저장 실패 시 오류 안내
- [ ] 통계/톡방 서비스 미구현 시 정상 화면 유지
- [x] 평균 평점 서비스 연결 후 정상 조회 (지혁 계정 4.5점, 로컬 화면 확인)
- [ ] 톡방 서비스 연결 후 정상 조회
- [ ] 타인 공개 프로필 추가 시 평균 평점 외 리뷰 상세 응답 및 UI 차단
- [x] Python 문법 검사 (5_participation.py)
- [x] 참여 탭 전환, 실제 내 모집 글 및 상세 이동 (사용자 로컬 화면 확인)
- [ ] 참여 서비스 연동 후 신청/취소/승인/거절 및 정원 초과 방지
- [ ] 승인 후 톡방 진입 권한, 식사 완료 및 리뷰 쓰기 이동
- [ ] 로그아웃 후 다른 사용자로 로그인 시 이전 계정 상태 제거
- [ ] 기존 자동 테스트 실행 및 실제 MySQL/브라우저 레이아웃 검수

검증 범위: 프로필의 실제 DB 조회 및 평균 평점, 받은 리뷰 표시와 참여 관리의 탭 전환·내 모집 글 조회·상세 이동을 사용자 로컬 화면에서 확인했다. 채팅 페이지는 Python 문법 검사만 완료했다. 미구현 참여·채팅 서비스의 실제 DB 연동 및 저장/권한 검증은 팀원 구현 후 사용자 환경에서 진행해야 한다.

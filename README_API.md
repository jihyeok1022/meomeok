# 프론트엔드 연동 API 명세

대상: `app.py`, `pages/1_feed.py`, `pages/2_write_post.py`, `pages/3_post_detail.py` (5번 담당).

## 1. 문서 상태와 공통 규칙

현재 화면은 `demo_data.py`의 예시 데이터를 사용하며 실제 DB 서비스와 연결하기 전입니다.
Streamlit에서 Python 서비스 함수를 직접 호출하는 구조로, 별도 HTTP 서버를 전제하지 않습니다.
인증 함수는 기존 README 계약을 따릅니다. 그 밖의 함수명·입력·반환값은 담당자와 합의할 **연동 제안**이며 구현 완료를 의미하지 않습니다.

| 항목 | 규칙 |
|---|---|
| ID | Python int |
| 여러 건 조회 | list[dict], 결과가 없으면 [] |
| 한 건 조회 | dict, 대상이 없으면 None |
| 날짜·시간 | Python datetime. 한국 현지 시각의 timezone 없는 값으로 통일하는 방안 제안 |
| 평점 없음 | None, 화면에는 평가 없음 |
| 로그인 정보 | st.session_state["user"] |
| 입력·권한 검사 | 프론트 검사와 별개로 백엔드에서도 검사 |
| DB 저장 | 서비스에서 commit·rollback 및 연결 종료 처리 |
| 화면 의존성 | 공통 인증 함수를 제외한 서비스에서 st.* 사용 금지 |

로그인 사용자 ID는 입력창이 아니라 세션에서 가져옵니다. 비밀번호·password_hash는 반환하지 않습니다.

### 오류 처리 제안

| 상황 | 처리 |
|---|---|
| 인증 실패 | None |
| 목록·단건 조회 결과 없음 | 각각 []·None |
| 입력 오류·중복·상태 충돌 | ValueError |
| 권한 없음 | PermissionError |
| 등록·변경 대상 없음 | LookupError |
| DB 장애 | 예외 전달, 화면에서 일반 오류 안내 |

예외 종류는 팀 합의 후 확정합니다. DB 장애를 빈 조회 결과나 성공으로 처리하지 않습니다.

## 2. DB 선택값

| 필드 | 허용값 |
|---|---|
| region | 교내, 복정동, 태평동, 기타 |
| food_category | 한식, 중식, 양식, 일식, 기타, 미정 |
| 게시물 status | OPEN, CLOSED, COMPLETED, CANCELED |
| 참여 status | PENDING, ACCEPTED, REJECTED, CANCELED |
| capacity | 작성자 포함 2~20명 |

검색의 '전체'는 서비스에 None으로 전달하며 DB에 저장하지 않습니다.

## 3. 공통 데이터 형식

### 3.1 로그인 사용자 — SessionUser

```python
{"user_id": 1, "nickname": "도윤"}
```

### 3.2 게시물 — PostView

피드·상세 화면의 공통 기본 형식입니다.

```python
from datetime import datetime

post = {
    "post_id": 1,
    "user_id": 1,  # 작성자 ID
    "nickname": "도윤",
    "title": "수업 끝나고 김치찌개 먹을 사람",
    "body": "수업 끝나고 같이 밥 먹어요.",
    "region": "교내",
    "food_category": "한식",
    "meal_time": datetime(2026, 11, 20, 18, 0),
    "capacity": 4,
    "status": "OPEN",
    "created_at": datetime(2026, 11, 19, 12, 0),
    "current_count": 2,
    "rating": 4.8,
    "like_count": 5,
    "comment_count": 3,
}
```

| 필드 | 타입 | 출처·의미 |
|---|---|---|
| post_id, user_id, capacity | int | Post의 ID·작성자·정원 |
| region, food_category, status | str | Post |
| meal_time, created_at | datetime | Post |
| title, body | str | Content |
| nickname | str | 작성자의 User |
| current_count | int | 작성자 1명 + ACCEPTED 참여자 수 |
| rating | float 또는 None | 작성자가 받은 리뷰의 평균 |
| like_count | int | 해당 글의 Like 행 수 |
| comment_count | int | 해당 글의 Comment 행 수 |

마지막 네 항목은 조회 집계값이며 Post에 새 컬럼을 만들 필요는 없습니다.
여러 1:N 테이블을 동시에 JOIN해 개수가 곱해지지 않도록 각각 집계한 뒤 결합합니다.
평점은 Review.reviewee_id = Post.user_id 기준입니다. MySQL의 Decimal 평균값은 float로 변환하고 표시 반올림은 화면에서 처리합니다.

상세 조회에는 현재 로그인 사용자별 표시값을 추가하는 방안을 제안합니다.

```python
# 기본 PostView에 추가
{"is_liked": False, "is_following_author": False}
```

두 값은 bool이며 비로그인 조회에서는 False입니다. 현재 예시의 세션 집합 직접 조회를 이 필드 사용으로 변경해야 합니다.

### 3.3 글쓰기 입력 — PostCreate

```python
payload = {
    "title": "같이 점심 먹을 사람",
    "body": "12시에 학생식당 입구에서 만나요.",
    "capacity": 4,
    "meal_time": datetime(2026, 11, 20, 12, 0),
    "region": "교내",
    "food_category": "한식",
}
```

| 필드 | 검증 |
|---|---|
| title | 공백 제거 후 필수, 100자 이하 |
| body | 공백 제거 후 필수, UTF-8 기준 65,535바이트 이하 |
| capacity | bool을 제외한 정수 2~20 |
| meal_time | 등록 시점보다 미래인 datetime |
| region, food_category | DB 허용값 중 하나 |

미래 시각 등은 앱의 제안 규칙으로 DB 제약에 모두 포함되지는 않습니다.
user_id는 로그인 세션에서 별도 인자로 전달합니다. post_id·created_at·초기 상태 OPEN은 백엔드에서 결정합니다.
별도 장소·예산 컬럼은 없으며 구체적인 약속 장소는 body에 작성합니다.

### 3.4 댓글 — CommentView

```python
{
    "comment_id": 1,
    "post_id": 1,
    "user_id": 4,
    "nickname": "수민",
    "content": "조금 늦게 합류해도 될까요?",
    "created_at": datetime(2026, 11, 19, 12, 5),
}
```

ID는 int, 닉네임·내용은 str, 작성 시각은 datetime입니다. nickname은 User와 JOIN하여 조회합니다.

### 3.5 확정 멤버 — MemberView

```python
[
    {"user_id": 1, "nickname": "도윤", "is_host": True},
    {"user_id": 5, "nickname": "민지", "is_host": False},
]
```

작성자를 첫 번째로 반환하고 ACCEPTED 참여자만 포함합니다.
작성자는 Participation에 별도 행을 만들지 않습니다.
빈자리는 화면에서 capacity - len(members)로 표시합니다.

## 4. API 목록과 담당자

| 담당 | 파일 | 함수 |
|---|---|---|
| 1번 | auth.py | login, get_current_user, require_login, logout |
| 2번 | services/post_service.py | list_posts, get_post, create_post |
| 2번 | services/social_service.py | list_comments, create_comment, set_like, set_follow |
| 3번 | services/participation_service.py | get_members, get_application_status, apply_to_post, cancel_application |
| 4번 | services/stats_service.py | get_user_average_rating |

프로필·리뷰 작성·참여 승인 관리·채팅 화면의 전체 명세는 각 담당자가 추가합니다. 이 문서는 5번 화면의 연동 범위입니다.

## 5. 인증 — 1번 담당

기존 README 계약을 따릅니다.

| 함수 | 입력 | 반환·동작 |
|---|---|---|
| login(login_id, password) | 아이디·비밀번호 str | 성공 SessionUser, 인증 실패 None |
| get_current_user() | 없음 | SessionUser 또는 None |
| require_login() | 없음 | SessionUser 반환, 비로그인이면 안내 후 실행 중단 |
| logout() | 없음 | 로그인 세션 제거, None 반환 |

login()은 인증 결과만 반환합니다. 로그인 화면이 결과를 세션에 저장하고 피드로 이동합니다.

```python
user = auth.login(login_id, password)
if user is None:
    st.error("아이디 또는 비밀번호를 확인해 주세요.")
else:
    st.session_state["user"] = user
    st.switch_page("pages/1_feed.py")
```

체험용 사용자를 실제 로그인 세션에 저장하지 않습니다.

## 6. 게시물 — 2번 담당

### 6.1 피드 조회

```python
list_posts(
    *, region=None, food_category=None, status=None,
    keyword="", sort="latest", limit=50, offset=0
) -> list[dict]
```

| 인자 | 기본값 | 설명 |
|---|---|---|
| region | None | 지역 필터 |
| food_category | None | 음식 필터 |
| status | None | OPEN·CLOSED 중 선택, None이면 두 상태 모두 |
| keyword | "" | 제목 또는 본문에 포함된 검색어 |
| sort | "latest" | latest: 작성 최신순, meal_time: 식사 시각 빠른순 |
| limit | 50 | 정수 1~100 |
| offset | 0 | 0 이상의 정수 |

- 반환: PostView 목록.
- **피드는 항상 OPEN·CLOSED만 반환합니다. 검색해도 COMPLETED·CANCELED는 노출하지 않습니다.**
- 필터·정렬 후 limit·offset을 적용합니다.
- 정렬값이 같으면 post_id 내림차순으로 순서를 고정합니다.
- 잘못된 선택값·정렬값은 ValueError입니다.
- 페이지 제한 적용 시 목록 길이와 전체 모집 중 개수가 다를 수 있습니다. 전체 개수가 필요하면 별도 집계 계약을 추가합니다.

### 6.2 상세 조회

```python
get_post(post_id: int, viewer_id: int | None = None) -> dict | None
```

- 반환: PostView + is_liked + is_following_author.
- viewer_id는 현재 로그인 사용자 ID로 작성자 ID와 구분합니다.
- 글이 없으면 None.
- 상세 조회는 피드의 상태 필터와 분리합니다. 완료·취소 글의 직접 링크 조회 허용 여부는 팀에서 확정합니다.

### 6.3 글 등록

```python
create_post(user_id: int, payload: dict) -> int
```

- 입력: 로그인 사용자 ID, PostCreate.
- 반환: 생성된 post_id.
- Post·Content를 하나의 트랜잭션으로 저장하고 하나라도 실패하면 전체 롤백합니다.
- 초기 상태 OPEN, 확정 인원은 작성자 1명이며 작성자의 Participation 행은 만들지 않습니다.
- 입력 오류는 ValueError, 사용자 없음은 LookupError입니다.
- 성공 후 생성된 글의 상세 화면으로 이동합니다.
- 현재 글쓰기는 미리보기까지 구현되어 있어 실제 등록 연결이 필요합니다.

## 7. 댓글·좋아요·팔로우 — 2번 담당

### 7.1 댓글 조회

```python
list_comments(post_id: int) -> list[dict]
```

CommentView 목록을 created_at 오름차순, 같은 시각이면 comment_id 오름차순으로 반환합니다.
댓글·게시물이 없으면 []입니다. 게시물 존재 여부는 상세 조회에서 판단합니다.

### 7.2 댓글 등록

```python
create_comment(post_id: int, user_id: int, content: str) -> dict
```

- 반환: 생성된 CommentView, 작성자 닉네임 포함.
- 공백 제거 후 필수, UTF-8 기준 65,535바이트 이하.
- 대상 없음은 LookupError, 내용 오류는 ValueError.
- 원문 저장 후 HTML 이스케이프는 화면에서 처리합니다.
- 성공 후 댓글 목록과 comment_count를 다시 조회합니다.
- 댓글 수정·삭제는 현재 화면 범위에 포함하지 않습니다.

### 7.3 좋아요 설정·해제

```python
set_like(post_id: int, user_id: int, liked: bool) -> dict
# 반환 예: {"is_liked": True, "like_count": 6}
```

- liked=True는 추가, False는 해제.
- 이미 원하는 상태이면 그대로 성공합니다. 같은 요청을 반복해도 반대 상태로 바뀌지 않습니다.
- (user_id, post_id) 복합키로 중복을 방지합니다.
- 대상 없음은 LookupError, 반환 개수는 DB 처리 결과 기준입니다.
- 예시 toggle_like() 대신 목표 상태를 전달하는 계약을 제안합니다.

### 7.4 팔로우 설정·해제

```python
set_follow(follower_id: int, followee_id: int, following: bool) -> dict
# 반환 예: {"is_following": True}
```

- follower_id는 로그인 사용자, followee_id는 게시물 작성자.
- following=True는 추가, False는 해제. 이미 원하는 상태이면 그대로 성공합니다.
- 자기 자신 팔로우는 ValueError, 대상 없음은 LookupError입니다.
- 같은 작성자의 다른 글에서도 동일한 팔로우 상태를 표시합니다.

## 8. 상세 화면의 참여 — 3번 담당

### 8.1 확정 멤버 조회

```python
get_members(post_id: int) -> list[dict]
```

MemberView 목록을 반환합니다. 작성자 우선, 나머지는 applied_at·user_id 오름차순입니다.
승인된 참여자만 포함하며 글이 없으면 []입니다.

### 8.2 내 신청 상태 조회

```python
get_application_status(post_id: int, user_id: int) -> str | None
```

PENDING·ACCEPTED·REJECTED·CANCELED 중 하나, 신청 내역이 없으면 None입니다.
작성자는 게시물 user_id로 따로 판단합니다.

### 8.3 참여 신청

```python
apply_to_post(post_id: int, user_id: int) -> dict
# 반환 예: {"post_id": 1, "user_id": 6, "status": "PENDING"}
```

- 글이 OPEN이고 확정 인원이 정원 미만일 때 허용합니다.
- 작성자 본인 신청은 금지합니다.
- 기존 PENDING·ACCEPTED·REJECTED 내역이 있으면 중복 신청을 거절합니다.
- 기존 CANCELED는 PENDING으로 바꾸고 applied_at을 갱신하는 방안을 제안합니다.
- 신청만으로 확정 인원이나 ChatMember를 늘리지 않습니다.
- 상태·정원 충돌은 ValueError, 본인 글 신청은 PermissionError, 대상 없음은 LookupError입니다.
- 재신청·거절 후 신청 정책은 팀 합의 후 확정합니다.
- 승인 시 동시 처리로 정원을 초과하지 않도록 백엔드 트랜잭션으로 보장해야 합니다.

### 8.4 신청 취소

```python
cancel_application(post_id: int, user_id: int) -> dict
# 반환 예: {"post_id": 1, "user_id": 6, "status": "CANCELED"}
```

PENDING 신청을 취소합니다. 이미 취소되었으면 같은 상태로 성공 처리하는 방안을 제안합니다.
다른 상태는 ValueError, 대상 없음은 LookupError입니다.
승인된 참여의 탈퇴는 별도 기능입니다. 게시물 취소와 내 신청 취소는 다릅니다.

### 8.5 참여 버튼 표시 규칙

위에서부터 우선 적용합니다.

| 조건 | 버튼 | 활성화 |
|---|---|---|
| 내가 작성자 | 내가 작성한 글 | 아니요 |
| 내 신청 ACCEPTED | 참여 확정 | 아니요 |
| 내 신청 PENDING, 글 OPEN 또는 CLOSED | 신청 취소 | 예 |
| 내 신청 REJECTED | 신청 거절 | 아니요 |
| 글이 OPEN 아님 | 해당 게시물 상태 | 아니요 |
| 확정 인원이 정원 이상 | 정원 마감 | 아니요 |
| 나머지 | 참가 신청 | 예 |

화면 버튼과 별개로 백엔드에서 처리 시점의 권한·정원을 다시 검사합니다.

## 9. 평균 평점 — 4번 담당

```python
get_user_average_rating(user_id: int) -> float | None
```

- Review.reviewee_id 기준으로 받은 리뷰의 rating 평균입니다.
- 리뷰가 없으면 None, 화면에는 평가 없음으로 표시합니다.
- 화면에서 소수점 한 자리로 표시합니다.
- 피드에서는 사용자마다 반복 호출하기보다 게시물 조회에 작성자별 평균을 결합하는 방안을 권장합니다.
- 인기 글 조회는 현재 5번 화면에 연결되지 않아 이 문서에서 제외합니다.

## 10. 예시 코드 → 서비스 연결표

| 현재 호출·상태 | 연결할 제안 API |
|---|---|
| demo_data.current_user() | auth.get_current_user() 또는 require_login() |
| demo_data.get_posts() | post_service.list_posts(...) |
| demo_data.get_post(...) | post_service.get_post(..., viewer_id) |
| 글쓰기 미리보기 | post_service.create_post(...) 등록 연결 추가 |
| demo_data.get_comments(...) | social_service.list_comments(...) |
| demo_data.add_comment(post_id, user, content) | social_service.create_comment(post_id, user_id, content) |
| demo_data.toggle_like(...) | social_service.set_like(..., liked) |
| demo_data.toggle_follow(...) | social_service.set_follow(..., following) |
| demo_data.get_members(...) | participation_service.get_members(...) |
| demo_data.application_state(...) | participation_service.get_application_status(...) |
| demo_data.apply_to_post(...) | participation_service.apply_to_post(...) |
| demo_data.cancel_application(...) | participation_service.cancel_application(...) |
| 세션 likes·follows 집합 직접 조회 | PostView.is_liked·is_following_author |

인자·반환값이 다르므로 import만 바꾸지 않고 호출부도 변경합니다.
처리 성공 후 관련 데이터를 다시 조회하며 실패 시 성공 표시나 수치를 먼저 변경하지 않습니다.

## 11. 연동 확인 기준

- [ ] app.py 실행 및 화면 간 이동
- [ ] 로그인 성공 시 공통 사용자 형식 저장
- [ ] 피드 검색에서도 완료·취소 글 제외
- [ ] 글 등록 시 Post·Content 함께 저장
- [ ] 등록 성공 후 생성된 글 상세로 이동
- [ ] 피드·상세의 댓글·좋아요 수 일치
- [ ] 좋아요·팔로우 반복 요청 시 중복 행 방지
- [ ] 신청만으로 확정 인원이 늘지 않음
- [ ] 새 브라우저 세션에서도 DB 저장 결과 조회
- [ ] 권한 없는 작업을 백엔드에서도 차단

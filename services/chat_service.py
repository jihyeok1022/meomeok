"""
services/chat_service.py - 모임 톡방 목록·멤버·메시지 (3번 담당)

톡방 규칙
- 톡방과 멤버는 참여 승인 프로시저(accept_participation)가 정원이 차는 순간 만든다.
  이 파일은 톡방을 새로 만들지 않는다.
- 모든 조회·전송에서 ChatMember 기준으로 요청자가 그 방의 멤버인지 확인한다.
  다른 사람의 room_id를 넘겨도 읽거나 쓸 수 없다.
  (Message의 (room_id, user_id) 복합 FK가 DB 단계에서도 멤버만 저장되도록 한 번 더 막는다.)

오류 규칙
- 방 없음: LookupError / 멤버 아님: PermissionError / 잘못된 입력·상태: ValueError
- 권한 실패를 빈 목록으로 숨기지 않는다.
"""

from db import query, query_one, transaction

MAX_MESSAGE_CHARS = 2000
MAX_MESSAGE_BYTES = 65535
MAX_MESSAGE_LIMIT = 100


# ---------------------------------------------------------------------------
# 내부 도우미
# ---------------------------------------------------------------------------
def _validate_id(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"유효하지 않은 {name}입니다.")
    return value


def _require_member(room_id, user_id):
    """방이 있고 user_id가 그 방 멤버인지 확인한다. 방의 post_id·글 상태를 반환."""
    room = query_one(
        """SELECT cr.room_id, cr.post_id, p.status AS post_status,
                  EXISTS (SELECT 1 FROM ChatMember cm
                          WHERE cm.room_id = cr.room_id AND cm.user_id = %s) AS is_member
           FROM ChatRoom cr
           JOIN Post p ON p.post_id = cr.post_id
           WHERE cr.room_id = %s""",
        (user_id, room_id),
    )
    if room is None:
        raise LookupError("톡방을 찾을 수 없습니다.")
    if not room["is_member"]:
        raise PermissionError("이 톡방의 멤버만 이용할 수 있습니다.")
    return room


# ---------------------------------------------------------------------------
# 톡방 목록 (프로필·참여 관리·톡방 화면 공통)
# ---------------------------------------------------------------------------
def get_chat_rooms(user_id):
    """내가 멤버인 톡방 목록 (메시지 없는 방 포함).
    정렬: 마지막 메시지 시각(없으면 방 생성 시각) 최신순, 같으면 room_id 내림차순.
    반환 키: room_id, post_id, title, post_status, member_count, last_message, last_message_at"""
    _validate_id(user_id, "사용자 ID")
    rows = query(
        """SELECT cr.room_id, cr.post_id, c.title, p.status AS post_status, cr.created_at,
                  (SELECT COUNT(*) FROM ChatMember cm2 WHERE cm2.room_id = cr.room_id) AS member_count,
                  lm.content    AS last_message,
                  lm.created_at AS last_message_at
           FROM ChatMember me
           JOIN ChatRoom cr ON cr.room_id = me.room_id
           JOIN Post p      ON p.post_id = cr.post_id
           JOIN Content c   ON c.post_id = cr.post_id
           LEFT JOIN Message lm
                  ON lm.message_id = (SELECT m.message_id FROM Message m
                                      WHERE m.room_id = cr.room_id
                                      ORDER BY m.created_at DESC, m.message_id DESC
                                      LIMIT 1)
           WHERE me.user_id = %s
           ORDER BY COALESCE(lm.created_at, cr.created_at) DESC, cr.room_id DESC""",
        (user_id,),
    )
    return [
        {
            "room_id": int(r["room_id"]),
            "post_id": int(r["post_id"]),
            "title": r["title"],
            "post_status": r["post_status"],
            "member_count": int(r["member_count"]),
            "last_message": r["last_message"],
            "last_message_at": r["last_message_at"],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# 톡방 안
# ---------------------------------------------------------------------------
def get_chat_members(room_id, user_id):
    """톡방 멤버 목록. 방장(모집 글 작성자) 먼저, 나머지는 입장 시각·user_id순.
    반환 키: user_id, nickname, is_host"""
    _validate_id(room_id, "톡방 ID")
    _validate_id(user_id, "사용자 ID")
    _require_member(room_id, user_id)
    rows = query(
        """SELECT cm.user_id, u.nickname, (cm.user_id = p.user_id) AS is_host
           FROM ChatMember cm
           JOIN ChatRoom cr ON cr.room_id = cm.room_id
           JOIN Post p      ON p.post_id = cr.post_id
           JOIN `User` u    ON u.user_id = cm.user_id
           WHERE cm.room_id = %s
           ORDER BY is_host DESC, cm.joined_at ASC, cm.user_id ASC""",
        (room_id,),
    )
    return [
        {"user_id": int(r["user_id"]), "nickname": r["nickname"], "is_host": bool(r["is_host"])}
        for r in rows
    ]


def get_messages(room_id, user_id, limit=MAX_MESSAGE_LIMIT):
    """최근 limit개 메시지를 오래된 순서로 반환 (같은 시각이면 message_id순).
    limit는 1~100 정수. 메시지가 없으면 [].
    반환 키: message_id, user_id, nickname, content, created_at"""
    _validate_id(room_id, "톡방 ID")
    _validate_id(user_id, "사용자 ID")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_MESSAGE_LIMIT:
        raise ValueError(f"메시지 개수는 1~{MAX_MESSAGE_LIMIT} 사이여야 합니다.")
    _require_member(room_id, user_id)
    rows = query(
        """SELECT recent.message_id, recent.user_id, u.nickname, recent.content, recent.created_at
           FROM (
               SELECT message_id, user_id, content, created_at
               FROM Message
               WHERE room_id = %s
               ORDER BY created_at DESC, message_id DESC
               LIMIT %s
           ) recent
           JOIN `User` u ON u.user_id = recent.user_id
           ORDER BY recent.created_at ASC, recent.message_id ASC""",
        (room_id, limit),
    )
    for r in rows:
        r["message_id"] = int(r["message_id"])
        r["user_id"] = int(r["user_id"])
    return rows


def send_message(room_id, user_id, content):
    """메시지 전송. 앞뒤 공백 제거 후 1~2,000자, UTF-8 65,535바이트 이하.
    취소(CANCELED)된 모임의 톡방에는 보낼 수 없다.
    반환: 저장된 메시지 dict (message_id, user_id, nickname, content, created_at)"""
    _validate_id(room_id, "톡방 ID")
    _validate_id(user_id, "사용자 ID")
    if not isinstance(content, str):
        raise ValueError("메시지는 문자열이어야 합니다.")
    content = content.strip()
    if not content:
        raise ValueError("메시지를 입력해 주세요.")
    if len(content) > MAX_MESSAGE_CHARS or len(content.encode("utf-8")) > MAX_MESSAGE_BYTES:
        raise ValueError(f"메시지는 {MAX_MESSAGE_CHARS}자 이하로 입력해 주세요.")

    room = _require_member(room_id, user_id)
    if room["post_status"] == "CANCELED":
        raise ValueError("취소된 모임의 톡방에는 메시지를 보낼 수 없습니다.")

    with transaction() as cur:
        cur.execute(
            "INSERT INTO Message (room_id, user_id, content) VALUES (%s, %s, %s)",
            (room_id, user_id, content),
        )
        message_id = cur.lastrowid
        cur.execute(
            """SELECT m.message_id, m.user_id, u.nickname, m.content, m.created_at
               FROM Message m JOIN `User` u ON u.user_id = m.user_id
               WHERE m.message_id = %s""",
            (message_id,),
        )
        saved = cur.fetchone()

    saved["message_id"] = int(saved["message_id"])
    saved["user_id"] = int(saved["user_id"])
    return saved

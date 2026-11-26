"""
services/participation_service.py - 참여 신청·승인·거절·마감·식사 완료 (3번 담당)

참여 규칙
- 작성자(방장)는 Participation 행을 만들지 않는다. 확정 인원 = 작성자 1명 + ACCEPTED 참여자 수.
- 신청만으로는 확정 인원이나 톡방 멤버가 늘지 않는다 (PENDING).
- 승인은 저장 프로시저 accept_participation(04_accept_transaction.sql)이 한 트랜잭션으로 처리한다.
  Post 행을 잠그고 정원을 확인한 뒤 승인하며, 이번 승인으로 정원이 차면
  모집 마감(CLOSED) · 톡방 생성 · 멤버 추가 · 남은 대기 신청 거절까지 함께 처리한다.
- 신청·취소·거절·식사 완료도 Post 행을 SELECT ... FOR UPDATE로 잠근 뒤 처리 시점의 상태를 다시 검사한다.

오류 규칙 (README_API.md 1절)
- 입력 오류·중복·상태 충돌: ValueError
- 권한 없음 (방장이 아님, 본인 글 신청 등): PermissionError
- 대상 없음 (글·신청 내역 없음): LookupError
- DB 장애: pymysql 예외를 그대로 전달
"""

import pymysql

from db import call_procedure, mysql_error_message, query, query_one, transaction

# 저장 프로시저의 SIGNAL 메시지 → 예외 종류
_SIGNAL_SQLSTATE_ERRNO = 1644  # SIGNAL SQLSTATE '45000' 이 만드는 MySQL 오류 번호
_PERMISSION_MESSAGES = {"작성자만 승인할 수 있습니다."}

# 식사 완료는 식사 시각이 지난 뒤에만 허용할지 여부 (시연 편의상 끄려면 False)
REQUIRE_MEAL_TIME_PASSED = True


# ---------------------------------------------------------------------------
# 내부 도우미
# ---------------------------------------------------------------------------
def _validate_id(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"유효하지 않은 {name}입니다.")
    return value


def _lock_post(cur, post_id):
    """Post 행을 잠그고 반환한다. 없으면 LookupError."""
    cur.execute(
        """SELECT post_id, user_id, capacity, status, meal_time,
                  (meal_time > NOW()) AS meal_in_future
           FROM Post WHERE post_id = %s FOR UPDATE""",
        (post_id,),
    )
    post = cur.fetchone()
    if post is None:
        raise LookupError("모집 글을 찾을 수 없습니다.")
    return post


def _accepted_count(cur, post_id):
    cur.execute(
        "SELECT COUNT(*) AS cnt FROM Participation WHERE post_id = %s AND status = 'ACCEPTED'",
        (post_id,),
    )
    return int(cur.fetchone()["cnt"])


def _get_post_owner(post_id):
    row = query_one("SELECT user_id FROM Post WHERE post_id = %s", (post_id,))
    if row is None:
        raise LookupError("모집 글을 찾을 수 없습니다.")
    return int(row["user_id"])


def _require_host(post_id, host_id):
    if _get_post_owner(post_id) != host_id:
        raise PermissionError("모집 글 작성자만 처리할 수 있습니다.")


# ---------------------------------------------------------------------------
# 상세 화면 (README_API.md 8절)
# ---------------------------------------------------------------------------
def get_members(post_id):
    """확정 멤버 목록. 작성자 먼저, 나머지는 applied_at·user_id 오름차순.
    반환: [{"user_id", "nickname", "is_host"}]  글이 없으면 []"""
    _validate_id(post_id, "게시글 ID")
    rows = query(
        """SELECT m.user_id, u.nickname, m.is_host
           FROM (
               SELECT p.user_id, 1 AS is_host, p.created_at AS sort_time
               FROM Post p WHERE p.post_id = %s
               UNION ALL
               SELECT pa.user_id, 0 AS is_host, pa.applied_at AS sort_time
               FROM Participation pa
               WHERE pa.post_id = %s AND pa.status = 'ACCEPTED'
           ) m
           JOIN `User` u ON u.user_id = m.user_id
           ORDER BY m.is_host DESC, m.sort_time ASC, m.user_id ASC""",
        (post_id, post_id),
    )
    return [
        {"user_id": int(r["user_id"]), "nickname": r["nickname"], "is_host": bool(r["is_host"])}
        for r in rows
    ]


def get_application_status(post_id, user_id):
    """내 신청 상태: 'PENDING'|'ACCEPTED'|'REJECTED'|'CANCELED', 신청 내역이 없으면 None.
    작성자 여부는 화면에서 Post.user_id로 따로 판단한다."""
    _validate_id(post_id, "게시글 ID")
    _validate_id(user_id, "사용자 ID")
    row = query_one(
        "SELECT status FROM Participation WHERE post_id = %s AND user_id = %s",
        (post_id, user_id),
    )
    return row["status"] if row else None


def apply_to_post(post_id, user_id):
    """참여 신청. 성공 시 {"post_id", "user_id", "status": "PENDING"}.
    - 글이 OPEN이고 확정 인원이 정원 미만일 때만 가능
    - 본인 글 신청은 PermissionError
    - PENDING·ACCEPTED·REJECTED 내역이 있으면 ValueError (중복 신청 방지)
    - 이전에 CANCELED였다면 PENDING으로 되돌리고 applied_at을 갱신"""
    _validate_id(post_id, "게시글 ID")
    _validate_id(user_id, "사용자 ID")

    with transaction() as cur:
        post = _lock_post(cur, post_id)
        if int(post["user_id"]) == user_id:
            raise PermissionError("본인이 작성한 모임에는 신청할 수 없습니다.")
        if post["status"] != "OPEN":
            raise ValueError("모집 중인 글이 아닙니다.")
        if _accepted_count(cur, post_id) + 1 >= int(post["capacity"]):
            raise ValueError("정원이 가득 찼습니다.")

        cur.execute("SELECT 1 FROM `User` WHERE user_id = %s", (user_id,))
        if cur.fetchone() is None:
            raise LookupError("사용자를 찾을 수 없습니다.")

        cur.execute(
            "SELECT status FROM Participation WHERE post_id = %s AND user_id = %s FOR UPDATE",
            (post_id, user_id),
        )
        existing = cur.fetchone()
        if existing is None:
            cur.execute(
                "INSERT INTO Participation (post_id, user_id, status) VALUES (%s, %s, 'PENDING')",
                (post_id, user_id),
            )
        elif existing["status"] == "CANCELED":
            cur.execute(
                """UPDATE Participation SET status = 'PENDING', applied_at = NOW()
                   WHERE post_id = %s AND user_id = %s""",
                (post_id, user_id),
            )
        elif existing["status"] == "PENDING":
            raise ValueError("이미 신청한 모임입니다. 방장의 승인을 기다려 주세요.")
        elif existing["status"] == "ACCEPTED":
            raise ValueError("이미 참여가 확정된 모임입니다.")
        else:  # REJECTED
            raise ValueError("거절된 신청은 다시 신청할 수 없습니다.")

    return {"post_id": post_id, "user_id": user_id, "status": "PENDING"}


def cancel_application(post_id, user_id):
    """대기 중(PENDING) 신청 취소. 성공 시 {"post_id", "user_id", "status": "CANCELED"}.
    이미 취소된 신청이면 그대로 성공. 신청 내역이 없으면 LookupError,
    승인·거절된 신청은 ValueError (승인 후 탈퇴는 별도 기능)."""
    _validate_id(post_id, "게시글 ID")
    _validate_id(user_id, "사용자 ID")

    with transaction() as cur:
        _lock_post(cur, post_id)  # 승인 프로시저와 같은 순서로 잠가 동시 처리 충돌을 막는다
        cur.execute(
            "SELECT status FROM Participation WHERE post_id = %s AND user_id = %s FOR UPDATE",
            (post_id, user_id),
        )
        row = cur.fetchone()
        if row is None:
            raise LookupError("신청 내역을 찾을 수 없습니다.")
        if row["status"] == "PENDING":
            cur.execute(
                """UPDATE Participation SET status = 'CANCELED'
                   WHERE post_id = %s AND user_id = %s""",
                (post_id, user_id),
            )
        elif row["status"] == "ACCEPTED":
            raise ValueError("이미 승인된 참여는 취소할 수 없습니다.")
        elif row["status"] == "REJECTED":
            raise ValueError("거절된 신청은 취소할 수 없습니다.")
        # CANCELED: 이미 원하는 상태이므로 그대로 성공

    return {"post_id": post_id, "user_id": user_id, "status": "CANCELED"}


# ---------------------------------------------------------------------------
# 참여 관리 화면 (README_FRONTEND.md 4.3절)
# ---------------------------------------------------------------------------
def get_my_applications(user_id):
    """신청자 본인의 참여 내역 (취소·거절 포함), 최신 신청순.
    반환 키: post_id, title, status(참여 상태), post_status(글 상태), meal_time, region, applied_at"""
    _validate_id(user_id, "사용자 ID")
    rows = query(
        """SELECT pa.post_id, c.title, pa.status, p.status AS post_status,
                  p.meal_time, p.region, pa.applied_at
           FROM Participation pa
           JOIN Post p    ON p.post_id = pa.post_id
           JOIN Content c ON c.post_id = pa.post_id
           WHERE pa.user_id = %s
           ORDER BY pa.applied_at DESC, pa.post_id DESC""",
        (user_id,),
    )
    for r in rows:
        r["post_id"] = int(r["post_id"])
    return rows


def get_post_applications(post_id, host_id):
    """방장이 자기 글의 신청자를 조회. 대기(PENDING) 먼저, 그다음 신청순, 같은 시각이면 user_id순.
    반환 키: user_id, nickname, status, applied_at
    글이 없으면 LookupError, 작성자가 아니면 PermissionError."""
    _validate_id(post_id, "게시글 ID")
    _validate_id(host_id, "사용자 ID")
    _require_host(post_id, host_id)
    rows = query(
        """SELECT pa.user_id, u.nickname, pa.status, pa.applied_at
           FROM Participation pa
           JOIN `User` u ON u.user_id = pa.user_id
           WHERE pa.post_id = %s
           ORDER BY (pa.status = 'PENDING') DESC, pa.applied_at ASC, pa.user_id ASC""",
        (post_id,),
    )
    for r in rows:
        r["user_id"] = int(r["user_id"])
    return rows


def accept_application(post_id, host_id, applicant_id):
    """신청 승인. 저장 프로시저 accept_participation(host_id, post_id, applicant_id)를 사용한다.
    이번 승인으로 정원이 차면 프로시저가 마감·톡방 생성·멤버 추가·남은 대기 거절까지 처리한다.
    반환: {"post_id", "user_id", "status": "ACCEPTED", "post_status", "room_id"(톡방이 생겼으면 int, 아니면 None)}"""
    _validate_id(post_id, "게시글 ID")
    _validate_id(host_id, "사용자 ID")
    _validate_id(applicant_id, "신청자 ID")
    _get_post_owner(post_id)  # 글이 없으면 LookupError (프로시저는 권한 오류로만 알려 주므로 먼저 구분)

    try:
        call_procedure("accept_participation", (host_id, post_id, applicant_id))
    except pymysql.MySQLError as err:
        if err.args and err.args[0] == _SIGNAL_SQLSTATE_ERRNO:
            message = mysql_error_message(err)
            if message in _PERMISSION_MESSAGES:
                raise PermissionError(message) from err
            raise ValueError(message) from err
        raise

    row = query_one(
        """SELECT p.status AS post_status, cr.room_id
           FROM Post p LEFT JOIN ChatRoom cr ON cr.post_id = p.post_id
           WHERE p.post_id = %s""",
        (post_id,),
    )
    return {
        "post_id": post_id,
        "user_id": applicant_id,
        "status": "ACCEPTED",
        "post_status": row["post_status"],
        "room_id": int(row["room_id"]) if row["room_id"] is not None else None,
    }


def reject_application(post_id, host_id, applicant_id):
    """대기 중인 신청 거절. 반환: {"post_id", "user_id", "status": "REJECTED"}"""
    _validate_id(post_id, "게시글 ID")
    _validate_id(host_id, "사용자 ID")
    _validate_id(applicant_id, "신청자 ID")

    with transaction() as cur:
        post = _lock_post(cur, post_id)
        if int(post["user_id"]) != host_id:
            raise PermissionError("모집 글 작성자만 거절할 수 있습니다.")
        if post["status"] != "OPEN":
            raise ValueError("모집 중인 글이 아닙니다.")
        affected = cur.execute(
            """UPDATE Participation SET status = 'REJECTED'
               WHERE post_id = %s AND user_id = %s AND status = 'PENDING'""",
            (post_id, applicant_id),
        )
        if affected == 0:
            raise ValueError("대기 중인 신청이 없습니다.")

    return {"post_id": post_id, "user_id": applicant_id, "status": "REJECTED"}


def complete_meal(post_id, host_id):
    """식사 완료 처리 (방장만, CLOSED → COMPLETED). 완료된 모임에서 리뷰를 쓸 수 있게 된다.
    REQUIRE_MEAL_TIME_PASSED가 True면 식사 시각이 지난 뒤에만 가능.
    반환: {"post_id", "status": "COMPLETED"}"""
    _validate_id(post_id, "게시글 ID")
    _validate_id(host_id, "사용자 ID")

    with transaction() as cur:
        post = _lock_post(cur, post_id)
        if int(post["user_id"]) != host_id:
            raise PermissionError("모집 글 작성자만 식사 완료로 바꿀 수 있습니다.")
        if post["status"] == "COMPLETED":
            return {"post_id": post_id, "status": "COMPLETED"}
        if post["status"] != "CLOSED":
            raise ValueError("모집이 마감된 모임만 식사 완료로 바꿀 수 있습니다.")
        if REQUIRE_MEAL_TIME_PASSED and post["meal_in_future"]:
            raise ValueError("식사 시간이 지난 뒤에 완료 처리할 수 있습니다.")
        cur.execute("UPDATE Post SET status = 'COMPLETED' WHERE post_id = %s", (post_id,))

    return {"post_id": post_id, "status": "COMPLETED"}

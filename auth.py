"""
auth.py - 회원가입, 로그인, 로그아웃, 비밀번호 변경

비밀번호는 bcrypt 해시로만 저장하고 원문은 저장하지 않는다.

팀 공통 약속 (README)
- login()은 인증 결과만 반환한다: 성공 {"user_id": 1, "nickname": "지혁"}, 실패 None
- 로그인 화면에서 st.session_state["user"]에 저장한다.
- get_current_user(), require_login(), logout()은 같은 세션 값을 사용한다.

화면에서 쓰는 방법)
    import streamlit as st
    import auth

    user = auth.login(login_id, password)    # 실패하면 None
    if user:
        st.session_state["user"] = user

    me = auth.require_login()     # 로그인 안 했으면 안내 후 페이지 중단
    auth.logout()
"""

import re

import bcrypt
import pymysql

from db import query_one, execute, transaction

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@gachon\.ac\.kr$")
MIN_PASSWORD_LENGTH = 8


class AuthError(Exception):
    """화면에 그대로 보여줄 수 있는 오류 메시지를 담는다."""


# ---------------------------------------------------------
# 비밀번호 해시
# ---------------------------------------------------------
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password, password_hash):
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # 형식이 bcrypt가 아닌 해시 (예: 데모 문자열)
        return False


def _check_password_rule(password):
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AuthError(f"비밀번호는 {MIN_PASSWORD_LENGTH}자 이상이어야 합니다.")


# ---------------------------------------------------------
# 회원가입
# ---------------------------------------------------------
def signup(login_id, gachon_email, password, name, nickname, birth_year, neighborhood):
    """회원을 만들고 빈 프로필도 함께 만든다. 새 user_id를 반환한다.
    입력이 잘못되었거나 중복이면 AuthError를 던진다."""
    login_id = login_id.strip()
    gachon_email = gachon_email.strip().lower()
    nickname = nickname.strip()

    if not all([login_id, gachon_email, password, name.strip(), nickname, neighborhood.strip()]):
        raise AuthError("모든 항목을 입력해 주세요.")
    if not EMAIL_PATTERN.match(gachon_email):
        raise AuthError("가천대 이메일(@gachon.ac.kr)만 가입할 수 있습니다.")
    _check_password_rule(password)
    if not 1950 <= int(birth_year) <= 2010:
        raise AuthError("출생 연도를 확인해 주세요.")

    try:
        with transaction() as cur:
            cur.execute(
                """INSERT INTO `User`
                   (login_id, gachon_email, password_hash, name, nickname, birth_year, neighborhood)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (login_id, gachon_email, hash_password(password), name.strip(),
                 nickname, int(birth_year), neighborhood.strip()),
            )
            user_id = cur.lastrowid
            cur.execute("INSERT INTO Profile (user_id) VALUES (%s)", (user_id,))
        return user_id
    except pymysql.IntegrityError as err:
        message = str(err)
        if "uq_user_login_id" in message:
            raise AuthError("이미 사용 중인 아이디입니다.") from err
        if "uq_user_email" in message:
            raise AuthError("이미 가입된 이메일입니다.") from err
        if "uq_user_nickname" in message:
            raise AuthError("이미 사용 중인 닉네임입니다.") from err
        raise AuthError("회원가입에 실패했습니다.") from err


# ---------------------------------------------------------
# 로그인 / 비밀번호 변경
# ---------------------------------------------------------
def login(login_id, password):
    """아이디와 비밀번호가 맞으면 {"user_id": ..., "nickname": ...}를, 틀리면 None을 반환한다.
    login_id 자리에 가천 이메일을 넣어도 로그인된다.
    세션 저장은 하지 않는다 (로그인 화면에서 st.session_state["user"]에 저장)."""
    key = (login_id or "").strip()
    if not key or not password:
        return None
    row = query_one(
        """SELECT user_id, nickname, password_hash
           FROM `User`
           WHERE login_id = %s OR gachon_email = %s""",
        (key, key.lower()),
    )
    if row is None or not verify_password(password, row["password_hash"]):
        return None
    return {"user_id": row["user_id"], "nickname": row["nickname"]}


def change_password(user_id, current_password, new_password):
    """현재 비밀번호를 확인한 뒤 새 비밀번호로 바꾼다. 실패하면 AuthError."""
    row = query_one("SELECT password_hash FROM `User` WHERE user_id = %s", (user_id,))
    if row is None:
        raise AuthError("회원 정보를 찾을 수 없습니다.")
    if not verify_password(current_password, row["password_hash"]):
        raise AuthError("현재 비밀번호가 일치하지 않습니다.")
    if current_password == new_password:
        raise AuthError("새 비밀번호가 현재 비밀번호와 같습니다.")
    _check_password_rule(new_password)
    execute("UPDATE `User` SET password_hash = %s WHERE user_id = %s",
            (hash_password(new_password), user_id))


# ---------------------------------------------------------
# Streamlit 로그인 상태 (session_state)
# ---------------------------------------------------------
def get_current_user():
    """현재 로그인한 사용자 {"user_id": ..., "nickname": ...} 또는 None."""
    import streamlit as st
    return st.session_state.get("user")


def logout():
    """로그인 정보를 세션에서 삭제한다."""
    import streamlit as st
    st.session_state.pop("user", None)


def require_login():
    """로그인하지 않았으면 안내 문구를 띄우고 화면 실행을 멈춘다.
    로그인했으면 사용자 정보를 반환한다. 각 페이지 맨 위에서 호출한다."""
    import streamlit as st
    user = get_current_user()
    if user is None:
        st.warning("로그인이 필요합니다. 홈 화면에서 로그인해 주세요.")
        st.stop()
    return user

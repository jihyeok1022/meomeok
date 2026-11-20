"""
db.py - MySQL 연결과 쿼리 실행 도우미

모든 서비스 파일은 이 파일의 함수만 사용한다.
- 값은 반드시 %s 자리표시자 + params 튜플로 넘긴다 (문자열 연결 금지: SQL injection 방지).
- SELECT 결과는 딕셔너리 리스트로 돌려준다. 예) [{"post_id": 1, "title": "..."}]

사용 예)
    from db import query, query_one, execute, transaction, call_procedure

    rows = query("SELECT * FROM Post WHERE user_id = %s", (user_id,))
    post = query_one("SELECT * FROM Post WHERE post_id = %s", (post_id,))
    new_id = execute("INSERT INTO Comment (user_id, post_id, content) VALUES (%s, %s, %s)", (u, p, text))

    # 여러 문장을 한 번에 성공/실패시켜야 할 때
    with transaction() as cur:
        cur.execute("INSERT INTO Post (...) VALUES (...)", (...))
        post_id = cur.lastrowid
        cur.execute("INSERT INTO Content (...) VALUES (...)", (post_id, ...))

    # 저장 프로시저 (승인 등)는 따로 부른다
    call_procedure("accept_participation", (host_id, post_id, user_id))
"""

import os
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor


def _load_config():
    """접속 정보를 .streamlit/secrets.toml의 [mysql]에서 읽는다.
    Streamlit 밖에서 테스트할 때는 MYSQL_* 환경 변수를 사용한다."""
    try:
        import streamlit as st
        cfg = dict(st.secrets["mysql"])
    except Exception:
        cfg = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": os.getenv("MYSQL_PORT", 3306),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DATABASE", "meal_mate"),
        }
    cfg["port"] = int(cfg.get("port", 3306))
    return cfg


def get_connection():
    """새 MySQL 연결(DictCursor, autocommit 꺼짐)을 만든다. [팀 공통 함수]
    연결을 연 쪽에서 commit/rollback과 close()를 책임진다.

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE ... WHERE id = %s", (x,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    위 과정을 대신 해 주는 query / query_one / execute / transaction을 써도 된다."""
    cfg = _load_config()
    return pymysql.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )


def query(sql, params=None):
    """SELECT 결과 전체를 딕셔너리 리스트로 반환한다. 결과가 없으면 []."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return list(cur.fetchall())
    finally:
        conn.close()


def query_one(sql, params=None):
    """SELECT 결과의 첫 행을 딕셔너리로 반환한다. 결과가 없으면 None."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()
    finally:
        conn.close()


def execute(sql, params=None):
    """INSERT / UPDATE / DELETE 한 문장을 실행하고 커밋한다.
    INSERT면 새로 생긴 AUTO_INCREMENT 값을, 그 외에는 바뀐 행 수를 반환한다."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            affected = cur.execute(sql, params)
            conn.commit()
            return cur.lastrowid if cur.lastrowid else affected
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def transaction():
    """with 블록 안의 문장을 한 트랜잭션으로 묶는다.
    블록이 정상 종료되면 COMMIT, 예외가 나면 ROLLBACK 후 예외를 다시 던진다.
    주의: 저장 프로시저는 이 안에서 다른 문장과 섞어 부르지 말고 call_procedure()를 쓴다."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def call_procedure(name, args=()):
    """저장 프로시저를 단독으로 호출하고 결과 행(있으면)을 딕셔너리 리스트로 반환한다.
    예) call_procedure("accept_participation", (host_id, post_id, user_id))

    accept_participation처럼 프로시저 안에서 START TRANSACTION을 하는 경우,
    같은 연결에서 먼저 실행한 문장이 자동으로 COMMIT된다.
    그래서 다른 문장과 한 트랜잭션으로 묶지 않고 이 함수로 따로 부른다.
    프로시저가 SIGNAL로 오류를 내면 pymysql.MySQLError가 발생하며,
    mysql_error_message(err)로 '정원이 가득 찼습니다.' 같은 문구를 꺼낼 수 있다."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.callproc(name, args)
            rows = list(cur.fetchall())
        conn.commit()
        return rows
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def mysql_error_message(err):
    """pymysql 예외에서 사람이 읽을 메시지만 꺼낸다.
    예) 프로시저의 SIGNAL 메시지 '정원이 가득 찼습니다.'"""
    if isinstance(err, pymysql.MySQLError) and len(err.args) >= 2:
        return str(err.args[1])
    return str(err)

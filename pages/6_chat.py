"""Meal chat UI. Run via app.py. Proposed service API: README_FRONTEND.md."""
from pathlib import Path

import streamlit as st

import auth
from services import chat_service, post_service
from ui_common import CSS, asset, e, user_avatar


PAGE_CSS = """
.chat-heading{background:white;padding:8px 20px 14px;font-size:20px;font-weight:800;}
.st-key-chat_body{padding:12px 16px 24px!important;}
.st-key-chat_body [data-testid='stVerticalBlock']{gap:8px!important;}
.st-key-chat_body [data-testid='stHorizontalBlock']{gap:8px!important;}
.st-key-chat_body [data-testid='stColumn']{min-width:0!important;}
.st-key-chat_body [class*='st-key-chat_room_card_']{background:white;border:1px solid var(--line);border-radius:14px;padding:12px!important;}
.chat-room-line{display:flex;align-items:center;gap:10px;}
.chat-avatar{width:40px;height:40px;flex-shrink:0;border-radius:50%;background:#ffdbc8;display:flex;align-items:center;justify-content:center;color:#d75d27;font-weight:800;}
.chat-room-info{flex:1;min-width:0;}
.chat-room-title{font-size:15px;font-weight:800;overflow-wrap:anywhere;}
.chat-room-preview{font-size:13px;color:#666;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.chat-muted{font-size:11px;color:var(--muted);overflow-wrap:anywhere;}
.chat-empty{background:white;border:1px solid var(--line);border-radius:12px;padding:17px;text-align:center;color:#888;font-size:12px;}
.chat-banner{background:#fff0e7;border-radius:10px;padding:12px;font-size:13px;white-space:pre-wrap;overflow-wrap:anywhere;}
.chat-date{text-align:center;margin:8px 0;color:#888;font-size:11px;}
.chat-message{display:flex;align-items:flex-end;gap:6px;margin:8px 0;}
.chat-message.mine{justify-content:flex-end;}
.chat-message .user-avatar{align-self:flex-start;}
.chat-message-body{max-width:78%;min-width:0;}
.chat-sender{font-size:11px;color:#777;margin-bottom:4px;overflow-wrap:anywhere;}
.chat-bubble{background:white;border-radius:13px 13px 13px 3px;padding:10px 12px;font-size:13px;white-space:pre-wrap;overflow-wrap:anywhere;}
.chat-message.mine .chat-bubble{background:var(--orange);color:white;border-radius:13px 13px 3px 13px;}
.chat-time{font-size:10px;color:#999;white-space:nowrap;}
.st-key-chat_body button{border:1px solid #e7e5e3;border-radius:9px;background:white;color:#333;font-size:13px;min-height:36px;}
.st-key-chat_body button[kind='primary'],.st-key-chat_body button[data-testid='stBaseButton-primary'],.st-key-chat_body button[data-testid='stFormSubmitButton']{border-color:var(--orange)!important;}
.st-key-chat_body button[kind='primary'],.st-key-chat_body button[data-testid='stBaseButton-primary']{background:var(--orange)!important;color:white!important;}
.st-key-chat_body button:disabled{background:#f1f0ee!important;color:#999!important;}
.st-key-bottom_nav .st-key-nav_home button{color:#a0a0a0!important;font-weight:400;}
.st-key-bottom_nav .st-key-nav_chat button{color:var(--orange)!important;font-weight:700;}
.st-key-bottom_nav button{position:relative;background-image:none!important;}
.st-key-bottom_nav button:before{content:'';position:absolute;top:0;left:50%;transform:translateX(-50%);width:24px;height:24px;background:currentColor;mask-size:contain;mask-repeat:no-repeat;mask-position:center;}
"""
for nav_key, asset_name in (("home", "home"), ("apply", "calendar"), ("chat", "groups"), ("profile", "user")):
    PAGE_CSS += f'.st-key-nav_{nav_key} button:before{{mask-image:url("{asset(asset_name)}");}}\n'


def html(markup):
    st.markdown(markup, unsafe_allow_html=True)


def empty(message):
    html(f'<div class="chat-empty">{e(message)}</div>')


def date_label(value, fmt="%m.%d %H:%M"):
    return value.strftime(fmt) if hasattr(value, "strftime") else str(value or "")


def read_list(func, args, required):
    try:
        rows = func(*args)
        if not isinstance(rows, list) or any(not isinstance(row, dict) or not required.issubset(row) for row in rows):
            raise TypeError("Unexpected service response")
        return rows
    except (ValueError, PermissionError, LookupError) as exc:
        st.error(str(exc))
    except Exception:
        st.error("정보를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.")
    return None


def navigate(filename, **params):
    path = Path(__file__).resolve().parent / filename
    if not path.is_file() or not path.read_text(encoding="utf-8-sig").strip():
        st.info("해당 화면은 아직 준비 중이에요.")
        return
    st.switch_page(f"pages/{filename}", query_params=params or None)


def back_to_rooms():
    st.query_params.pop("room", None)
    st.rerun()


def bottom_nav():
    items = [("모집 글", "1_feed.py", "nav_home"), ("내 신청", "5_participation.py", "nav_apply"),
             ("톡방", None, "nav_chat"), ("내 프로필", "4_profile.py", "nav_profile")]
    with st.container(key="bottom_nav"):
        for col, (label, filename, key) in zip(st.columns(4), items):
            with col, st.container(key=key):
                if st.button(label, key=f"chat_{key}", use_container_width=True):
                    if filename:
                        navigate(filename)
                    elif "room" in st.query_params:
                        back_to_rooms()


def render_rooms(rooms):
    if not rooms:
        empty("아직 참여 중인 톡방이 없어요.")
        st.caption("정원이 채워져 모집이 마감되면 모임의 톡방이 열려요.")
        if st.button("모집 글 둘러보기", key="chat_browse", use_container_width=True):
            navigate("1_feed.py")
        return
    st.caption(f"참여 중인 톡방 {len(rooms)}개")
    for room in rooms:
        room_id = room["room_id"]
        count = room.get("member_count")
        members = f"{count}명" if count is not None else ""
        when = date_label(room.get("last_message_at"))
        with st.container(key=f"chat_room_card_{room_id}"):
            html(f'<div class="chat-room-line"><div class="chat-avatar">톡</div>'
                 f'<div class="chat-room-info"><div class="chat-room-title">{e(room["title"])}</div>'
                 f'<div class="chat-muted">{e(members)} {e(when)}</div>'
                 f'<div class="chat-room-preview">{e(room.get("last_message") or "아직 메시지가 없어요.")}</div></div></div>')
            if st.button("톡방 입장", key=f"chat_open_{room_id}", use_container_width=True):
                st.query_params["room"] = str(room_id)
                st.rerun()


def render_members(room_id, user_id):
    with st.expander("참여 멤버 보기"):
        func = getattr(chat_service, "get_chat_members", None)
        if not callable(func):
            st.caption("멤버 조회 기능은 연동 준비 중이에요.")
            return
        rows = read_list(func, (room_id, user_id), {"user_id", "nickname"})
        if rows is None:
            return
        if not rows:
            st.caption("표시할 멤버가 없어요.")
        for row in rows:
            tags = (" · 모집자" if row.get("is_host") else "") + (" · 나" if row["user_id"] == user_id else "")
            # Plain escaped text, not user-supplied markup.
            html(f'<div class="chat-sender">{e(row["nickname"])}{e(tags)}</div>')


def render_messages(rows, user_id):
    if not rows:
        empty("아직 메시지가 없어요. 먼저 인사를 건네 보세요!")
        return
    previous_day = None
    chunks = []
    for row in rows:
        stamp = row.get("created_at")
        day = date_label(stamp, "%Y년 %m월 %d일")
        if day and day != previous_day:
            chunks.append(f'<div class="chat-date">{e(day)}</div>')
            previous_day = day
        time = e(date_label(stamp, "%H:%M"))
        content = e(row["content"])
        if row["user_id"] == user_id:
            chunks.append(f'<div class="chat-message mine"><span class="chat-time">{time}</span>'
                          f'<div class="chat-message-body"><div class="chat-bubble">{content}</div></div></div>')
        else:
            nickname = str(row["nickname"] or "회원")
            chunks.append(f'<div class="chat-message">{user_avatar(row["user_id"], 29)}'
                          f'<div class="chat-message-body"><div class="chat-sender">{e(nickname)}</div>'
                          f'<div class="chat-bubble">{content}</div></div><span class="chat-time">{time}</span></div>')
    html("".join(chunks))


def render_composer(room_id, user_id, available):
    send = getattr(chat_service, "send_message", None)
    if not callable(send) or not available:
        st.caption("메시지 전송 연동 준비 중" if not callable(send) else "메시지를 조회한 뒤 전송할 수 있어요.")
        st.text_area("메시지 입력", placeholder="메시지를 입력하세요", disabled=True, key=f"chat_disabled_{user_id}_{room_id}", height=70, label_visibility="collapsed")
        st.button("전송", disabled=True, key=f"chat_disabled_send_{user_id}_{room_id}", use_container_width=True)
        return
    draft = f"chat_draft_{user_id}_{room_id}"
    reset = f"chat_reset_{user_id}_{room_id}"
    if st.session_state.pop(reset, False):
        st.session_state[draft] = ""
    with st.form(f"chat_form_{user_id}_{room_id}", clear_on_submit=False, border=False):
        content = st.text_area("메시지 입력", placeholder="메시지를 입력하세요", key=draft, height=70, max_chars=2000, label_visibility="collapsed")
        submitted = st.form_submit_button("전송", type="primary", use_container_width=True)
    if not submitted:
        return
    content = content.strip()
    if not content:
        st.warning("메시지를 입력해 주세요.")
        return
    try:
        result = send(room_id, user_id, content)
        if result is False:
            raise ValueError("메시지를 전송하지 못했어요.")
    except (ValueError, PermissionError, LookupError) as exc:
        st.error(str(exc))
    except Exception:
        st.error("전송 결과를 확인하지 못했어요. 새로고침으로 확인한 후 다시 시도해 주세요.")
    else:
        st.session_state[reset] = True
        st.rerun()


def render_room(room, user_id):
    room_id, post_id = room["room_id"], room["post_id"]
    if st.button("‹ 톡방 목록", key="chat_back", use_container_width=True):
        back_to_rooms()
    html(f'<div class="chat-room-title">{e(room["title"])}</div>'
         f'<div class="chat-muted">참여 인원 {e(room.get("member_count") if room.get("member_count") is not None else "확인 중")}명</div>')
    # Read the existing public post contract; no separate SQL or invented place field.
    try:
        post = post_service.get_post(post_id, user_id)
    except Exception:
        post = None
        st.caption("모임 정보를 불러오지 못했어요.")
    if post:
        html(f'<div class="chat-banner">{e(date_label(post.get("meal_time")))} · {e(post.get("region") or "")}\n{e(post.get("body") or "")}</div>')
    if st.button("모임 정보 보기", key=f"chat_post_{room_id}", use_container_width=True):
        st.session_state["selected_post_id"] = post_id
        st.session_state["detail_scroll_to_top"] = True
        navigate("3_post_detail.py", post=post_id)
    render_members(room_id, user_id)
    # Manual refresh intentionally avoids clearing a draft through automatic reruns.
    st.button("새 메시지 확인", key=f"chat_refresh_{room_id}", use_container_width=True)
    func = getattr(chat_service, "get_messages", None)
    rows = None
    if not callable(func):
        empty("메시지 조회 기능은 연동 준비 중이에요.")
    else:
        rows = read_list(func, (room_id, user_id, 100), {"message_id", "user_id", "nickname", "content", "created_at"})
        if rows is not None:
            st.caption("최근 메시지 최대 100개")
            render_messages(rows, user_id)
    render_composer(room_id, user_id, rows is not None)


def main():
    st.set_page_config(page_title="머먹 · 톡방", page_icon="🍚", layout="centered")
    user_id = auth.require_login()["user_id"]
    html(f"<style>{CSS}{PAGE_CSS}</style>")
    html('<div class="status-bar" aria-hidden="true"><strong>9:41</strong><span>LTE 100%</span></div>'
         '<div class="chat-heading">톡방</div>')
    with st.container(key="chat_body"):
        func = getattr(chat_service, "get_chat_rooms", None)
        if not callable(func):
            empty("톡방 목록은 백엔드 연동 준비 중이에요.")
            st.caption("참여가 확정된 모임의 대화방을 이곳에서 확인할 수 있어요.")
            if "room" in st.query_params and st.button("톡방 목록", key="chat_wait_back"):
                back_to_rooms()
        else:
            rooms = read_list(func, (user_id,), {"room_id", "post_id", "title"})
            if rooms is not None:
                requested = st.query_params.get("room")
                if requested is None:
                    render_rooms(rooms)
                else:
                    # Only rooms returned for the signed-in user may be opened.
                    # Backend must still check membership on EVERY read and write.
                    selected = next((r for r in rooms if str(r["room_id"]) == str(requested)), None)
                    if selected is None:
                        st.warning("참여하지 않은 톡방이거나 존재하지 않는 톡방이에요.")
                        if st.button("톡방 목록으로", key="chat_forbidden_back"):
                            back_to_rooms()
                    else:
                        render_room(selected, user_id)
    bottom_nav()


if __name__ == "__main__":
    main()

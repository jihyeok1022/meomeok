"""My applications and hosted meals. Run via app.py.
Service contracts marked proposed are documented in README_FRONTEND.md.
"""
from pathlib import Path

import streamlit as st

import auth
from services import user_service, participation_service, chat_service, review_service
from ui_common import CSS, asset, e, user_avatar


PAGE_CSS = """
.apply-heading{padding:20px 16px 8px;font-size:22px;font-weight:800;}
[data-testid='stMainBlockContainer'] .st-key-apply_body{padding:0 16px 24px!important;gap:12px!important;}
[data-testid='stMainBlockContainer'] .st-key-apply_body [data-testid='stVerticalBlock']{gap:8px!important;}
.st-key-apply_body [data-testid='stRadio']{width:100%!important;}
.st-key-apply_body [data-testid='stRadio'] [role='radiogroup']{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0;width:100%;}
.st-key-apply_body [data-testid='stRadio'] label{margin:0;min-height:44px;justify-content:center;
 border-bottom:1px solid #ddd8d4;cursor:pointer;color:var(--muted);}
.st-key-apply_body [data-testid='stRadio'] label > div:has(> [data-testid='stMarkdownContainer']){justify-content:center;}
.st-key-apply_body [data-testid='stRadio'] label > div > div:first-child:not([data-testid='stMarkdownContainer']),
.st-key-apply_body [data-testid='stRadio'] label > div:first-of-type:not(:has([data-testid='stMarkdownContainer'])):not([data-testid='stMarkdownContainer']){
 display:none;}
.st-key-apply_body [data-testid='stRadio'] label:has(input:checked){border-bottom:2px solid var(--orange);
 color:var(--ink);font-weight:700;}
.st-key-apply_body [data-testid='stRadio'] label:has(input:focus-visible){outline:2px solid #b5461b;outline-offset:-3px;}
.st-key-apply_body [data-testid='stRadio'] label p{color:inherit;font-size:14px;}
.st-key-apply_body [data-testid='stRadio'] label:has(input:checked) p{font-weight:700;}
.st-key-apply_body [data-testid='stHorizontalBlock']{gap:8px!important;}
.st-key-apply_body [data-testid='stColumn']{min-width:0!important;}
.st-key-apply_body [class*='st-key-apply_card_']{background:white;border:1px solid var(--line);border-radius:14px;padding:13px!important;}
.apply-title{font-size:15px;font-weight:800;overflow-wrap:anywhere;}
.apply-meta{font-size:12px;color:var(--muted);line-height:1.7;overflow-wrap:anywhere;}
.apply-top{display:flex;align-items:flex-start;justify-content:space-between;gap:8px;}
.apply-badge{display:inline-block;font-size:11px;font-weight:700;white-space:nowrap;border-radius:6px;padding:3px 7px;background:#eee;color:#777;}
.apply-badge.pending{background:#fff3cd;color:#8a6411;}
.apply-badge.accepted,.apply-badge.completed{background:#e5f4eb;color:#24734a;}
.apply-badge.open{background:#fff0e7;color:#c65a24;}
.apply-badge.closed{background:#e8eef7;color:#526d91;}
.apply-section{font-size:14px;font-weight:750;margin:5px 0 0;}
.apply-note{padding:0 3px;color:var(--muted);font-size:12px;line-height:1.6;}
.apply-empty{background:white;border:1px solid var(--line);border-radius:12px;padding:16px;text-align:center;color:#888;font-size:12px;}
.apply-person{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:700;overflow-wrap:anywhere;}
.st-key-apply_body button{border:1px solid #e7e5e3;border-radius:9px;background:white;color:#333;font-size:13px;min-height:36px;}
.st-key-apply_body button[kind='primary'],.st-key-apply_body button[data-testid='stBaseButton-primary']{background:var(--orange)!important;color:white!important;border-color:var(--orange)!important;}
.st-key-apply_body button:disabled{background:#f1f0ee!important;color:#999!important;}
.st-key-apply_body [class*='st-key-apply_post_link_'] button{position:relative;justify-content:flex-start;
 border:0;border-top:1px solid var(--line);border-radius:0;background:transparent;color:var(--ink);
 padding:8px 18px 0 2px;min-height:38px;font-weight:650;text-align:left;}
.st-key-apply_body [class*='st-key-apply_post_link_'] button > div{justify-content:flex-start;}
.st-key-apply_body [class*='st-key-apply_post_link_'] button::after{content:"";position:absolute;right:5px;top:calc(50% + 1px);
 width:7px;height:7px;border:solid var(--muted);border-width:0 1.5px 1.5px 0;transform:rotate(-45deg);}
.st-key-apply_body [class*='st-key-apply_post_link_'] button:hover{color:#b5461b;background:#fff9f5;}
.st-key-bottom_nav .st-key-nav_home button{color:#a0a0a0!important;font-weight:400;}
.st-key-bottom_nav .st-key-nav_apply button{color:var(--orange)!important;font-weight:700;}
.st-key-bottom_nav button{position:relative;background-image:none!important;}
.st-key-bottom_nav button:before{content:'';position:absolute;top:0;left:50%;transform:translateX(-50%);width:24px;height:24px;background:currentColor;mask-size:contain;mask-repeat:no-repeat;mask-position:center;}
"""
for nav_key, asset_name in (("home", "home"), ("apply", "calendar"), ("chat", "groups"), ("profile", "user")):
    PAGE_CSS += f'.st-key-nav_{nav_key} button:before{{mask-image:url("{asset(asset_name)}");}}\n'

APPLICATION_LABELS = {"PENDING": "대기 중", "ACCEPTED": "승인", "REJECTED": "거절", "CANCELED": "신청 취소"}
POST_LABELS = {"OPEN": "모집 중", "CLOSED": "모집 마감", "COMPLETED": "식사 완료", "CANCELED": "모임 취소"}


def html(markup):
    st.markdown(markup, unsafe_allow_html=True)


def empty(message):
    html(f'<div class="apply-empty">{e(message)}</div>')


def date_label(value):
    return value.strftime("%m.%d %H:%M") if hasattr(value, "strftime") else str(value or "")


def status_badge(status, application=False):
    labels = APPLICATION_LABELS if application else POST_LABELS
    css = str(status).lower() if status in labels else "unknown"
    return f'<span class="apply-badge {css}">{e(labels.get(status, "상태 확인 필요"))}</span>'


def read_list(func, *args):
    if not callable(func):
        return False, None
    try:
        rows = func(*args)
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise TypeError("Expected list[dict]")
        return True, rows
    except (ValueError, PermissionError, LookupError) as exc:
        st.error(str(exc))
    except Exception:
        st.error("정보를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.")
    return False, None


def perform(user_id, func, args, message):
    if not callable(func):
        st.info("아직 연동 준비 중인 기능이에요.")
        return
    try:
        func(*args)
    except (ValueError, PermissionError, LookupError) as exc:
        st.error(str(exc))
    except Exception:
        st.error("처리하지 못했어요. 잠시 후 다시 시도해 주세요.")
    else:
        st.session_state[f"apply_flash_{user_id}"] = message
        st.rerun()


def navigate(filename, **params):
    path = Path(__file__).resolve().parent / filename
    if not path.is_file() or not path.read_text(encoding="utf-8-sig").strip():
        st.info("해당 화면은 아직 준비 중이에요.")
        return
    st.switch_page(f"pages/{filename}", query_params=params or None)


def open_post(post_id):
    st.session_state["selected_post_id"] = post_id
    st.session_state["detail_scroll_to_top"] = True
    navigate("3_post_detail.py", post=post_id)


def bottom_nav():
    items = [("모집 글", "1_feed.py", "nav_home"), ("내 신청", None, "nav_apply"),
             ("톡방", "6_chat.py", "nav_chat"), ("내 프로필", "4_profile.py", "nav_profile")]
    with st.container(key="bottom_nav"):
        for col, (label, filename, key) in zip(st.columns(4), items):
            with col, st.container(key=key):
                if st.button(label, key=f"apply_{key}", use_container_width=True) and filename:
                    navigate(filename)


def room_map(user_id):
    """Use the same proposed chat contract as the profile; never guess a room ID."""
    func = getattr(chat_service, "get_chat_rooms", None)
    if not callable(func):
        return None
    ok, rooms = read_list(func, user_id)
    if not ok:
        return None
    return {room["post_id"]: room["room_id"] for room in rooms
            if room.get("post_id") is not None and room.get("room_id") is not None}


def post_link(post_id, source):
    if st.button("게시글 보기", key=f"apply_post_link_{source}_{post_id}", width="stretch"):
        open_post(post_id)


def room_button(post_id, rooms, key):
    room_id = rooms.get(post_id) if rooms is not None else None
    if room_id is not None and st.button("톡방 가기", key=key, type="primary", width="stretch"):
        navigate("6_chat.py", room=room_id)


def get_review_status(user_id):
    """Use the same outstanding-review query as the profile page."""
    ok, mates = read_list(review_service.get_reviewable_mates, user_id)
    if not ok:
        return None, None
    try:
        remaining = {str(row["post_id"]) for row in mates}
    except (KeyError, TypeError):
        st.error("리뷰 상태를 불러오지 못했어요.")
        return None, None
    ok, written = read_list(review_service.get_written_reviews, user_id)
    if not ok:
        return remaining, None
    try:
        completed = {str(row["post_id"]) for row in written}
    except (KeyError, TypeError):
        st.error("리뷰 상태를 불러오지 못했어요.")
        return remaining, None
    return remaining, completed


def review_status_button(post_id, key, review_status):
    remaining, written = review_status
    post_key = str(post_id)
    if remaining is not None and post_key in remaining:
        if st.button("리뷰 쓰기", key=key, type="primary", width="stretch"):
            navigate("4_profile.py", review_post=post_id)
    else:
        if remaining is None or written is None:
            label = "리뷰 상태 확인 불가"
        elif post_key in written:
            label = "리뷰 작성 완료"
        else:
            label = "리뷰 대상 없음"
        st.button(label, key=key, disabled=True, width="stretch")


def render_applications(user_id, rooms):
    # Proposed list contract. cancel_application already appears in README_API.md.
    func = getattr(participation_service, "get_my_applications", None)
    if not callable(func):
        empty("신청한 모임 목록은 백엔드 연동 준비 중이에요.")
        st.caption("참여 신청 내역 조회·취소·승인 상태를 이곳에서 확인할 수 있어요.")
        return
    ok, rows = read_list(func, user_id)
    if not ok:
        return
    html(f'<div class="apply-section">신청 내역 {len(rows)}개</div>')
    if not rows:
        empty("아직 신청한 모임이 없어요.")
        if st.button("모집 글 둘러보기", key="apply_browse", use_container_width=True):
            navigate("1_feed.py")
        return
    cancel = getattr(participation_service, "cancel_application", None)
    review_status = get_review_status(user_id) if any(
        row["status"] == "ACCEPTED" and row["post_status"] == "COMPLETED" for row in rows
    ) else (None, None)
    for row in rows:
        post_id = row["post_id"]
        status = row["status"]
        post_status = row["post_status"]
        with st.container(key=f"apply_card_application_{post_id}"):
            html(f'<div class="apply-top"><div class="apply-title">{e(row["title"])}</div>{status_badge(status, True)}</div>'
                 f'<div class="apply-meta">{e(date_label(row.get("meal_time")))} · {e(row.get("region") or "")} · {e(POST_LABELS.get(post_status, "상태 확인 필요"))}</div>')
            post_link(post_id, "application")
            if status == "PENDING" and post_status in ("OPEN", "CLOSED") and callable(cancel):
                if st.button("신청 취소", key=f"apply_cancel_{post_id}", width="stretch"):
                    perform(user_id, cancel, (post_id, user_id), "신청을 취소했어요.")
            elif status == "ACCEPTED" and post_status == "COMPLETED":
                review_status_button(post_id, f"apply_review_{post_id}", review_status)
            elif status == "ACCEPTED" and post_status in ("OPEN", "CLOSED"):
                room_button(post_id, rooms, f"apply_room_{post_id}")


def render_applicants(user_id, post, func):
    post_id = post["post_id"]
    ok, rows = read_list(func, post_id, user_id)
    if not ok:
        return
    pending = sum(row.get("status") == "PENDING" for row in rows)
    html(f'<div class="apply-section">신청자 {len(rows)}명 · 승인 대기 {pending}명</div>')
    if not rows:
        st.caption("아직 신청자가 없어요.")
    accept = getattr(participation_service, "accept_application", None)
    reject = getattr(participation_service, "reject_application", None)
    for row in rows:
        applicant = row["user_id"]
        status = row["status"]
        html(f'<div class="apply-top"><div class="apply-person">{user_avatar(applicant, 28)}{e(row["nickname"])}</div>'
             f'{status_badge(status, True)}</div>')
        if status == "PENDING" and post["status"] == "OPEN":
            actions = []
            if callable(accept):
                actions.append(("승인", "accept", accept, "참여 신청을 승인했어요."))
            if callable(reject):
                actions.append(("거절", "reject", reject, "참여 신청을 거절했어요."))
            if not actions:
                continue
            full = post["current_count"] >= post["capacity"]
            for col, (label, key, action, message) in zip(st.columns(len(actions)), actions):
                with col:
                    if st.button(label, key=f"apply_{key}_{post_id}_{applicant}", width="stretch",
                                 type="primary" if key == "accept" else "secondary",
                                 disabled=key == "accept" and full):
                        perform(user_id, action, (post_id, user_id, applicant), message)


def render_hosted(user_id, rooms):
    # Existing, implemented user_service is enough to show real hosted posts today.
    ok, posts = read_list(user_service.get_user_posts, user_id)
    if not ok:
        return
    html(f'<div class="apply-section">모집한 모임 {len(posts)}개</div>')
    if not posts:
        empty("아직 모집한 모임이 없어요.")
        if st.button("모집 글 작성", key="apply_create_post", use_container_width=True):
            navigate("2_write_post.py")
        return
    applicants = getattr(participation_service, "get_post_applications", None)
    complete = getattr(participation_service, "complete_meal", None)
    review_status = get_review_status(user_id) if any(
        post["status"] == "COMPLETED" for post in posts
    ) else (None, None)
    for post in posts:
        post_id = post["post_id"]
        status = post["status"]
        with st.container(key=f"apply_card_host_{post_id}"):
            html(f'<div class="apply-top"><div class="apply-title">{e(post["title"])}</div>{status_badge(status)}</div>'
                 f'<div class="apply-meta">{e(date_label(post.get("meal_time")))} · {e(post.get("region") or "")}<br>'
                 f'참여 {e(post["current_count"])}/{e(post["capacity"])}명 · 작성자 포함</div>')
            post_link(post_id, "host")
            if callable(applicants):
                render_applicants(user_id, post, applicants)
            if status == "CLOSED":
                room_button(post_id, rooms, f"apply_host_room_{post_id}")
                if callable(complete):
                    confirm = st.checkbox("실제로 식사를 마쳤어요", key=f"apply_confirm_complete_{user_id}_{post_id}")
                    if st.button("식사 완료 처리", key=f"apply_complete_{post_id}", disabled=not confirm, width="stretch"):
                        perform(user_id, complete, (post_id, user_id), "식사 완료로 변경했어요.")
            elif status == "COMPLETED":
                review_status_button(post_id, f"apply_host_review_{post_id}", review_status)

    pending = []
    if not all(callable(getattr(participation_service, name, None))
               for name in ("get_post_applications", "accept_application", "reject_application")):
        pending.append("신청자 관리")
    if any(post["status"] == "CLOSED" for post in posts):
        if not callable(getattr(chat_service, "get_chat_rooms", None)):
            pending.append("톡방")
        if not callable(complete):
            pending.append("식사 완료")
    if pending:
        html(f'<div class="apply-note">{e("·".join(pending))} 기능은 준비 중이에요.</div>')


def main():
    st.set_page_config(page_title="머먹 · 내 신청", page_icon="🍚", layout="centered")
    user_id = auth.require_login()["user_id"]
    html(f"<style>{CSS}{PAGE_CSS}</style>")
    html('<div class="apply-heading">내 신청 · 참여</div>')
    with st.container(key="apply_body"):
        if message := st.session_state.pop(f"apply_flash_{user_id}", None):
            st.success(message)
        tab = st.radio("참여 메뉴", ["신청한 모임", "내가 모집한 모임"], horizontal=True,
                       label_visibility="collapsed", width="stretch", key=f"apply_tab_{user_id}")
        rooms = room_map(user_id)
        if tab == "신청한 모임":
            render_applications(user_id, rooms)
        else:
            render_hosted(user_id, rooms)
    bottom_nav()


if __name__ == "__main__":
    main()

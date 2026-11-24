"""My profile and meal reviews. Run via app.py, not as a separate app."""
from pathlib import Path

import pymysql
import streamlit as st

import auth
from services import user_service, review_service, stats_service, chat_service, social_service
from ui_common import CSS, STATUS_LABELS, asset, e, user_avatar


PROFILE_CSS = """

/* Compact native-button hit area; the visible HTML retains the existing design. */
.st-key-profile_body [class*="st-key-public_follow_hit_"]{position:relative!important;isolation:isolate;gap:0!important;}
.st-key-profile_body [class*="st-key-public_follow_hit_"] > :is([data-testid="stElementContainer"],[data-testid="stLayoutWrapper"]):has([data-testid="stButton"]){position:absolute!important;inset:0!important;width:100%!important;height:100%!important;z-index:2;margin:0!important;padding:0!important;}
.st-key-profile_body [class*="st-key-public_follow_hit_"] [data-testid="stButton"]{width:100%!important;height:100%!important;}
.st-key-profile_body [class*="st-key-public_follow_hit_"] button{display:block!important;width:100%!important;height:100%!important;min-height:0!important;min-width:0!important;padding:0!important;border:0!important;border-radius:6px!important;background:transparent!important;box-shadow:none!important;cursor:pointer!important;}
.st-key-profile_body [class*="st-key-public_follow_hit_"] button p{opacity:0!important;}
.st-key-profile_body [class*="st-key-public_follow_hit_"] button:focus-visible{outline:2px solid var(--orange)!important;outline-offset:1px;}
.st-key-profile_body [class*="st-key-public_follow_hit_"] button:hover{background:rgba(255,122,61,.06)!important;}

.st-key-profile_body [class*="st-key-public_follow_hit_"]{width:fit-content!important;max-width:100%;align-self:flex-start;}
.public-follow-person{width:max-content;max-width:100%;padding:2px 4px 2px 0;}
/* Same back-icon dimensions as the existing post detail header. */
.st-key-public_profile_back{width:26px!important;min-width:26px!important;height:26px!important;margin-left:-4px;gap:0!important;}
.st-key-public_profile_back [data-testid="stButton"]{width:26px!important;height:26px!important;line-height:0;}
.st-key-public_profile_back button{display:block!important;width:26px!important;min-width:26px!important;height:26px!important;min-height:26px!important;padding:0!important;border:0!important;border-radius:0!important;background-color:transparent!important;background-repeat:no-repeat!important;background-position:center!important;box-shadow:none!important;cursor:pointer!important;}
.st-key-public_profile_back button p{font-size:0!important;line-height:0!important;}
.st-key-public_profile_back button:focus-visible{outline:2px solid var(--orange)!important;outline-offset:2px;}
.profile-heading{background:white;padding:8px 20px 16px;font-size:20px;font-weight:800;}
.st-key-profile_body{padding:12px 16px 24px!important;}
.st-key-profile_body [data-testid='stVerticalBlock']{gap:8px!important;}
.st-key-profile_body [data-testid='stHorizontalBlock']{gap:8px!important;}
.st-key-profile_body [data-testid='stColumn']{min-width:0!important;}
.st-key-profile_body [data-testid='stVerticalBlockBorderWrapper'],
.st-key-profile_body [data-testid='stLayoutWrapper']> [data-testid='stVerticalBlock'][data-border='true']{border-radius:14px;}
.st-key-profile_identity,.st-key-profile_edit,.st-key-profile_review_form,
.st-key-profile_followers,.st-key-profile_followings,[class*='st-key-profile_post_'],
[class*='st-key-profile_room_']{background:white;border:1px solid var(--line);border-radius:14px;padding:14px!important;}
.profile-person{display:flex;align-items:center;gap:11px;min-width:0;}
.profile-name{font-size:18px;font-weight:800;overflow-wrap:anywhere;}
.profile-muted{font-size:12px;color:var(--muted);overflow-wrap:anywhere;}
.profile-bio{font-size:14px;white-space:pre-wrap;overflow-wrap:anywhere;margin:5px 0;}
.profile-tastes{padding:10px 12px;border-radius:10px;background:var(--paper);font-size:12px;color:#666;overflow-wrap:anywhere;white-space:pre-wrap;}
.profile-stat{text-align:center;padding:8px 0;}
.profile-stat strong{font-size:19px;display:block;line-height:25px;}
.profile-stat small{font-size:11px;color:var(--muted);}
.profile-section{display:flex;align-items:center;justify-content:space-between;margin-top:12px;font-size:15px;font-weight:800;}
.profile-section small{font-size:11px;font-weight:400;color:#777;}
.profile-empty{background:white;border:1px solid var(--line);border-radius:12px;padding:16px;text-align:center;color:#888;font-size:12px;}
.profile-post-title{font-size:15px;font-weight:750;overflow-wrap:anywhere;}
.profile-post-text{font-size:13px;white-space:pre-wrap;overflow-wrap:anywhere;margin:5px 0;}
.profile-post-meta{font-size:12px;color:#777;line-height:1.7;}
.profile-status{display:inline-block;border-radius:6px;padding:3px 8px;background:#fff0e7;color:#d95f29;font-size:11px;font-weight:700;}
.profile-review{background:white;border:1px solid var(--line);border-radius:12px;padding:13px;}
.profile-review-top{display:flex;gap:9px;align-items:center;}
.profile-review-name{font-size:13px;font-weight:700;overflow-wrap:anywhere;}
.profile-stars{color:#e9a500;font-size:14px;letter-spacing:1px;}
.profile-review-content{font-size:13px;white-space:pre-wrap;overflow-wrap:anywhere;margin-top:8px;}
.st-key-profile_body button{border:1px solid #e7e5e3;border-radius:9px;background:white;color:#333;font-size:13px;min-height:36px;}
.st-key-profile_body button[kind='primary'],.st-key-profile_body button[data-testid='stBaseButton-primary'],
.st-key-profile_body button[data-testid='stBaseButton-primaryFormSubmit']{background:var(--orange)!important;color:white!important;border-color:var(--orange)!important;}
.st-key-profile_body button:disabled{background:#f1f0ee!important;color:#999!important;}
.st-key-profile_body .st-key-profile_account button{color:var(--muted);background:transparent;border:0;box-shadow:none;}
.st-key-profile_body .st-key-profile_account button:hover{background:var(--paper);}
.st-key-profile_account button p{font-size:12px;}
.st-key-profile_body [data-testid='stForm']{padding:0;border:0;}
.st-key-profile_body [data-baseweb='input'],.st-key-profile_body [data-baseweb='textarea']{border-radius:9px;background:white;}
.st-key-profile_body input,.st-key-profile_body textarea{color:#222;background:white;}
.st-key-profile_body [data-testid='stTabs'] button{border:0;border-radius:0;background:transparent;}
.st-key-profile_body [data-testid='stTabs'] [aria-selected='true']{color:var(--orange)!important;}
.st-key-bottom_nav .st-key-nav_home button{color:#a0a0a0!important;font-weight:400;}
.st-key-bottom_nav .st-key-nav_profile button{color:var(--orange)!important;font-weight:700;}
.st-key-bottom_nav button{position:relative;background-image:none!important;}
.st-key-bottom_nav button:before{content:'';position:absolute;top:0;left:50%;transform:translateX(-50%);width:24px;height:24px;background:currentColor;mask-size:contain;mask-repeat:no-repeat;mask-position:center;}
"""
for nav_key, asset_name in (("home", "home"), ("apply", "calendar"), ("chat", "groups"), ("profile", "user")):
    PROFILE_CSS += f'.st-key-nav_{nav_key} button:before{{mask-image:url("{asset(asset_name)}");}}\n'


PROFILE_CSS += f'.st-key-public_profile_back button{{background-image:url("{asset("write_back")}")!important;}}\n'


def html(markup):
    st.markdown(markup, unsafe_allow_html=True)


def date_label(value, pattern="%m.%d %H:%M"):
    return value.strftime(pattern) if hasattr(value, "strftime") else str(value or "")


def section(title, detail=""):
    html(f'<div class="profile-section">{e(title)}<small>{e(detail)}</small></div>')


def empty(message):
    html(f'<div class="profile-empty">{e(message)}</div>')


def read_data(func, *args):
    """Do not present a failed query as an empty result."""
    try:
        return True, func(*args)
    except (ValueError, PermissionError, LookupError) as exc:
        st.error(str(exc))
    except Exception:
        st.error("정보를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.")
    return False, None


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
    items = [("모집 글", "1_feed.py", "nav_home"), ("내 신청", "5_participation.py", "nav_apply"),
             ("톡방", "6_chat.py", "nav_chat"), ("내 프로필", "4_profile.py", "nav_profile")]
    with st.container(key="bottom_nav"):
        for column, (label, filename, key) in zip(st.columns(4), items):
            with column, st.container(key=key):
                if st.button(label, key=f"profile_{key}", use_container_width=True) and filename:
                    if key != "nav_profile" or st.query_params.get("user") or st.query_params.get("back_post"):
                        navigate(filename)


def render_follow_list(user_id, followers):
    func = user_service.get_followers if followers else user_service.get_followings
    ok, rows = read_data(func, user_id)
    if not ok:
        return
    if not rows:
        empty("아직 팔로워가 없어요." if followers else "아직 팔로잉하는 사람이 없어요.")
    for row in rows:
        target = int(row["user_id"])
        suffix = "followers" if followers else "followings"
        with st.container(key=f"public_follow_hit_{suffix}_{target}", width="content", gap=None):
            html(f'<div class="profile-review-top public-follow-person">{user_avatar(row["user_id"], 30)}'
                 f'<div><div class="profile-review-name">{e(row["nickname"])}</div>'
                 f'<div class="profile-muted">{e(row.get("neighborhood") or "")}</div></div></div>')
            if st.button(f'{row["nickname"]} 프로필 보기', key=f"public_follow_open_{suffix}_{target}"):
                navigate("4_profile.py", user=target, back_list=suffix)


def render_edit(user_id, profile):
    # Separate forms because the existing backend exposes two independent writes.
    with st.container(key="profile_edit"):
        section("프로필 수정")
        with st.form(f"profile_edit_info_{user_id}"):
            neighborhood = st.text_input("동네", value=profile.get("neighborhood") or "", max_chars=30)
            preference = st.text_input("음식 취향", value=profile.get("food_preference") or "", max_chars=100)
            favorite = st.text_input("선호 음식", value=profile.get("favorite_food") or "", max_chars=50)
            bio = st.text_area("자기소개", value=profile.get("bio") or "", max_chars=200)
            if st.form_submit_button("프로필 저장", type="primary", use_container_width=True):
                if not neighborhood.strip():
                    st.warning("동네를 입력해 주세요.")
                else:
                    try:
                        user_service.update_profile(user_id, neighborhood.strip(), preference.strip(), favorite.strip(), bio.strip())
                    except ValueError as exc:
                        st.error(str(exc))
                    except Exception:
                        st.error("프로필을 저장하지 못했어요. 입력 내용을 확인하고 다시 시도해 주세요.")
                    else:
                        st.session_state["profile_flash"] = "프로필을 수정했어요."
                        st.rerun()
        with st.form(f"profile_edit_nickname_{user_id}"):
            nickname = st.text_input("닉네임", value=profile["nickname"], max_chars=30)
            if st.form_submit_button("닉네임 저장", use_container_width=True):
                if not nickname.strip():
                    st.warning("닉네임을 입력해 주세요.")
                else:
                    try:
                        user_service.update_nickname(user_id, nickname.strip())
                    except ValueError as exc:
                        st.error(str(exc))
                    except Exception:
                        st.error("닉네임을 저장하지 못했어요. 다시 시도해 주세요.")
                    else:
                        st.session_state["user"] = {"user_id": user_id, "nickname": nickname.strip()}
                        st.session_state["profile_flash"] = "닉네임을 수정했어요."
                        st.rerun()


def render_logout():
    with st.container(key="profile_account", horizontal=True, horizontal_alignment="right"):
        if st.button("로그아웃", key="profile_logout"):
            auth.logout()
            st.session_state.clear()
            st.query_params.clear()
            st.switch_page("pages/1_feed.py")


def render_identity(user_id, profile, viewer_id=None):
    own = viewer_id is None or viewer_id == user_id
    rating_label = "연동 대기"
    rating_func = getattr(stats_service, "get_user_average_rating", None)
    if callable(rating_func):
        try:
            rating = rating_func(user_id)
            rating_label = "평가 없음" if rating is None else f"★ {float(rating):.1f}"
        except Exception:
            rating_label = "조회 실패"
    with st.container(key="profile_identity"):
        if own:
            private_info = (f' · {e(profile["birth_year"])}년생</div>'
                            f'<div class="profile-muted">{e(profile["gachon_email"])}</div>')
        else:
            private_info = '</div>'
        html(f'<div class="profile-person">{user_avatar(user_id, 58)}<div>'
             f'<div class="profile-name">{e(profile["nickname"])}</div>'
             f'<div class="profile-muted">{e(profile.get("neighborhood") or "")}{private_info}</div></div>')
        html(f'<div class="profile-bio">{e(profile.get("bio") or "아직 자기소개가 없어요.")}</div>')
        html(f'<div class="profile-tastes">음식 취향 · {e(profile.get("food_preference") or "미등록")}<br>'
             f'선호 음식 · {e(profile.get("favorite_food") or "미등록")}</div>')
        for col, (value, label) in zip(st.columns(3), [(rating_label,"평균 평점"), (profile["follower_count"],"팔로워"), (profile["following_count"],"팔로잉")]):
            with col:
                html(f'<div class="profile-stat"><strong>{e(value)}</strong><small>{e(label)}</small></div>')
        if not own:
            render_public_follow(viewer_id, user_id)
            return
        if st.button("프로필 수정" if not st.session_state.get("profile_edit_open") else "수정 닫기", key="profile_edit_toggle", use_container_width=True):
            st.session_state["profile_edit_open"] = not st.session_state.get("profile_edit_open", False)
            st.rerun()
        a, b = st.columns(2)
        with a:
            if st.button("팔로워 보기", key="profile_follower_toggle", use_container_width=True):
                st.session_state["profile_follow_view"] = None if st.session_state.get("profile_follow_view") == "followers" else "followers"
        with b:
            if st.button("팔로잉 보기", key="profile_following_toggle", use_container_width=True):
                st.session_state["profile_follow_view"] = None if st.session_state.get("profile_follow_view") == "followings" else "followings"
    render_logout()
    follow_view = st.session_state.get("profile_follow_view")
    if follow_view:
        with st.container(key=f"profile_{follow_view}"):
            section("팔로워" if follow_view == "followers" else "팔로잉")
            render_follow_list(user_id, follow_view == "followers")
    if st.session_state.get("profile_edit_open"):
        render_edit(user_id, profile)


def render_rooms(user_id):
    section("참여 중인 톡방")
    # PROPOSED contract: see README_FRONTEND.md; no database access in the page.
    func = getattr(chat_service, "get_chat_rooms", None)
    if not callable(func):
        empty("톡방 기능은 연동 준비 중이에요.")
        return
    ok, rooms = read_data(func, user_id)
    if not ok:
        return
    if not rooms:
        empty("참여 중인 톡방이 없어요.")
    for room in rooms:
        with st.container(key=f'profile_room_{room["room_id"]}'):
            html(f'<div class="profile-post-title">{e(room["title"])}</div>'
                 f'<div class="profile-muted">{e(room.get("last_message") or "아직 메시지가 없어요.")}</div>')
            if st.button("톡방 가기", key=f'profile_room_open_{room["room_id"]}', use_container_width=True):
                navigate("6_chat.py", room=room["room_id"])


def render_posts(user_id):
    ok, posts = read_data(user_service.get_user_posts, user_id)
    section("작성한 포스트", f"{len(posts)}개" if ok else "")
    if not ok:
        return
    if not posts:
        empty("아직 작성한 모집 글이 없어요.")
    for post in posts:
        with st.container(key=f'profile_post_{post["post_id"]}'):
            html(f'<span class="profile-status">{e(STATUS_LABELS.get(post["status"], post["status"]))}</span>'
                 f'<div class="profile-post-title">{e(post["title"])}</div>'
                 f'<div class="profile-post-text">{e(post["body"])}</div>'
                 f'<div class="profile-post-meta">{e(post["region"])} · {e(date_label(post["meal_time"]))} · {e(post["food_category"])}<br>'
                 f'{e(post["current_count"])}/{e(post["capacity"])}명 · ♡ {e(post["like_count"])} · 댓글 {e(post["comment_count"])}</div>')
            if st.button("상세 보기", key=f'profile_post_open_{post["post_id"]}', use_container_width=True):
                open_post(post["post_id"])


def render_review_list(rows, written=False):
    if not rows:
        empty("아직 작성한 리뷰가 없어요." if written else "아직 받은 리뷰가 없어요.")
    for review in rows:
        nickname = review["reviewee_nickname" if written else "reviewer_nickname"]
        avatar_id = review["reviewee_id" if written else "reviewer_id"]
        rating = int(review["rating"])
        html(f'<div class="profile-review"><div class="profile-review-top">{user_avatar(avatar_id, 30)}<div>'
             f'<div class="profile-review-name">{e(nickname)} {"님에게" if written else ""}</div>'
             f'<div class="profile-stars" aria-label="별점 {rating}점">{"★" * rating}{"☆" * (5-rating)}</div></div></div>'
             f'<div class="profile-muted">{e(review["post_title"])} · {e(date_label(review["created_at"], "%m.%d"))}</div>'
             f'<div class="profile-review-content">{e(review.get("content") or "별점만 남긴 리뷰예요.")}</div></div>')


def render_review_form(user_id):
    ok, mates = read_data(review_service.get_reviewable_mates, user_id)
    if not ok:
        return
    if not mates:
        empty("리뷰를 작성할 식사 메이트가 없어요.")
        return
    # post_id + mate_id is the review identity, not a nickname or list index.
    by_key = {(m["post_id"], m["mate_id"]): m for m in mates}
    options = list(by_key)
    requested = st.query_params.get("review_post")
    if requested:
        options.sort(key=lambda k: str(k[0]) != str(requested))
    with st.container(key="profile_review_form"):
        selected = st.selectbox("리뷰할 식사 메이트", options,
            format_func=lambda k: f'{by_key[k]["post_title"]} · {by_key[k]["mate_nickname"]}', key=f"profile_review_target_{user_id}")
        with st.form(f"profile_review_{user_id}_{selected[0]}_{selected[1]}"):
            rating = st.radio("별점", [1, 2, 3, 4, 5], index=4, horizontal=True, format_func=lambda v: f"{v}점")
            content = st.text_area("리뷰 내용 (선택)", placeholder="함께한 식사는 어땠나요?", max_chars=1000)
            if st.form_submit_button("리뷰 등록", type="primary", use_container_width=True):
                try:
                    review_service.write_review(selected[0], user_id, selected[1], rating, content)
                except review_service.ReviewError as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("리뷰를 저장하지 못했어요. 다시 시도해 주세요.")
                else:
                    st.session_state["profile_flash"] = "리뷰를 등록했어요."
                    st.query_params.pop("review_post", None)
                    st.rerun()


def positive_query(name):
    """Query parameters identify targets, never the authenticated account."""
    value = st.query_params.get(name)
    if value is None:
        return None
    try:
        result = int(value)
        return result if 0 < result <= 2**64 - 1 else None
    except (ValueError, TypeError):
        return None


def render_public_follow(viewer_id, target_id):
    ok, followers = read_data(user_service.get_followings, viewer_id)
    if not ok:
        return
    following = any(int(row["user_id"]) == target_id for row in followers)
    if st.button("팔로잉" if following else "팔로우", key=f"public_follow_{target_id}",
                 type="secondary" if following else "primary", use_container_width=True):
        ok, _ = read_data(social_service.set_follow, int(viewer_id), target_id, not following)
        if ok:
            st.rerun()


def return_from_profile():
    post_id = positive_query("back_post")
    if post_id:
        st.session_state["selected_post_id"] = post_id
        st.session_state["detail_scroll_to_top"] = True
        params = {"post": post_id}
        if st.query_params.get("back_from") == "search":
            params["from"] = "search"
        navigate("3_post_detail.py", **params)
    source = st.query_params.get("back_list")
    if source in ("followers", "followings"):
        st.session_state["profile_follow_view"] = source
    navigate("4_profile.py")


def render_profile_back():
    with st.container(key="public_profile_back", width="content"):
        if st.button("뒤로", key="public_profile_return"):
            return_from_profile()


def render_public_profile(viewer_id, target_id):
    # Explicit public branch: no review-detail, email, rooms, edit or logout calls.
    html('<div class="status-bar" aria-hidden="true"><strong>9:41</strong><span>LTE 100%</span></div>')
    with st.container(key="profile_body"):
        render_profile_back()
        if target_id is None:
            empty("프로필을 찾을 수 없어요.")
            return
        ok, profile = read_data(user_service.get_profile, target_id)
        if not ok:
            if st.button("다시 불러오기", key="public_profile_retry"):
                st.rerun()
            return
        if profile is None:
            empty("프로필을 찾을 수 없어요.")
            return
        section(f'{profile["nickname"]}님의 프로필')
        render_identity(target_id, profile, viewer_id=viewer_id)
        render_posts(target_id)


def main():
    st.set_page_config(page_title="머먹 · 내 프로필", page_icon="🍚", layout="centered")
    user = auth.require_login()
    user_id = user["user_id"]
    html(f"<style>{CSS}{PROFILE_CSS}</style>")
    target_id = positive_query("user")
    view_token = (int(user_id), target_id, st.query_params.get("back_post"))
    if st.session_state.get("_public_profile_view") != view_token:
        st.session_state["_public_profile_view"] = view_token
        st.html("""<script>
        (() => {
            const reset = () => document.querySelector('[data-testid="stMain"]')?.scrollTo(0, 0);
            requestAnimationFrame(reset); setTimeout(reset, 150);
        })();
        </script>""", unsafe_allow_javascript=True)
    if "user" in st.query_params and target_id != int(user_id):
        render_public_profile(int(user_id), target_id)
        bottom_nav()
        return
    if positive_query("back_post"):
        render_profile_back()
    html('<div class="status-bar" aria-hidden="true"><strong>9:41</strong><span>LTE 100%</span></div>'
         '<div class="profile-heading">내 프로필</div>')
    with st.container(key="profile_body"):
        if message := st.session_state.pop("profile_flash", None):
            st.success(message)
        ok, profile = read_data(user_service.get_profile, user_id)
        if ok and profile is not None:
            render_identity(user_id, profile)
            render_rooms(user_id)
            render_posts(user_id)
            section("리뷰")
            # A link from participation can request the review-writing tab.
            review_labels = ["받은 리뷰", "작성한 리뷰", "리뷰 쓰기"]
            default = "리뷰 쓰기" if st.query_params.get("review_post") else "받은 리뷰"
            choice = st.radio("리뷰 메뉴", review_labels, index=review_labels.index(default), horizontal=True,
                              label_visibility="collapsed", key=f"profile_review_menu_{user_id}_{default}")
            if choice == "리뷰 쓰기":
                render_review_form(user_id)
            else:
                written = choice == "작성한 리뷰"
                ok, reviews = read_data(review_service.get_written_reviews if written else review_service.get_received_reviews, user_id)
                if ok:
                    render_review_list(reviews, written)
        elif ok:
            empty("프로필을 찾을 수 없어요.")
        if not ok or profile is None:
            render_logout()
            if st.button("다시 불러오기", key="profile_retry", use_container_width=True):
                st.rerun()
    bottom_nav()


if __name__ == "__main__":
    main()

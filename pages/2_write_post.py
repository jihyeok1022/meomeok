"""Write post page. Run the application with: streamlit run app.py.

Input validation, preview and persistence through post_service.
"""
from datetime import datetime, timedelta

import streamlit as st
import pymysql
import auth
from services import post_service

# 피드와 같은 DB 선택값 및 공통 스타일을 사용한다.
import ui_common as ui
REGIONS = ui.REGIONS
FOOD_CATEGORIES = ui.FOOD_CATEGORIES


def build_payload(values):
    return {
        'title': values.get('title', '').strip(),
        'body': values.get('body', '').strip(),
        'capacity': values.get('capacity', 3),
        'meal_time': values.get('meal_time'),
        'region': values.get('region', REGIONS[0]),
        'food_category': values.get('food_category', FOOD_CATEGORIES[0]),
    }


def validate_post(payload, now=None):
    """UI 입력 검사. 권한과 업무 규칙은 백엔드에서도 검사해야 한다."""
    errors = []
    if not payload['title']:
        errors.append('제목을 입력해 주세요.')
    elif len(payload['title']) > 100:
        errors.append('제목은 100자 이내로 작성해 주세요.')
    if not payload['body']:
        errors.append('내용과 구체적인 약속 장소를 적어 주세요.')
    elif len(payload['body'].encode('utf-8')) > 65535:
        errors.append('내용이 너무 길어요. 조금 줄여 주세요.')
    if type(payload['capacity']) is not int or not 2 <= payload['capacity'] <= 20:
        errors.append('정원은 작성자를 포함해 2~20명으로 정해 주세요.')
    if payload['region'] not in REGIONS:
        errors.append('지역을 선택해 주세요.')
    if payload['food_category'] not in FOOD_CATEGORIES:
        errors.append('음식 종류를 선택해 주세요.')
    if not isinstance(payload['meal_time'], datetime):
        errors.append('식사 날짜와 시간을 선택해 주세요.')
    elif payload['meal_time'] <= (now or datetime.now()):
        errors.append('식사 시간은 현재보다 나중으로 정해 주세요.')
    return errors


def remember_draft():
    draft = dict(st.session_state.get('write_draft', {}))
    for field in ('title', 'body', 'capacity', 'meal_time', 'region', 'food_category'):
        if f'write_{field}' in st.session_state:
            draft[field] = st.session_state[f'write_{field}']
    st.session_state['write_draft'] = draft
    return draft


def close_preview():
    st.session_state.pop('_write_preview_payload', None)
    st.session_state.pop('_write_publish_error', None)


def finish_publish():
    if (post_id := st.session_state.pop('_write_saved_id', None)) is not None:
        st.switch_page('pages/3_post_detail.py', query_params={'post': post_id})


def publish_post(payload):
    """Called before the next page/fragment render; never store a fake post."""
    user = auth.require_login()
    st.session_state.pop('_write_publish_error', None)
    errors = validate_post(payload)
    if errors:
        st.session_state['_write_publish_error'] = '\n'.join(errors)
        return
    try:
        post_id = post_service.create_post(user['user_id'], payload)
    except (ValueError, LookupError, PermissionError) as exc:
        st.session_state['_write_publish_error'] = str(exc)
    except (pymysql.MySQLError, OSError):
        st.session_state['_write_publish_error'] = '글을 등록하지 못했어요. DB 연결을 확인한 후 다시 시도해 주세요.'
    else:
        close_preview()
        st.session_state['_write_reset'] = True
        st.session_state['_write_saved_id'] = post_id
        st.session_state['selected_post_id'] = post_id
        st.session_state['detail_scroll_to_top'] = True
        st.session_state['_post_created'] = True


@st.dialog('작성한 모집 글', on_dismiss=close_preview)
def show_preview(payload):
    finish_publish()
    st.subheader(payload['title'])
    st.write(payload['body'])
    st.write(f"지역: {payload['region']} · 음식 종류: {payload['food_category']}")
    st.write(f"식사 시간: {payload['meal_time']:%Y-%m-%d %H:%M}")
    st.write(f"정원: {payload['capacity']}명 (작성자 포함)")
    st.info('미리보기입니다. 아직 게시되지 않았어요.')
    if error := st.session_state.get('_write_publish_error'):
        st.error(error)
    st.button('이대로 모집 글 등록', key='write_publish', use_container_width=True,
              on_click=publish_post, args=(payload,))


WRITE_CSS = """
[data-testid="stMainBlockContainer"]{background:white!important;padding-bottom:126px!important;}
.st-key-write_header{height:44px;min-height:44px;box-sizing:border-box;padding:6px 20px 12px 12px;}
.st-key-write_header [data-testid="stHorizontalBlock"]{height:26px;align-items:center;gap:10px;flex-wrap:nowrap!important;}
.st-key-write_header [data-testid="stColumn"]{min-width:0!important;}
.st-key-write_header [data-testid="stColumn"]:first-child{flex:0 0 26px;}
.st-key-write_header [data-testid="stColumn"]:last-child{flex:1 1 auto;}
.write-title{font-size:17px;font-weight:700;line-height:25px;color:#1f1f1f;}
.st-key-write_header button{display:block;width:26px!important;height:26px!important;min-height:26px!important;
 padding:0;border:0;background-color:transparent!important;background-repeat:no-repeat;background-position:center;}
.st-key-write_header button p{font-size:0;line-height:0;}
.st-key-write_form{padding:12px 20px 16px;}
.st-key-write_form label p{font-size:13px!important;line-height:19px!important;font-weight:700;color:#1f1f1f!important;}
.st-key-write_form [data-testid="stWidgetLabel"]{margin-bottom:6px;min-height:19px;padding:0;}
.st-key-write_form [data-testid="stTextInput"],.st-key-write_form [data-testid="stTextArea"],
.st-key-write_form [data-testid="stSelectbox"],.st-key-write_form [data-testid="stDateTimeInput"]{margin-bottom:16px;}
.st-key-write_form [data-baseweb="input"],.st-key-write_form [data-baseweb="textarea"],
.st-key-write_form [data-baseweb="select"]>div{background:white!important;border:1px solid #dcdcdc!important;
 border-radius:10px!important;box-shadow:none!important;}
.st-key-write_form [data-baseweb="input"],.st-key-write_form [data-baseweb="select"]>div{min-height:46px;}
.st-key-write_form input,.st-key-write_form textarea{font-size:14px!important;line-height:20px!important;
 color:#1f1f1f!important;-webkit-text-fill-color:#1f1f1f!important;background:white!important;}
.st-key-write_form input{padding:12px 14px!important;}
.st-key-write_form input::placeholder,.st-key-write_form textarea::placeholder{-webkit-text-fill-color:#a0a0a0!important;opacity:1;}
.st-key-write_form textarea{padding:14px!important;min-height:94px!important;resize:vertical;}
.st-key-write_form [data-baseweb="select"]{font-size:14px!important;color:#1f1f1f!important;}
.st-key-write_form [data-baseweb="select"]>div{padding:0 14px;}
.st-key-write_form [data-baseweb="select"]>div>div:first-child{padding:0;margin:0;}
.st-key-write_form [data-baseweb="select"] div[value]{color:#1f1f1f!important;}
.st-key-write_form [data-baseweb="select"] input{padding:0!important;background:transparent!important;}
.st-key-write_form [data-baseweb="select"]>div>div:last-child{width:18px;height:18px;
 background-repeat:no-repeat;background-position:center;flex-shrink:0;}
.st-key-write_form [data-baseweb="select"] svg{visibility:hidden;}
.st-key-write_form [data-testid="stDateTimeInput"] [data-baseweb="input"]{
 background-repeat:no-repeat!important;background-position:right 14px center!important;}
.st-key-write_form [data-testid="stDateTimeInput"] input{background:transparent!important;padding-right:42px!important;}
[role="listbox"]{background:white!important;color:#1f1f1f!important;}
[role="option"]{color:#1f1f1f!important;}
.st-key-write_form svg{fill:#6b6b6b!important;}
.write-label{font-size:13px;font-weight:700;line-height:19px;color:#1f1f1f;margin-bottom:6px;}
.write-help{font-size:11px;color:#a0a0a0;line-height:16px;margin-top:6px;}
.st-key-write_capacity_field{margin-bottom:16px;}
.st-key-write_capacity{border:1px solid #dcdcdc;border-radius:10px;padding:6px 8px;box-sizing:border-box;
 height:44px!important;min-height:44px;max-height:44px;}
.st-key-write_capacity [data-testid="stButton"]{height:30px;line-height:0;}
.st-key-write_capacity [data-testid="stHorizontalBlock"]{gap:0;flex-wrap:nowrap!important;align-items:center;height:30px;}
.st-key-write_capacity [data-testid="stColumn"]{min-width:0!important;}
.st-key-write_capacity [data-testid="stColumn"]:first-child,
.st-key-write_capacity [data-testid="stColumn"]:last-child{flex:0 0 30px;}
.st-key-write_capacity [data-testid="stColumn"]:nth-child(2){flex:1 1 auto;}
.capacity-value{text-align:center;font-size:16px;font-weight:700;line-height:23px;color:#1f1f1f;}
.st-key-write_capacity button{display:block;width:30px!important;height:30px!important;min-height:30px!important;
 border:0;border-radius:8px;padding:0;background-color:#f7f6f4!important;background-repeat:no-repeat;background-position:center;}
.st-key-write_capacity button p{font-size:0;line-height:0;}
.st-key-write_capacity [data-testid="stColumn"]:last-child button{background-color:#fff1e9!important;}
.st-key-write_capacity button:disabled{opacity:.35;}
.st-key-write_options [data-testid="stHorizontalBlock"]{gap:10px;flex-wrap:nowrap!important;}
.st-key-write_options [data-testid="stColumn"]{min-width:0!important;flex:1 1 0;}
.st-key-write_submit{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:min(390px,100vw)!important;
 box-sizing:border-box;background:white;border-top:1px solid #ececec;padding:10px 16px 24px;z-index:30;}
.write-submit-hint{text-align:center;font-size:11px;color:#a0a0a0;line-height:16px;margin-bottom:8px;}
.st-key-write_submit [data-testid="stElementContainer"],.st-key-write_submit [data-testid="stButton"]{width:100%!important;}
.st-key-write_submit button{width:100%!important;min-height:51px;height:51px;background:#ff7a3d!important;
 color:white!important;border:0;border-radius:12px;padding:14px!important;}
.st-key-write_submit button p{font-size:16px!important;font-weight:700;line-height:23px;}
.st-key-write_errors [data-testid="stAlert"]{margin-bottom:8px;}
"""


def render_write_page():
    auth.require_login()
    finish_publish()
    if st.session_state.pop('_write_reset', False):
        st.session_state.pop('write_draft', None)
        for field in ('title', 'body', 'capacity', 'meal_time', 'region', 'food_category'):
            st.session_state.pop(f'write_{field}', None)
    css = ui.CSS + WRITE_CSS
    css += f'.st-key-write_header button{{background-image:url("{ui.asset("write_back")}");}}'
    for position, name in (('first', 'write_minus'), ('last', 'write_plus')):
        css += f'.st-key-write_capacity [data-testid="stColumn"]:{position}-child button{{background-image:url("{ui.asset(name)}");}}'
    css += f'.st-key-write_form [data-baseweb="select"]>div>div:last-child{{background-image:url("{ui.asset("write_chevron")}");}}'
    css += f'.st-key-write_form [data-testid="stDateTimeInput"] [data-baseweb="input"]{{background-image:url("{ui.asset("write_calendar")}")!important;}}'
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    draft = st.session_state.get('write_draft', {})
    default_time = (datetime.now() + timedelta(hours=1)).replace(second=0, microsecond=0)
    defaults = {'title': '', 'body': '', 'capacity': 3, 'meal_time': default_time,
                'region': REGIONS[0], 'food_category': FOOD_CATEGORIES[0]}
    for field, default in defaults.items():
        st.session_state.setdefault(f'write_{field}', draft.get(field, default))
    st.markdown('<div class="status-bar" aria-hidden="true"><strong>9:41</strong><span>LTE 100%</span></div>', unsafe_allow_html=True)
    with st.container(key='write_header'):
        back, title = st.columns([26, 1])
        with back:
            if st.button('뒤로', key='write_back'):
                remember_draft()
                st.switch_page('pages/1_feed.py')
        with title:
            st.markdown('<div class="write-title">모집 글 작성</div>', unsafe_allow_html=True)
    with st.container(key='write_form'):
        st.text_input('제목', key='write_title', max_chars=100, placeholder='같이 먹고 싶은 메뉴를 알려주세요')
        st.text_area('내용 · 구체적인 약속 장소', key='write_body', height=94,
                     placeholder='언제, 어디에서 만날지 자유롭게 적어 주세요')
        with st.container(key='write_capacity_field'):
            st.markdown('<div class="write-label">정원 (작성자 포함)</div>', unsafe_allow_html=True)
            with st.container(key='write_capacity'):
                minus, count, plus = st.columns([30, 1, 30])
                with minus:
                    if st.button('정원 줄이기', key='write_minus', disabled=st.session_state.write_capacity <= 2):
                        st.session_state.write_capacity -= 1
                        remember_draft()
                        st.rerun()
                with count:
                    st.markdown(f'<div class="capacity-value">{st.session_state.write_capacity}명</div>', unsafe_allow_html=True)
                with plus:
                    if st.button('정원 늘리기', key='write_plus', disabled=st.session_state.write_capacity >= 20):
                        st.session_state.write_capacity += 1
                        remember_draft()
                        st.rerun()
            st.markdown('<div class="write-help">나를 포함해 2~20명까지 가능해요</div>', unsafe_allow_html=True)
        st.datetime_input('식사 날짜와 시간', key='write_meal_time', format='YYYY-MM-DD', step=timedelta(minutes=15))
        with st.container(key='write_options'):
            region, food = st.columns(2)
            with region:
                st.selectbox('지역', REGIONS, key='write_region')
            with food:
                st.selectbox('음식 종류', FOOD_CATEGORIES, key='write_food_category')
        with st.container(key='write_errors'):
            errors_slot = st.empty()
    payload = build_payload(remember_draft())
    with st.container(key='write_submit'):
        st.markdown('<div class="write-submit-hint">미리보기에서 확인한 후 모집 글을 등록할 수 있어요</div>', unsafe_allow_html=True)
        if st.button('모집 글 미리보기', key='write_preview', use_container_width=True):
            errors = validate_post(payload)
            if errors:
                with errors_slot.container():
                    for message in errors:
                        st.error(message)
            else:
                st.session_state['_write_preview_payload'] = payload
                st.session_state.pop('_write_publish_error', None)
    if snapshot := st.session_state.get('_write_preview_payload'):
        show_preview(snapshot)


def main():
    st.set_page_config(page_title='머먹 · 모집 글 작성', page_icon='🍚', layout='centered')
    render_write_page()


if __name__ == '__main__':
    main()

"""Shared DB choices, Figma styles and local SVG assets for the front end."""
import base64
from html import escape
from pathlib import Path
import streamlit as st

FOOD_CATEGORIES = ('한식', '중식', '양식', '일식', '기타', '미정')


REGIONS = ('교내', '복정동', '태평동', '기타')


STATUS_LABELS = {
    'OPEN': '모집중', 'CLOSED': '마감',
    'COMPLETED': '식사 완료', 'CANCELED': '취소',
}


FEED_STATUSES = ('OPEN', 'CLOSED')


@st.cache_data
def asset(name):
    path = Path(__file__).resolve().parent / 'assets' / f'{name}.svg'
    return 'data:image/svg+xml;base64,' + base64.b64encode(path.read_bytes()).decode('ascii')


def icon(name):
    return f'<img src="{asset(name)}" alt="" aria-hidden="true">'


def e(value):
    return escape(str(value))


CSS = """
/* Reference: Figma 2:40. All dimensions below are CSS pixels. */
:root{--orange:#ff7a3d;--paper:#f7f6f4;--line:#ececec;--ink:#1f1f1f;--muted:#6b6b6b;}
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"]{
 background:#efeeec!important;color:var(--ink)!important;color-scheme:light;}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stSidebar"],
[data-testid="stDecoration"],#MainMenu,footer{display:none!important;}
[data-testid="stMain"]{scrollbar-width:none;}
[data-testid="stMain"]::-webkit-scrollbar{display:none;}
[data-testid="stMainBlockContainer"]{--text-color:#1f1f1f;--background-color:#fff;
 --secondary-background-color:#f7f6f4;width:100%!important;max-width:390px!important;
 height:auto!important;min-height:100dvh;flex:0 0 auto!important;
 padding:0 0 94px!important;margin:0 auto!important;
 background:var(--paper);font-family:'Noto Sans KR','Malgun Gothic',sans-serif;}
[data-testid="stMainBlockContainer"] p,[data-testid="stMainBlockContainer"] button{
 font-family:'Noto Sans KR','Malgun Gothic',sans-serif;}
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"]{gap:0!important;}
/* Streamlit 1.56 gives MarkdownContainer a -16px bottom margin.
   Raw HTML has no paragraph margin to offset, so remove it explicitly. */
[data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"]{margin-bottom:0!important;}
[data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"] p{margin:0;}
[data-testid="stElementContainer"]:has(>.stMarkdown style){display:none;}
.status-bar{height:40px;box-sizing:border-box;padding:14px 24px 6px;display:flex;
 align-items:center;justify-content:space-between;background:white;color:var(--ink);font-size:12px;line-height:20px;}
.status-bar strong{font-size:14px;font-weight:700;}
.st-key-header{background:white;height:51px!important;min-height:51px!important;max-height:51px!important;
 padding:8px 20px 12px!important;box-sizing:border-box;}
.st-key-header [data-testid="stHorizontalBlock"]{height:31px;gap:16px;align-items:center;flex-wrap:nowrap!important;}
.st-key-header [data-testid="stColumn"]{min-width:0!important;}
.st-key-header [data-testid="stColumn"]:first-child{flex:1 1 auto;}
.st-key-header [data-testid="stColumn"]:not(:first-child){flex:0 0 24px;}
.brand{font-size:22px;font-weight:800;line-height:31px;color:var(--orange);}
.st-key-header [data-testid="stButton"]{height:24px;line-height:0;}
.st-key-header button{display:flex;width:24px!important;min-width:24px!important;height:24px!important;
 min-height:24px!important;padding:0!important;border:0;border-radius:0;box-shadow:none;
 background-color:transparent!important;background-repeat:no-repeat;background-position:center;}
.st-key-header button p{font-size:0!important;line-height:0!important;}
.st-key-header button:hover{background-color:#fff1e9!important;border-radius:4px;}
.intro-block{height:49px;box-sizing:border-box;background:white;padding:4px 20px 0;}
.intro{font-size:18px;line-height:25px;font-weight:700;letter-spacing:-.6px;color:var(--ink);white-space:nowrap;}
.sub{font-size:13px;line-height:18px;color:var(--muted);margin-top:2px;}
.st-key-categories{height:62px;min-height:62px;box-sizing:border-box;background:white;
 padding:12px 8px 16px 20px!important;}
.st-key-categories [data-testid="stPills"]{overflow:hidden;}
.st-key-categories [role="radiogroup"]{display:flex;align-items:center;gap:8px!important;flex-wrap:nowrap!important;
 overflow-x:auto;scrollbar-width:none;max-width:100%;padding:0;}
.st-key-categories [role="radiogroup"]::-webkit-scrollbar{display:none;}
.st-key-categories button{height:34px!important;min-height:34px!important;min-width:54px;
 flex-shrink:0;border:1px solid var(--line)!important;border-radius:999px;background:white!important;
 color:var(--muted)!important;padding:7px 14px!important;white-space:nowrap;box-shadow:none!important;}
.st-key-categories button p{font-size:13px;line-height:18px;font-weight:500;}
.st-key-categories button[data-testid="stBaseButton-pillsActive"]{
 min-width:52px;height:32px!important;min-height:32px!important;border:0!important;
 background:var(--orange)!important;color:white!important;}
.st-key-categories button[data-testid="stBaseButton-pillsActive"] p{font-weight:700;}
.st-key-tools{background:white;padding:0 20px 16px!important;color:var(--ink);}
.st-key-tools [data-testid="stVerticalBlock"]{gap:8px!important;}
.st-key-tools label,.st-key-tools label p{color:var(--ink)!important;}
.st-key-tools [data-baseweb="select"]>div,.st-key-tools [data-baseweb="input"]{
 background:white!important;color:var(--ink)!important;border-color:#ddd!important;}
.st-key-tools input{background:white!important;color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important;}
.st-key-tools svg{fill:var(--muted)!important;}
.st-key-section{height:50px!important;min-height:50px!important;max-height:50px!important;
 padding:18px 20px 10px!important;box-sizing:border-box;}
.st-key-section [data-testid="stHorizontalBlock"]{height:22px;gap:0;align-items:center;flex-wrap:nowrap!important;}
.st-key-section [data-testid="stColumn"]{min-width:0!important;}
.st-key-section [data-testid="stColumn"]:first-child{flex:1 1 auto;}
.st-key-section [data-testid="stColumn"]:last-child{flex:0 0 84px;}
.section-title{font-size:16px;line-height:22px;font-weight:700;color:var(--ink);white-space:nowrap;}
.st-key-section [data-testid="stElementContainer"],.st-key-section [data-testid="stButton"]{width:100%!important;}
.st-key-section button{display:flex;width:100%!important;height:22px!important;min-height:22px!important;
 padding:0!important;border:0;border-radius:0;box-shadow:none;background:transparent!important;
 color:var(--muted)!important;justify-content:flex-end;align-items:center;}
.st-key-section button p{font-size:13px!important;line-height:18px!important;font-weight:500;}
.st-key-section button>div{justify-content:flex-end!important;}
[class*="st-key-card_"]{position:relative;height:160px!important;min-height:160px!important;
 max-height:160px!important;width:calc(100% - 40px)!important;margin:0 20px 12px!important;flex-shrink:0;}
.meetup-card{height:160px;width:100%;box-sizing:border-box;padding:16px;border:1px solid var(--line);
 border-radius:16px;background:white;box-shadow:0 2px 4px #0000000d;color:var(--ink);
 display:flex;flex-direction:column;gap:10px;}
.card-top,.card-bottom{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-shrink:0;}
.tags{display:flex;align-items:center;gap:6px;}
.badge,.food{border-radius:6px;padding:3px 8px;font-size:11px;line-height:15px;white-space:nowrap;}
.badge{background:var(--orange);color:white;font-weight:700;}
.badge.closed{background:#bdbdbd;}
.badge.completed{background:#e5f3ea;color:#277245;}
.badge.canceled{background:#fce8e6;color:#ae3930;}
.food{background:#fff1e9;color:var(--orange);font-weight:500;}
.time{display:flex;align-items:center;gap:4px;font-size:12px;line-height:17px;color:var(--muted);white-space:nowrap;}
.card-title{font-size:16px;font-weight:700;line-height:22px;letter-spacing:-.5px;
 margin:0;padding:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex-shrink:0;}
.region{display:flex;align-items:center;gap:4px;font-size:13px;line-height:18px;color:var(--muted);}
.card-rule{height:1px;background:var(--line);flex-shrink:0;}
.host{display:flex;align-items:center;gap:6px;font-size:12px;line-height:17px;white-space:nowrap;min-width:0;}
.host span{overflow:hidden;text-overflow:ellipsis;}
.stats{display:flex;align-items:center;gap:10px;white-space:nowrap;flex-shrink:0;}
.stat{display:flex;align-items:center;gap:3px;font-size:12px;line-height:17px;color:#a0a0a0;}
.stat.members{color:var(--orange);font-weight:700;}
.meetup-card img{display:block;flex-shrink:0;max-width:none;}
/* Keep the native button for keyboard interaction without adding layout height. */
[class*="st-key-card_"] [data-testid="stElementContainer"]:has(>[data-testid="stButton"]){
 position:absolute!important;inset:0;width:100%!important;z-index:2;}
[class*="st-key-card_"] [data-testid="stButton"]{position:absolute;inset:0;width:100%!important;height:160px;}
[class*="st-key-card_"] button{display:block;width:100%!important;height:160px!important;
 min-height:160px!important;padding:0;border:0;border-radius:16px;background:transparent!important;box-shadow:none;}
[class*="st-key-card_"] button p{font-size:0!important;line-height:0!important;}
[class*="st-key-card_"] button:hover{box-shadow:inset 0 0 0 1px #ff7a3d88;}
[class*="st-key-card_"] button:focus-visible{outline:3px solid var(--orange);outline-offset:3px;}
.st-key-fab{position:fixed;bottom:100px;left:calc(50% + 76px);width:99px!important;z-index:20;}
.st-key-fab button{display:flex;align-items:center;height:44px!important;min-height:44px!important;width:99px!important;
 padding:12px 20px 12px 40px!important;border:0;border-radius:999px;background-color:var(--orange)!important;
 background-repeat:no-repeat;background-position:16px center;color:white!important;box-shadow:0 4px 12px #ff7a3d59;}
.st-key-fab button p{font-size:14px!important;font-weight:700;line-height:20px;white-space:nowrap;}
.st-key-fab button:hover{background-color:#ed682b!important;}
.st-key-bottom_nav{position:fixed;bottom:0;left:50%;transform:translateX(-50%);z-index:30;
 width:min(390px,100vw)!important;height:70px!important;min-height:70px!important;box-sizing:border-box;
 padding:8px 0 20px!important;border-top:1px solid var(--line);background:white;}
.st-key-bottom_nav [data-testid="stHorizontalBlock"]{height:41px;gap:0;flex-wrap:nowrap!important;}
.st-key-bottom_nav [data-testid="stColumn"]{min-width:0!important;flex:1 1 0;}
.st-key-bottom_nav [data-testid="stElementContainer"],.st-key-bottom_nav [data-testid="stButton"]{width:100%!important;height:41px;}
.st-key-bottom_nav button{display:flex;align-items:flex-start;justify-content:center;height:41px!important;
 min-height:41px!important;width:100%!important;padding:26px 0 0!important;border:0;border-radius:0;
 background-color:transparent!important;background-repeat:no-repeat;background-position:center top;color:#a0a0a0!important;}
.st-key-bottom_nav button p{font-size:11px!important;line-height:15px!important;white-space:nowrap;}
.st-key-nav_home button{color:var(--orange)!important;font-weight:700;}
.demo-note{font-size:11px;line-height:16px;text-align:center;color:#777;padding:8px 20px 18px;}
.empty{margin:0 20px 16px;padding:28px 16px;background:white;border:1px solid var(--line);
 border-radius:16px;text-align:center;font-size:13px;color:var(--muted);}
[data-testid="stDialog"] [role="dialog"]{background:white!important;color:var(--ink)!important;}
[data-testid="stDialog"] p,[data-testid="stDialog"] h1,
[data-testid="stDialog"] h2,[data-testid="stDialog"] h3{color:var(--ink)!important;}
[data-testid="stDialog"] button{color:var(--ink)!important;}
[data-testid="stDialog"] button svg{fill:currentColor;}
[data-testid="stDialog"] button:disabled{background:#f7f6f4!important;border-color:#ececec!important;}
[data-testid="stDialog"] button:disabled p{color:#a0a0a0!important;}
@media(max-width:390px){.st-key-fab{left:auto;right:20px;}}
@media(max-width:350px){.intro{font-size:17px;letter-spacing:-.8px;}.host{font-size:11px;}.stats{gap:6px;}}
"""


for key, name in {'search_button': 'search', 'bell_button': 'bell', 'fab': 'plus',
                  'nav_home': 'home', 'nav_apply': 'calendar', 'nav_chat': 'groups', 'nav_profile': 'user'}.items():
    CSS += f'.st-key-{key} button{{background-image:url("{asset(name)}");}}\n'



"""Browser-session-only demo data. Replace these calls with team services for DB integration."""
from datetime import datetime, timedelta
import streamlit as st


def _seed_posts():
    """서비스 연결 지점. 아래 반환 형식은 화면용 제안이며 확정 API가 아니다.

    Post + Content + User를 합쳐 표시한다.
    current_count = ACCEPTED 참여자 수 + 작성자 1명.
    rating = 작성자가 받은 Review.rating의 평균 (평가 없으면 None).
    like_count / comment_count = 해당 게시물의 좋아요 / 댓글 수.
    위 네 값은 저장 컬럼이 아닌 조회 집계값이다.
    """
    now = datetime.now().replace(second=0, microsecond=0)
    rows = [
        (1, 1, '도윤', '수업 끝나고 김치찌개 먹을 사람', '교내', '한식',
         now + timedelta(hours=2), 4, 'OPEN', '수업 끝나고 같이 저녁 먹어요.', 2, 4.8, 5, 3),
        (2, 5, '민지', '내일 점심 돈가스 먹으러 갈 분', '복정동', '일식',
         (now + timedelta(days=1)).replace(hour=12, minute=0), 3, 'OPEN',
         '복정동에서 점심 먹을 분 구해요. 가게는 같이 정해요!', 1, None, 8, 2),
        (3, 4, '수민', '오늘 같이 식사하실 분', '태평동', '기타',
         now + timedelta(hours=1), 4, 'CLOSED', '인원이 모두 모여 모집을 마감했어요.', 4, 4.5, 12, 6),
        (4, 2, '지우', '다음 모임 메뉴는 같이 정해요', '기타', '미정',
         now - timedelta(days=1), 2, 'COMPLETED', '함께 식사해 주셔서 감사합니다.', 2, 5.0, 2, 1),
        (5, 3, '현우', '저녁 모임 취소 안내', '교내', '양식',
         now + timedelta(days=1), 3, 'CANCELED', '개인 사정으로 모임을 취소했습니다.', 1, None, 0, 0),
    ]
    keys = ('post_id', 'user_id', 'nickname', 'title', 'region', 'food_category',
            'meal_time', 'capacity', 'status', 'body', 'current_count',
            'rating', 'like_count', 'comment_count')
    posts = [dict(zip(keys, row)) for row in rows]
    for index, post in enumerate(posts):
        post['created_at'] = now - timedelta(minutes=10 * (index + 1))
    return posts


DEMO_USER = {'user_id': 6, 'nickname': '체험회원'}
USERS = {1: '도윤', 2: '지우', 3: '현우', 4: '수민', 5: '민지', 6: '체험회원'}


def get_store():
    if 'detail_demo_store' not in st.session_state:
        posts = _seed_posts()
        comments = {}
        samples = {
            1: [(4, '혹시 조금 늦게 합류해도 괜찮을까요?'),
                (1, '네 괜찮아요! 신청해 주세요.'),
                (5, '식당 입구에서 만나요!')],
            2: [(4, '내일 점심에 시간 돼요!'), (5, '좋아요. 신청해 주세요.')],
            3: [(1, '같이 먹어요!'), (4, '신청해 주세요.'), (2, '신청했어요.'),
                (5, '저도 함께할게요!'), (4, '네 확인했어요.'), (1, '그때 봬요!')],
        }
        next_id = 1
        for post in posts:
            rows = []
            for index, (uid, content) in enumerate(samples.get(post['post_id'], [])):
                rows.append({'comment_id': next_id, 'post_id': post['post_id'],
                             'user_id': uid, 'nickname': USERS[uid], 'content': content,
                             'created_at': post['created_at'] + timedelta(minutes=index + 1)})
                next_id += 1
            comments[post['post_id']] = rows
        st.session_state['detail_demo_store'] = {
            'posts': {p['post_id']: p for p in posts},
            'comments': comments, 'next_comment_id': next_id,
            'likes': set(), 'follows': set(),
            'participation': {(1, 5): 'ACCEPTED', (3, 1): 'ACCEPTED',
                              (3, 2): 'ACCEPTED', (3, 5): 'ACCEPTED'},
        }
    return st.session_state['detail_demo_store']


def current_user():
    # A separate demo identity never writes to the actual authentication session.
    return st.session_state.get('user') or dict(DEMO_USER)


def get_members(post_id):
    store = get_store()
    post = store['posts'].get(post_id)
    if post is None:
        return []
    rows = [{'user_id': post['user_id'], 'nickname': post['nickname'], 'is_host': True}]
    for (pid, uid), status in store['participation'].items():
        if pid == post_id and status == 'ACCEPTED' and uid != post['user_id']:
            rows.append({'user_id': uid, 'nickname': USERS.get(uid, '회원'), 'is_host': False})
    return rows


def get_post(post_id):
    store = get_store()
    original = store['posts'].get(post_id)
    if original is None:
        return None
    post = dict(original)
    post['current_count'] = len(get_members(post_id))
    post['like_count'] += sum(pid == post_id for uid, pid in store['likes'])
    post['comment_count'] = len(store['comments'][post_id])
    return post


def get_posts():
    return [get_post(pid) for pid in get_store()['posts']]


def get_comments(post_id):
    return [dict(c) for c in get_store()['comments'].get(post_id, [])]


def toggle_like(post_id, user_id):
    if get_post(post_id) is None:
        raise ValueError('게시물을 찾을 수 없어요.')
    likes = get_store()['likes']
    key = (user_id, post_id)
    if key in likes:
        likes.remove(key)
    else:
        likes.add(key)


def toggle_follow(user_id, author_id):
    if user_id == author_id:
        raise ValueError('자기 자신은 팔로우할 수 없어요.')
    follows = get_store()['follows']
    key = (user_id, author_id)
    if key in follows:
        follows.remove(key)
    else:
        follows.add(key)


def add_comment(post_id, user, content):
    text = content.strip()
    if not text:
        raise ValueError('댓글 내용을 입력해 주세요.')
    if len(text.encode('utf-8')) > 65535:
        raise ValueError('댓글이 너무 길어요. 조금 줄여 주세요.')
    if get_post(post_id) is None:
        raise ValueError('게시물을 찾을 수 없어요.')
    store = get_store()
    store['comments'][post_id].append({
        'comment_id': store['next_comment_id'], 'post_id': post_id,
        'user_id': user['user_id'], 'nickname': user['nickname'],
        'content': text, 'created_at': datetime.now(),
    })
    store['next_comment_id'] += 1


def application_state(post_id, user_id):
    return get_store()['participation'].get((post_id, user_id))


def apply_to_post(post_id, user_id):
    post = get_post(post_id)
    if post is None:
        raise ValueError('게시물을 찾을 수 없어요.')
    if post['user_id'] == user_id:
        raise ValueError('본인이 작성한 글에는 신청할 수 없어요.')
    if post['status'] != 'OPEN':
        raise ValueError('모집 중인 글에만 신청할 수 있어요.')
    if post['current_count'] >= post['capacity']:
        raise ValueError('이미 정원이 찼어요.')
    if application_state(post_id, user_id) in ('PENDING', 'ACCEPTED', 'REJECTED'):
        raise ValueError('이미 처리 중이거나 처리된 신청이에요.')
    get_store()['participation'][(post_id, user_id)] = 'PENDING'


def cancel_application(post_id, user_id):
    if application_state(post_id, user_id) != 'PENDING':
        raise ValueError('승인 대기 중인 신청만 취소할 수 있어요.')
    get_store()['participation'][(post_id, user_id)] = 'CANCELED'


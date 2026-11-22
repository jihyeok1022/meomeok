"""Exercise frontend service contracts without touching a real database."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import pymysql
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services import post_service, social_service
from test_login import post_fixture


class FrontendIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.post = post_fixture()
        self.comments = []
        self.list_posts = self.mock(post_service, 'list_posts', return_value=[self.post])
        self.get_post = self.mock(post_service, 'get_post', side_effect=lambda *a, **kw: dict(self.post))
        self.mock(social_service, 'list_comments', side_effect=lambda *a: list(self.comments))

    def mock(self, module, name, **kwargs):
        patcher = patch.object(module, name, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def app(self, page='1_feed.py'):
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=10)
        app.session_state['user'] = {'user_id': 1, 'nickname': '테스트'}
        app.run()
        if page != '1_feed.py':
            app.switch_page(f'pages/{page}').run()
        self.assertFalse(app.exception)
        return app

    def test_feed_filters_sort_and_pagination_call_service(self):
        app = self.app()
        self.list_posts.assert_called_with(region=None, food_category=None, status=None,
                                           keyword='', sort='latest', limit=21, offset=0)
        app.button(key='search_button').click().run()
        app.text_input(key='db_feed_query').input('김치').run()
        app.selectbox(key='db_feed_region').select('교내').run()
        app.selectbox(key='db_feed_status').select('OPEN').run()
        app.button(key='sort').click().run()
        self.assertEqual(self.list_posts.call_args.kwargs['keyword'], '김치')
        self.assertEqual(self.list_posts.call_args.kwargs['region'], '교내')
        self.assertEqual(self.list_posts.call_args.kwargs['status'], 'OPEN')
        self.assertEqual(self.list_posts.call_args.kwargs['sort'], 'meal_time')
        self.list_posts.return_value = [dict(self.post, post_id=i) for i in range(1, 22)]
        app.run()
        app.button(key='feed_next').click().run()
        self.assertEqual(self.list_posts.call_args.kwargs['offset'], 20)
        app.text_input(key='db_feed_query').input('다른 검색').run()
        self.assertEqual(self.list_posts.call_args.kwargs['offset'], 0)
        self.assertFalse(app.exception)

    def test_feed_connection_error_has_retry_and_logout(self):
        self.list_posts.side_effect = pymysql.OperationalError(2003, 'private-detail')
        app = self.app()
        self.assertIn('불러오지 못했어요', app.error[0].value)
        self.assertNotIn('private-detail', app.error[0].value)
        self.assertTrue(app.button(key='feed_retry'))
        self.assertTrue(app.button(key='feed_logout'))

    def test_feed_never_renders_completed_or_canceled_posts(self):
        self.list_posts.return_value = [dict(self.post, status=status, post_id=i)
                                        for i, status in enumerate(('OPEN', 'CLOSED', 'COMPLETED', 'CANCELED'), 1)]
        app = self.app()
        self.assertEqual({b.key for b in app.button if b.key.startswith('db_open_')},
                         {'db_open_1', 'db_open_2'})

    def prepare_preview(self, app):
        app.text_input(key='write_title').input('등록 테스트').run()
        app.text_area(key='write_body').input('테스트 약속 장소').run()
        app.button(key='write_preview').click().run()
        self.assertFalse(app.exception)
        self.assertTrue(app.button(key='write_publish'))

    def test_publish_real_service_contract_and_reset_draft(self):
        create = self.mock(post_service, 'create_post', return_value=30)
        app = self.app('2_write_post.py')
        self.prepare_preview(app)
        app.button(key='write_publish').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(create.call_count, 1)
        user_id, payload = create.call_args.args
        self.assertEqual(user_id, 1)
        self.assertEqual(set(payload), {'title', 'body', 'capacity', 'meal_time', 'region', 'food_category'})
        self.assertEqual(payload['title'], '등록 테스트')
        self.assertEqual(app.session_state['selected_post_id'], 30)
        app.switch_page('pages/2_write_post.py').run()
        self.assertEqual(app.text_input(key='write_title').value, '')
        self.assertFalse(app.exception)

    def test_publish_failure_preserves_input(self):
        self.mock(post_service, 'create_post', side_effect=pymysql.OperationalError(2003, 'private-detail'))
        app = self.app('2_write_post.py')
        self.prepare_preview(app)
        app.button(key='write_publish').click().run()
        self.assertFalse(app.exception)
        self.assertIn('등록하지 못했어요', app.error[0].value)
        self.assertEqual(app.session_state['write_draft']['title'], '등록 테스트')

    def test_like_follow_use_target_state_and_refresh(self):
        def like(post_id, user_id, liked):
            self.post.update(is_liked=liked, like_count=int(liked))
            return {'is_liked': liked, 'like_count': int(liked)}
        def follow(user_id, author_id, following):
            self.post['is_following_author'] = following
            return {'is_following': following}
        set_like = self.mock(social_service, 'set_like', side_effect=like)
        set_follow = self.mock(social_service, 'set_follow', side_effect=follow)
        app = self.app('3_post_detail.py')
        app.session_state['selected_post_id'] = 3
        app.run()
        app.button(key='detail_like_button').click().run()
        set_like.assert_called_with(3, 1, True)
        self.assertEqual(app.button(key='detail_like_button').label, '좋아요 취소')
        app.button(key='detail_like_button').click().run()
        set_like.assert_called_with(3, 1, False)
        app.button(key='detail_follow_button').click().run()
        set_follow.assert_called_with(1, 2, True)
        self.assertEqual(app.button(key='detail_follow_button').label, '팔로잉')
        self.assertTrue(app.button(key='detail_apply').disabled)
        self.assertFalse(app.exception)

    def test_failed_like_does_not_show_success_or_change_state(self):
        self.mock(social_service, 'set_like', side_effect=pymysql.OperationalError(2003, 'private'))
        app = self.app('3_post_detail.py')
        app.session_state['selected_post_id'] = 3
        app.run()
        app.button(key='detail_like_button').click().run()
        self.assertIn('저장하지 못했어요', app.error[0].value)
        self.assertEqual(app.button(key='detail_like_button').label, '좋아요')
        self.assertFalse(app.exception)

    def test_comment_failure_retains_text_success_escapes_and_clears(self):
        create = self.mock(social_service, 'create_comment', side_effect=pymysql.OperationalError(2003, 'private'))
        app = self.app('3_post_detail.py')
        app.session_state['selected_post_id'] = 3
        app.run()
        app.text_area(key='detail_comment_input_3').input('<script>test</script>')
        next(b for b in app.button if b.key.startswith('FormSubmitter:')).click().run()
        self.assertIn('등록하지 못했어요', app.error[0].value)
        self.assertEqual(app.text_area(key='detail_comment_input_3').value, '<script>test</script>')
        def save(post_id, user_id, content):
            from datetime import datetime
            row = dict(comment_id=1, post_id=post_id, user_id=user_id, nickname='테스트',
                       content=content, created_at=datetime.now())
            self.comments.append(row)
            self.post['comment_count'] += 1
            return row
        create.side_effect = save
        next(b for b in app.button if b.key.startswith('FormSubmitter:')).click().run()
        create.assert_called_with(3, 1, '<script>test</script>')
        self.assertEqual(app.text_area(key='detail_comment_input_3').value, '')
        self.assertTrue(any('&lt;script&gt;test&lt;/script&gt;' in m.value for m in app.markdown))
        self.assertFalse(app.exception)

    def test_detail_database_failure_and_invalid_link(self):
        self.get_post.side_effect = pymysql.OperationalError(2003, 'private')
        app = self.app('3_post_detail.py')
        self.assertIn('게시물을 불러오지 못했어요', app.error[0].value)
        self.assertTrue(app.button(key='detail_retry'))
        self.assertTrue(app.button(key='detail_back'))
        self.assertFalse(any(b.key == 'detail_like_button' for b in app.button))
        self.get_post.side_effect = ValueError('invalid post id')
        app.run()
        self.assertTrue(app.warning)
        self.assertFalse(app.exception)


if __name__ == '__main__':
    unittest.main()

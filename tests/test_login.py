"""Login UI contract tests; no MySQL server or real credentials required."""
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

import pymysql
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import auth
from services import post_service
from datetime import datetime, timedelta


def post_fixture():
    return dict(post_id=3, user_id=2, nickname='도윤', title='테스트 모집 글', body='테스트 본문',
                region='교내', food_category='한식', meal_time=datetime.now() + timedelta(days=1),
                capacity=4, status='OPEN', created_at=datetime.now(), current_count=1,
                rating=None, like_count=0, comment_count=0, is_liked=False,
                is_following_author=False)


class LoginTests(unittest.TestCase):
    def setUp(self):
        self.list_patch = patch.object(post_service, 'list_posts', return_value=[])
        self.detail_patch = patch.object(post_service, 'get_post', return_value=post_fixture())
        self.list_patch.start()
        self.detail_patch.start()
        self.addCleanup(self.list_patch.stop)
        self.addCleanup(self.detail_patch.stop)

    def app(self):
        app = AppTest.from_file(str(ROOT / 'app.py')).run()
        self.assertFalse(app.exception)
        return app

    def submit(self, app, login_id='test', password='test-password'):
        app.text_input(key='login_id').input(login_id)
        app.text_input(key='login_password').input(password)
        app.button[0].click().run()
        self.assertFalse(app.exception)

    def test_blank_fields_do_not_call_backend(self):
        with patch.object(auth, 'login') as login:
            app = self.app()
            self.submit(app, login_id=' ', password='')
            login.assert_not_called()
            self.assertIn('모두 입력', app.error[0].value)

    def test_rejected_credentials_clear_password_keep_identity(self):
        with patch.object(auth, 'login', return_value=None) as login:
            app = self.app()
            self.submit(app, login_id=' test@gachon.ac.kr ')
            login.assert_called_once_with('test@gachon.ac.kr', 'test-password')
            self.assertIn('일치하지', app.error[0].value)
            self.assertEqual(app.text_input(key='login_password').value, '')
            self.assertEqual(app.text_input(key='login_id').value, ' test@gachon.ac.kr ')
            self.assertNotIn('user', app.session_state)

    def test_connection_error_does_not_leak_details(self):
        with patch.object(auth, 'login', side_effect=pymysql.OperationalError(2003, 'private-db-detail')):
            app = self.app()
            self.submit(app)
            self.assertIn('연결하지 못했어요', app.error[0].value)
            self.assertNotIn('private-db-detail', app.error[0].value)
            self.assertEqual(app.text_input(key='login_password').value, '')
            self.assertNotIn('user', app.session_state)

    def test_login_and_logout_clear_account_state(self):
        with patch.object(auth, 'login', return_value={'user_id': 1, 'nickname': '테스트'}):
            app = self.app()
            self.submit(app)
            self.assertEqual(app.session_state['user'], {'user_id': 1, 'nickname': '테스트'})
            self.assertTrue(app.button(key='db_write_post'))
            app.session_state['write_draft'] = {'title': 'private draft'}
            app.button(key='feed_logout').click().run()
            self.assertFalse(app.exception)
            self.assertTrue(app.text_input(key='login_password'))
            self.assertNotIn('user', app.session_state)
            self.assertNotIn('write_draft', app.session_state)
            self.assertNotIn('detail_demo_store', app.session_state)

    def test_direct_routes_require_login(self):
        # AppTest.switch_page uses the legacy pages-directory runner, bypassing
        # the st.navigation entry point. Check the app gate at its boundary,
        # and each implemented page's independent require_login guard instead.
        page = Mock()
        with patch('streamlit.navigation', return_value=page):
            self.assertTrue(self.app().text_input(key='login_password'))
            page.run.assert_not_called()
        for filename in ('1_feed.py', '2_write_post.py', '3_post_detail.py'):
            with self.subTest(page=filename):
                app = AppTest.from_file(str(ROOT / 'pages' / filename)).run()
                self.assertFalse(app.exception)
                self.assertTrue(app.warning)
                self.assertFalse(app.text_input)

    def test_shared_post_link_survives_login(self):
        with patch.object(auth, 'login', return_value={'user_id': 1, 'nickname': '테스트'}):
            app = AppTest.from_file(str(ROOT / 'app.py'))
            app.query_params['post'] = '3'
            app.run()
            self.submit(app)
            self.assertEqual(app.session_state['selected_post_id'], 3)
            self.assertTrue(app.button(key='detail_back'))

    def test_actual_login_function_verifies_seed_bcrypt_password(self):
        import re
        seed = (ROOT / '05_demo_passwords.sql').read_text(encoding='utf-8')
        password_hash = re.search(r"SET password_hash = '([^']+)'", seed).group(1)
        row = {'user_id': 1, 'nickname': '테스트', 'password_hash': password_hash}
        with patch.object(auth, 'query_one', return_value=row) as query:
            app = self.app()
            self.submit(app, login_id='jihyeok03', password='pass1234')
            self.assertEqual(app.session_state['user']['user_id'], 1)
            self.assertEqual(query.call_args.args[1], ('jihyeok03', 'jihyeok03'))


if __name__ == '__main__':
    unittest.main()

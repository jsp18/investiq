"""
Unit tests for services/auth_service.py — register, login, profile CRUD.
"""
import pytest
from services.auth_service import register_user, login_user, get_user_profile, update_user_profile
from database import User, Profile


class TestRegisterUser:
    def test_successful_registration(self, app, db_session):
        result = register_user('newuser', 'new@example.com', 'pass123', 'New User')
        assert result['success'] is True
        assert 'user_id' in result

    def test_register_creates_empty_profile(self, app, db_session):
        result = register_user('profcheck', 'prof@check.com', 'pass123')
        profile = Profile.query.filter_by(user_id=result['user_id']).first()
        assert profile is not None

    def test_missing_username(self, app, db_session):
        assert register_user('', 'a@b.com', 'pass123')['success'] is False

    def test_missing_email(self, app, db_session):
        assert register_user('user1', '', 'pass123')['success'] is False

    def test_missing_password(self, app, db_session):
        assert register_user('user2', 'u2@test.com', '')['success'] is False

    def test_short_password(self, app, db_session):
        r = register_user('user3', 'u3@test.com', '12345')
        assert r['success'] is False and '6 characters' in r['error']

    def test_short_username(self, app, db_session):
        r = register_user('ab', 'ab@test.com', 'password')
        assert r['success'] is False and '3 characters' in r['error']

    def test_invalid_email(self, app, db_session):
        r = register_user('user4', 'not-an-email', 'password')
        assert r['success'] is False and 'email' in r['error'].lower()

    def test_duplicate_username(self, app, db_session):
        register_user('dupuser', 'first@test.com', 'password')
        assert register_user('dupuser', 'second@test.com', 'password')['success'] is False

    def test_duplicate_email(self, app, db_session):
        register_user('user_a', 'dup@test.com', 'password')
        assert register_user('user_b', 'dup@test.com', 'password')['success'] is False


class TestLoginUser:
    def _register(self, db_session):
        register_user('logintest', 'login@test.com', 'secret123', 'Login Test')

    def test_successful_login_by_username(self, app, db_session):
        self._register(db_session)
        r = login_user('logintest', 'secret123')
        assert r['success'] is True and r['user']['username'] == 'logintest'

    def test_successful_login_by_email(self, app, db_session):
        self._register(db_session)
        assert login_user('login@test.com', 'secret123')['success'] is True

    def test_wrong_password(self, app, db_session):
        self._register(db_session)
        assert login_user('logintest', 'wrongpass')['success'] is False

    def test_nonexistent_user(self, app, db_session):
        assert login_user('ghost', 'nopass')['success'] is False

    def test_empty_credentials(self, app, db_session):
        assert login_user('', '')['success'] is False

    def test_login_updates_last_login(self, app, db_session):
        self._register(db_session)
        login_user('logintest', 'secret123')
        user = User.query.filter_by(username='logintest').first()
        assert user.last_login is not None

    def test_login_returns_user_data(self, app, db_session):
        self._register(db_session)
        user_data = login_user('logintest', 'secret123')['user']
        assert all(k in user_data for k in ('id', 'email', 'full_name'))


class TestGetUserProfile:
    def test_get_existing_profile(self, app, db_session):
        r = register_user('getprof', 'gp@test.com', 'password')
        assert get_user_profile(r['user_id']) is not None

    def test_get_nonexistent_profile(self, app, db_session):
        assert get_user_profile(99999) is None

    def test_profile_returns_dict(self, app, db_session):
        r = register_user('dictprof', 'dp@test.com', 'password')
        p = get_user_profile(r['user_id'])
        assert isinstance(p, dict) and 'age' in p


class TestUpdateUserProfile:
    def test_successful_update(self, app, db_session):
        reg = register_user('upduser', 'upd@test.com', 'password')
        data = {'age': 32, 'risk_tolerance': 'aggressive', 'investment_horizon': 'long'}
        assert update_user_profile(reg['user_id'], data)['success'] is True
        assert get_user_profile(reg['user_id'])['age'] == 32

    def test_update_nonexistent_profile(self, app, db_session):
        r = update_user_profile(99999, {'age': 25})
        assert r['success'] is False and 'not found' in r['error'].lower()

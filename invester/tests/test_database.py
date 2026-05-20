"""
Unit tests for database.py — SQLAlchemy models, relationships, and constraints.
"""
import pytest
from datetime import datetime
from werkzeug.security import generate_password_hash
from database import db, User, Profile, Portfolio, Prediction, Recommendation, Watchlist, init_db


class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, app, db_session):
        user = User(
            username='alice',
            email='alice@example.com',
            password_hash=generate_password_hash('securepass'),
            full_name='Alice Smith'
        )
        db_session.add(user)
        db_session.commit()

        fetched = User.query.filter_by(username='alice').first()
        assert fetched is not None
        assert fetched.email == 'alice@example.com'
        assert fetched.full_name == 'Alice Smith'

    def test_user_created_at_auto_set(self, app, db_session):
        user = User(username='bob', email='bob@test.com',
                    password_hash=generate_password_hash('pass123'))
        db_session.add(user)
        db_session.commit()
        assert user.created_at is not None

    def test_duplicate_username_raises(self, app, db_session):
        u1 = User(username='dup', email='a@a.com',
                  password_hash=generate_password_hash('p'))
        db_session.add(u1)
        db_session.commit()

        u2 = User(username='dup', email='b@b.com',
                  password_hash=generate_password_hash('p'))
        db_session.add(u2)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()

    def test_duplicate_email_raises(self, app, db_session):
        u1 = User(username='user1', email='same@mail.com',
                  password_hash=generate_password_hash('p'))
        db_session.add(u1)
        db_session.commit()

        u2 = User(username='user2', email='same@mail.com',
                  password_hash=generate_password_hash('p'))
        db_session.add(u2)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()

    def test_user_default_full_name(self, app, db_session):
        user = User(username='noname', email='no@name.com',
                    password_hash=generate_password_hash('p'))
        db_session.add(user)
        db_session.commit()
        assert user.full_name == ''


class TestProfileModel:
    """Tests for the Profile model."""

    def _create_user(self, session):
        user = User(username='profuser', email='prof@test.com',
                    password_hash=generate_password_hash('pass'))
        session.add(user)
        session.flush()
        return user

    def test_create_profile(self, app, db_session):
        user = self._create_user(db_session)
        profile = Profile(
            user_id=user.id, age=28, monthly_income=60000,
            investment_amount=200000, risk_tolerance='aggressive',
            investment_horizon='long', experience_level='expert',
            goals='wealth_growth', profession='Doctor'
        )
        db_session.add(profile)
        db_session.commit()

        fetched = Profile.query.filter_by(user_id=user.id).first()
        assert fetched.age == 28
        assert fetched.risk_tolerance == 'aggressive'

    def test_profile_defaults(self, app, db_session):
        user = self._create_user(db_session)
        profile = Profile(user_id=user.id)
        db_session.add(profile)
        db_session.commit()

        assert profile.risk_tolerance == 'moderate'
        assert profile.investment_horizon == 'medium'
        assert profile.experience_level == 'beginner'
        assert profile.goals == 'wealth_growth'
        assert profile.investment_amount == 0

    def test_user_profile_relationship(self, app, db_session):
        user = self._create_user(db_session)
        profile = Profile(user_id=user.id, age=35)
        db_session.add(profile)
        db_session.commit()

        assert user.profile is not None
        assert user.profile.age == 35

    def test_cascade_delete_profile(self, app, db_session):
        user = self._create_user(db_session)
        profile = Profile(user_id=user.id, age=40)
        db_session.add(profile)
        db_session.commit()

        db_session.delete(user)
        db_session.commit()

        assert Profile.query.filter_by(user_id=user.id).first() is None


class TestPortfolioModel:
    """Tests for the Portfolio model."""

    def test_create_portfolio_entry(self, app, db_session):
        user = User(username='portuser', email='port@test.com',
                    password_hash=generate_password_hash('p'))
        db_session.add(user)
        db_session.flush()

        entry = Portfolio(
            user_id=user.id, asset_type='stocks',
            symbol='RELIANCE.NS', name='Reliance Industries',
            allocation_pct=25.0, amount=50000, buy_price=2500, quantity=20
        )
        db_session.add(entry)
        db_session.commit()

        assert entry.id is not None
        assert user.portfolios[0].symbol == 'RELIANCE.NS'

    def test_multiple_portfolio_entries(self, app, db_session):
        user = User(username='multiport', email='mp@test.com',
                    password_hash=generate_password_hash('p'))
        db_session.add(user)
        db_session.flush()

        for sym in ['TCS.NS', 'INFY.NS', 'SBIN.NS']:
            db_session.add(Portfolio(user_id=user.id, asset_type='stocks', symbol=sym))
        db_session.commit()

        assert len(user.portfolios) == 3


class TestPredictionModel:
    """Tests for the Prediction model."""

    def test_create_prediction(self, app, db_session):
        user = User(username='preduser', email='pred@test.com',
                    password_hash=generate_password_hash('p'))
        db_session.add(user)
        db_session.flush()

        pred = Prediction(
            user_id=user.id, symbol='TCS.NS',
            prediction_type='price', predicted_value=3800.50,
            confidence=72.5, direction='UP', model_used='random_forest'
        )
        db_session.add(pred)
        db_session.commit()

        assert pred.id is not None
        assert pred.direction == 'UP'
        assert pred.created_at is not None


class TestRecommendationModel:
    """Tests for the Recommendation model."""

    def test_create_recommendation(self, app, db_session):
        user = User(username='recuser', email='rec@test.com',
                    password_hash=generate_password_hash('p'))
        db_session.add(user)
        db_session.flush()

        rec = Recommendation(
            user_id=user.id, category='stocks',
            symbol='HDFCBANK.NS', name='HDFC Bank',
            allocation_pct=15.0, amount=15000, risk_score=4.2,
            expected_return=12.5, reasoning='BUY', confidence=68.0
        )
        db_session.add(rec)
        db_session.commit()

        assert rec.id is not None
        assert user.recommendations[0].category == 'stocks'


class TestWatchlistModel:
    """Tests for the Watchlist model."""

    def test_add_to_watchlist(self, app, db_session):
        user = User(username='watchuser', email='watch@test.com',
                    password_hash=generate_password_hash('p'))
        db_session.add(user)
        db_session.flush()

        wl = Watchlist(user_id=user.id, symbol='INFY.NS')
        db_session.add(wl)
        db_session.commit()

        assert user.watchlist[0].symbol == 'INFY.NS'

    def test_unique_constraint_user_symbol(self, app, db_session):
        user = User(username='uniqwatch', email='uw@test.com',
                    password_hash=generate_password_hash('p'))
        db_session.add(user)
        db_session.flush()

        db_session.add(Watchlist(user_id=user.id, symbol='SBIN.NS'))
        db_session.commit()

        db_session.add(Watchlist(user_id=user.id, symbol='SBIN.NS'))
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()


class TestInitDb:
    """Tests for the init_db function."""

    def test_init_db_creates_tables(self, app):
        with app.app_context():
            try:
                init_db(app)
            except RuntimeError as e:
                assert "already been registered" in str(e)
            # Verify tables exist by querying
            assert User.query.all() is not None
            assert Profile.query.all() is not None

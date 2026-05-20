"""
Shared pytest fixtures for InvestIQ unit tests.
Uses an in-memory SQLite database so tests run without MySQL.
"""
import sys
import os
import pytest
import numpy as np
import pandas as pd

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Override SQLALCHEMY_DATABASE_URI to use SQLite in-memory db before any flask code runs
from config import Config
Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

from app import create_app
from database import db as _db, User, Profile, Portfolio, Prediction, Recommendation, Watchlist


# ---------------------------------------------------------------------------
# Flask app & database fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def app():
    """Create a Flask app configured for testing with in-memory SQLite."""
    test_app = create_app()
    test_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
    })
    # db is already initialized inside create_app(), so we just need to create tables
    with test_app.app_context():
        _db.create_all()
    yield test_app
    with test_app.app_context():
        _db.drop_all()


@pytest.fixture(scope='function')
def db_session(app):
    """Provide a clean database session for each test function."""
    with app.app_context():
        _db.create_all()
        yield _db.session
        _db.session.rollback()
        # Clean all tables after each test
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def auth_client(app, db_session):
    """Flask test client with a pre-authenticated session."""
    from werkzeug.security import generate_password_hash

    user = User(
        username='testuser',
        email='test@example.com',
        password_hash=generate_password_hash('password123'),
        full_name='Test User'
    )
    db_session.add(user)
    db_session.flush()

    profile = Profile(
        user_id=user.id,
        age=30,
        monthly_income=50000,
        investment_amount=100000,
        risk_tolerance='moderate',
        investment_horizon='medium',
        experience_level='intermediate',
        goals='wealth_growth',
        profession='Engineer'
    )
    db_session.add(profile)
    db_session.commit()

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = user.id
        sess['username'] = user.username
        sess['full_name'] = user.full_name

    return client, user


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_ohlcv_df():
    """Generate a synthetic OHLCV DataFrame (200 trading days)."""
    np.random.seed(42)
    n = 200
    dates = pd.bdate_range(start='2024-01-01', periods=n)

    close = 1000 + np.cumsum(np.random.randn(n) * 5)
    high = close + np.abs(np.random.randn(n) * 3)
    low = close - np.abs(np.random.randn(n) * 3)
    open_ = close + np.random.randn(n) * 2
    volume = np.random.randint(100000, 5000000, size=n).astype(float)

    df = pd.DataFrame({
        'Open': open_,
        'High': high,
        'Low': low,
        'Close': close,
        'Volume': volume
    }, index=dates)
    return df


@pytest.fixture
def small_ohlcv_df():
    """Generate a very small OHLCV DataFrame (20 rows) for edge-case tests."""
    np.random.seed(99)
    n = 20
    dates = pd.bdate_range(start='2024-06-01', periods=n)
    close = 500 + np.cumsum(np.random.randn(n) * 2)
    return pd.DataFrame({
        'Open': close + np.random.randn(n),
        'High': close + 2,
        'Low': close - 2,
        'Close': close,
        'Volume': np.random.randint(50000, 1000000, n).astype(float)
    }, index=dates)


@pytest.fixture
def sample_market_df():
    """Generate a synthetic market-index OHLCV DataFrame."""
    np.random.seed(7)
    n = 200
    dates = pd.bdate_range(start='2024-01-01', periods=n)
    close = 20000 + np.cumsum(np.random.randn(n) * 50)
    return pd.DataFrame({
        'Open': close + np.random.randn(n) * 20,
        'High': close + np.abs(np.random.randn(n) * 30),
        'Low': close - np.abs(np.random.randn(n) * 30),
        'Close': close,
        'Volume': np.random.randint(1e6, 1e8, n).astype(float)
    }, index=dates)

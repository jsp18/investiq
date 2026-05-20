"""
Database models and initialization for InvestIQ using SQLAlchemy
Converted from raw SQLite to SQLAlchemy for MySQL support
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    profile = db.relationship('Profile', backref='user', uselist=False, cascade="all, delete-orphan")
    portfolios = db.relationship('Portfolio', backref='user', cascade="all, delete-orphan")
    predictions = db.relationship('Prediction', backref='user', cascade="all, delete-orphan")
    recommendations = db.relationship('Recommendation', backref='user', cascade="all, delete-orphan")
    watchlist = db.relationship('Watchlist', backref='user', cascade="all, delete-orphan")

class Profile(db.Model):
    __tablename__ = 'profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    age = db.Column(db.Integer)
    monthly_income = db.Column(db.Float)
    investment_amount = db.Column(db.Float, default=0)
    risk_tolerance = db.Column(db.String(20), default='moderate')
    investment_horizon = db.Column(db.String(20), default='medium')
    experience_level = db.Column(db.String(20), default='beginner')
    goals = db.Column(db.String(50), default='wealth_growth')
    profession = db.Column(db.String(100), default='')
    existing_investments = db.Column(db.Text, default='')
    preferred_sectors = db.Column(db.String(255), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), default='')
    allocation_pct = db.Column(db.Float, default=0)
    amount = db.Column(db.Float, default=0)
    buy_price = db.Column(db.Float, default=0)
    quantity = db.Column(db.Float, default=0)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

class Prediction(db.Model):
    __tablename__ = 'predictions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    symbol = db.Column(db.String(20), nullable=False)
    prediction_type = db.Column(db.String(50), default='price')
    predicted_value = db.Column(db.Float)
    actual_value = db.Column(db.Float)
    confidence = db.Column(db.Float)
    direction = db.Column(db.String(10))
    features_used = db.Column(db.Text)
    model_used = db.Column(db.String(50), default='random_forest')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(20))
    name = db.Column(db.String(100))
    allocation_pct = db.Column(db.Float)
    amount = db.Column(db.Float)
    risk_score = db.Column(db.Float)
    expected_return = db.Column(db.Float)
    reasoning = db.Column(db.Text)
    confidence = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Watchlist(db.Model):
    __tablename__ = 'watchlist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'symbol', name='_user_symbol_uc'),)

def init_db(app):
    """Initialize database with SQLAlchemy"""
    db.init_app(app)
    with app.app_context():
        try:
            db.create_all()
            print("[OK] Database models created successfully")
        except Exception as e:
            print(f"[ERROR] Failed to initialize database: {e}")
            print("Make sure your MySQL server is running and the database exists.")

def get_db():
    """Helper to maintain backward compatibility if needed (returns session)"""
    return db.session

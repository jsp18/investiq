"""
Authentication Service — User registration, login, session management
Converted to SQLAlchemy for MySQL support
"""
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, User, Profile
from datetime import datetime


def register_user(username, email, password, full_name=''):
    """
    Register a new user.
    """
    if not username or not email or not password:
        return {'success': False, 'error': 'All fields are required'}
    
    if len(password) < 6:
        return {'success': False, 'error': 'Password must be at least 6 characters'}
    
    if len(username) < 3:
        return {'success': False, 'error': 'Username must be at least 3 characters'}
    
    if '@' not in email:
        return {'success': False, 'error': 'Invalid email address'}
    
    try:
        # Check if username or email already exists
        existing = User.query.filter((User.username == username) | (User.email == email)).first()
        
        if existing:
            return {'success': False, 'error': 'Username or email already exists'}
        
        password_hash = generate_password_hash(password)
        
        # Create user
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name
        )
        db.session.add(new_user)
        db.session.flush()  # To get the ID
        
        # Create empty profile
        new_profile = Profile(user_id=new_user.id)
        db.session.add(new_profile)
        
        db.session.commit()
        
        return {'success': True, 'user_id': new_user.id, 'username': username}
    
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}


def login_user(username, password):
    """
    Authenticate user and return user data.
    """
    if not username or not password:
        return {'success': False, 'error': 'Username and password are required'}
    
    try:
        # Search by username or email
        user = User.query.filter((User.username == username) | (User.email == username)).first()
        
        if not user:
            return {'success': False, 'error': 'Invalid username or password'}
        
        if not check_password_hash(user.password_hash, password):
            return {'success': False, 'error': 'Invalid username or password'}
        
        # Update last login
        user.last_login = datetime.now()
        db.session.commit()
        
        return {
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name
            }
        }
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_user_profile(user_id):
    """Get user profile data"""
    try:
        profile = Profile.query.filter_by(user_id=user_id).first()
        if profile:
            # Convert to dict for backward compatibility with existing route logic
            profile_data = {c.name: getattr(profile, c.name) for c in profile.__table__.columns}
            return profile_data
        return None
    except Exception:
        return None


def update_user_profile(user_id, data):
    """Update user investment profile"""
    try:
        profile = Profile.query.filter_by(user_id=user_id).first()
        if not profile:
            return {'success': False, 'error': 'Profile not found'}
        
        # Update fields
        profile.age = data.get('age')
        profile.monthly_income = data.get('monthly_income')
        profile.investment_amount = data.get('investment_amount')
        profile.risk_tolerance = data.get('risk_tolerance', 'moderate')
        profile.investment_horizon = data.get('investment_horizon', 'medium')
        profile.experience_level = data.get('experience_level', 'beginner')
        profile.goals = data.get('goals', 'wealth_growth')
        profile.profession = data.get('profession', '')
        profile.existing_investments = data.get('existing_investments', '')
        profile.preferred_sectors = data.get('preferred_sectors', '')
        profile.updated_at = datetime.now()
        
        db.session.commit()
        return {'success': True}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}

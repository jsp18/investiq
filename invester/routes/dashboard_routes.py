"""
Dashboard & Profile Routes
"""
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from services.auth_service import get_user_profile, update_user_profile
from services.recommendation import get_recommendation_history
from functools import wraps

dashboard_bp = Blueprint('dashboard', __name__)


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Login required'}), 401
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@dashboard_bp.route('/')
@login_required
def home():
    """Main dashboard page"""
    profile = get_user_profile(session['user_id'])
    has_profile = profile and profile.get('age') is not None
    return render_template('dashboard.html', 
                         username=session.get('username', ''),
                         full_name=session.get('full_name', ''),
                         has_profile=has_profile,
                         profile=profile)


@dashboard_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Investment profile page"""
    if request.method == 'GET':
        profile_data = get_user_profile(session['user_id'])
        return render_template('profile.html', profile=profile_data)
    
    # POST — update profile
    data = request.get_json() if request.is_json else request.form.to_dict()
    result = update_user_profile(session['user_id'], data)
    
    if request.is_json:
        return jsonify(result)
    return redirect(url_for('dashboard.home'))


@dashboard_bp.route('/market')
@login_required
def market():
    """Market data page"""
    return render_template('market.html')


@dashboard_bp.route('/predictions')
@login_required
def predictions():
    """ML Predictions page"""
    return render_template('predictions.html')


@dashboard_bp.route('/portfolio')
@login_required
def portfolio():
    """Portfolio optimizer page"""
    profile = get_user_profile(session['user_id'])
    return render_template('portfolio.html', profile=profile)


@dashboard_bp.route('/api/profile', methods=['GET'])
@login_required
def get_profile_api():
    """API: Get user profile"""
    profile = get_user_profile(session['user_id'])
    return jsonify(profile or {})


@dashboard_bp.route('/api/profile', methods=['POST'])
@login_required
def update_profile_api():
    """API: Update user profile"""
    data = request.get_json()
    result = update_user_profile(session['user_id'], data)
    return jsonify(result)

"""
Authentication Routes — Login, Register, Logout
"""
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from services.auth_service import register_user, login_user

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler"""
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('dashboard.home'))
        return render_template('login.html')
    
    # POST — API login
    data = request.get_json() if request.is_json else request.form
    username = data.get('username', '')
    password = data.get('password', '')
    
    result = login_user(username, password)
    
    if result['success']:
        session['user_id'] = result['user']['id']
        session['username'] = result['user']['username']
        session['full_name'] = result['user']['full_name']
        
        if request.is_json:
            return jsonify(result)
        return redirect(url_for('dashboard.home'))
    
    if request.is_json:
        return jsonify(result), 401
    return render_template('login.html', error=result['error'])


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page and handler"""
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('dashboard.home'))
        return render_template('register.html')
    
    data = request.get_json() if request.is_json else request.form
    username = data.get('username', '')
    email = data.get('email', '')
    password = data.get('password', '')
    full_name = data.get('full_name', '')
    
    result = register_user(username, email, password, full_name)
    
    if result['success']:
        session['user_id'] = result['user_id']
        session['username'] = result['username']
        session['full_name'] = full_name
        
        if request.is_json:
            return jsonify(result)
        return redirect(url_for('dashboard.profile'))
    
    if request.is_json:
        return jsonify(result), 400
    return render_template('register.html', error=result['error'])


@auth_bp.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('auth.login'))


@auth_bp.route('/api/auth/status')
def auth_status():
    """Check authentication status"""
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'username': session['username'],
                'full_name': session.get('full_name', '')
            }
        })
    return jsonify({'authenticated': False})

"""
Unit tests for all Flask routes/blueprints — auth, dashboard, market, and prediction.
"""
import pytest
import json
import pandas as pd
from unittest.mock import patch, MagicMock
from database import User, Profile, Prediction, Recommendation, Watchlist, db


class TestAuthRoutes:
    """Tests for auth_routes.py."""

    def test_login_page_get_not_authenticated(self, client):
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()

    def test_login_page_get_already_authenticated(self, auth_client):
        client, _ = auth_client
        response = client.get('/login')
        assert response.status_code == 302  # Redirects to home/dashboard

    @patch('routes.auth_routes.login_user')
    def test_login_api_success(self, mock_login, client):
        mock_login.return_value = {
            'success': True,
            'user': {'id': 1, 'username': 'testuser', 'full_name': 'Test User', 'email': 'test@test.com'}
        }
        
        response = client.post('/login', 
                               data=json.dumps({'username': 'testuser', 'password': 'password123'}),
                               content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['user']['username'] == 'testuser'

    @patch('routes.auth_routes.login_user')
    def test_login_api_failure(self, mock_login, client):
        mock_login.return_value = {'success': False, 'error': 'Invalid username or password'}
        
        response = client.post('/login', 
                               data=json.dumps({'username': 'testuser', 'password': 'wrong'}),
                               content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False

    @patch('routes.auth_routes.register_user')
    def test_register_api_success(self, mock_register, client):
        mock_register.return_value = {
            'success': True,
            'user_id': 2,
            'username': 'newuser'
        }
        
        response = client.post('/register',
                               data=json.dumps({
                                   'username': 'newuser',
                                   'email': 'new@mail.com',
                                   'password': 'password123',
                                   'full_name': 'New User'
                               }),
                               content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    @patch('routes.auth_routes.register_user')
    def test_register_api_failure(self, mock_register, client):
        mock_register.return_value = {'success': False, 'error': 'Username already exists'}
        
        response = client.post('/register',
                               data=json.dumps({
                                   'username': 'dup',
                                   'email': 'dup@mail.com',
                                   'password': 'pass'
                               }),
                               content_type='application/json')
        
        assert response.status_code == 400

    def test_logout(self, auth_client):
        client, _ = auth_client
        response = client.get('/logout')
        assert response.status_code == 302
        
        # Verify session is cleared
        with client.session_transaction() as sess:
            assert 'user_id' not in sess

    def test_auth_status_authenticated(self, auth_client):
        client, user = auth_client
        response = client.get('/api/auth/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['authenticated'] is True
        assert data['user']['username'] == user.username

    def test_auth_status_not_authenticated(self, client):
        response = client.get('/api/auth/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['authenticated'] is False


class TestDashboardRoutes:
    """Tests for dashboard_routes.py."""

    def test_dashboard_home_requires_login(self, client):
        response = client.get('/')
        assert response.status_code == 302  # Redirects to login

    def test_dashboard_home_success(self, auth_client):
        client, _ = auth_client
        response = client.get('/')
        assert response.status_code == 200
        assert b'dashboard' in response.data.lower()

    def test_profile_page_get(self, auth_client):
        client, _ = auth_client
        response = client.get('/profile')
        assert response.status_code == 200

    @patch('routes.dashboard_routes.update_user_profile')
    def test_profile_page_post_api(self, mock_update, auth_client):
        client, _ = auth_client
        mock_update.return_value = {'success': True}
        
        response = client.post('/profile',
                               data=json.dumps({'age': 30, 'risk_tolerance': 'moderate'}),
                               content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_get_profile_api(self, auth_client):
        client, _ = auth_client
        response = client.get('/api/profile')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['age'] == 30
        assert data['risk_tolerance'] == 'moderate'


class TestMarketRoutes:
    """Tests for market_routes.py."""

    @patch('routes.market_routes.get_market_indices')
    def test_market_indices_api(self, mock_indices, client):
        mock_indices.return_value = {
            'NIFTY50': {'symbol': '^NSEI', 'price': 22000.0, 'display_name': 'NIFTY50'}
        }
        response = client.get('/api/market/indices')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'NIFTY50' in data['data']

    @patch('routes.market_routes.get_stock_info')
    @patch('routes.market_routes.get_live_price')
    @patch('routes.market_routes.get_historical_json')
    @patch('routes.market_routes.get_technical_indicators')
    def test_stock_detail_api(self, mock_indicators, mock_hist, mock_price, mock_info, client):
        mock_info.return_value = {'symbol': 'TCS.NS', 'name': 'TCS'}
        mock_price.return_value = {'price': 3800.0}
        mock_hist.return_value = {'dates': [], 'prices': []}
        mock_indicators.return_value = {'rsi': 55.0}

        response = client.get('/api/market/stock/TCS')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['info']['name'] == 'TCS'
        assert data['price']['price'] == 3800.0

    @patch('routes.market_routes.search_stocks')
    def test_search_api(self, mock_search, client):
        mock_search.return_value = [{'symbol': 'INFY.NS', 'name': 'Infosys'}]
        
        response = client.get('/api/market/search?q=INFY')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['results']) == 1
        assert data['results'][0]['symbol'] == 'INFY.NS'

    @patch('routes.market_routes.get_top_movers')
    def test_movers_api(self, mock_movers, client):
        mock_movers.return_value = {'gainers': [], 'losers': []}
        
        response = client.get('/api/market/movers')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestPredictionRoutes:
    """Tests for prediction_routes.py."""

    @patch('routes.prediction_routes.get_historical_data')
    @patch('routes.prediction_routes.get_stock_info')
    @patch('routes.prediction_routes.StockPredictor')
    @patch('routes.prediction_routes.ReturnEstimator')
    @patch('routes.prediction_routes.RiskScorer')
    def test_predict_api(self, mock_risk_scorer, mock_return_est_class, mock_predictor_class, mock_info, mock_hist, client):
        # We need historical data len >= 60 to pass route check
        dates = pd.date_range(end=pd.Timestamp.now(), periods=100)
        mock_hist.return_value = pd.DataFrame({'Close': range(100)}, index=dates)
        
        mock_info.return_value = {'symbol': 'RELIANCE.NS', 'name': 'Reliance'}
        
        # Setup mock predictor instance
        mock_pred_instance = MagicMock()
        mock_pred_instance.is_trained = True
        mock_pred_instance.train.return_value = {'accuracy': 85.0}
        mock_pred_instance.predict.return_value = {'predicted_price': 2550.0, 'confidence': 80.0, 'direction': 'UP'}
        mock_predictor_class.return_value = mock_pred_instance
        
        # Setup mock return estimator instance
        mock_est_instance = MagicMock()
        mock_est_instance.is_trained = True
        mock_est_instance.train.return_value = {}
        mock_est_instance.estimate.return_value = {'expected_annual_return': 15.0}
        mock_return_est_class.return_value = mock_est_instance
        
        # Setup mock risk scorer
        mock_risk_scorer.calculate_risk.return_value = {'risk_score': 3.5}

        response = client.post('/api/predict',
                               data=json.dumps({'symbol': 'RELIANCE'}),
                               content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['prediction']['predicted_price'] == 2550.0

    @patch('routes.prediction_routes.get_personalized_recommendations')
    def test_recommend_api(self, mock_recommend, auth_client):
        client, _ = auth_client
        mock_recommend.return_value = {'total_amount': 100000.0, 'categories': {}}
        
        response = client.post('/api/recommend',
                               data=json.dumps({'amount': 100000}),
                               content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['total_amount'] == 100000.0

    def test_prediction_history_api(self, auth_client, db_session):
        client, user = auth_client
        
        # Save a mock prediction
        pred = Prediction(
            user_id=user.id,
            symbol='TCS.NS',
            prediction_type='price',
            predicted_value=3900.0,
            confidence=85.0,
            direction='UP',
            model_used='random_forest'
        )
        db_session.add(pred)
        db_session.commit()
        
        response = client.get('/api/predictions/history')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['symbol'] == 'TCS.NS'

    def test_rec_history_api(self, auth_client, db_session):
        client, user = auth_client
        
        # Save a mock recommendation
        rec = Recommendation(
            user_id=user.id,
            category='stocks',
            symbol='INFY.NS',
            name='Infosys',
            allocation_pct=20.0,
            amount=20000.0
        )
        db_session.add(rec)
        db_session.commit()
        
        response = client.get('/api/recommendations/history')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['symbol'] == 'INFY.NS'

    @patch('routes.prediction_routes.get_historical_data')
    @patch('models.portfolio_optimizer.PortfolioOptimizer.optimize')
    @patch('models.portfolio_optimizer.PortfolioOptimizer.efficient_frontier')
    def test_optimize_api(self, mock_frontier, mock_optimize, mock_hist, auth_client):
        client, _ = auth_client
        
        # Stock historical data
        dates = pd.date_range(end=pd.Timestamp.now(), periods=50)
        mock_hist.return_value = pd.DataFrame({'Close': range(50)}, index=dates)
        
        mock_optimize.return_value = {'allocation': {'TCS.NS': {'weight': 50.0}, 'INFY.NS': {'weight': 50.0}}}
        mock_frontier.return_value = [{'return': 15.0, 'volatility': 10.0, 'sharpe': 1.5}]

        response = client.post('/api/optimize',
                               data=json.dumps({
                                   'symbols': ['TCS.NS', 'INFY.NS'],
                                   'risk_tolerance': 'moderate',
                                   'amount': 100000
                               }),
                               content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'optimization' in data
        assert 'efficient_frontier' in data
        assert 'allocation' in data

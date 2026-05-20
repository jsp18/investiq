"""
Unit tests for services/recommendation.py — recommendation engine, allocation adjustments, sub-category recommendations, DB logging.
"""
import pytest
from unittest.mock import patch, MagicMock
from services.recommendation import (
    get_personalized_recommendations, adjust_allocation,
    build_recommendations, _build_stock_recs, _build_mf_recs,
    _build_metal_recs, _build_bond_recs, _build_fd_recs,
    save_recommendations, get_recommendation_history
)
from database import User, Profile, Recommendation


class TestRecommendationService:
    """Unit tests for the Recommendation Service."""

    def test_adjust_allocation_short_horizon(self):
        # Base: moderate {'stocks': 35, 'mutual_funds': 30, 'gold': 10, 'bonds': 15, 'fd': 10}
        base = {'stocks': 35, 'mutual_funds': 30, 'gold': 10, 'bonds': 15, 'fd': 10}
        adjusted = adjust_allocation(base, horizon='short', goals='wealth_growth', experience='beginner')
        
        # Short horizon should decrease stocks, increase fd and bonds
        assert adjusted['stocks'] < 35
        assert adjusted['fd'] > 10
        # Verify normalization to exactly 100%
        assert pytest.approx(sum(adjusted.values()), 0.1) == 100.0

    def test_adjust_allocation_long_horizon_wealth_growth(self):
        base = {'stocks': 35, 'mutual_funds': 30, 'gold': 10, 'bonds': 15, 'fd': 10}
        adjusted = adjust_allocation(base, horizon='long', goals='wealth_growth', experience='expert')
        
        # Long horizon and wealth growth goals should significantly boost stocks
        assert adjusted['stocks'] > 35
        assert pytest.approx(sum(adjusted.values()), 0.1) == 100.0

    def test_adjust_allocation_income_goals(self):
        base = {'stocks': 35, 'mutual_funds': 30, 'gold': 10, 'bonds': 15, 'fd': 10}
        adjusted = adjust_allocation(base, horizon='medium', goals='income', experience='intermediate')
        
        # Income goals should boost bonds and fd, lower stocks
        assert adjusted['bonds'] > 15
        assert adjusted['fd'] > 10
        assert adjusted['stocks'] < 35
        assert pytest.approx(sum(adjusted.values()), 0.1) == 100.0

    def test_build_stock_recs(self):
        mock_stock_recs = [
            {'symbol': 'RELIANCE.NS', 'name': 'Reliance', 'sector': 'Energy', 'risk': {'risk_level': 'Low'}, 'recommendation_score': 85},
            {'symbol': 'TCS.NS', 'name': 'TCS', 'sector': 'IT', 'risk': {'risk_level': 'Low'}, 'recommendation_score': 80},
            {'symbol': 'INFY.NS', 'name': 'Infosys', 'sector': 'IT', 'risk': {'risk_level': 'Medium'}, 'recommendation_score': 75},
            {'symbol': 'HDFCBANK.NS', 'name': 'HDFC Bank', 'sector': 'Financials', 'risk': {'risk_level': 'Low'}, 'recommendation_score': 70},
            {'symbol': 'SBIN.NS', 'name': 'SBI', 'sector': 'Financials', 'risk': {'risk_level': 'Medium'}, 'recommendation_score': 65}
        ]
        
        cat_amount = 50000.0
        recs = _build_stock_recs(mock_stock_recs, cat_amount)
        
        assert len(recs) == 5
        assert recs[0]['symbol'] == 'RELIANCE.NS'
        assert recs[0]['action'] == 'BUY'
        assert pytest.approx(sum(r['amount'] for r in recs), 0.1) == cat_amount
        assert pytest.approx(sum(r['weight'] for r in recs), 0.1) == 100.0

    def test_build_mf_recs_different_risk_levels(self):
        cat_amount = 30000.0
        
        # Conservative
        con_recs = _build_mf_recs(cat_amount, 'conservative', 'medium')
        assert len(con_recs) > 0
        for r in con_recs:
            assert r['risk_level'] in ['Very Low', 'Low', 'Low-Moderate', 'Moderate']
            assert r['amount'] > 0
        assert pytest.approx(sum(r['weight'] for r in con_recs), 0.1) == 100.0

        # Aggressive
        agg_recs = _build_mf_recs(cat_amount, 'aggressive', 'long')
        assert len(agg_recs) > 0
        for r in agg_recs:
            assert r['risk_level'] in ['Moderate', 'Moderate-High', 'High', 'Very High']

    def test_build_metal_recs(self):
        cat_amount = 15000.0
        
        recs = _build_metal_recs(cat_amount, 'moderate', 'medium')
        assert len(recs) > 0
        assert pytest.approx(sum(r['amount'] for r in recs), 0.1) == cat_amount
        for r in recs:
            assert 'name' in r
            assert 'purity' in r
            assert 'provider' in r

    def test_build_bond_recs(self):
        cat_amount = 20000.0
        
        recs = _build_bond_recs(cat_amount, 'conservative', 'medium')
        assert len(recs) > 0
        assert pytest.approx(sum(r['amount'] for r in recs), 0.1) == cat_amount
        for r in recs:
            assert 'name' in r
            assert 'yield' in r
            assert 'risk_level' in r

    def test_build_fd_recs(self):
        cat_amount = 10000.0
        
        recs = _build_fd_recs(cat_amount, 'conservative', 'short')
        assert len(recs) > 0
        assert pytest.approx(sum(r['amount'] for r in recs), 0.1) == cat_amount
        for r in recs:
            assert 'name' in r
            assert 'rate' in r
            assert 'maturity_amount' in r
            assert r['maturity_amount'] > r['amount']

    def test_save_and_get_recommendation_history(self, app, db_session):
        # Create a user first
        user = User(username='testrecuser', email='rec@mail.com', password_hash='hash')
        db_session.add(user)
        db_session.flush()
        
        mock_recommendations = {
            'categories': {
                'stocks': {
                    'allocation_pct': 30.0,
                    'recommendations': [
                        {'symbol': 'TCS.NS', 'name': 'TCS', 'weight': 100.0, 'amount': 30000.0, 'action': 'BUY'}
                    ]
                },
                'fd': {
                    'allocation_pct': 70.0,
                    'recommendations': [
                        {'name': 'SBI FD', 'weight': 100.0, 'amount': 70000.0, 'action': 'SIP'}
                    ]
                }
            }
        }
        
        save_recommendations(user.id, mock_recommendations)
        
        history = get_recommendation_history(user.id)
        assert len(history) == 2
        categories = [h['category'] for h in history]
        assert 'stocks' in categories
        assert 'fd' in categories

    @patch('services.recommendation.analyze_stocks')
    def test_get_personalized_recommendations_success(self, mock_analyze_stocks, app, db_session):
        user = User(username='getrecuser', email='grec@mail.com', password_hash='hash')
        db_session.add(user)
        db_session.flush()
        
        profile = Profile(
            user_id=user.id,
            age=30,
            monthly_income=50000,
            investment_amount=100000,
            risk_tolerance='moderate',
            investment_horizon='medium',
            experience_level='beginner',
            goals='wealth_growth'
        )
        db_session.add(profile)
        db_session.commit()

        # Mock stock analysis return values
        mock_analyze_stocks.return_value = [
            {'symbol': 'RELIANCE.NS', 'name': 'Reliance', 'sector': 'Energy', 'risk': {'risk_level': 'Low'}, 'recommendation_score': 80}
        ]

        result = get_personalized_recommendations(user.id)
        
        assert 'total_amount' in result
        assert result['total_amount'] == 100000.0
        assert result['risk_profile'] == 'moderate'
        assert 'categories' in result
        assert 'stocks' in result['categories']
        assert 'mutual_funds' in result['categories']
        
        # Check that recommendations were logged to database
        recs = Recommendation.query.filter_by(user_id=user.id).all()
        assert len(recs) > 0

    def test_get_personalized_recommendations_no_profile(self, app, db_session):
        user = User(username='noprofuser', email='np@mail.com', password_hash='hash')
        db_session.add(user)
        db_session.commit()

        result = get_personalized_recommendations(user.id)
        assert 'error' in result
        assert 'complete your investment profile' in result['error']

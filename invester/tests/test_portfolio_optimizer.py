"""
Unit tests for models/portfolio_optimizer.py — Modern Portfolio Theory optimization and allocation.
"""
import pytest
import numpy as np
import pandas as pd
from models.portfolio_optimizer import PortfolioOptimizer


class TestPortfolioOptimizer:
    """Tests for the PortfolioOptimizer class."""

    @pytest.fixture
    def mock_price_data(self):
        """Mock price data for 3 assets (100 days)."""
        np.random.seed(42)
        n = 100
        dates = pd.bdate_range(start='2024-01-01', periods=n)
        
        # Asset A: steady up-trend
        price_a = 100 * (1 + 0.001 + np.random.randn(n) * 0.01).cumprod()
        # Asset B: volatile but higher returns
        price_b = 100 * (1 + 0.002 + np.random.randn(n) * 0.02).cumprod()
        # Asset C: low volatility, low return
        price_c = 100 * (1 + 0.0002 + np.random.randn(n) * 0.005).cumprod()
        
        return {
            'RELIANCE.NS': pd.Series(price_a, index=dates),
            'TCS.NS': pd.Series(price_b, index=dates),
            'HDFCBANK.NS': pd.Series(price_c, index=dates)
        }

    def test_prepare_success(self, mock_price_data):
        optimizer = PortfolioOptimizer()
        success = optimizer.prepare(mock_price_data)
        
        assert success is True
        assert optimizer.num_assets == 3
        assert set(optimizer.symbols) == {'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS'}
        assert optimizer.returns.shape[1] == 3
        assert optimizer.cov_matrix.shape == (3, 3)

    def test_prepare_insufficient_data(self):
        optimizer = PortfolioOptimizer()
        # Small length (less than 30)
        short_data = {
            'A': pd.Series(np.random.rand(10)),
            'B': pd.Series(np.random.rand(10))
        }
        success = optimizer.prepare(short_data)
        assert success is False

    def test_portfolio_performance(self, mock_price_data):
        optimizer = PortfolioOptimizer()
        optimizer.prepare(mock_price_data)
        
        weights = np.array([0.4, 0.4, 0.2])
        ret, vol = optimizer.portfolio_performance(weights)
        
        assert isinstance(ret, float)
        assert isinstance(vol, float)
        assert vol > 0

    def test_negative_sharpe(self, mock_price_data):
        optimizer = PortfolioOptimizer()
        optimizer.prepare(mock_price_data)
        
        weights = np.array([0.33, 0.33, 0.34])
        neg_sharpe = optimizer.negative_sharpe(weights)
        
        assert isinstance(neg_sharpe, float)

    def test_optimize_different_risk_tolerances(self, mock_price_data):
        optimizer = PortfolioOptimizer()
        optimizer.prepare(mock_price_data)
        
        for risk in ['conservative', 'moderate', 'aggressive', 'very_aggressive']:
            result = optimizer.optimize(risk)
            
            assert 'allocation' in result
            assert 'portfolio_return' in result
            assert 'portfolio_volatility' in result
            assert 'sharpe_ratio' in result
            assert result['num_assets'] == 3
            assert result['risk_tolerance'] == risk
            
            # Check weights sum up to ~100%
            total_weight = sum(asset['weight'] for asset in result['allocation'].values())
            assert pytest.approx(total_weight, 1.0) == 100.0

    def test_optimize_unprepared_error(self):
        optimizer = PortfolioOptimizer()
        result = optimizer.optimize('moderate')
        assert 'error' in result

    def test_efficient_frontier(self, mock_price_data):
        optimizer = PortfolioOptimizer()
        optimizer.prepare(mock_price_data)
        
        frontier = optimizer.efficient_frontier(num_points=10)
        
        assert isinstance(frontier, list)
        assert len(frontier) <= 10
        if len(frontier) > 0:
            assert 'return' in frontier[0]
            assert 'volatility' in frontier[0]
            assert 'sharpe' in frontier[0]

    def test_allocate_amount(self, mock_price_data):
        optimizer = PortfolioOptimizer()
        optimizer.prepare(mock_price_data)
        
        opt_results = optimizer.optimize('moderate')
        amount = 150000.0
        
        allocated = PortfolioOptimizer.allocate_amount(amount, opt_results['allocation'], 'moderate')
        
        assert allocated['total_amount'] == amount
        assert allocated['risk_profile'] == 'moderate'
        assert 'categories' in allocated
        
        # Verify specific categories exist
        for category in ['stocks', 'mutual_funds', 'gold', 'bonds', 'fd']:
            assert category in allocated['categories']
            cat_data = allocated['categories'][category]
            assert 'name' in cat_data
            assert 'allocation_pct' in cat_data
            assert 'amount' in cat_data
            assert 'sub_allocations' in cat_data
            
        # Check sum of category amounts matches total_amount
        total_allocated = sum(c['amount'] for c in allocated['categories'].values())
        assert pytest.approx(total_allocated, 1.0) == amount

        # Verify stock-level allocation details
        stock_allocations = allocated['categories']['stocks']['sub_allocations']
        assert len(stock_allocations) == 3
        for sub in stock_allocations:
            assert 'symbol' in sub
            assert 'weight' in sub
            assert 'amount' in sub
            assert 'expected_return' in sub
            
        # Verify fixed deposit sub-allocations
        fd_allocations = allocated['categories']['fd']['sub_allocations']
        assert len(fd_allocations) > 0
        for sub in fd_allocations:
            assert 'bank' in sub
            assert 'rate' in sub
            assert 'amount' in sub

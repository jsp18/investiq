"""
Unit tests for services/market_data.py — mock-based testing of yfinance data fetching and caching.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from services.market_data import (
    get_stock_info, get_live_price, get_historical_data,
    get_historical_json, get_market_indices, get_top_movers,
    search_stocks, get_technical_indicators, _cache, _cache_timestamps
)


@pytest.fixture(autouse=True)
def clear_market_data_cache():
    """Clear the in-memory cache in market_data before each test."""
    _cache.clear()
    _cache_timestamps.clear()


class TestMarketDataService:
    """Mock-based tests for Market Data Service."""

    @patch('yfinance.Ticker')
    def test_get_stock_info_success(self, mock_ticker):
        # Set up mock info dict
        mock_instance = MagicMock()
        mock_instance.info = {
            'longName': 'Reliance Industries Limited',
            'sector': 'Energy',
            'industry': 'Oil & Gas',
            'marketCap': 15000000000000,
            'trailingPE': 25.5,
            'priceToBook': 2.3,
            'dividendYield': 0.005,
            'fiftyTwoWeekHigh': 2800.0,
            'fiftyTwoWeekLow': 2100.0,
            'averageVolume': 5000000,
            'currency': 'INR',
            'exchange': 'NSE'
        }
        mock_ticker.return_value = mock_instance

        info = get_stock_info('RELIANCE.NS')

        assert info['symbol'] == 'RELIANCE.NS'
        assert info['name'] == 'Reliance Industries Limited'
        assert info['sector'] == 'Energy'
        assert info['pe_ratio'] == 25.5
        assert info['dividend_yield'] == 0.5  # round(0.005 * 100, 2)
        assert info['exchange'] == 'NSE'

        # Test caching: second call shouldn't call yfinance again
        mock_ticker.reset_mock()
        info_cached = get_stock_info('RELIANCE.NS')
        assert info_cached == info
        mock_ticker.assert_not_called()

    @patch('yfinance.Ticker')
    def test_get_stock_info_failure(self, mock_ticker):
        mock_ticker.side_effect = Exception("Ticker not found")
        
        info = get_stock_info('INVALID')
        assert info['symbol'] == 'INVALID'
        assert info['name'] == 'INVALID'
        assert 'error' in info

    @patch('yfinance.Ticker')
    def test_get_live_price_success(self, mock_ticker):
        # Setup mock history DataFrame
        dates = pd.date_range(end=pd.Timestamp.now(), periods=5)
        mock_hist = pd.DataFrame({
            'Open': [2400.0, 2410.0, 2420.0, 2430.0, 2440.0],
            'High': [2420.0, 2430.0, 2440.0, 2450.0, 2460.0],
            'Low': [2390.0, 2400.0, 2410.0, 2420.0, 2430.0],
            'Close': [2410.0, 2420.0, 2425.0, 2435.0, 2450.0],
            'Volume': [100000, 120000, 110000, 130000, 150000]
        }, index=dates)

        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_instance

        price_data = get_live_price('RELIANCE.NS')

        assert price_data['symbol'] == 'RELIANCE.NS'
        assert price_data['price'] == 2450.0
        assert price_data['open'] == 2440.0
        assert price_data['high'] == 2460.0
        assert price_data['low'] == 2430.0
        assert price_data['volume'] == 150000
        assert price_data['change'] == 15.0  # 2450.0 - 2435.0
        assert price_data['change_pct'] == round((15.0 / 2435.0) * 100, 2)
        assert price_data['prev_close'] == 2435.0

        # Caching check
        mock_ticker.reset_mock()
        price_cached = get_live_price('RELIANCE.NS')
        assert price_cached == price_data
        mock_ticker.assert_not_called()

    @patch('yfinance.Ticker')
    def test_get_live_price_empty_history(self, mock_ticker):
        mock_instance = MagicMock()
        mock_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_instance

        price_data = get_live_price('EMPTY')
        assert price_data is None

    @patch('yfinance.Ticker')
    def test_get_historical_data_success(self, mock_ticker):
        dates = pd.date_range(start='2024-01-01', periods=10)
        mock_df = pd.DataFrame({
            'Open': np.random.rand(10),
            'High': np.random.rand(10),
            'Low': np.random.rand(10),
            'Close': np.random.rand(10),
            'Volume': np.random.rand(10)
        }, index=dates)

        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_df
        mock_ticker.return_value = mock_instance

        df = get_historical_data('RELIANCE.NS', period='1y')
        assert not df.empty
        assert len(df) == 10
        assert list(df.columns) == ['Open', 'High', 'Low', 'Close', 'Volume']

    @patch('services.market_data.get_historical_data')
    def test_get_historical_json(self, mock_get_hist):
        dates = pd.to_datetime(['2024-01-01', '2024-01-02'])
        mock_df = pd.DataFrame({
            'Open': [100.0, 105.0],
            'High': [106.0, 110.0],
            'Low': [99.0, 104.0],
            'Close': [102.5, 108.0],
            'Volume': [1000, 2000]
        }, index=dates)
        mock_get_hist.return_value = mock_df

        result = get_historical_json('RELIANCE.NS')
        assert result['dates'] == ['2024-01-01', '2024-01-02']
        assert result['prices'] == [102.5, 108.0]
        assert result['opens'] == [100.0, 105.0]
        assert result['highs'] == [106.0, 110.0]
        assert result['lows'] == [99.0, 104.0]
        assert result['volumes'] == [1000, 2000]

    @patch('services.market_data.get_live_price')
    def test_get_market_indices(self, mock_get_price):
        mock_get_price.side_effect = lambda sym: {
            'symbol': sym,
            'price': 22000.0 if sym == '^NSEI' else 72000.0 if sym == '^BSESN' else 2000.0
        }

        indices = get_market_indices()
        assert 'NIFTY50' in indices
        assert 'SENSEX' in indices
        assert indices['NIFTY50']['display_name'] == 'NIFTY50'
        assert indices['NIFTY50']['price'] == 22000.0

    @patch('services.market_data.get_live_price')
    @patch('services.market_data.get_stock_info')
    def test_get_top_movers(self, mock_info, mock_price):
        # We only check NIFTY50_SYMBOLS[:20] for speed, let's mock it
        mock_info.return_value = {'name': 'Mock Company'}
        
        # Make some gainers and some losers
        mock_price.side_effect = lambda sym: {
            'symbol': sym,
            'price': 100.0,
            'change_pct': 3.5 if 'RELIANCE' in sym or 'TCS' in sym else -2.5
        }

        movers = get_top_movers()
        assert 'gainers' in movers
        assert 'losers' in movers
        assert len(movers['gainers']) > 0
        assert len(movers['losers']) > 0
        assert movers['gainers'][0]['change_pct'] == 3.5
        assert movers['losers'][0]['change_pct'] == -2.5

    def test_search_stocks_nifty_found(self):
        # Search for 'RELIANCE'
        results = search_stocks('RELIANCE')
        assert len(results) >= 1
        assert results[0]['symbol'] == 'RELIANCE.NS'

    @patch('services.market_data.get_stock_info')
    def test_search_stocks_direct_ticker(self, mock_info):
        mock_info.return_value = {'name': 'State Bank of India', 'sector': 'Financial Services'}
        results = search_stocks('SBIN')
        assert len(results) >= 1
        assert results[0]['symbol'] == 'SBIN.NS'

    @patch('services.market_data.get_historical_data')
    def test_get_technical_indicators(self, mock_get_hist, sample_ohlcv_df):
        mock_get_hist.return_value = sample_ohlcv_df

        indicators = get_technical_indicators('RELIANCE.NS')

        assert 'sma_5' in indicators
        assert 'sma_20' in indicators
        assert 'rsi' in indicators
        assert 'macd' in indicators
        assert 'signals' in indicators
        assert len(indicators['signals']) > 0
        assert 'indicator' in indicators['signals'][0]
        assert 'action' in indicators['signals'][0]

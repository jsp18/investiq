"""
Unit tests for models/ml_models.py — FeatureEngineer, StockPredictor, ReturnEstimator, RiskScorer.
"""
import pytest
import numpy as np
import pandas as pd
from models.ml_models import FeatureEngineer, StockPredictor, ReturnEstimator, RiskScorer


class TestFeatureEngineer:
    """Tests for the FeatureEngineer class."""

    def test_calculate_features_adds_columns(self, sample_ohlcv_df):
        df_features = FeatureEngineer.calculate_features(sample_ohlcv_df)
        
        # Check that we have a subset of expected columns
        expected_cols = [
            'SMA_5', 'SMA_20', 'SMA_50', 'EMA_12', 'EMA_26', 'MACD', 'MACD_Signal',
            'RSI', 'BB_Upper', 'BB_Lower', 'BB_Width', 'Volume_Change', 'Volume_Ratio',
            'Daily_Return', 'Price_Change_5d', 'Price_Change_10d', 'Volatility_20',
            'Volatility_5', 'Momentum_10', 'Momentum_20', 'Price_vs_SMA20', 'Price_vs_SMA50'
        ]
        for col in expected_cols:
            assert col in df_features.columns, f"{col} not found in engineered features"

    def test_calculate_features_handles_missing_close(self):
        # Empty df or df without 'Close'
        df = pd.DataFrame({'Open': [1, 2], 'High': [2, 3], 'Low': [0, 1]})
        result = FeatureEngineer.calculate_features(df)
        assert 'SMA_5' not in result.columns
        assert result.equals(df)

    def test_calculate_features_drops_nans(self, sample_ohlcv_df):
        # Check that we don't have NaNs in the final output
        df_features = FeatureEngineer.calculate_features(sample_ohlcv_df)
        assert not df_features.isnull().values.any()
        # Since we use 50-day moving average, rolling window means we drop at least 49 rows
        assert len(df_features) <= len(sample_ohlcv_df) - 49


class TestStockPredictor:
    """Tests for the StockPredictor class."""

    def test_train_predictor_success(self, sample_ohlcv_df):
        predictor = StockPredictor()
        metrics = predictor.train(sample_ohlcv_df)
        
        assert 'direction_accuracy' in metrics
        assert 'magnitude_r2' in metrics
        assert 'magnitude_rmse' in metrics
        assert predictor.is_trained is True

    def test_train_predictor_insufficient_data(self, small_ohlcv_df):
        predictor = StockPredictor()
        metrics = predictor.train(small_ohlcv_df)
        
        assert 'error' in metrics
        assert predictor.is_trained is False

    def test_predict_success(self, sample_ohlcv_df):
        predictor = StockPredictor()
        predictor.train(sample_ohlcv_df)
        
        prediction = predictor.predict(sample_ohlcv_df)
        assert prediction is not None
        assert 'current_price' in prediction
        assert 'predicted_price' in prediction
        assert 'direction' in prediction
        assert prediction['direction'] in ['UP', 'DOWN']
        assert 0 <= prediction['confidence'] <= 100

    def test_predict_untrained_returns_none(self, sample_ohlcv_df):
        predictor = StockPredictor()
        assert predictor.predict(sample_ohlcv_df) is None


class TestReturnEstimator:
    """Tests for the ReturnEstimator class."""

    def test_train_estimator_success(self, sample_ohlcv_df):
        estimator = ReturnEstimator()
        metrics = estimator.train(sample_ohlcv_df)
        
        assert 'r2_score' in metrics
        assert 'training_samples' in metrics
        assert estimator.is_trained is True

    def test_estimate_success(self, sample_ohlcv_df):
        estimator = ReturnEstimator()
        estimator.train(sample_ohlcv_df)
        
        est = estimator.estimate(sample_ohlcv_df)
        assert est is not None
        assert 'expected_annual_return' in est
        assert 'monthly_estimate' in est

    def test_estimate_untrained_returns_none(self, sample_ohlcv_df):
        estimator = ReturnEstimator()
        assert estimator.estimate(sample_ohlcv_df) is None


class TestRiskScorer:
    """Tests for the RiskScorer class."""

    def test_calculate_risk_without_market(self, sample_ohlcv_df):
        risk = RiskScorer.calculate_risk(sample_ohlcv_df)
        
        assert 'risk_score' in risk
        assert 'risk_level' in risk
        assert 'annual_volatility' in risk
        assert 'max_drawdown' in risk
        assert 1.0 <= risk['risk_score'] <= 10.0
        assert risk['risk_level'] in ['Low', 'Moderate', 'High', 'Very High']

    def test_calculate_risk_with_market(self, sample_ohlcv_df, sample_market_df):
        risk = RiskScorer.calculate_risk(sample_ohlcv_df, sample_market_df)
        
        assert 'beta' in risk
        assert isinstance(risk['beta'], float)
        assert 1.0 <= risk['risk_score'] <= 10.0

    def test_calculate_risk_insufficient_data(self, small_ohlcv_df):
        risk = RiskScorer.calculate_risk(small_ohlcv_df)
        assert risk['risk_score'] == 5.0
        assert risk['risk_level'] == 'Medium'
        assert 'Insufficient data' in risk['details']

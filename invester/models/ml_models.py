"""
ML Models for Personal Investing Assistant
Includes:
  1. StockPredictor    — Random Forest for price trend prediction
  2. ReturnEstimator   — Linear Regression for expected return
  3. RiskScorer        — Volatility-based risk assessment
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

from config import Config


class FeatureEngineer:
    """Calculate technical indicators from OHLCV data"""
    
    @staticmethod
    def calculate_features(df):
        """
        Given a DataFrame with OHLCV columns, calculate technical indicators.
        Returns DataFrame with new feature columns.
        """
        data = df.copy()
        
        # Ensure we have the right columns
        if 'Close' not in data.columns:
            return data
        
        # Simple Moving Averages
        data['SMA_5'] = data['Close'].rolling(window=5).mean()
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        
        # Exponential Moving Averages
        data['EMA_12'] = data['Close'].ewm(span=12, adjust=False).mean()
        data['EMA_26'] = data['Close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        data['MACD'] = data['EMA_12'] - data['EMA_26']
        data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
        
        # RSI (Relative Strength Index)
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-10)
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        bb_sma = data['Close'].rolling(window=20).mean()
        bb_std = data['Close'].rolling(window=20).std()
        data['BB_Upper'] = bb_sma + (bb_std * 2)
        data['BB_Lower'] = bb_sma - (bb_std * 2)
        data['BB_Width'] = (data['BB_Upper'] - data['BB_Lower']) / bb_sma
        
        # Volume features
        if 'Volume' in data.columns:
            data['Volume_Change'] = data['Volume'].pct_change()
            data['Volume_SMA_20'] = data['Volume'].rolling(window=20).mean()
            data['Volume_Ratio'] = data['Volume'] / (data['Volume_SMA_20'] + 1)
        else:
            data['Volume_Change'] = 0
            data['Volume_Ratio'] = 1
        
        # Price features
        data['Daily_Return'] = data['Close'].pct_change()
        data['Price_Change_5d'] = data['Close'].pct_change(periods=5)
        data['Price_Change_10d'] = data['Close'].pct_change(periods=10)
        
        # Volatility
        data['Volatility_20'] = data['Daily_Return'].rolling(window=20).std()
        data['Volatility_5'] = data['Daily_Return'].rolling(window=5).std()
        
        # Momentum
        data['Momentum_10'] = data['Close'] / data['Close'].shift(10) - 1
        data['Momentum_20'] = data['Close'] / data['Close'].shift(20) - 1
        
        # Price position relative to moving averages
        data['Price_vs_SMA20'] = (data['Close'] - data['SMA_20']) / (data['SMA_20'] + 1e-10)
        data['Price_vs_SMA50'] = (data['Close'] - data['SMA_50']) / (data['SMA_50'] + 1e-10)
        
        # Handle Infinity and extremely large values
        data = data.replace([np.inf, -np.inf], np.nan)
        
        # Drop NaN rows created by rolling calculations or infinity replacement
        data = data.dropna()
        
        # Final safety check: ensure all values are within a reasonable float64 range
        # and remove any remaining rows with invalid values
        for col in data.select_dtypes(include=[np.number]).columns:
            # Clip extremely large values to prevent float64 overflow in scikit-learn
            data[col] = data[col].clip(lower=-1e10, upper=1e10)
            
        return data


class StockPredictor:
    """
    Random Forest based stock price trend predictor.
    Predicts next-day price direction and magnitude.
    """
    
    FEATURE_COLS = [
        'SMA_5', 'SMA_20', 'EMA_12', 'EMA_26', 'RSI', 'MACD', 'MACD_Signal',
        'BB_Upper', 'BB_Lower', 'BB_Width', 'Volume_Change', 'Volume_Ratio',
        'Daily_Return', 'Price_Change_5d', 'Price_Change_10d',
        'Volatility_20', 'Volatility_5', 'Momentum_10', 'Momentum_20',
        'Price_vs_SMA20', 'Price_vs_SMA50'
    ]
    
    def __init__(self):
        self.direction_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )
        self.magnitude_model = RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.training_metrics = {}
    
    def prepare_data(self, df):
        """Prepare features and target from engineered DataFrame"""
        data = df.copy()
        
        # Target: next-day return
        data['Next_Return'] = data['Close'].shift(-1) / data['Close'] - 1
        data['Direction'] = (data['Next_Return'] > 0).astype(int)
        
        data = data.dropna()
        
        available_features = [c for c in self.FEATURE_COLS if c in data.columns]
        
        X = data[available_features].values
        y_direction = data['Direction'].values
        y_magnitude = data['Next_Return'].values
        
        return X, y_direction, y_magnitude, available_features
    
    def train(self, df):
        """Train both direction and magnitude models"""
        engineered = FeatureEngineer.calculate_features(df)
        
        if len(engineered) < 60:
            return {'error': 'Not enough data points for training (need >= 60)'}
        
        X, y_dir, y_mag, features = self.prepare_data(engineered)
        
        if len(X) < 30:
            return {'error': 'Not enough clean data for training'}
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data (chronological — no shuffle for time series)
        split = int(len(X_scaled) * 0.8)
        X_train, X_test = X_scaled[:split], X_scaled[split:]
        y_dir_train, y_dir_test = y_dir[:split], y_dir[split:]
        y_mag_train, y_mag_test = y_mag[:split], y_mag[split:]
        
        # Train direction classifier
        self.direction_model.fit(X_train, y_dir_train)
        dir_accuracy = accuracy_score(y_dir_test, self.direction_model.predict(X_test))
        
        # Train magnitude regressor
        self.magnitude_model.fit(X_train, y_mag_train)
        mag_predictions = self.magnitude_model.predict(X_test)
        mag_r2 = r2_score(y_mag_test, mag_predictions)
        mag_rmse = np.sqrt(mean_squared_error(y_mag_test, mag_predictions))
        
        self.is_trained = True
        self.training_metrics = {
            'direction_accuracy': round(dir_accuracy * 100, 2),
            'magnitude_r2': round(mag_r2, 4),
            'magnitude_rmse': round(mag_rmse, 6),
            'training_samples': split,
            'test_samples': len(X_test),
            'features_used': features
        }
        
        return self.training_metrics
    
    def predict(self, df):
        """Predict next-day direction and magnitude for the latest data"""
        if not self.is_trained:
            return None
        
        engineered = FeatureEngineer.calculate_features(df)
        
        available_features = [c for c in self.FEATURE_COLS if c in engineered.columns]
        latest = engineered[available_features].iloc[-1:].values
        latest_scaled = self.scaler.transform(latest)
        
        direction_proba = self.direction_model.predict_proba(latest_scaled)[0]
        direction = self.direction_model.predict(latest_scaled)[0]
        magnitude = self.magnitude_model.predict(latest_scaled)[0]
        
        current_price = df['Close'].iloc[-1]
        predicted_price = current_price * (1 + magnitude)
        
        confidence = max(direction_proba) * 100
        
        return {
            'current_price': round(float(current_price), 2),
            'predicted_price': round(float(predicted_price), 2),
            'predicted_change_pct': round(float(magnitude * 100), 4),
            'direction': 'UP' if direction == 1 else 'DOWN',
            'confidence': round(float(confidence), 2),
            'up_probability': round(float(direction_proba[1] * 100), 2) if len(direction_proba) > 1 else 50.0,
            'down_probability': round(float(direction_proba[0] * 100), 2) if len(direction_proba) > 1 else 50.0
        }
    
    def save(self, symbol):
        """Save trained model to disk"""
        os.makedirs(Config.MODEL_DIR, exist_ok=True)
        safe_symbol = symbol.replace('.', '_').replace('^', '')
        joblib.dump(self.direction_model, os.path.join(Config.MODEL_DIR, f'{safe_symbol}_dir.pkl'))
        joblib.dump(self.magnitude_model, os.path.join(Config.MODEL_DIR, f'{safe_symbol}_mag.pkl'))
        joblib.dump(self.scaler, os.path.join(Config.MODEL_DIR, f'{safe_symbol}_scaler.pkl'))
    
    def load(self, symbol):
        """Load trained model from disk"""
        safe_symbol = symbol.replace('.', '_').replace('^', '')
        dir_path = os.path.join(Config.MODEL_DIR, f'{safe_symbol}_dir.pkl')
        mag_path = os.path.join(Config.MODEL_DIR, f'{safe_symbol}_mag.pkl')
        scaler_path = os.path.join(Config.MODEL_DIR, f'{safe_symbol}_scaler.pkl')
        
        if all(os.path.exists(p) for p in [dir_path, mag_path, scaler_path]):
            self.direction_model = joblib.load(dir_path)
            self.magnitude_model = joblib.load(mag_path)
            self.scaler = joblib.load(scaler_path)
            self.is_trained = True
            return True
        return False


class ReturnEstimator:
    """
    Linear Regression model to estimate expected annual returns
    based on historical performance and technical indicators.
    """
    
    def __init__(self):
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def train(self, df):
        """Train on historical return data"""
        data = FeatureEngineer.calculate_features(df)
        
        if len(data) < 60:
            return {'error': 'Not enough data'}
        
        # Use monthly returns as target (annualized)
        data['Monthly_Return'] = data['Close'].pct_change(periods=21) * 12  # Annualized
        data = data.dropna()
        
        feature_cols = ['RSI', 'MACD', 'Volatility_20', 'Momentum_20', 
                       'Price_vs_SMA20', 'Volume_Ratio', 'BB_Width']
        available = [c for c in feature_cols if c in data.columns]
        
        X = data[available].values
        y = data['Monthly_Return'].values
        
        X_scaled = self.scaler.fit_transform(X)
        
        split = int(len(X_scaled) * 0.8)
        X_train, X_test = X_scaled[:split], X_scaled[split:]
        y_train, y_test = y[:split], y[split:]
        
        self.model.fit(X_train, y_train)
        
        predictions = self.model.predict(X_test)
        r2 = r2_score(y_test, predictions)
        
        self.is_trained = True
        
        return {
            'r2_score': round(r2, 4),
            'training_samples': split,
            'test_samples': len(X_test)
        }
    
    def estimate(self, df):
        """Estimate expected annual return for current conditions"""
        if not self.is_trained:
            return None
        
        data = FeatureEngineer.calculate_features(df)
        
        feature_cols = ['RSI', 'MACD', 'Volatility_20', 'Momentum_20',
                       'Price_vs_SMA20', 'Volume_Ratio', 'BB_Width']
        available = [c for c in feature_cols if c in data.columns]
        
        latest = data[available].iloc[-1:].values
        latest_scaled = self.scaler.transform(latest)
        
        expected_return = self.model.predict(latest_scaled)[0]
        
        return {
            'expected_annual_return': round(float(expected_return * 100), 2),
            'monthly_estimate': round(float(expected_return * 100 / 12), 2)
        }


class RiskScorer:
    """
    Risk assessment model using volatility, beta, and drawdown metrics.
    Produces a composite risk score on a 1-10 scale.
    """
    
    @staticmethod
    def calculate_risk(df, market_df=None):
        """
        Calculate comprehensive risk metrics for a stock.
        
        Args:
            df: Stock OHLCV DataFrame
            market_df: Market index (NIFTY50) DataFrame for beta calculation
        
        Returns:
            dict with risk metrics and composite score
        """
        if len(df) < 30:
            return {'risk_score': 5.0, 'risk_level': 'Medium', 'details': 'Insufficient data'}
        
        returns = df['Close'].pct_change().dropna()
        
        # Annualized volatility
        annual_volatility = float(returns.std() * np.sqrt(252) * 100)
        
        # Maximum drawdown
        cumulative = (1 + returns).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        max_drawdown = float(abs(drawdown.min()) * 100)
        
        # Sharpe ratio (assuming risk-free rate of 7% for India)
        risk_free_daily = 0.07 / 252
        excess_returns = returns - risk_free_daily
        sharpe = float(np.sqrt(252) * excess_returns.mean() / (returns.std() + 1e-10))
        
        # Beta (if market data available)
        beta = 1.0
        if market_df is not None and len(market_df) > 30:
            market_returns = market_df['Close'].pct_change().dropna()
            min_len = min(len(returns), len(market_returns))
            if min_len > 20:
                stock_r = returns.iloc[-min_len:]
                market_r = market_returns.iloc[-min_len:]
                covariance = np.cov(stock_r, market_r)[0][1]
                market_variance = np.var(market_r)
                beta = float(covariance / (market_variance + 1e-10))
        
        # Value at Risk (VaR) — 95% confidence
        var_95 = float(np.percentile(returns, 5) * 100)
        
        # Composite risk score (1=low risk, 10=high risk)
        vol_score = min(10, annual_volatility / 5)  # Normalize
        dd_score = min(10, max_drawdown / 5)
        beta_score = min(10, abs(beta) * 3)
        var_score = min(10, abs(var_95) * 2)
        
        composite = (vol_score * 0.3 + dd_score * 0.25 + beta_score * 0.25 + var_score * 0.2)
        composite = max(1, min(10, round(composite, 1)))
        
        # Risk level label
        if composite <= 3:
            risk_level = 'Low'
        elif composite <= 5:
            risk_level = 'Moderate'
        elif composite <= 7:
            risk_level = 'High'
        else:
            risk_level = 'Very High'
        
        return {
            'risk_score': composite,
            'risk_level': risk_level,
            'annual_volatility': round(annual_volatility, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe, 3),
            'beta': round(beta, 3),
            'var_95': round(var_95, 3),
            'details': {
                'volatility_score': round(vol_score, 2),
                'drawdown_score': round(dd_score, 2),
                'beta_score': round(beta_score, 2),
                'var_score': round(var_score, 2)
            }
        }

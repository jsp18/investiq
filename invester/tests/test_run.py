import os
import sys
import sqlite3
import json
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from config import Config
from services.recommendation import get_personalized_recommendations
from database import init_db

# --- Mocking Data ---

def create_mock_df(symbol, trend='neutral'):
    """Create a mock pandas DataFrame for stock history"""
    dates = pd.date_range(end=pd.Timestamp.now(), periods=500, freq='D')
    np.random.seed(42)
    
    if trend == 'bull':
        prices = 100 + np.cumsum(np.random.normal(0.5, 2, 500))
    elif trend == 'bear':
        prices = 100 + np.cumsum(np.random.normal(-0.5, 2, 500))
    else:
        prices = 100 + np.cumsum(np.random.normal(0, 2, 500))
        
    prices = np.maximum(prices, 10) # Ensure no negative prices
    
    df = pd.DataFrame({
        'Open': prices * 0.99,
        'High': prices * 1.01,
        'Low': prices * 0.98,
        'Close': prices,
        'Volume': np.random.randint(100000, 1000000, 500)
    }, index=dates)
    return df

def mock_get_historical_data(symbol, period='1y', interval='1d'):
    # Determine trend based on symbol name for varied results
    if 'TATA' in symbol or 'ADANI' in symbol:
        return create_mock_df(symbol, 'bull')
    elif 'RELIANCE' in symbol or 'TCS' in symbol:
        return create_mock_df(symbol, 'neutral')
    else:
        return create_mock_df(symbol, 'bear')

def mock_get_stock_info(symbol):
    return {
        'symbol': symbol,
        'name': symbol.split('.')[0],
        'sector': 'Technology' if 'TCS' in symbol else 'Energy' if 'RELIANCE' in symbol else 'Various',
        'pe_ratio': 25,
        'dividend_yield': 1.5
    }

# Mocking the ML models to avoid slow training
class MockPredictor:
    is_trained = True
    def train(self, df): return {'accuracy': 85}
    def predict(self, df):
        return {
            'current_price': 150.0,
            'predicted_price': 165.0,
            'predicted_change_pct': 10.0,
            'direction': 'UP',
            'confidence': 75.0
        }

class MockEstimator:
    is_trained = True
    def train(self, df): return {'r2': 0.8}
    def estimate(self, df):
        return {'expected_annual_return': 12.0, 'monthly_estimate': 1.0}

# --- Test Execution ---

def run_test_scenarios():
    print("\n" + "="*80)
    print("  InvestIQ SYSTEM TEST RUN - Multiple User Conditions")
    print("="*80)
    
    # Use a unique temporary test database for this run
    import time
    test_db_path = os.path.join(project_root, f'test_investiq_{int(time.time())}.db')
    
    # Patch Config.DATABASE and services
    with patch('config.Config.DATABASE', test_db_path), \
         patch('services.market_data.get_historical_data', side_effect=mock_get_historical_data), \
         patch('services.market_data.get_stock_info', side_effect=mock_get_stock_info), \
         patch('services.recommendation.get_historical_data', side_effect=mock_get_historical_data), \
         patch('services.recommendation.get_stock_info', side_effect=mock_get_stock_info), \
         patch('services.recommendation.StockPredictor', side_effect=MockPredictor), \
         patch('services.recommendation.ReturnEstimator', side_effect=MockEstimator), \
         patch('services.recommendation.RiskScorer.calculate_risk', return_value={'risk_score': 3.0, 'risk_level': 'Low'}):
        
        # Initialize DB
        init_db()
        db = sqlite3.connect(test_db_path)
        
        # Personas to test
        personas = [
            {
                'name': 'P1: Aggressive Young Professional',
                'profile': {
                    'age': 24, 'monthly_income': 80000, 'investment_amount': 500000,
                    'risk_tolerance': 'aggressive', 'investment_horizon': 'long',
                    'experience_level': 'beginner', 'goals': 'wealth_growth'
                }
            },
            {
                'name': 'P2: Conservative Family Man',
                'profile': {
                    'age': 38, 'monthly_income': 150000, 'investment_amount': 300000,
                    'risk_tolerance': 'conservative', 'investment_horizon': 'medium',
                    'experience_level': 'intermediate', 'goals': 'retirement'
                }
            },
            {
                'name': 'P4: Retired Income Seeker',
                'profile': {
                    'age': 65, 'monthly_income': 40000, 'investment_amount': 1000000,
                    'risk_tolerance': 'conservative', 'investment_horizon': 'short',
                    'experience_level': 'expert', 'goals': 'income'
                }
            },
            {
                'name': 'P5: Tax Saver',
                'profile': {
                    'age': 28, 'monthly_income': 100000, 'investment_amount': 150000,
                    'risk_tolerance': 'moderate', 'investment_horizon': 'long',
                    'experience_level': 'beginner', 'goals': 'tax_saving'
                }
            }
        ]
        
        results_summary = []
        
        for i, p in enumerate(personas):
            user_id = i + 1
            # Create user and profile in DB
            db.execute("INSERT INTO users (id, username, email, password_hash) VALUES (?, ?, ?, ?)",
                       (user_id, f"user{user_id}", f"user{user_id}@test.com", "hash"))
            
            profile_query = "INSERT INTO profiles (user_id, " + ", ".join(p['profile'].keys()) + ") VALUES (" + "?, " + ", ".join(["?"] * len(p['profile'])) + ")"
            db.execute(profile_query, [user_id] + list(p['profile'].values()))
            db.commit()
            
            print(f"\n[RUNNING] Testing Scenario: {p['name']}...")
            
            # Run recommendation engine
            recommendations = get_personalized_recommendations(user_id)
            
            # Collect summary info
            alloc = recommendations.get('categories', {})
            stock_pct = alloc.get('stocks', {}).get('allocation_pct', 0)
            mf_pct = alloc.get('mutual_funds', {}).get('allocation_pct', 0)
            safety_pct = alloc.get('fd', {}).get('allocation_pct', 0) + alloc.get('bonds', {}).get('allocation_pct', 0)
            
            results_summary.append({
                'Persona': p['name'],
                'Equity %': f"{stock_pct}%",
                'Mutual Funds %': f"{mf_pct}%",
                'Safety %': f"{safety_pct}%",
                'Key Stocks': [s['symbol'] for s in alloc.get('stocks', {}).get('recommendations', [])[:3]]
            })
            
            print(f"  - Allocation: Stocks {stock_pct}%, MFs {mf_pct}%, Safety {safety_pct}%")
            if 'stocks' in alloc:
                recs = alloc['stocks']['recommendations']
                if recs:
                    print(f"  - Top Stock Pick: {recs[0]['symbol']} ({recs[0]['action']})")
        
        db.close()
        
        # Print Final Summary Table
        print("\n" + "="*80)
        print(f"{'PERSONA':<35} | {'EQUITY':<8} | {'MF':<8} | {'SAFETY':<8} | {'TOP STOCKS'}")
        print("-"*80)
        for r in results_summary:
            stocks = ", ".join(r['Key Stocks'])
            print(f"{r['Persona']:<35} | {r['Equity %']:<8} | {r['Mutual Funds %']:<8} | {r['Safety %']:<8} | {stocks}")
        print("="*80 + "\n")
        
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)

if __name__ == "__main__":
    run_test_scenarios()

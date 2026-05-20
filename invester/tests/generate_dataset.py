import os
import sys
import sqlite3
import json
import random
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from config import Config
from services.recommendation import get_personalized_recommendations
from database import init_db

# --- Mocking Data (Same as before but simplified) ---

def mock_get_historical_data(symbol, period='1y', interval='1d'):
    dates = pd.date_range(end=pd.Timestamp.now(), periods=200, freq='D')
    prices = 100 + np.cumsum(np.random.normal(0.1, 1, 200))
    return pd.DataFrame({'Close': prices}, index=dates)

def mock_get_stock_info(symbol):
    return {'symbol': symbol, 'name': symbol.split('.')[0], 'sector': 'Various'}

class MockPredictor:
    is_trained = True
    def train(self, df): return {}
    def predict(self, df): return {'current_price': 100, 'direction': 'UP', 'confidence': 70}

class MockEstimator:
    is_trained = True
    def train(self, df): return {}
    def estimate(self, df): return {'expected_annual_return': 12.0}

# --- Dataset Generation ---

def generate_dataset(num_cases=55):
    print(f"\n[START] Generating {num_cases} test cases...")
    
    test_db_path = os.path.join(project_root, f'dataset_gen_{int(random.random()*1000)}.db')
    
    with patch('config.Config.DATABASE', test_db_path), \
         patch('services.recommendation.get_historical_data', side_effect=mock_get_historical_data), \
         patch('services.recommendation.get_stock_info', side_effect=mock_get_stock_info), \
         patch('services.recommendation.StockPredictor', side_effect=MockPredictor), \
         patch('services.recommendation.ReturnEstimator', side_effect=MockEstimator), \
         patch('services.recommendation.RiskScorer.calculate_risk', return_value={'risk_score': 4.0, 'risk_level': 'Moderate'}):
        
        init_db()
        db = sqlite3.connect(test_db_path)
        
        dataset = []
        
        # Ranges for randomization
        risk_options = ['conservative', 'moderate', 'aggressive', 'very_aggressive']
        horizon_options = ['short', 'medium', 'long']
        experience_options = ['beginner', 'intermediate', 'expert']
        goal_options = ['wealth_growth', 'retirement', 'income', 'tax_saving']
        
        for i in range(num_cases):
            user_id = i + 1
            
            # Generate random profile
            profile = {
                'age': random.randint(20, 70),
                'monthly_income': random.randint(30000, 500000),
                'investment_amount': random.choice([10000, 50000, 100000, 250000, 500000, 1000000, 2500000]),
                'risk_tolerance': random.choice(risk_options),
                'investment_horizon': random.choice(horizon_options),
                'experience_level': random.choice(experience_options),
                'goals': random.choice(goal_options)
            }
            
            # Insert into DB
            db.execute("INSERT INTO users (id, username, email, password_hash) VALUES (?, ?, ?, ?)",
                       (user_id, f"testuser{user_id}", f"test{user_id}@example.com", "hash"))
            
            profile_query = "INSERT INTO profiles (user_id, " + ", ".join(profile.keys()) + ") VALUES (" + "?, " + ", ".join(["?"] * len(profile)) + ")"
            db.execute(profile_query, [user_id] + list(profile.values()))
            db.commit()
            
            # Run Recommendation
            recommendations = get_personalized_recommendations(user_id)
            
            # Store in dataset
            case_data = {
                'case_id': user_id,
                'input_profile': profile,
                'output_allocation': {cat: data['allocation_pct'] for cat, data in recommendations['categories'].items()},
                'total_amount': recommendations['total_amount'],
                'risk_profile_assigned': recommendations['risk_profile']
            }
            dataset.append(case_data)
            
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{num_cases} cases...")
        
        db.close()
        
        # Save to JSON
        output_file = os.path.join(project_root, 'investment_test_dataset.json')
        with open(output_file, 'w') as f:
            json.dump(dataset, f, indent=2)
        
        # Also save a summary CSV for quick viewing
        summary_data = []
        for d in dataset:
            row = d['input_profile'].copy()
            row.update(d['output_allocation'])
            summary_data.append(row)
        
        df = pd.DataFrame(summary_data)
        csv_file = os.path.join(project_root, 'investment_test_summary.csv')
        df.to_csv(csv_file, index=False)
        
        print(f"\n[SUCCESS] Dataset generated!")
        print(f"  - JSON: {output_file}")
        print(f"  - CSV: {csv_file}")
        
        # Cleanup
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
            except:
                pass

if __name__ == "__main__":
    generate_dataset(55)

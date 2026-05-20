"""
InvestIQ — AI-Powered Personal Investing Assistant
Main Flask Application Entry Point

Features:
  - ML-powered stock prediction (Random Forest, Linear Regression)
  - Real-time NSE/BSE market data via yfinance
  - Portfolio optimization using Modern Portfolio Theory
  - Personalized investment recommendations
  - Risk assessment and scoring

Author: InvestIQ Team
Tech Stack: Python, Flask, scikit-learn, yfinance, SQLite
"""

from flask import Flask
from flask_cors import CORS
import os

from config import Config
from database import init_db
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.market_routes import market_bp
from routes.prediction_routes import prediction_bp


def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Configuration
    app.config.from_object(Config)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # CORS
    CORS(app)
    
    # Initialize database
    init_db(app)
    
    # Create model directory
    os.makedirs(Config.MODEL_DIR, exist_ok=True)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(market_bp)
    app.register_blueprint(prediction_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def server_error(e):
        return {'error': 'Internal server error'}, 500
    
    return app


# Create app instance
app = create_app()


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  InvestIQ - Personal Investing Assistant")
    print("  ML-Powered | Real-time NSE/BSE Data")
    print("="*60)
    print(f"\n  Running at: http://127.0.0.1:5000")
    print(f"  Database: {Config.SQLALCHEMY_DATABASE_URI}")
    print(f"  Models: {Config.MODEL_DIR}")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

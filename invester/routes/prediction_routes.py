"""
ML Prediction and Recommendation Routes
Converted to SQLAlchemy for MySQL support
"""
from flask import Blueprint, request, jsonify, session
from models.ml_models import StockPredictor, ReturnEstimator, RiskScorer
from models.portfolio_optimizer import PortfolioOptimizer
from services.market_data import get_historical_data, get_stock_info
from services.recommendation import get_personalized_recommendations, get_recommendation_history
from config import Config
from database import db, Prediction
import json

prediction_bp = Blueprint('prediction', __name__)


@prediction_bp.route('/api/predict', methods=['POST'])
def predict():
    """Run ML prediction for a stock symbol"""
    data = request.get_json()
    symbol = data.get('symbol', '')
    
    if not symbol:
        return jsonify({'success': False, 'error': 'Symbol is required'}), 400
    
    if '.' not in symbol:
        symbol = f"{symbol}.NS"
    
    try:
        df = get_historical_data(symbol, period=Config.TRAINING_PERIOD)
        if df.empty or len(df) < 60:
            return jsonify({'success': False, 'error': 'Insufficient data for prediction'}), 400
        
        market_df = get_historical_data(Config.INDICES['NIFTY50'], period='1y')
        
        predictor = StockPredictor()
        metrics = predictor.train(df)
        if not predictor.is_trained:
            return jsonify({'success': False, 'error': 'Model training failed'}), 500
        
        prediction = predictor.predict(df)
        estimator = ReturnEstimator()
        estimator.train(df)
        return_est = estimator.estimate(df) if estimator.is_trained else {}
        risk = RiskScorer.calculate_risk(df, market_df)
        info = get_stock_info(symbol)
        
        # Save prediction if user logged in
        if 'user_id' in session:
            try:
                new_pred = Prediction(
                    user_id=session['user_id'],
                    symbol=symbol,
                    prediction_type='price',
                    predicted_value=prediction.get('predicted_price', 0),
                    confidence=prediction.get('confidence', 0),
                    direction=prediction.get('direction', ''),
                    model_used='random_forest'
                )
                db.session.add(new_pred)
                db.session.commit()
            except Exception:
                db.session.rollback()
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'info': info,
            'prediction': prediction,
            'training_metrics': metrics,
            'risk': risk,
            'expected_return': return_est
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@prediction_bp.route('/api/recommend', methods=['POST'])
def recommend():
    """Get personalized investment recommendations"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Login required'}), 401
    
    data = request.get_json() or {}
    amount = data.get('amount', None)
    
    try:
        if amount: amount = float(amount)
        recommendations = get_personalized_recommendations(session['user_id'], amount)
        if 'error' in recommendations:
            return jsonify({'success': False, 'error': recommendations['error']}), 400
        return jsonify({'success': True, 'data': recommendations})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@prediction_bp.route('/api/predictions/history')
def prediction_history():
    """Get past predictions for the logged-in user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Login required'}), 401
    
    try:
        preds = Prediction.query.filter_by(user_id=session['user_id']).order_by(Prediction.created_at.desc()).limit(50).all()
        data = [{c.name: getattr(p, c.name) for c in p.__table__.columns} for p in preds]
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@prediction_bp.route('/api/recommendations/history')
def rec_history():
    """Get past recommendations history"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Login required'}), 401
    
    try:
        history = get_recommendation_history(session['user_id'])
        return jsonify({'success': True, 'data': history})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@prediction_bp.route('/api/optimize', methods=['POST'])
def optimize():
    """Optimize portfolio using MPT"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Login required'}), 401
    
    data = request.get_json()
    symbols = data.get('symbols', [])
    risk_tolerance = data.get('risk_tolerance', 'moderate')
    amount = float(data.get('amount', 100000))
    
    if not symbols or len(symbols) < 2:
        return jsonify({'success': False, 'error': 'At least 2 symbols required'}), 400
    
    try:
        # Fetch historical data for all symbols
        price_data = {}
        for symbol in symbols:
            df = get_historical_data(symbol, period='1y')
            if not df.empty:
                price_data[symbol] = df['Close']
        
        if len(price_data) < 2:
            return jsonify({'success': False, 'error': 'Insufficient historical data for selected stocks'}), 400
            
        optimizer = PortfolioOptimizer()
        if not optimizer.prepare(price_data):
            return jsonify({'success': False, 'error': 'Failed to prepare portfolio data'}), 500
            
        opt_results = optimizer.optimize(risk_tolerance)
        frontier = optimizer.efficient_frontier()
        
        # Add full allocation details
        full_allocation = PortfolioOptimizer.allocate_amount(amount, opt_results['allocation'], risk_tolerance)
        
        return jsonify({
            'success': True,
            'optimization': opt_results,
            'efficient_frontier': frontier,
            'allocation': full_allocation
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

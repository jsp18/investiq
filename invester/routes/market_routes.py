"""
Market Data API Routes
"""
from flask import Blueprint, request, jsonify, session
from services.market_data import (
    get_live_price, get_stock_info, get_historical_json,
    get_market_indices, get_top_movers, search_stocks,
    get_technical_indicators
)

market_bp = Blueprint('market', __name__)


@market_bp.route('/api/market/indices')
def indices():
    """Get major Indian market indices"""
    try:
        data = get_market_indices()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@market_bp.route('/api/market/stock/<symbol>')
def stock_detail(symbol):
    """Get detailed stock data"""
    try:
        # Add .NS suffix if not present
        if '.' not in symbol:
            symbol = f"{symbol}.NS"
        
        info = get_stock_info(symbol)
        price = get_live_price(symbol)
        
        period = request.args.get('period', '1y')
        history = get_historical_json(symbol, period)
        
        indicators = get_technical_indicators(symbol)
        
        return jsonify({
            'success': True,
            'info': info,
            'price': price,
            'history': history,
            'indicators': indicators
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@market_bp.route('/api/market/search')
def search():
    """Search stocks"""
    query = request.args.get('q', '')
    if len(query) < 1:
        return jsonify({'success': True, 'results': []})
    
    try:
        results = search_stocks(query)
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@market_bp.route('/api/market/movers')
def movers():
    """Get top gainers and losers"""
    try:
        data = get_top_movers()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@market_bp.route('/api/market/history/<symbol>')
def history(symbol):
    """Get historical price data"""
    if '.' not in symbol:
        symbol = f"{symbol}.NS"
    
    period = request.args.get('period', '1y')
    
    try:
        data = get_historical_json(symbol, period)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

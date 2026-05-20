"""
Market Data Service — Real-time and historical data via yfinance
Includes caching layer to avoid rate limits
"""
import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
import time
from datetime import datetime, timedelta
from config import Config


# In-memory cache
_cache = {}
_cache_timestamps = {}


def _get_cached(key, ttl=Config.CACHE_TTL):
    """Check if cached data exists and is fresh"""
    if key in _cache and key in _cache_timestamps:
        if time.time() - _cache_timestamps[key] < ttl:
            return _cache[key]
    return None


def _set_cache(key, data):
    """Store data in cache"""
    _cache[key] = data
    _cache_timestamps[key] = time.time()


def get_stock_info(symbol):
    """Get basic stock info (name, sector, market cap, etc.)"""
    cache_key = f'info_{symbol}'
    cached = _get_cached(cache_key, ttl=3600)  # 1 hour cache for info
    if cached:
        return cached
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        result = {
            'symbol': symbol,
            'name': info.get('longName', info.get('shortName', symbol)),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'pb_ratio': info.get('priceToBook', 0),
            'dividend_yield': round((info.get('dividendYield', 0) or 0) * 100, 2),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
            'avg_volume': info.get('averageVolume', 0),
            'currency': info.get('currency', 'INR'),
            'exchange': info.get('exchange', 'NSE')
        }
        
        _set_cache(cache_key, result)
        return result
    except Exception as e:
        return {'symbol': symbol, 'name': symbol, 'error': str(e)}


def get_live_price(symbol):
    """Get current / latest price for a symbol"""
    cache_key = f'price_{symbol}'
    cached = _get_cached(cache_key, ttl=60)  # 1 min cache
    if cached:
        return cached
    
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='5d')
        
        if hist.empty:
            return None
        
        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else latest
        
        change = float(latest['Close'] - prev['Close'])
        change_pct = float((change / prev['Close']) * 100) if prev['Close'] != 0 else 0
        
        result = {
            'symbol': symbol,
            'price': round(float(latest['Close']), 2),
            'open': round(float(latest['Open']), 2),
            'high': round(float(latest['High']), 2),
            'low': round(float(latest['Low']), 2),
            'volume': int(latest['Volume']),
            'change': round(change, 2),
            'change_pct': round(change_pct, 2),
            'prev_close': round(float(prev['Close']), 2),
            'timestamp': str(hist.index[-1])
        }
        
        _set_cache(cache_key, result)
        return result
    except Exception as e:
        return {'symbol': symbol, 'error': str(e)}


def get_historical_data(symbol, period='1y', interval='1d'):
    """
    Get historical OHLCV data.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE.NS')
        period: '1mo', '3mo', '6mo', '1y', '2y', '5y'
        interval: '1d', '1wk', '1mo'
    
    Returns:
        pandas DataFrame with OHLCV columns
    """
    cache_key = f'hist_{symbol}_{period}_{interval}'
    cached = _get_cached(cache_key, ttl=300)
    if cached is not None:
        return cached
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            return pd.DataFrame()
        
        # Clean up
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df = df.dropna()
        
        _set_cache(cache_key, df)
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return pd.DataFrame()


def get_historical_json(symbol, period='1y'):
    """Get historical data as JSON-serializable format for charts"""
    df = get_historical_data(symbol, period)
    
    if df.empty:
        return {'dates': [], 'prices': [], 'volumes': []}
    
    return {
        'dates': [str(d.date()) for d in df.index],
        'prices': [round(p, 2) for p in df['Close'].tolist()],
        'opens': [round(p, 2) for p in df['Open'].tolist()],
        'highs': [round(p, 2) for p in df['High'].tolist()],
        'lows': [round(p, 2) for p in df['Low'].tolist()],
        'volumes': df['Volume'].tolist()
    }


def get_market_indices():
    """Get current values for major Indian market indices"""
    cache_key = 'market_indices'
    cached = _get_cached(cache_key, ttl=120)
    if cached:
        return cached
    
    indices = {}
    for name, symbol in Config.INDICES.items():
        price_data = get_live_price(symbol)
        if price_data:
            indices[name] = price_data
            indices[name]['display_name'] = name
    
    # Gold price
    gold_data = get_live_price(Config.GOLD_SYMBOL)
    if gold_data:
        indices['GOLD'] = gold_data
        indices['GOLD']['display_name'] = 'Gold (USD/oz)'
    
    _set_cache(cache_key, indices)
    return indices


def get_top_movers(limit=10):
    """Get top gaining and losing stocks from NIFTY50 list"""
    cache_key = 'top_movers'
    cached = _get_cached(cache_key, ttl=300)
    if cached:
        return cached
    
    movers = []
    
    # Use a subset for speed
    symbols = Config.NIFTY50_SYMBOLS[:20]
    
    for symbol in symbols:
        try:
            price_data = get_live_price(symbol)
            if price_data and 'error' not in price_data:
                info = get_stock_info(symbol)
                price_data['name'] = info.get('name', symbol)
                movers.append(price_data)
        except Exception:
            continue
    
    # Sort by change percentage
    gainers = sorted([m for m in movers if m.get('change_pct', 0) > 0], 
                     key=lambda x: x['change_pct'], reverse=True)[:limit]
    losers = sorted([m for m in movers if m.get('change_pct', 0) < 0], 
                    key=lambda x: x['change_pct'])[:limit]
    
    result = {'gainers': gainers, 'losers': losers}
    _set_cache(cache_key, result)
    return result


def search_stocks(query):
    """Search for stocks matching a query"""
    query = query.upper().strip()
    results = []
    
    for symbol in Config.NIFTY50_SYMBOLS:
        clean_symbol = symbol.replace('.NS', '').replace('.BO', '')
        if query in clean_symbol or query in symbol:
            info = get_stock_info(symbol)
            results.append({
                'symbol': symbol,
                'name': info.get('name', symbol),
                'sector': info.get('sector', 'N/A')
            })
    
    # Also try as a direct ticker
    if not results:
        test_symbol = f"{query}.NS"
        info = get_stock_info(test_symbol)
        if 'error' not in info:
            results.append({
                'symbol': test_symbol,
                'name': info.get('name', test_symbol),
                'sector': info.get('sector', 'N/A')
            })
    
    return results


def get_technical_indicators(symbol, period='1y'):
    """Get technical indicators for a stock"""
    from models.ml_models import FeatureEngineer
    
    df = get_historical_data(symbol, period)
    if df.empty:
        return {}
    
    engineered = FeatureEngineer.calculate_features(df)
    
    if engineered.empty:
        return {}
    
    latest = engineered.iloc[-1]
    
    indicators = {
        'sma_5': round(float(latest.get('SMA_5', 0)), 2),
        'sma_20': round(float(latest.get('SMA_20', 0)), 2),
        'sma_50': round(float(latest.get('SMA_50', 0)), 2),
        'ema_12': round(float(latest.get('EMA_12', 0)), 2),
        'ema_26': round(float(latest.get('EMA_26', 0)), 2),
        'rsi': round(float(latest.get('RSI', 50)), 2),
        'macd': round(float(latest.get('MACD', 0)), 4),
        'macd_signal': round(float(latest.get('MACD_Signal', 0)), 4),
        'bb_upper': round(float(latest.get('BB_Upper', 0)), 2),
        'bb_lower': round(float(latest.get('BB_Lower', 0)), 2),
        'volatility': round(float(latest.get('Volatility_20', 0)) * 100, 2),
        'momentum': round(float(latest.get('Momentum_20', 0)) * 100, 2),
    }
    
    # Signal interpretation
    signals = []
    if indicators['rsi'] > 70:
        signals.append({'indicator': 'RSI', 'signal': 'Overbought', 'action': 'SELL', 'strength': 'Strong'})
    elif indicators['rsi'] < 30:
        signals.append({'indicator': 'RSI', 'signal': 'Oversold', 'action': 'BUY', 'strength': 'Strong'})
    else:
        signals.append({'indicator': 'RSI', 'signal': 'Neutral', 'action': 'HOLD', 'strength': 'Weak'})
    
    if indicators['macd'] > indicators['macd_signal']:
        signals.append({'indicator': 'MACD', 'signal': 'Bullish Crossover', 'action': 'BUY', 'strength': 'Moderate'})
    else:
        signals.append({'indicator': 'MACD', 'signal': 'Bearish Crossover', 'action': 'SELL', 'strength': 'Moderate'})
    
    current_price = float(df['Close'].iloc[-1])
    if current_price > indicators['sma_20']:
        signals.append({'indicator': 'SMA20', 'signal': 'Above MA', 'action': 'BUY', 'strength': 'Moderate'})
    else:
        signals.append({'indicator': 'SMA20', 'signal': 'Below MA', 'action': 'SELL', 'strength': 'Moderate'})
    
    indicators['signals'] = signals
    
    return indicators

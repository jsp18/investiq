"""
Recommendation Engine
Combines ML predictions, user profile, and risk metrics
to generate personalized investment suggestions.
Converted to SQLAlchemy for MySQL support
"""
import numpy as np
from models.ml_models import StockPredictor, ReturnEstimator, RiskScorer
from services.market_data import get_historical_data, get_stock_info
from config import Config
from database import db, Profile, Recommendation
from datetime import datetime


def get_personalized_recommendations(user_id, investment_amount=None):
    """
    Generate personalized investment recommendations based on user profile,
    ML predictions, and market conditions.
    """
    try:
        # Get user profile using SQLAlchemy
        profile = Profile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            return {'error': 'Please complete your investment profile first'}
        
        risk_tolerance = profile.risk_tolerance or 'moderate'
        amount = investment_amount or profile.investment_amount or 100000
        horizon = profile.investment_horizon or 'medium'
        experience = profile.experience_level or 'beginner'
        goals = profile.goals or 'wealth_growth'
        
        if amount <= 0:
            amount = 100000
        
        # Step 1: Get base asset allocation
        base_allocation = Config.RISK_PROFILES.get(risk_tolerance, Config.RISK_PROFILES['moderate'])
        
        # Step 2: Adjust allocation
        adjusted = adjust_allocation(base_allocation, horizon, goals, experience)
        
        # Step 3: Run ML analysis
        stock_recommendations = analyze_stocks(risk_tolerance)
        
        # Step 4: Build final recommendations
        # Convert profile to dict for build_recommendations if it expects one
        profile_dict = {c.name: getattr(profile, c.name) for c in profile.__table__.columns}
        recommendations = build_recommendations(
            adjusted, stock_recommendations, amount, risk_tolerance, profile_dict
        )
        
        # Step 5: Save recommendations to DB
        save_recommendations(user_id, recommendations)
        
        return recommendations
    except Exception as e:
        return {'error': str(e)}


def adjust_allocation(base, horizon, goals, experience):
    """Adjust asset allocation based on investment horizon and goals"""
    allocation = base.copy()
    
    # Horizon adjustments
    if horizon == 'short':
        allocation['stocks'] = max(5, allocation['stocks'] - 15)
        allocation['fd'] = allocation.get('fd', 0) + 10
        allocation['bonds'] = allocation.get('bonds', 0) + 5
    elif horizon == 'long':
        allocation['stocks'] = min(70, allocation['stocks'] + 10)
        allocation['mutual_funds'] = min(40, allocation.get('mutual_funds', 0) + 5)
        allocation['fd'] = max(0, allocation.get('fd', 0) - 10)
        allocation['bonds'] = max(0, allocation.get('bonds', 0) - 5)
    
    # Goal adjustments
    if goals == 'retirement':
        allocation['mutual_funds'] = min(40, allocation.get('mutual_funds', 0) + 5)
        allocation['stocks'] = max(10, allocation['stocks'] - 5)
    elif goals == 'wealth_growth':
        allocation['stocks'] = min(70, allocation['stocks'] + 5)
        allocation['gold'] = max(0, allocation.get('gold', 0) - 5)
    elif goals == 'income':
        allocation['bonds'] = min(35, allocation.get('bonds', 0) + 10)
        allocation['fd'] = min(25, allocation.get('fd', 0) + 5)
        allocation['stocks'] = max(10, allocation['stocks'] - 15)
    
    # Normalize to 100%
    total = sum(allocation.values())
    if total != 100 and total > 0:
        factor = 100 / total
        allocation = {k: round(v * factor, 1) for k, v in allocation.items()}
    
    return allocation


def analyze_stocks(risk_tolerance):
    """Run ML analysis on stocks"""
    if risk_tolerance in ['conservative', 'moderate']:
        # Stable, top-tier blue chip stocks
        symbols = [
            'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS', 
            'LT.NS', 'SBIN.NS', 'AXISBANK.NS', 'KOTAKBANK.NS', 'BHARTIARTL.NS',
            'HINDUNILVR.NS', 'ITC.NS', 'ASIANPAINT.NS', 'NESTLEIND.NS', 'TITAN.NS',
            'SUNPHARMA.NS', 'HCLTECH.NS', 'ULTRACEMCO.NS', 'BRITANNIA.NS', 'TATACONSUM.NS',
            'WIPRO.NS', 'CIPLA.NS', 'DIVISLAB.NS', 'APOLLOHOSP.NS', 'BAJAJFINSV.NS',
            'HEROMOTOCO.NS', 'M&M.NS', 'TRENT.NS', 'GRASIM.NS', 'BAJAJ-AUTO.NS'
        ]
    else:
        # High-growth and more volatile large-cap stocks
        symbols = [
            'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS',
            'LT.NS', 'SBIN.NS', 'AXISBANK.NS', 'KOTAKBANK.NS', 'BHARTIARTL.NS',
            'TATAMOTORS.NS', 'BAJFINANCE.NS', 'ADANIENT.NS', 'JSWSTEEL.NS', 'TATASTEEL.NS',
            'TECHM.NS', 'MARUTI.NS', 'ONGC.NS', 'NTPC.NS', 'POWERGRID.NS',
            'JIOFIN.NS', 'COALINDIA.NS', 'VEDL.NS', 'HINDALCO.NS', 'BPCL.NS',
            'IOC.NS', 'ADANIPORTS.NS', 'DLF.NS', 'HAL.NS', 'BEL.NS'
        ]
    
    results = []
    market_df = get_historical_data(Config.INDICES['NIFTY50'], period='1y')
    
    for symbol in symbols:
        try:
            df = get_historical_data(symbol, period=Config.TRAINING_PERIOD)
            if df.empty or len(df) < 60: continue
            
            risk = RiskScorer.calculate_risk(df, market_df)
            predictor = StockPredictor()
            predictor.train(df)
            prediction = predictor.predict(df) if predictor.is_trained else None
            
            estimator = ReturnEstimator()
            estimator.train(df)
            return_est = estimator.estimate(df) if estimator.is_trained else None
            
            info = get_stock_info(symbol)
            
            stock_result = {
                'symbol': symbol,
                'name': info.get('name', symbol),
                'sector': info.get('sector', 'N/A'),
                'current_price': prediction.get('current_price', 0) if prediction else 0,
                'prediction': prediction,
                'risk': risk,
                'expected_return': return_est,
                'pe_ratio': info.get('pe_ratio', 0),
                'dividend_yield': info.get('dividend_yield', 0)
            }
            
            score = 50
            if prediction:
                score += (20 if prediction.get('direction') == 'UP' else -15) * (prediction.get('confidence', 50)/100)
            
            stock_result['recommendation_score'] = max(0, min(100, round(score, 1)))
            results.append(stock_result)
        except Exception: continue
    
    results.sort(key=lambda x: x.get('recommendation_score', 0), reverse=True)
    return results


def build_recommendations(allocation, stock_recs, amount, risk_tolerance, profile):
    """Build final recommendation response with classified suggestions for all categories"""
    horizon = profile.get('investment_horizon', 'medium')
    
    result = {
        'total_amount': amount,
        'risk_profile': risk_tolerance,
        'investment_horizon': horizon,
        'timestamp': datetime.now().isoformat(),
        'categories': {},
        'disclaimer': 'This is for educational purposes only.'
    }
    
    for category, pct in allocation.items():
        cat_amount = round(amount * pct / 100, 2)
        cat_data = {
            'name': Config.INVESTMENT_TYPES.get(category, category),
            'allocation_pct': pct,
            'amount': cat_amount,
            'recommendations': []
        }
        
        if category == 'stocks' and stock_recs:
            cat_data['recommendations'] = _build_stock_recs(stock_recs, cat_amount)
        elif category == 'mutual_funds':
            cat_data['recommendations'] = _build_mf_recs(cat_amount, risk_tolerance, horizon)
        elif category == 'gold':
            cat_data['recommendations'] = _build_metal_recs(cat_amount, risk_tolerance, horizon)
        elif category == 'bonds':
            cat_data['recommendations'] = _build_bond_recs(cat_amount, risk_tolerance, horizon)
        elif category == 'fd':
            cat_data['recommendations'] = _build_fd_recs(cat_amount, risk_tolerance, horizon)
        
        result['categories'][category] = cat_data
        
    return result


def _build_stock_recs(stock_recs, cat_amount):
    """Generate stock sub-recommendations"""
    top_stocks = stock_recs[:5]
    weights = np.array([s.get('recommendation_score', 50) for s in top_stocks])
    weights = weights / weights.sum() if weights.sum() > 0 else np.array([1/len(top_stocks)]*len(top_stocks))
    
    recs = []
    for i, stock in enumerate(top_stocks):
        recs.append({
            'symbol': stock['symbol'],
            'name': stock['name'],
            'amount': round(cat_amount * weights[i], 2),
            'weight': round(weights[i] * 100, 1),
            'risk_level': stock.get('risk', {}).get('risk_level', 'Medium'),
            'score': stock.get('recommendation_score', 50),
            'action': 'BUY' if stock.get('recommendation_score', 0) >= 55 else 'HOLD',
            'sector': stock.get('sector', 'N/A')
        })
    return recs


def _build_mf_recs(cat_amount, risk_tolerance, horizon):
    """Generate mutual fund sub-recommendations based on risk profile"""
    catalog = Config.MUTUAL_FUNDS_CATALOG
    
    # Risk-based filtering: pick schemes suitable for user's profile
    risk_map = {
        'conservative': ['Very Low', 'Low', 'Low-Moderate', 'Moderate'],
        'moderate': ['Low-Moderate', 'Moderate', 'Moderate-High'],
        'aggressive': ['Moderate', 'Moderate-High', 'High'],
        'very_aggressive': ['Moderate-High', 'High', 'Very High']
    }
    allowed_risks = risk_map.get(risk_tolerance, risk_map['moderate'])
    
    # Filter and score funds
    suitable = []
    for name, info in catalog.items():
        if info.get('risk') in allowed_risks:
            score = info.get('returns_3y', 0) * 0.6 + info.get('returns_1y', 0) * 0.4
            # Boost index funds for conservatives, sectoral for aggressive
            if risk_tolerance in ['conservative', 'moderate'] and info.get('category') in ['Index Fund', 'Hybrid', 'Debt', 'ELSS']:
                score += 3
            if risk_tolerance in ['aggressive', 'very_aggressive'] and info.get('category') in ['Sectoral', 'Mid Cap', 'Small Cap', 'Flexi Cap']:
                score += 3
            # Horizon boost
            if horizon == 'short' and info.get('category') in ['Liquid', 'Debt']:
                score += 5
            if horizon == 'long' and info.get('category') in ['Index Fund', 'Mid Cap', 'Small Cap', 'ELSS', 'Flexi Cap']:
                score += 4
            suitable.append((name, info, score))
    
    suitable.sort(key=lambda x: x[2], reverse=True)
    selected = suitable[:5]  # Top 5 funds
    
    if not selected:
        return []
    
    # Distribute amount weighted by score
    total_score = sum(s[2] for s in selected)
    recs = []
    for name, info, score in selected:
        weight = score / total_score if total_score > 0 else 1 / len(selected)
        recs.append({
            'name': name,
            'amount': round(cat_amount * weight, 2),
            'weight': round(weight * 100, 1),
            'category': info.get('category', ''),
            'type': info.get('type', ''),
            'risk_level': info.get('risk', 'Moderate'),
            'returns_1y': info.get('returns_1y', 0),
            'returns_3y': info.get('returns_3y', 0),
            'expense_ratio': info.get('expense_ratio', 0),
            'min_sip': info.get('min_sip', 500),
            'amc': info.get('amc', ''),
            'note': info.get('note', ''),
            'action': 'SIP' if horizon in ['medium', 'long'] else 'LUMPSUM'
        })
    return recs


def _build_metal_recs(cat_amount, risk_tolerance, horizon):
    """Generate gold & precious metals sub-recommendations"""
    catalog = Config.METALS_CATALOG
    
    # Scoring based on risk profile
    selected = []
    for name, info in catalog.items():
        score = info.get('returns_3y', 0) * 0.5 + info.get('returns_1y', 0) * 0.5
        # Favor SGB and Gold MF for conservative, ETF for aggressive
        if risk_tolerance in ['conservative', 'moderate']:
            if 'Government' in info.get('type', '') or 'Mutual Fund' in info.get('type', ''):
                score += 5
            if 'Silver' in name:
                score -= 3
        if risk_tolerance in ['aggressive', 'very_aggressive']:
            if 'ETF' in info.get('type', '') or 'Silver' in name:
                score += 3
        # Horizon
        if horizon == 'long' and 'SGB' in name:
            score += 5
        if horizon == 'short' and 'Digital' in name:
            score += 4
        selected.append((name, info, score))
    
    selected.sort(key=lambda x: x[2], reverse=True)
    top = selected[:3]
    
    total_score = sum(s[2] for s in top)
    recs = []
    for name, info, score in top:
        weight = score / total_score if total_score > 0 else 1 / len(top)
        recs.append({
            'name': name,
            'amount': round(cat_amount * weight, 2),
            'weight': round(weight * 100, 1),
            'type': info.get('type', ''),
            'purity': info.get('purity', ''),
            'risk_level': info.get('risk', 'Moderate'),
            'returns_1y': info.get('returns_1y', 0),
            'returns_3y': info.get('returns_3y', 0),
            'provider': info.get('provider', ''),
            'storage': info.get('storage', ''),
            'min_investment': info.get('min_investment', 0),
            'note': info.get('note', '')
        })
    return recs


def _build_bond_recs(cat_amount, risk_tolerance, horizon):
    """Generate government & corporate bond sub-recommendations"""
    catalog = Config.BONDS_CATALOG
    
    selected = []
    for name, info in catalog.items():
        score = info.get('yield', 0) * 10  # Higher yield = higher score
        # Conservative: favor government bonds
        if risk_tolerance in ['conservative', 'moderate']:
            if info.get('type') == 'Government':
                score += 8
        # Aggressive: favor corporate bonds (higher yield)
        if risk_tolerance in ['aggressive', 'very_aggressive']:
            if info.get('type') == 'Corporate':
                score += 6
        # Horizon
        if horizon == 'short' and '5Y' in name:
            score += 4
        if horizon == 'long' and ('10Y' in name or 'Floating' in name):
            score += 4
        selected.append((name, info, score))
    
    selected.sort(key=lambda x: x[2], reverse=True)
    top = selected[:4]
    
    total_score = sum(s[2] for s in top)
    recs = []
    for name, info, score in top:
        weight = score / total_score if total_score > 0 else 1 / len(top)
        recs.append({
            'name': name,
            'amount': round(cat_amount * weight, 2),
            'weight': round(weight * 100, 1),
            'yield': info.get('yield', 0),
            'type': info.get('type', ''),
            'risk_level': info.get('risk', 'Low'),
            'tenure': info.get('tenure', ''),
            'taxable': info.get('taxable', ''),
            'min_investment': info.get('min_investment', 0),
            'note': info.get('note', '')
        })
    return recs


def _build_fd_recs(cat_amount, risk_tolerance, horizon):
    """Generate fixed deposit sub-recommendations"""
    fd_rates = Config.FD_RATES
    
    # Pick the best tenure based on horizon
    tenure_key = '1yr'
    if horizon == 'medium':
        tenure_key = '3yr'
    elif horizon == 'long':
        tenure_key = '5yr'
    
    # Score FDs by their rate for the chosen tenure
    selected = []
    for bank, info in fd_rates.items():
        rate = info.get(tenure_key, 0)
        score = rate * 10
        # Boost government-backed options for conservative
        if risk_tolerance == 'conservative' and ('SBI' in bank or 'Post Office' in bank):
            score += 3
        selected.append((bank, info, rate, score))
    
    selected.sort(key=lambda x: x[3], reverse=True)
    top = selected[:4]
    
    total_score = sum(s[3] for s in top)
    recs = []
    for bank, info, rate, score in top:
        weight = score / total_score if total_score > 0 else 1 / len(top)
        tenure_display = tenure_key.replace('yr', ' Year')
        maturity_amount = round(cat_amount * weight * (1 + rate/100), 2)
        recs.append({
            'name': f"{bank} Fixed Deposit",
            'amount': round(cat_amount * weight, 2),
            'weight': round(weight * 100, 1),
            'rate': rate,
            'tenure': tenure_display,
            'senior_extra': info.get('senior_extra', 0),
            'min_deposit': info.get('min_deposit', 1000),
            'maturity_amount': maturity_amount,
            'risk_level': 'Very Low',
            'insured': 'DICGC insured up to ₹5,00,000' if 'Post Office' not in bank else 'Government of India guaranteed',
            'note': info.get('note', '')
        })
    return recs


def save_recommendations(user_id, recommendations):
    """Save recommendations to database using SQLAlchemy"""
    try:
        for category, data in recommendations.get('categories', {}).items():
            for rec in data.get('recommendations', []):
                new_rec = Recommendation(
                    user_id=user_id,
                    category=category,
                    symbol=rec.get('symbol', ''),
                    name=rec.get('name', ''),
                    allocation_pct=rec.get('weight', data.get('allocation_pct', 0)),
                    amount=rec.get('amount', 0),
                    risk_score=rec.get('risk_score', 0),
                    expected_return=rec.get('expected_return', 0),
                    reasoning=rec.get('action', ''),
                    confidence=rec.get('confidence', 0)
                )
                db.session.add(new_rec)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error saving recommendations: {e}")


def get_recommendation_history(user_id, limit=20):
    """Get past recommendations for a user"""
    try:
        recs = Recommendation.query.filter_by(user_id=user_id).order_by(Recommendation.created_at.desc()).limit(limit).all()
        return [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in recs]
    except Exception:
        return []

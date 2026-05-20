"""
Configuration settings for Personal Investing Assistant
"""
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'investiq-secret-key-2026-prod')
    
    # SQLite (Local Dev)
    # DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'investiq.db')
    
    # MySQL Configuration (Change these values as per your setup)
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'investiq_db')
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cache settings
    CACHE_TTL = 300  # 5 minutes cache for market data
    
    # Indian Market Symbols
    NIFTY50_SYMBOLS = [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
        'HINDUNILVR.NS', 'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS',
        'LT.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'MARUTI.NS', 'TITAN.NS',
        'SUNPHARMA.NS', 'BAJFINANCE.NS', 'WIPRO.NS', 'HCLTECH.NS', 'ULTRACEMCO.NS',
        'TATAMOTORS.NS', 'NTPC.NS', 'POWERGRID.NS', 'TATASTEEL.NS', 'ADANIENT.NS',
        'TECHM.NS', 'NESTLEIND.NS', 'JSWSTEEL.NS', 'BAJAJFINSV.NS', 'ONGC.NS',
        'M&M.NS', 'ADANIPORTS.NS', 'COALINDIA.NS', 'GRASIM.NS', 'HINDALCO.NS',
        'INDUSINDBK.NS', 'APOLLOHOSP.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CIPLA.NS',
        'DIVISLAB.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'HEROMOTOCO.NS', 'HDFCLIFE.NS',
        'LTIM.NS', 'SBILIFE.NS', 'SHRIRAMFIN.NS', 'TATACONSUM.NS', 'BAJAJ-AUTO.NS'
    ]
    
    # Market indices
    INDICES = {
        'NIFTY50': '^NSEI',
        'SENSEX': '^BSESN',
        'NIFTYBANK': '^NSEBANK',
        'NIFTYIT': '^CNXIT'
    }
    
    # Gold & commodities
    GOLD_SYMBOL = 'GC=F'
    SILVER_SYMBOL = 'SI=F'
    
    # Investment categories
    INVESTMENT_TYPES = {
        'stocks': 'Equity Stocks (NSE/BSE)',
        'mutual_funds': 'Mutual Funds (Index & Sectoral)',
        'gold': 'Gold & Precious Metals',
        'bonds': 'Government & Corporate Bonds',
        'fd': 'Fixed Deposits'
    }
    
    # Risk profiles
    RISK_PROFILES = {
        'conservative': {'stocks': 20, 'mutual_funds': 25, 'gold': 15, 'bonds': 25, 'fd': 15},
        'moderate': {'stocks': 35, 'mutual_funds': 30, 'gold': 10, 'bonds': 15, 'fd': 10},
        'aggressive': {'stocks': 50, 'mutual_funds': 30, 'gold': 5, 'bonds': 10, 'fd': 5},
        'very_aggressive': {'stocks': 65, 'mutual_funds': 25, 'gold': 5, 'bonds': 3, 'fd': 2}
    }
    
    # FD Rates (major banks, approximate 2025-26)
    FD_RATES = {
        'SBI': {
            '1yr': 6.80, '2yr': 7.00, '3yr': 7.10, '5yr': 6.50,
            'senior_extra': 0.50, 'min_deposit': 1000,
            'note': 'Largest public sector bank — safest FD in India'
        },
        'HDFC Bank': {
            '1yr': 6.60, '2yr': 7.15, '3yr': 7.20, '5yr': 7.00,
            'senior_extra': 0.50, 'min_deposit': 5000,
            'note': 'Best private sector rates for 2-3 year tenure'
        },
        'ICICI Bank': {
            '1yr': 6.70, '2yr': 7.10, '3yr': 7.10, '5yr': 7.00,
            'senior_extra': 0.50, 'min_deposit': 5000,
            'note': 'Flexible premature withdrawal options'
        },
        'Axis Bank': {
            '1yr': 6.70, '2yr': 7.10, '3yr': 7.15, '5yr': 7.00,
            'senior_extra': 0.50, 'min_deposit': 5000,
            'note': 'Online FD with auto-renewal facility'
        },
        'Kotak Mahindra': {
            '1yr': 6.50, '2yr': 7.05, '3yr': 7.10, '5yr': 6.90,
            'senior_extra': 0.50, 'min_deposit': 5000,
            'note': 'Sweep-in FD facility available'
        },
        'Post Office TD': {
            '1yr': 6.90, '2yr': 7.00, '3yr': 7.10, '5yr': 7.50,
            'senior_extra': 0.00, 'min_deposit': 1000,
            'note': 'Government-backed, 5yr eligible for 80C tax deduction'
        }
    }
    
    # Bond & Fixed Income Products (approximate yields 2025-26)
    BOND_YIELDS = {
        'GOI_10Y': 7.10,
        'GOI_5Y': 7.05,
        'AAA_Corporate': 7.80,
        'AA_Corporate': 8.20,
        'SGBs': 2.50  # Sovereign Gold Bonds coupon rate
    }
    
    BONDS_CATALOG = {
        'GOI Securities (10Y)': {
            'yield': 7.10, 'type': 'Government', 'risk': 'Sovereign (Zero)',
            'tenure': '10 Years', 'taxable': 'Yes (Income Tax slab)',
            'min_investment': 10000,
            'note': 'Safest fixed-income — backed by Government of India'
        },
        'GOI Securities (5Y)': {
            'yield': 7.05, 'type': 'Government', 'risk': 'Sovereign (Zero)',
            'tenure': '5 Years', 'taxable': 'Yes (Income Tax slab)',
            'min_investment': 10000,
            'note': 'Medium-term government bond with guaranteed returns'
        },
        'Sovereign Gold Bond (SGB)': {
            'yield': 2.50, 'type': 'Government', 'risk': 'Sovereign (Zero)',
            'tenure': '8 Years (exit after 5Y)', 'taxable': 'No (if held to maturity)',
            'min_investment': 5000,
            'note': 'Gold price appreciation + 2.5% annual interest — tax-free on maturity'
        },
        'AAA Corporate Bond': {
            'yield': 7.80, 'type': 'Corporate', 'risk': 'Low',
            'tenure': '3-5 Years', 'taxable': 'Yes (Income Tax slab)',
            'min_investment': 10000,
            'note': 'Issued by top-rated corporates like HDFC, REC, PFC'
        },
        'AA Corporate Bond': {
            'yield': 8.20, 'type': 'Corporate', 'risk': 'Low-Medium',
            'tenure': '2-5 Years', 'taxable': 'Yes (Income Tax slab)',
            'min_investment': 10000,
            'note': 'Slightly higher risk for better yields — NBFC and infra companies'
        },
        'RBI Floating Rate Bond': {
            'yield': 8.05, 'type': 'Government', 'risk': 'Sovereign (Zero)',
            'tenure': '7 Years', 'taxable': 'Yes (Income Tax slab)',
            'min_investment': 1000,
            'note': 'Interest rate resets every 6 months — linked to NSC rate'
        }
    }
    
    # Mutual Fund Schemes Catalog (approximate 2025-26 data)
    MUTUAL_FUNDS_CATALOG = {
        # Large-Cap / Index Funds
        'Nifty 50 Index Fund': {
            'category': 'Index Fund', 'type': 'Large Cap',
            'risk': 'Moderate', 'returns_1y': 12.5, 'returns_3y': 14.2,
            'expense_ratio': 0.10, 'min_sip': 500, 'min_lumpsum': 1000,
            'amc': 'UTI / HDFC / ICICI',
            'note': 'Passive fund tracking NIFTY 50 — lowest expense ratio'
        },
        'Sensex Index Fund': {
            'category': 'Index Fund', 'type': 'Large Cap',
            'risk': 'Moderate', 'returns_1y': 11.8, 'returns_3y': 13.9,
            'expense_ratio': 0.10, 'min_sip': 500, 'min_lumpsum': 1000,
            'amc': 'HDFC / SBI / Nippon',
            'note': 'Tracks BSE SENSEX — suitable for long-term SIP investors'
        },
        'Nifty Next 50 Fund': {
            'category': 'Index Fund', 'type': 'Large-Mid Cap',
            'risk': 'Moderate-High', 'returns_1y': 18.3, 'returns_3y': 16.1,
            'expense_ratio': 0.12, 'min_sip': 500, 'min_lumpsum': 1000,
            'amc': 'ICICI / UTI / Motilal Oswal',
            'note': 'Next 50 large companies — higher growth potential than Nifty 50'
        },
        # Flexi-Cap & Multi-Cap
        'Flexi Cap Fund': {
            'category': 'Flexi Cap', 'type': 'Multi Cap',
            'risk': 'Moderate-High', 'returns_1y': 15.2, 'returns_3y': 17.5,
            'expense_ratio': 0.45, 'min_sip': 500, 'min_lumpsum': 5000,
            'amc': 'Parag Parikh / HDFC / Kotak',
            'note': 'Fund manager picks from large, mid, and small caps — diversified'
        },
        # Sectoral / Thematic
        'IT Sector Fund': {
            'category': 'Sectoral', 'type': 'Technology',
            'risk': 'High', 'returns_1y': 22.1, 'returns_3y': 18.4,
            'expense_ratio': 0.55, 'min_sip': 500, 'min_lumpsum': 5000,
            'amc': 'ICICI / SBI / Tata',
            'note': 'Concentrated bet on Indian IT services — TCS, Infy, Wipro'
        },
        'Banking & Financial Fund': {
            'category': 'Sectoral', 'type': 'BFSI',
            'risk': 'High', 'returns_1y': 14.0, 'returns_3y': 15.8,
            'expense_ratio': 0.50, 'min_sip': 500, 'min_lumpsum': 5000,
            'amc': 'Nippon / ICICI / SBI',
            'note': 'Banks, NBFCs, insurance — India\'s largest sector by market cap'
        },
        'Pharma & Healthcare Fund': {
            'category': 'Sectoral', 'type': 'Healthcare',
            'risk': 'High', 'returns_1y': 19.5, 'returns_3y': 16.9,
            'expense_ratio': 0.55, 'min_sip': 500, 'min_lumpsum': 5000,
            'amc': 'SBI / Nippon / ICICI',
            'note': 'Sun Pharma, Dr Reddy, Cipla — defensive sector with global demand'
        },
        # Small / Mid Cap
        'Mid Cap Fund': {
            'category': 'Mid Cap', 'type': 'Mid Cap',
            'risk': 'High', 'returns_1y': 20.3, 'returns_3y': 19.8,
            'expense_ratio': 0.50, 'min_sip': 500, 'min_lumpsum': 5000,
            'amc': 'Kotak / HDFC / Axis',
            'note': 'Companies ranked 101-250 by market cap — high growth, moderate risk'
        },
        'Small Cap Fund': {
            'category': 'Small Cap', 'type': 'Small Cap',
            'risk': 'Very High', 'returns_1y': 25.8, 'returns_3y': 22.6,
            'expense_ratio': 0.55, 'min_sip': 500, 'min_lumpsum': 5000,
            'amc': 'Nippon / SBI / Quant',
            'note': 'Highest growth potential — only for aggressive investors with 5Y+ horizon'
        },
        # Debt / Hybrid
        'Balanced Advantage Fund': {
            'category': 'Hybrid', 'type': 'Dynamic Asset Allocation',
            'risk': 'Low-Moderate', 'returns_1y': 10.5, 'returns_3y': 11.2,
            'expense_ratio': 0.40, 'min_sip': 500, 'min_lumpsum': 5000,
            'amc': 'ICICI / HDFC / Edelweiss',
            'note': 'Auto-balances between equity and debt — ideal for moderate investors'
        },
        'Debt Short Duration Fund': {
            'category': 'Debt', 'type': 'Short Duration',
            'risk': 'Low', 'returns_1y': 7.2, 'returns_3y': 7.0,
            'expense_ratio': 0.25, 'min_sip': 1000, 'min_lumpsum': 5000,
            'amc': 'HDFC / ICICI / Axis',
            'note': 'Stable returns with low volatility — park money for 1-3 years'
        },
        'Liquid Fund': {
            'category': 'Debt', 'type': 'Liquid',
            'risk': 'Very Low', 'returns_1y': 6.8, 'returns_3y': 5.9,
            'expense_ratio': 0.15, 'min_sip': 500, 'min_lumpsum': 500,
            'amc': 'SBI / HDFC / Kotak',
            'note': 'Park idle cash — better than savings account, instant redemption'
        },
        # Tax-saving
        'ELSS Tax Saver Fund': {
            'category': 'ELSS', 'type': 'Tax Saving (80C)',
            'risk': 'Moderate-High', 'returns_1y': 16.7, 'returns_3y': 15.3,
            'expense_ratio': 0.35, 'min_sip': 500, 'min_lumpsum': 500,
            'amc': 'Mirae / Quant / HDFC',
            'note': 'Shortest lock-in among 80C options (3 years) — equity exposure'
        }
    }
    
    # Gold & Precious Metals Catalog
    METALS_CATALOG = {
        'Digital Gold (24K)': {
            'type': 'Digital', 'purity': '99.9%', 'risk': 'Moderate',
            'returns_1y': 15.0, 'returns_3y': 12.5,
            'min_investment': 1, 'storage': 'Vault (insured)',
            'provider': 'SafeGold / MMTC-PAMP / Augmont',
            'note': 'Buy gold in grams — stored in insured vaults, deliverable'
        },
        'Gold ETF': {
            'type': 'ETF', 'purity': '99.5%', 'risk': 'Moderate',
            'returns_1y': 14.8, 'returns_3y': 12.2,
            'min_investment': 500, 'storage': 'Demat account',
            'provider': 'Nippon Gold ETF / HDFC Gold ETF / SBI Gold ETF',
            'note': 'Exchange-traded — no storage hassle, high liquidity'
        },
        'Sovereign Gold Bond (SGB)': {
            'type': 'Government Bond', 'purity': 'N/A (linked to 999 gold)', 'risk': 'Very Low',
            'returns_1y': 17.5, 'returns_3y': 14.8,
            'min_investment': 5000, 'storage': 'RBI / Demat',
            'provider': 'Reserve Bank of India',
            'note': 'Gold returns + 2.5% interest — tax-free if held 8 years'
        },
        'Silver ETF': {
            'type': 'ETF', 'purity': '99.9%', 'risk': 'High',
            'returns_1y': 20.5, 'returns_3y': 10.1,
            'min_investment': 500, 'storage': 'Demat account',
            'provider': 'ICICI Silver ETF / Nippon Silver ETF',
            'note': 'Industrial + precious metal — higher volatility than gold'
        },
        'Gold Mutual Fund (FoF)': {
            'type': 'Mutual Fund', 'purity': 'N/A', 'risk': 'Moderate',
            'returns_1y': 14.5, 'returns_3y': 12.0,
            'min_investment': 500, 'storage': 'N/A',
            'provider': 'SBI / HDFC / Kotak Gold Fund',
            'note': 'No demat needed — invest via SIP like regular mutual funds'
        }
    }
    
    # ML Model settings
    MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'trained')
    TRAINING_PERIOD = '2y'  # 2 years of historical data for training
    PREDICTION_FEATURES = ['SMA_5', 'SMA_20', 'EMA_12', 'EMA_26', 'RSI', 'MACD', 
                           'BB_Upper', 'BB_Lower', 'Volume_Change', 'Daily_Return',
                           'Volatility_20', 'Price_Change_5d']

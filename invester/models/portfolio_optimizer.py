"""
Portfolio Optimizer using Modern Portfolio Theory (MPT)
Finds optimal asset allocation by maximizing the Sharpe Ratio
using scipy.optimize on the efficient frontier.
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from config import Config


class PortfolioOptimizer:
    """
    Modern Portfolio Theory based portfolio optimizer.
    Maximizes risk-adjusted returns (Sharpe Ratio) subject to constraints.
    """
    
    RISK_FREE_RATE = 0.07  # India 10Y govt bond yield ~7%
    
    def __init__(self):
        self.returns = None
        self.cov_matrix = None
        self.symbols = []
        self.num_assets = 0
    
    def prepare(self, price_data_dict):
        """
        Prepare return data from a dictionary of {symbol: price_series}.
        
        Args:
            price_data_dict: dict mapping symbol to pandas Series of closing prices
        """
        prices_df = pd.DataFrame(price_data_dict)
        prices_df = prices_df.dropna()
        
        if len(prices_df) < 30:
            return False
        
        # Daily returns
        self.returns = prices_df.pct_change().dropna()
        self.cov_matrix = self.returns.cov() * 252  # Annualized
        self.symbols = list(price_data_dict.keys())
        self.num_assets = len(self.symbols)
        
        return True
    
    def portfolio_performance(self, weights):
        """Calculate portfolio return and volatility for given weights"""
        mean_returns = self.returns.mean() * 252  # Annualized
        
        port_return = np.dot(weights, mean_returns)
        port_volatility = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
        
        return port_return, port_volatility
    
    def negative_sharpe(self, weights):
        """Objective function: negative Sharpe ratio (minimize = maximize Sharpe)"""
        ret, vol = self.portfolio_performance(weights)
        sharpe = (ret - self.RISK_FREE_RATE) / (vol + 1e-10)
        return -sharpe
    
    def optimize(self, risk_tolerance='moderate'):
        """
        Find optimal portfolio weights.
        
        Args:
            risk_tolerance: 'conservative', 'moderate', 'aggressive', 'very_aggressive'
        
        Returns:
            dict with optimal weights, expected return, volatility, sharpe ratio
        """
        if self.returns is None or self.num_assets == 0:
            return {'error': 'No data prepared. Call prepare() first.'}
        
        # Constraints: weights sum to 1
        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
        
        # Bounds: each weight between 0% and 40% (diversification)
        max_weight = {
            'conservative': 0.25,
            'moderate': 0.35,
            'aggressive': 0.45,
            'very_aggressive': 0.60
        }.get(risk_tolerance, 0.35)
        
        bounds = tuple((0.02, max_weight) for _ in range(self.num_assets))
        
        # Initial guess: equal weight
        init_weights = np.array([1.0 / self.num_assets] * self.num_assets)
        
        # Optimize
        result = minimize(
            self.negative_sharpe,
            init_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000, 'ftol': 1e-10}
        )
        
        if not result.success:
            # Fallback to equal weight
            optimal_weights = init_weights
        else:
            optimal_weights = result.x
        
        # Calculate final portfolio metrics
        port_return, port_volatility = self.portfolio_performance(optimal_weights)
        sharpe = (port_return - self.RISK_FREE_RATE) / (port_volatility + 1e-10)
        
        # Build allocation result
        allocation = {}
        for i, symbol in enumerate(self.symbols):
            allocation[symbol] = {
                'weight': round(float(optimal_weights[i]) * 100, 2),
                'expected_return': round(float(self.returns[symbol].mean() * 252 * 100), 2)
            }
        
        return {
            'allocation': allocation,
            'portfolio_return': round(float(port_return * 100), 2),
            'portfolio_volatility': round(float(port_volatility * 100), 2),
            'sharpe_ratio': round(float(sharpe), 3),
            'risk_tolerance': risk_tolerance,
            'num_assets': self.num_assets,
            'optimization_success': result.success
        }
    
    def efficient_frontier(self, num_points=50):
        """
        Generate efficient frontier data points for visualization.
        
        Returns:
            list of dicts with return, volatility, sharpe for each point
        """
        if self.returns is None:
            return []
        
        # Generate random portfolios
        results = []
        mean_returns = self.returns.mean() * 252
        
        for _ in range(num_points * 20):
            weights = np.random.random(self.num_assets)
            weights /= np.sum(weights)
            
            ret = np.dot(weights, mean_returns) * 100
            vol = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights))) * 100
            sharpe = (ret / 100 - self.RISK_FREE_RATE) / (vol / 100 + 1e-10)
            
            results.append({
                'return': round(ret, 2),
                'volatility': round(vol, 2),
                'sharpe': round(sharpe, 3)
            })
        
        # Sort by volatility and take evenly spaced points
        results = sorted(results, key=lambda x: x['volatility'])
        step = max(1, len(results) // num_points)
        frontier = results[::step][:num_points]
        
        return frontier
    
    @staticmethod
    def allocate_amount(amount, allocation, risk_tolerance='moderate'):
        """
        Given a total investment amount and optimal allocation,
        distribute the amount across asset classes.
        
        Args:
            amount: Total investment amount in INR
            allocation: dict from optimize() output
            risk_tolerance: User's risk profile
        
        Returns:
            dict with amount allocated to each asset
        """
        base_allocation = Config.RISK_PROFILES.get(risk_tolerance, Config.RISK_PROFILES['moderate'])
        
        result = {
            'total_amount': amount,
            'risk_profile': risk_tolerance,
            'categories': {}
        }
        
        for category, pct in base_allocation.items():
            cat_amount = amount * pct / 100
            display_name = Config.INVESTMENT_TYPES.get(category, category)
            
            result['categories'][category] = {
                'name': display_name,
                'allocation_pct': pct,
                'amount': round(cat_amount, 2),
                'sub_allocations': []
            }
        
        # Add stock-level allocations if available
        if allocation:
            stock_total = result['categories'].get('stocks', {}).get('amount', 0)
            for symbol, data in allocation.items():
                weight = data.get('weight', 0)
                sub_amount = stock_total * weight / 100
                result['categories'].setdefault('stocks', {}).setdefault('sub_allocations', []).append({
                    'symbol': symbol,
                    'weight': weight,
                    'amount': round(sub_amount, 2),
                    'expected_return': data.get('expected_return', 0)
                })
        
        # Add FD details
        if 'fd' in result['categories']:
            fd_amount = result['categories']['fd']['amount']
            result['categories']['fd']['sub_allocations'] = [
                {'bank': bank, 'rate': rates['1yr'], 'amount': round(fd_amount / len(Config.FD_RATES), 2)}
                for bank, rates in list(Config.FD_RATES.items())[:3]
            ]
        
        # Add bond details
        if 'bonds' in result['categories']:
            bond_amount = result['categories']['bonds']['amount']
            result['categories']['bonds']['sub_allocations'] = [
                {'type': 'Government Securities (10Y)', 'yield': Config.BOND_YIELDS['GOI_10Y'], 
                 'amount': round(bond_amount * 0.5, 2)},
                {'type': 'AAA Corporate Bonds', 'yield': Config.BOND_YIELDS['AAA_Corporate'],
                 'amount': round(bond_amount * 0.3, 2)},
                {'type': 'Sovereign Gold Bonds', 'yield': Config.BOND_YIELDS['SGBs'],
                 'amount': round(bond_amount * 0.2, 2)}
            ]
        
        return result

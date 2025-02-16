from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from itertools import product
from concurrent.futures import ProcessPoolExecutor
from .backtester import Backtester

class GridOptimizer:
    def __init__(self, base_config: Dict, historical_data: pd.DataFrame):
        self.base_config = base_config
        self.data = historical_data
        
    def generate_parameter_grid(self) -> List[Dict]:
        """Generate grid of parameters to test"""
        param_ranges = {
            'grid_size': [8, 10, 12, 14],
            'grid_spacing': [0.003, 0.005, 0.007, 0.01],
            'position_size': [0.01, 0.02, 0.03],
            'rsi_oversold': [20, 25, 30],
            'rsi_overbought': [70, 75, 80],
            'min_profit_usd': [0.5, 1.0, 1.5]
        }
        
        # Generate all combinations
        keys = param_ranges.keys()
        values = param_ranges.values()
        configurations = []
        
        for combination in product(*values):
            config = self.base_config.copy()
            for key, value in zip(keys, combination):
                if key in ['rsi_oversold', 'rsi_overbought']:
                    config['indicators'][key] = value
                else:
                    config['trading'][key] = value
            configurations.append(config)
            
        return configurations
        
    def evaluate_configuration(self, config: Dict) -> Tuple[Dict, Dict]:
        """Evaluate a single configuration"""
        backtester = Backtester(config, self.data)
        results = backtester.run()
        
        # Calculate overall score based on multiple metrics
        score = (
            results['total_return'] * 0.4 +  # 40% weight on returns
            results['win_rate'] * 0.3 +      # 30% weight on win rate
            (1 - results['max_drawdown']) * 0.2 +  # 20% weight on drawdown
            (results['sharpe_ratio'] / 10) * 0.1   # 10% weight on Sharpe ratio
        )
        
        return config, {**results, 'score': score}
        
    def optimize(self, num_workers: int = 4) -> List[Tuple[Dict, Dict]]:
        """Run parallel optimization"""
        configurations = self.generate_parameter_grid()
        results = []
        
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            future_results = [executor.submit(self.evaluate_configuration, config) 
                            for config in configurations]
            
            for future in future_results:
                try:
                    config, metrics = future.result()
                    results.append((config, metrics))
                except Exception as e:
                    print(f"Error evaluating configuration: {e}")
                    
        # Sort by score
        results.sort(key=lambda x: x[1]['score'], reverse=True)
        return results
        
    def get_optimal_config(self) -> Dict:
        """Run optimization and return the best configuration"""
        results = self.optimize()
        if results:
            return results[0][0]  # Return the configuration with highest score
        return self.base_config
        
class GridWalkForward:
    """Walk-forward optimization to prevent overfitting"""
    def __init__(self, base_config: Dict, historical_data: pd.DataFrame):
        self.base_config = base_config
        self.data = historical_data
        
    def split_data(self, train_size: float = 0.7) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Split data into training and testing sets"""
        split_idx = int(len(self.data) * train_size)
        train_data = self.data.iloc[:split_idx]
        test_data = self.data.iloc[split_idx:]
        return train_data, test_data
        
    def optimize(self) -> Tuple[Dict, Dict]:
        """Perform walk-forward optimization"""
        # Split data
        train_data, test_data = self.split_data()
        
        # Optimize on training data
        optimizer = GridOptimizer(self.base_config, train_data)
        optimal_config = optimizer.get_optimal_config()
        
        # Validate on test data
        test_backtester = Backtester(optimal_config, test_data)
        test_results = test_backtester.run()
        
        return optimal_config, test_results
        
    def validate_robustness(self, optimal_config: Dict, windows: int = 5) -> Dict:
        """Validate configuration robustness across multiple time windows"""
        window_size = len(self.data) // windows
        results = []
        
        for i in range(windows):
            start_idx = i * window_size
            end_idx = start_idx + window_size
            window_data = self.data.iloc[start_idx:end_idx]
            
            backtester = Backtester(optimal_config, window_data)
            window_results = backtester.run()
            results.append(window_results)
            
        # Calculate stability metrics
        returns = [r['total_return'] for r in results]
        win_rates = [r['win_rate'] for r in results]
        
        return {
            'return_mean': np.mean(returns),
            'return_std': np.std(returns),
            'win_rate_mean': np.mean(win_rates),
            'win_rate_std': np.std(win_rates),
            'stability_score': 1 - (np.std(returns) / abs(np.mean(returns)))
                if np.mean(returns) != 0 else 0
        }
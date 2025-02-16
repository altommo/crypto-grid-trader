import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from .strategy import GridStrategy

class Trade:
    def __init__(self, timestamp: datetime, action: str, price: float, 
                 size: float, fees: float, indicators: Dict):
        self.timestamp = timestamp
        self.action = action
        self.price = price
        self.size = size
        self.fees = fees
        self.indicators = indicators
        self.pnl = 0.0
        self.cumulative_pnl = 0.0
        self.drawdown = 0.0

class Backtester:
    def __init__(self, config: Dict, historical_data: pd.DataFrame):
        self.config = config
        self.data = historical_data
        self.strategy = GridStrategy(config)
        
        self.initial_balance = config['backtest']['initial_capital']
        self.current_balance = self.initial_balance
        self.peak_balance = self.initial_balance
        self.positions = {}
        self.trades: List[Trade] = []
        
        # Fee configuration
        self.maker_fee = 0.001  # 0.1%
        self.taker_fee = 0.001
        if config['binance']['use_bnb_fees']:
            self.maker_fee *= 0.75  # 25% discount
            self.taker_fee *= 0.75
            
        print(f"Initialized backtester with balance: {self.initial_balance}")

    def calculate_fees(self, price: float, size: float, is_maker: bool = True) -> float:
        """Calculate trading fees based on configuration"""
        fee_rate = self.maker_fee if is_maker else self.taker_fee
        return price * size * fee_rate

    def execute_trade(self, signal: Dict, timestamp: datetime) -> Optional[Trade]:
        """Execute a trade signal in the backtesting environment"""
        price = signal['price']
        size = signal['size']
        action = signal['action']
        indicators = signal.get('indicators', {})

        print(f"Executing trade: {action} {size} @ {price}")
        
        if action == 'BUY':
            cost = price * size
            fees = self.calculate_fees(price, size)
            total_cost = cost + fees
            
            if total_cost <= self.current_balance:
                self.current_balance -= total_cost
                self.positions[price] = size
                
                trade = Trade(timestamp, action, price, size, fees, indicators)
                trade.pnl = -fees
                trade.cumulative_pnl = self.calculate_cumulative_pnl()
                
                self.trades.append(trade)
                print(f"Buy executed: Balance={self.current_balance}")
                return trade
            else:
                print(f"Insufficient balance for buy: {total_cost} > {self.current_balance}")
                
        elif action == 'SELL':
            if price in self.positions:
                size = min(size, self.positions[price])
                revenue = price * size
                fees = self.calculate_fees(price, size)
                total_revenue = revenue - fees
                
                self.current_balance += total_revenue
                self.positions[price] -= size
                if self.positions[price] <= 0:
                    del self.positions[price]
                
                trade = Trade(timestamp, action, price, size, fees, indicators)
                trade.pnl = total_revenue - (price * size)
                trade.cumulative_pnl = self.calculate_cumulative_pnl()
                
                self.trades.append(trade)
                
                # Update peak balance and drawdown
                self.peak_balance = max(self.peak_balance, self.current_balance)
                print(f"Sell executed: Balance={self.current_balance}, PnL={trade.pnl}")
                return trade
            else:
                print(f"No position to sell at price {price}")
                
        return None

    def calculate_cumulative_pnl(self) -> float:
        """Calculate cumulative PnL"""
        return self.current_balance - self.initial_balance
        
    def calculate_drawdown(self) -> Tuple[float, float]:
        """Calculate current and maximum drawdown"""
        if not self.trades:
            return 0.0, 0.0
            
        current_dd = (self.peak_balance - self.current_balance) / self.peak_balance
        max_dd = max((t.drawdown for t in self.trades), default=0.0)
        return current_dd, max_dd

    def run(self) -> Dict:
        """Run backtest on historical data"""
        # Initialize grid with first price
        first_price = self.data['close'].iloc[0]
        print(f"Initializing grid at price {first_price}")
        self.strategy.initialize_grid(first_price)
        
        # Create trading window for indicators
        window_size = max(
            self.config['indicators']['rsi_period'],
            self.config['indicators']['macd_slow'] + self.config['indicators']['macd_signal']
        )
        
        # Run simulation
        for i in range(window_size, len(self.data)):
            window = self.data.iloc[i-window_size:i+1]
            current_price = window['close'].iloc[-1]
            timestamp = window.index[-1]
            
            # Generate trading signals
            signals = self.strategy.update(current_price, window)
            print(f"Generated {len(signals)} signals at {timestamp}")
            
            # Execute signals
            for signal in signals:
                self.execute_trade(signal, timestamp)
                
        # Calculate performance metrics
        results = self.calculate_performance()
        print(f"Backtest completed: {len(self.trades)} trades executed")
        return results
        
    def calculate_performance(self) -> Dict:
        """Calculate comprehensive backtest performance metrics"""
        if not self.trades:
            return self.empty_performance_metrics()
            
        trades_df = pd.DataFrame([{
            'timestamp': t.timestamp,
            'action': t.action,
            'price': t.price,
            'size': t.size,
            'fees': t.fees,
            'pnl': t.pnl,
            'cumulative_pnl': t.cumulative_pnl
        } for t in self.trades])
        
        # Basic metrics
        total_trades = len(trades_df)
        profitable_trades = len(trades_df[trades_df['pnl'] > 0])
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        
        # PnL metrics
        total_pnl = self.calculate_cumulative_pnl()
        total_return = total_pnl / self.initial_balance
        
        # Risk metrics
        current_dd, max_dd = self.calculate_drawdown()
        
        # Trading metrics
        avg_trade_pnl = trades_df['pnl'].mean()
        std_trade_pnl = trades_df['pnl'].std()
        
        # Calculate Sharpe Ratio (assuming risk-free rate of 0)
        if std_trade_pnl > 0:
            sharpe_ratio = (avg_trade_pnl / std_trade_pnl) * np.sqrt(252)  # Annualized
        else:
            sharpe_ratio = 0
            
        metrics = {
            'total_return': total_return,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_trade_pnl': avg_trade_pnl,
            'max_drawdown': max_dd,
            'current_drawdown': current_dd,
            'sharpe_ratio': sharpe_ratio,
            'final_balance': self.current_balance,
            'total_fees': trades_df['fees'].sum(),
            'trades_per_day': total_trades / len(self.data.index.unique()),
            'profit_factor': abs(trades_df[trades_df['pnl'] > 0]['pnl'].sum() / 
                               trades_df[trades_df['pnl'] < 0]['pnl'].sum()) 
                               if len(trades_df[trades_df['pnl'] < 0]) > 0 else float('inf')
        }
        
        print(f"Performance metrics: {metrics}")
        return metrics
        
    def empty_performance_metrics(self) -> Dict:
        """Return empty performance metrics when no trades are made"""
        return {
            'total_return': 0.0,
            'total_trades': 0,
            'win_rate': 0.0,
            'avg_trade_pnl': 0.0,
            'max_drawdown': 0.0,
            'current_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'final_balance': self.initial_balance,
            'total_fees': 0.0,
            'trades_per_day': 0.0,
            'profit_factor': 0.0
        }
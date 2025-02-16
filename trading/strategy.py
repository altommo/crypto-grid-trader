import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands

@dataclass
class GridLevel:
    price: float
    position_size: float = 0.0
    entry_price: Optional[float] = None
    entry_time: Optional[datetime] = None
    last_update: Optional[datetime] = None

class GridStrategy:
    def __init__(self, config: Dict):
        self.config = config
        self.symbol = config['trading']['symbol']
        self.grid_size = config['trading']['grid_size']
        self.grid_spacing = config['trading']['grid_spacing']
        self.position_size = config['trading']['position_size']
        self.max_positions = config['trading']['max_positions']
        
        # Risk parameters
        self.stop_loss = config['risk']['stop_loss']
        self.take_profit = config['risk']['take_profit']
        
        # Indicator parameters
        self.rsi_period = config['indicators']['rsi_period']
        self.rsi_oversold = config['indicators']['rsi_oversold']
        self.rsi_overbought = config['indicators']['rsi_overbought']
        
        self.grid_levels: List[GridLevel] = []
        self.current_price = None
        self.last_trade_time = None
        self.total_positions = 0
        
        print(f"Strategy initialized: grid_size={self.grid_size}, spacing={self.grid_spacing*100}%")
        
    def initialize_grid(self, current_price: float) -> None:
        """Initialize grid levels around the current price"""
        self.current_price = current_price
        
        # Calculate total range
        total_range = self.grid_spacing * self.grid_size
        min_price = current_price * (1 - total_range/2)
        
        # Generate grid levels
        self.grid_levels = []
        for i in range(self.grid_size):
            price = min_price * (1 + self.grid_spacing * i)
            self.grid_levels.append(GridLevel(price=price))
            
        print(f"Grid initialized with {len(self.grid_levels)} levels from {self.grid_levels[0].price:.4f} to {self.grid_levels[-1].price:.4f}")
        
    def calculate_indicators(self, historical_data: pd.DataFrame) -> Dict:
        """Calculate technical indicators"""
        close_prices = historical_data['close'].values
        
        # RSI
        rsi = RSIIndicator(close=historical_data['close'], window=self.rsi_period)
        current_rsi = rsi.rsi().iloc[-1]
        
        # MACD
        macd = MACD(close=historical_data['close'])
        macd_hist = macd.macd_diff().iloc[-1]
        
        # Simple trend
        short_trend = (close_prices[-1] / close_prices[-3] - 1) * 100  # 3-period trend
        
        # Price momentum
        momentum = (close_prices[-1] / close_prices[-2] - 1) * 100
        
        indicators = {
            'rsi': current_rsi,
            'macd_hist': macd_hist,
            'trend': short_trend,
            'momentum': momentum
        }
        
        print(f"Indicators - RSI: {current_rsi:.1f}, MACD: {macd_hist:.6f}, Trend: {short_trend:.1f}%")
        return indicators
    
    def should_buy(self, level: GridLevel, indicators: Dict) -> bool:
        """Determine if we should buy at this grid level"""
        if level.position_size > 0 or self.total_positions >= self.max_positions:
            return False
            
        # Basic price condition - price is near or below grid level
        price_diff = (self.current_price - level.price) / level.price
        price_condition = -self.grid_spacing <= price_diff <= self.grid_spacing/2
        
        # RSI oversold condition
        rsi_condition = indicators['rsi'] <= self.rsi_oversold
        
        # Trend conditions
        trend_condition = indicators['trend'] >= -1.0  # Not strongly downward
        momentum_condition = indicators['momentum'] > -0.5  # Price not falling fast
        
        # Combined signal
        signal = (
            price_condition and
            (rsi_condition or indicators['macd_hist'] > 0) and
            (trend_condition and momentum_condition)
        )
        
        if signal:
            print(f"Buy signal at {level.price:.4f} - Price diff: {price_diff*100:.1f}%, RSI: {indicators['rsi']:.1f}")
            
        return signal
    
    def should_sell(self, level: GridLevel, indicators: Dict) -> bool:
        """Determine if we should sell at this grid level"""
        if level.position_size <= 0 or not level.entry_price:
            return False
            
        # Calculate profit
        profit_pct = (self.current_price - level.entry_price) / level.entry_price
        
        # Price conditions
        price_diff = (self.current_price - level.price) / level.price
        price_condition = abs(price_diff) <= self.grid_spacing
        
        # Take profit or stop loss
        take_profit = profit_pct >= self.take_profit
        stop_loss = profit_pct <= -self.stop_loss
        
        # Technical conditions
        rsi_condition = indicators['rsi'] >= self.rsi_overbought
        trend_condition = indicators['trend'] <= 1.0  # Not strongly upward
        
        # Time-based exit - minimum 15 minutes hold time
        time_condition = True
        if level.entry_time:
            hold_time = datetime.now() - level.entry_time
            time_condition = hold_time.total_seconds() > 900
            
        # Exit signal
        signal = time_condition and (
            take_profit or
            stop_loss or
            (price_condition and rsi_condition and trend_condition)
        )
        
        if signal:
            reason = "Take profit" if take_profit else "Stop loss" if stop_loss else "Technical"
            print(f"Sell signal at {level.price:.4f} - {reason}, Profit: {profit_pct*100:.1f}%")
            
        return signal
    
    def calculate_position_size(self, price: float) -> float:
        """Calculate position size based on risk"""
        return self.position_size
        
    def update(self, current_price: float, historical_data: pd.DataFrame) -> List[Dict]:
        """Update strategy state and generate trading signals"""
        self.current_price = current_price
        print(f"\nUpdating strategy at price {current_price:.4f}")
        
        # Calculate indicators
        indicators = self.calculate_indicators(historical_data)
        signals = []
        
        # Check each grid level for trading opportunities
        for level in self.grid_levels:
            # Check for sell signals first
            if level.position_size > 0 and self.should_sell(level, indicators):
                signals.append({
                    'action': 'SELL',
                    'price': level.price,
                    'size': level.position_size,
                    'indicators': indicators
                })
                continue
                
            # Then check for buy signals
            if self.total_positions < self.max_positions and self.should_buy(level, indicators):
                size = self.calculate_position_size(level.price)
                signals.append({
                    'action': 'BUY',
                    'price': level.price,
                    'size': size,
                    'indicators': indicators
                })
                
        return signals
        
    def update_position(self, level: GridLevel, size: float, price: float) -> None:
        """Update position information after trade execution"""
        if size > 0:  # Buy
            level.position_size = size
            level.entry_price = price
            level.entry_time = datetime.now()
            self.total_positions += 1
        else:  # Sell
            self.total_positions -= 1
            level.position_size = 0
            level.entry_price = None
            level.entry_time = None
            
        level.last_update = datetime.now()
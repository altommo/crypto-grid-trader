import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass
from ta.momentum import RSIIndicator
from ta.trend import MACD

@dataclass
class GridLevel:
    price: float
    buy_order_id: str = None
    sell_order_id: str = None
    position_size: float = 0.0

class GridStrategy:
    def __init__(self, config: Dict):
        self.symbol = config['trading']['symbol']
        self.grid_size = config['trading']['grid_size']
        self.grid_spacing = config['trading']['grid_spacing']
        self.position_size = config['trading']['position_size']
        self.max_positions = config['trading']['max_positions']
        
        # Risk parameters
        self.stop_loss = config['risk']['stop_loss']
        self.take_profit = config['risk']['take_profit']
        self.max_leverage = config['risk']['max_leverage']
        
        # Indicator parameters
        self.rsi_period = config['indicators']['rsi_period']
        self.rsi_oversold = config['indicators']['rsi_oversold']
        self.rsi_overbought = config['indicators']['rsi_overbought']
        
        self.grid_levels: List[GridLevel] = []
        self.current_price = None
        
    def initialize_grid(self, current_price: float) -> None:
        """Initialize grid levels around the current price"""
        self.current_price = current_price
        
        # Calculate grid levels
        spacing_factor = 1 + self.grid_spacing
        levels = []
        
        # Add levels above current price
        price = current_price
        for _ in range(self.grid_size // 2):
            price *= spacing_factor
            levels.append(GridLevel(price=price))
            
        # Add levels below current price
        price = current_price
        for _ in range(self.grid_size // 2):
            price /= spacing_factor
            levels.insert(0, GridLevel(price=price))
            
        self.grid_levels = sorted(levels, key=lambda x: x.price)
        
    def calculate_indicators(self, historical_data: pd.DataFrame) -> Tuple[float, float, float]:
        """Calculate RSI and MACD indicators"""
        rsi = RSIIndicator(close=historical_data['close'], window=self.rsi_period)
        macd = MACD(close=historical_data['close'])
        
        current_rsi = rsi.rsi().iloc[-1]
        current_macd = macd.macd().iloc[-1]
        current_signal = macd.macd_signal().iloc[-1]
        
        return current_rsi, current_macd, current_signal
    
    def should_buy(self, level: GridLevel, rsi: float, macd: float, signal: float) -> bool:
        """Determine if we should buy at this grid level"""
        if level.position_size > 0:
            return False
            
        price_condition = self.current_price <= level.price
        rsi_condition = rsi <= self.rsi_oversold
        macd_condition = macd > signal  # MACD crosses above signal line
        
        return price_condition and rsi_condition and macd_condition
    
    def should_sell(self, level: GridLevel, rsi: float, macd: float, signal: float) -> bool:
        """Determine if we should sell at this grid level"""
        if level.position_size <= 0:
            return False
            
        price_condition = self.current_price >= level.price
        rsi_condition = rsi >= self.rsi_overbought
        macd_condition = macd < signal  # MACD crosses below signal line
        
        return price_condition and rsi_condition and macd_condition
    
    def calculate_position_size(self, price: float) -> float:
        """Calculate position size based on account balance and risk parameters"""
        return self.position_size  # Implement your position sizing logic here
    
    def update(self, current_price: float, historical_data: pd.DataFrame) -> List[Dict]:
        """Update strategy state and generate trading signals"""
        self.current_price = current_price
        rsi, macd, signal = self.calculate_indicators(historical_data)
        
        signals = []
        for level in self.grid_levels:
            if self.should_buy(level, rsi, macd, signal):
                signals.append({
                    'action': 'BUY',
                    'price': level.price,
                    'size': self.calculate_position_size(level.price)
                })
            elif self.should_sell(level, rsi, macd, signal):
                signals.append({
                    'action': 'SELL',
                    'price': level.price,
                    'size': level.position_size
                })
                
        return signals
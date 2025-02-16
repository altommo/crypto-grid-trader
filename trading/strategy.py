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
    buy_order_id: Optional[str] = None
    sell_order_id: Optional[str] = None
    position_size: float = 0.0
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
        self.min_profit_usd = config['trading']['min_profit_usd']
        
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
        
        print(f"Strategy initialized with {self.grid_size} levels, {self.grid_spacing} spacing")
        
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
        print(f"Grid initialized with {len(self.grid_levels)} levels around {current_price}")
        
    def calculate_indicators(self, historical_data: pd.DataFrame) -> Dict:
        """Calculate RSI and MACD indicators"""
        # RSI
        rsi = RSIIndicator(close=historical_data['close'], window=self.rsi_period)
        current_rsi = rsi.rsi().iloc[-1]
        
        # MACD
        macd = MACD(close=historical_data['close'])
        current_macd = macd.macd().iloc[-1]
        current_signal = macd.macd_signal().iloc[-1]
        macd_hist = macd.macd_diff().iloc[-1]
        
        # Bollinger Bands
        bb = BollingerBands(close=historical_data['close'])
        bb_upper = bb.bollinger_hband().iloc[-1]
        bb_lower = bb.bollinger_lband().iloc[-1]
        
        print(f"Indicators - RSI: {current_rsi:.2f}, MACD Hist: {macd_hist:.6f}")
        
        return {
            'rsi': current_rsi,
            'macd': current_macd,
            'macd_signal': current_signal,
            'macd_hist': macd_hist,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower
        }
    
    def should_buy(self, level: GridLevel, indicators: Dict) -> bool:
        """Determine if we should buy at this grid level"""
        if level.position_size > 0:
            return False
            
        # Basic price condition - buy if price is near the grid level
        price_condition = (
            self.current_price >= level.price * (1 - self.grid_spacing) and 
            self.current_price <= level.price * (1 + self.grid_spacing)
        )
        
        # RSI condition (more aggressive)
        rsi_condition = indicators['rsi'] <= 45  # Increased from 30
        
        # MACD condition (more aggressive)
        macd_condition = indicators['macd_hist'] > -0.0001  # Near crossing
        
        result = price_condition and (rsi_condition or macd_condition)  # More aggressive with OR
        if result:
            print(f"Buy signal at {level.price}: RSI={indicators['rsi']:.2f}, MACD_hist={indicators['macd_hist']:.6f}")
            
        return result
    
    def should_sell(self, level: GridLevel, indicators: Dict) -> bool:
        """Determine if we should sell at this grid level"""
        if level.position_size <= 0:
            return False
            
        # Basic price condition - sell if price is near the grid level
        price_condition = (
            self.current_price >= level.price * (1 - self.grid_spacing) and 
            self.current_price <= level.price * (1 + self.grid_spacing)
        )
        
        # RSI condition (more aggressive)
        rsi_condition = indicators['rsi'] >= 55  # Decreased from 70
        
        # MACD condition (more aggressive)
        macd_condition = indicators['macd_hist'] < 0.0001  # Near crossing
        
        # Profit condition - any profit is acceptable
        profit = (self.current_price - level.price) * level.position_size
        profit_condition = profit > 0
        
        # Stop loss condition
        loss_percentage = (self.current_price - level.price) / level.price
        stop_loss_condition = loss_percentage <= -self.stop_loss
        
        result = (price_condition and (rsi_condition or macd_condition) and profit_condition) or stop_loss_condition
        
        if result:
            print(f"Sell signal at {level.price}: RSI={indicators['rsi']:.2f}, MACD_hist={indicators['macd_hist']:.6f}, Profit={profit:.2f}")
            
        return result
        
    def calculate_position_size(self, price: float) -> float:
        """Calculate position size based on current price and configuration"""
        # Base position size from config
        base_size = self.position_size
        
        # Scale by current price
        price_factor = 1.0
        if self.current_price:
            price_diff = abs(price - self.current_price) / price
            if price_diff > self.grid_spacing:
                price_factor = self.grid_spacing / price_diff
                
        return base_size * price_factor
        
    def update(self, current_price: float, historical_data: pd.DataFrame) -> List[Dict]:
        """Update strategy state and generate trading signals"""
        self.current_price = current_price
        print(f"\nUpdating strategy at price {current_price}")
        
        # Calculate indicators
        indicators = self.calculate_indicators(historical_data)
        
        signals = []
        for level in self.grid_levels:
            if self.should_buy(level, indicators):
                position_size = self.calculate_position_size(level.price)
                signals.append({
                    'action': 'BUY',
                    'price': level.price,
                    'size': position_size,
                    'indicators': indicators
                })
                print(f"Generated BUY signal at {level.price}")
            elif self.should_sell(level, indicators):
                signals.append({
                    'action': 'SELL',
                    'price': level.price,
                    'size': level.position_size,
                    'indicators': indicators
                })
                print(f"Generated SELL signal at {level.price}")
                
        return signals
        
    def update_position(self, level: GridLevel, size: float, price: float) -> None:
        """Update position information after trade execution"""
        level.position_size = size
        level.last_update = datetime.now()
        if size > 0:
            level.entry_time = datetime.now()
        else:
            level.entry_time = None
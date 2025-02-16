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
        
    def initialize_grid(self, current_price: float) -> None:
        """Initialize grid levels around the current price"""
        self.current_price = current_price
        
        # Calculate range based on volatility
        range_size = self.grid_spacing * (self.grid_size // 2)
        
        # Generate grid levels
        levels = []
        for i in range(self.grid_size):
            price = current_price * (1 - range_size + i * self.grid_spacing)
            levels.append(GridLevel(price=price))
            
        self.grid_levels = sorted(levels, key=lambda x: x.price)
        print(f"Grid initialized with {len(self.grid_levels)} levels around {current_price}")
        
    def calculate_indicators(self, historical_data: pd.DataFrame) -> Dict:
        """Calculate technical indicators"""
        # RSI
        rsi = RSIIndicator(close=historical_data['close'], window=self.rsi_period)
        current_rsi = rsi.rsi().iloc[-1]
        
        # MACD
        macd = MACD(close=historical_data['close'])
        macd_hist = macd.macd_diff().iloc[-1]
        
        # Bollinger Bands
        bb = BollingerBands(close=historical_data['close'])
        bb_upper = bb.bollinger_hband().iloc[-1]
        bb_lower = bb.bollinger_lband().iloc[-1]
        
        # Price trends
        close_prices = historical_data['close'].values
        short_trend = (close_prices[-1] / close_prices[-5] - 1) * 100
        
        return {
            'rsi': current_rsi,
            'macd_hist': macd_hist,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'trend': short_trend
        }
    
    def should_buy(self, level: GridLevel, indicators: Dict) -> bool:
        """Determine if we should buy at this grid level"""
        if level.position_size > 0 or self.total_positions >= self.max_positions:
            return False
            
        # Price must be near grid level
        price_condition = abs(self.current_price - level.price) / level.price < self.grid_spacing
        
        # Only buy if trending up
        trend_condition = indicators['trend'] > 0
        
        # Technical conditions - any of these can trigger
        rsi_condition = indicators['rsi'] < self.rsi_oversold and indicators['macd_hist'] > 0
        bb_condition = self.current_price < indicators['bb_lower'] and indicators['rsi'] < 45
        
        # Time cooldown
        time_condition = True
        if self.last_trade_time:
            cooldown = datetime.now() - self.last_trade_time
            time_condition = cooldown.total_seconds() > 3600  # 1 hour between trades
            
        signal = price_condition and time_condition and (rsi_condition or bb_condition) and trend_condition
        
        if signal:
            print(f"Buy signal at {level.price}: RSI={indicators['rsi']:.1f}, MACD={indicators['macd_hist']:.6f}, Trend={indicators['trend']:.1f}%")
            
        return signal
    
    def should_sell(self, level: GridLevel, indicators: Dict) -> bool:
        """Determine if we should sell at this grid level"""
        if level.position_size <= 0 or not level.entry_price:
            return False
            
        # Calculate profit
        profit_pct = (self.current_price - level.entry_price) / level.entry_price
        
        # Take profit or stop loss
        take_profit = profit_pct >= self.take_profit
        stop_loss = profit_pct <= -self.stop_loss
        
        # Only sell if trending down
        trend_condition = indicators['trend'] < 0
        
        # Technical conditions
        rsi_condition = indicators['rsi'] > self.rsi_overbought and indicators['macd_hist'] < 0
        bb_condition = self.current_price > indicators['bb_upper'] and indicators['rsi'] > 55
        
        # Time-based exit
        min_hold_time = 3600  # 1 hour minimum hold
        time_condition = True
        if level.entry_time:
            hold_time = datetime.now() - level.entry_time
            time_condition = hold_time.total_seconds() > min_hold_time
            
        signal = time_condition and (
            take_profit or 
            stop_loss or 
            (trend_condition and (rsi_condition or bb_condition))
        )
        
        if signal:
            print(f"Sell signal at {level.price}: Profit={profit_pct*100:.1f}%, RSI={indicators['rsi']:.1f}")
            
        return signal
    
    def calculate_position_size(self, price: float) -> float:
        """Calculate position size based on risk"""
        return self.position_size  # Fixed size for now
        
    def update(self, current_price: float, historical_data: pd.DataFrame) -> List[Dict]:
        """Update strategy state and generate trading signals"""
        self.current_price = current_price
        
        # Calculate indicators
        indicators = self.calculate_indicators(historical_data)
        signals = []
        
        # Check for buy signals
        if self.total_positions < self.max_positions:
            for level in self.grid_levels:
                if self.should_buy(level, indicators):
                    size = self.calculate_position_size(level.price)
                    signals.append({
                        'action': 'BUY',
                        'price': level.price,
                        'size': size,
                        'indicators': indicators
                    })
                    self.last_trade_time = datetime.now()
                    break  # Only one buy signal at a time
                    
        # Check for sell signals
        for level in self.grid_levels:
            if self.should_sell(level, indicators):
                signals.append({
                    'action': 'SELL',
                    'price': level.price,
                    'size': level.position_size,
                    'indicators': indicators
                })
                self.last_trade_time = datetime.now()
                
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
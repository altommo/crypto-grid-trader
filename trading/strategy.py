import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
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
        self.max_drawdown = config['risk']['max_drawdown']
        self.position_timeout = config['risk']['position_timeout']
        
        # Indicator parameters
        self.rsi_period = config['indicators']['rsi_period']
        self.rsi_oversold = config['indicators']['rsi_oversold']
        self.rsi_overbought = config['indicators']['rsi_overbought']
        self.min_volatility = config['indicators']['min_volatility']
        self.max_volatility = config['indicators']['max_volatility']
        
        self.grid_levels: List[GridLevel] = []
        self.current_price = None
        self.last_update_time = None
        self.total_pnl = 0.0
        self.drawdown = 0.0
        
    def initialize_grid(self, current_price: float) -> None:
        """Initialize grid levels around the current price with adaptive spacing"""
        self.current_price = current_price
        self.last_update_time = datetime.now()
        
        # Calculate adaptive grid spacing based on volatility
        volatility = self.calculate_volatility(current_price)
        adjusted_spacing = min(max(volatility * 2, self.grid_spacing), self.max_volatility)
        
        # Calculate grid levels
        spacing_factor = 1 + adjusted_spacing
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
        
    def calculate_indicators(self, historical_data: pd.DataFrame) -> Dict:
        """Calculate technical indicators for trading decisions"""
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
        
        # Volume analysis
        volume_sma = historical_data['volume'].rolling(
            window=self.config['indicators']['volume_periods']
        ).mean().iloc[-1]
        current_volume = historical_data['volume'].iloc[-1]
        volume_ratio = current_volume / volume_sma if volume_sma > 0 else 0
        
        return {
            'rsi': current_rsi,
            'macd': current_macd,
            'macd_signal': current_signal,
            'macd_hist': macd_hist,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'volume_ratio': volume_ratio
        }
        
    def calculate_volatility(self, current_price: float) -> float:
        """Calculate current market volatility"""
        if not self.grid_levels:
            return self.grid_spacing
            
        price_changes = []
        for level in self.grid_levels:
            if level.last_update and level.entry_time:
                time_diff = (level.last_update - level.entry_time).total_seconds()
                if time_diff > 0:
                    price_change = abs(current_price - level.price) / level.price
                    price_changes.append(price_change)
                    
        if price_changes:
            return np.mean(price_changes)
        return self.grid_spacing
        
    def should_buy(self, level: GridLevel, indicators: Dict) -> bool:
        """Determine if we should buy at this grid level"""
        if level.position_size > 0:
            return False
            
        # Basic price condition
        price_condition = self.current_price <= level.price
        
        # Technical indicator conditions
        rsi_condition = indicators['rsi'] <= self.rsi_oversold
        macd_condition = indicators['macd_hist'] > 0  # MACD histogram is positive
        
        # Volume condition
        volume_condition = indicators['volume_ratio'] > 1.2  # Volume is above average
        
        # Volatility condition
        volatility = self.calculate_volatility(self.current_price)
        volatility_condition = self.min_volatility <= volatility <= self.max_volatility
        
        # Combined conditions
        return (price_condition and rsi_condition and macd_condition and 
                volume_condition and volatility_condition)
        
    def should_sell(self, level: GridLevel, indicators: Dict) -> bool:
        """Determine if we should sell at this grid level"""
        if level.position_size <= 0:
            return False
            
        # Check position timeout
        if level.entry_time:
            time_held = (datetime.now() - level.entry_time).total_seconds()
            if time_held > self.position_timeout:
                return True
                
        # Basic price condition
        price_condition = self.current_price >= level.price
        
        # Technical indicator conditions
        rsi_condition = indicators['rsi'] >= self.rsi_overbought
        macd_condition = indicators['macd_hist'] < 0  # MACD histogram is negative
        
        # Profit target condition
        profit = (self.current_price - level.price) * level.position_size
        profit_condition = profit >= self.min_profit_usd
        
        # Stop loss condition
        loss_percentage = (self.current_price - level.price) / level.price
        stop_loss_condition = loss_percentage <= -self.stop_loss
        
        return (
            (price_condition and rsi_condition and macd_condition and profit_condition) or
            stop_loss_condition
        )
        
    def calculate_position_size(self, price: float) -> float:
        """Calculate adaptive position size based on volatility and risk parameters"""
        volatility = self.calculate_volatility(price)
        base_size = self.position_size
        
        # Reduce position size when volatility is high
        volatility_factor = 1.0
        if volatility > self.grid_spacing:
            volatility_factor = self.grid_spacing / volatility
            
        # Consider current drawdown
        drawdown_factor = 1.0
        if self.drawdown > 0:
            drawdown_factor = 1.0 - (self.drawdown / self.max_drawdown)
            
        return base_size * volatility_factor * drawdown_factor
        
    def update(self, current_price: float, historical_data: pd.DataFrame) -> List[Dict]:
        """Update strategy state and generate trading signals"""
        self.current_price = current_price
        self.last_update_time = datetime.now()
        
        # Calculate indicators
        indicators = self.calculate_indicators(historical_data)
        
        # Update drawdown
        if self.total_pnl < 0:
            self.drawdown = abs(self.total_pnl)
        
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
            elif self.should_sell(level, indicators):
                signals.append({
                    'action': 'SELL',
                    'price': level.price,
                    'size': level.position_size,
                    'indicators': indicators
                })
                
        return signals
        
    def update_position(self, level: GridLevel, size: float, price: float) -> None:
        """Update position information after trade execution"""
        level.position_size = size
        level.last_update = datetime.now()
        if size > 0:
            level.entry_time = datetime.now()
        else:
            level.entry_time = None
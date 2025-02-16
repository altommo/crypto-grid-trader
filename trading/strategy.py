import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

@dataclass
class GridLevel:
    price: float
    position_size: float = 0.0
    entry_price: Optional[float] = None
    entry_time: Optional[datetime] = None
    last_update: Optional[datetime] = None
    trades_taken: int = 0
    successful_trades: int = 0

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
        self.last_trend = 0
        
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
        
        # Bollinger Bands
        bb = BollingerBands(close=historical_data['close'])
        bb_upper = bb.bollinger_hband().iloc[-1]
        bb_lower = bb.bollinger_lband().iloc[-1]
        bb_width = (bb_upper - bb_lower) / close_prices[-1]
        
        # Trends at different timeframes
        short_trend = (close_prices[-1] / close_prices[-3] - 1) * 100  # 3-period trend
        medium_trend = (close_prices[-1] / close_prices[-6] - 1) * 100  # 6-period trend
        
        # Momentum and volatility
        momentum = close_prices[-1] / close_prices[-2] - 1
        volatility = np.std(np.diff(close_prices[-10:])) / close_prices[-1]
        
        indicators = {
            'rsi': current_rsi,
            'bb_width': bb_width,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'short_trend': short_trend,
            'medium_trend': medium_trend,
            'momentum': momentum,
            'volatility': volatility
        }
        
        print(f"Indicators - RSI: {current_rsi:.1f}, Trends: {short_trend:.1f}%/{medium_trend:.1f}%, BB Width: {bb_width*100:.1f}%")
        return indicators
    
    def should_buy(self, level: GridLevel, indicators: Dict) -> bool:
        """Determine if we should buy at this grid level"""
        if level.position_size > 0 or self.total_positions >= self.max_positions:
            return False
            
        # Only take trades with good history
        if level.trades_taken > 0:
            success_rate = level.successful_trades / level.trades_taken
            if success_rate < 0.3:  # Avoid levels with poor performance
                return False
            
        # Wait for cooldown after losses
        if self.last_trade_time:
            cooldown = datetime.now() - self.last_trade_time
            if cooldown.total_seconds() < 3600:  # 1 hour cooldown
                return False
                
        # Price is near grid level
        price_diff = (self.current_price - level.price) / level.price
        price_condition = -self.grid_spacing/2 <= price_diff <= self.grid_spacing/4
        
        # Technical conditions
        rsi_condition = indicators['rsi'] <= self.rsi_oversold
        bb_condition = self.current_price <= indicators['bb_lower'] * 1.01
        
        # Trend analysis
        trend_reversal = (
            indicators['short_trend'] > -0.5 and  # Downtrend slowing
            indicators['medium_trend'] < -1.0 and  # Overall downtrend
            indicators['momentum'] > -0.001  # Price stabilizing
        )
        
        # Volatility check
        volatility_condition = (
            0.001 <= indicators['volatility'] <= 0.01 and  # Not too volatile
            indicators['bb_width'] >= 0.02  # Enough room to profit
        )
        
        signal = (
            price_condition and
            volatility_condition and
            (rsi_condition or bb_condition) and
            trend_reversal
        )
        
        if signal:
            print(f"Buy signal at {level.price:.4f} - RSI: {indicators['rsi']:.1f}, Trend: {indicators['short_trend']:.1f}%")
            
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
        
        # Technical exit conditions
        technical_exit = (
            indicators['rsi'] >= self.rsi_overbought or
            self.current_price >= indicators['bb_upper'] * 0.99
        )
        
        # Trend-based exit
        trend_exit = (
            indicators['short_trend'] < -1.0 and
            indicators['medium_trend'] < 0
        )
        
        # Time-based exit - minimum 30 minutes hold
        time_condition = True
        if level.entry_time:
            hold_time = datetime.now() - level.entry_time
            time_condition = hold_time.total_seconds() > 1800
            
        signal = time_condition and (
            take_profit or
            stop_loss or
            (technical_exit and trend_exit)
        )
        
        if signal:
            # Update level statistics
            level.trades_taken += 1
            if profit_pct > 0:
                level.successful_trades += 1
            print(f"Sell signal at {level.price:.4f} - Profit: {profit_pct*100:.1f}%, RSI: {indicators['rsi']:.1f}")
            
        return signal
        
    def calculate_position_size(self, price: float, indicators: Dict) -> float:
        """Calculate position size based on risk and volatility"""
        base_size = self.position_size
        
        # Reduce size in high volatility
        if indicators['volatility'] > 0.005:
            base_size *= 0.5
            
        # Increase size in strong setups
        if indicators['rsi'] < 30 and indicators['short_trend'] > 0:
            base_size *= 1.5
            
        return base_size
        
    def update(self, current_price: float, historical_data: pd.DataFrame) -> List[Dict]:
        """Update strategy state and generate trading signals"""
        self.current_price = current_price
        
        # Calculate indicators
        indicators = self.calculate_indicators(historical_data)
        signals = []
        
        # Check for sell signals first
        for level in self.grid_levels:
            if level.position_size > 0 and self.should_sell(level, indicators):
                signals.append({
                    'action': 'SELL',
                    'price': level.price,
                    'size': level.position_size,
                    'indicators': indicators
                })
                
        # Then check for buy signals if we have capacity
        if self.total_positions < self.max_positions:
            for level in self.grid_levels:
                if self.should_buy(level, indicators):
                    size = self.calculate_position_size(level.price, indicators)
                    signals.append({
                        'action': 'BUY',
                        'price': level.price,
                        'size': size,
                        'indicators': indicators
                    })
                    break  # Only one buy signal at a time
                    
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
        self.last_trade_time = datetime.now()
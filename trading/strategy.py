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
        
        # Wolfpack parameters
        self.sampling_period = 27  # Sampling period from PineScript
        self.range_multiplier = 1.0  # Range multiplier from PineScript
        
        # Risk parameters
        self.stop_loss = config['risk']['stop_loss']
        self.take_profit = config['risk']['take_profit']
        
        # State variables
        self.grid_levels: List[GridLevel] = []
        self.current_price = None
        self.last_trade_time = None
        self.total_positions = 0
        self.filtered_price = None
        self.upward_count = 0
        self.downward_count = 0
        
        print(f"Strategy initialized with Wolfpack settings: period={self.sampling_period}, mult={self.range_multiplier}")
        
    def calculate_smooth_range(self, prices: np.array) -> float:
        """Calculate smooth range using Wolfpack method"""
        # Calculate absolute price changes
        price_changes = np.abs(np.diff(prices))
        if len(price_changes) < self.sampling_period:
            return 0.0
            
        # EMA of price changes
        alpha = 2.0 / (self.sampling_period + 1)
        avg_range = 0.0
        for change in price_changes[-self.sampling_period:]:
            avg_range = (alpha * change) + ((1 - alpha) * avg_range)
            
        # Double smoothing
        wper = self.sampling_period * 2 - 1
        alpha2 = 2.0 / (wper + 1)
        smooth_range = avg_range
        for _ in range(wper):
            smooth_range = (alpha2 * avg_range) + ((1 - alpha2) * smooth_range)
            
        return smooth_range * self.range_multiplier
        
    def calculate_range_filter(self, price: float, smooth_range: float) -> float:
        """Calculate range filtered price"""
        if self.filtered_price is None:
            self.filtered_price = price
            return price
            
        if price > self.filtered_price:
            new_filter = max(self.filtered_price, price - smooth_range)
        else:
            new_filter = min(self.filtered_price, price + smooth_range)
            
        self.filtered_price = new_filter
        return new_filter
        
    def update_trend_counts(self, current_filter: float):
        """Update upward/downward trend counts"""
        if self.filtered_price is None:
            return
            
        if current_filter > self.filtered_price:
            self.upward_count += 1
            self.downward_count = 0
        elif current_filter < self.filtered_price:
            self.upward_count = 0
            self.downward_count += 1
        
    def initialize_grid(self, current_price: float) -> None:
        """Initialize grid levels around the current price"""
        self.current_price = current_price
        
        # Calculate range based on volatility
        total_range = self.grid_spacing * self.grid_size
        min_price = current_price * (1 - total_range/2)
        
        # Generate grid levels
        self.grid_levels = []
        for i in range(self.grid_size):
            price = min_price * (1 + self.grid_spacing * i)
            self.grid_levels.append(GridLevel(price=price))
            
        print(f"Grid initialized with {len(self.grid_levels)} levels from {self.grid_levels[0].price:.4f} to {self.grid_levels[-1].price:.4f}")
        
    def calculate_indicators(self, historical_data: pd.DataFrame) -> Dict:
        """Calculate technical indicators including Wolfpack filter"""
        close_prices = historical_data['close'].values
        
        # RSI for confirmation
        rsi = RSIIndicator(close=historical_data['close'], window=14)
        current_rsi = rsi.rsi().iloc[-1]
        
        # Wolfpack calculations
        smooth_range = self.calculate_smooth_range(close_prices)
        filtered_price = self.calculate_range_filter(close_prices[-1], smooth_range)
        self.update_trend_counts(filtered_price)
        
        # Bollinger Bands for volatility
        bb = BollingerBands(close=historical_data['close'])
        bb_width = (bb.bollinger_hband() - bb.bollinger_lband()) / historical_data['close']
        bb_width = bb_width.iloc[-1]
        
        # Calculate trends at different timeframes
        short_trend = (close_prices[-1] / close_prices[-3] - 1) * 100  # 3-period
        medium_trend = (close_prices[-1] / close_prices[-6] - 1) * 100  # 6-period
        
        indicators = {
            'rsi': current_rsi,
            'filtered_price': filtered_price,
            'smooth_range': smooth_range,
            'bb_width': bb_width,
            'short_trend': short_trend,
            'medium_trend': medium_trend,
            'upward_count': self.upward_count,
            'downward_count': self.downward_count
        }
        
        print(f"Indicators - RSI: {current_rsi:.1f}, Trends: {short_trend:.1f}%/{medium_trend:.1f}%, BB Width: {bb_width*100:.1f}%")
        return indicators
    
    def should_buy(self, level: GridLevel, indicators: Dict) -> bool:
        """Determine if we should buy at this grid level using Wolfpack logic"""
        if level.position_size > 0 or self.total_positions >= self.max_positions:
            return False
            
        # Check level history
        if level.trades_taken > 2 and level.successful_trades / level.trades_taken < 0.4:
            return False
            
        # Price conditions
        price_above_filter = self.current_price > indicators['filtered_price']
        price_near_level = abs(self.current_price - level.price) / level.price < self.grid_spacing/2
        
        # Trend conditions
        upward_trend = indicators['upward_count'] > 0
        trend_strength = indicators['short_trend'] > -0.5 and indicators['medium_trend'] < -1.0
        
        # Technical conditions
        rsi_oversold = indicators['rsi'] < 40
        volatility_ok = 0.005 <= indicators['bb_width'] <= 0.03
        
        # Combined signal
        signal = (
            price_above_filter and 
            price_near_level and 
            upward_trend and
            trend_strength and
            (rsi_oversold or volatility_ok)
        )
        
        if signal:
            print(f"Buy signal at {level.price:.4f} - RSI: {indicators['rsi']:.1f}, Up Count: {indicators['upward_count']}")
            
        return signal
    
    def should_sell(self, level: GridLevel, indicators: Dict) -> bool:
        """Determine if we should sell using Wolfpack logic"""
        if level.position_size <= 0 or not level.entry_price:
            return False
            
        # Calculate profit
        profit_pct = (self.current_price - level.entry_price) / level.entry_price
        
        # Take profit or stop loss
        take_profit = profit_pct >= self.take_profit
        stop_loss = profit_pct <= -self.stop_loss
        
        # Wolfpack conditions
        price_below_filter = self.current_price < indicators['filtered_price']
        downward_trend = indicators['downward_count'] > 0
        
        # RSI and trend conditions
        rsi_overbought = indicators['rsi'] > 60
        trend_reversal = indicators['short_trend'] < 0 and indicators['medium_trend'] < 0
        
        # Time-based exit - minimum 30 minutes hold
        time_condition = True
        if level.entry_time:
            hold_time = datetime.now() - level.entry_time
            time_condition = hold_time.total_seconds() > 1800
            
        signal = time_condition and (
            take_profit or
            stop_loss or
            (price_below_filter and downward_trend and (rsi_overbought or trend_reversal))
        )
        
        if signal:
            level.trades_taken += 1
            if profit_pct > 0:
                level.successful_trades += 1
            print(f"Sell signal at {level.price:.4f} - Profit: {profit_pct*100:.1f}%, Down Count: {indicators['downward_count']}")
            
        return signal
        
    def calculate_position_size(self, price: float, indicators: Dict) -> float:
        """Calculate position size based on Wolfpack indicators"""
        base_size = self.position_size
        
        # Reduce size in high volatility
        if indicators['bb_width'] > 0.02:
            base_size *= 0.5
            
        # Increase size in strong setups
        if indicators['upward_count'] > 2 and indicators['rsi'] < 30:
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
                
        # Then look for buy signals
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
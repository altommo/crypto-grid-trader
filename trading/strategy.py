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
    entry_price: Optional[float] = None

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
        self.last_trade_time = None
        self.total_positions = 0
        
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
        
        # Calculate price trends
        close_prices = historical_data['close'].values
        short_trend = (close_prices[-1] / close_prices[-5] - 1) * 100  # 5-period trend
        medium_trend = (close_prices[-1] / close_prices[-10] - 1) * 100  # 10-period trend
        
        print(f"Indicators - RSI: {current_rsi:.2f}, MACD Hist: {macd_hist:.6f}, Trends: {short_trend:.2f}%/{medium_trend:.2f}%")
        
        return {
            'rsi': current_rsi,
            'macd': current_macd,
            'macd_signal': current_signal,
            'macd_hist': macd_hist,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'short_trend': short_trend,
            'medium_trend': medium_trend
        }
    
    def should_buy(self, level: GridLevel, indicators: Dict) -> bool:
        """Determine if we should buy at this grid level"""
        if level.position_size > 0 or self.total_positions >= self.max_positions:
            return False
            
        # Price is below the grid level (buying opportunity)
        price_condition = self.current_price <= level.price * (1 + self.grid_spacing)
        
        # Technical conditions
        rsi_condition = indicators['rsi'] <= 45  # More aggressive
        macd_condition = indicators['macd_hist'] > -0.0001  # Near crossing
        trend_condition = indicators['short_trend'] > -0.5  # Not strongly downward
        bb_condition = self.current_price <= indicators['bb_lower'] * 1.01  # Near or below BB
        
        # Combine conditions (need price + (RSI or MACD) + trend)
        technical_condition = (rsi_condition or macd_condition or bb_condition) and trend_condition
        
        # Time condition - avoid trading too frequently
        time_condition = True
        if self.last_trade_time:
            time_diff = datetime.now() - self.last_trade_time
            time_condition = time_diff.total_seconds() > 300  # 5 minutes between trades
        
        result = price_condition and technical_condition and time_condition
        
        if result:
            print(f"Buy signal at {level.price}: RSI={indicators['rsi']:.2f}, MACD_hist={indicators['macd_hist']:.6f}")
            
        return result
    
    def should_sell(self, level: GridLevel, indicators: Dict) -> bool:
        """Determine if we should sell at this grid level"""
        if level.position_size <= 0 or not level.entry_price:
            return False
            
        # Calculate profit
        price_change = (self.current_price - level.entry_price) / level.entry_price
        profit_pct = price_change * 100
        
        # Price is above the grid level (selling opportunity)
        price_condition = self.current_price >= level.price * (1 - self.grid_spacing)
        
        # Technical conditions
        rsi_condition = indicators['rsi'] >= 55  # More aggressive
        macd_condition = indicators['macd_hist'] < 0.0001  # Near crossing
        trend_condition = indicators['short_trend'] < 0.5  # Not strongly upward
        bb_condition = self.current_price >= indicators['bb_upper'] * 0.99  # Near or above BB
        
        # Profit conditions
        take_profit_condition = profit_pct >= 0.5  # Take profit at 0.5%
        stop_loss_condition = profit_pct <= -1.0  # Stop loss at -1%
        
        # Time-based exit
        time_condition = True
        if level.entry_time:
            hold_time = datetime.now() - level.entry_time
            time_condition = hold_time.total_seconds() > 1800  # 30 minutes minimum hold
        
        # Exit conditions
        technical_exit = price_condition and (rsi_condition or macd_condition or bb_condition) and trend_condition and time_condition
        profit_exit = take_profit_condition or stop_loss_condition
        
        result = technical_exit or profit_exit
        
        if result:
            print(f"Sell signal at {level.price}: Profit={profit_pct:.2f}%, RSI={indicators['rsi']:.2f}")
            
        return result
        
    def calculate_position_size(self, price: float) -> float:
        """Calculate adaptive position size based on distance from current price"""
        base_size = self.position_size  # Base size from config
        
        # Reduce size when far from current price
        if self.current_price:
            distance = abs(price - self.current_price) / self.current_price
            if distance > self.grid_spacing:
                base_size *= (self.grid_spacing / distance)
        
        return base_size
        
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
                self.last_trade_time = datetime.now()
                
            elif self.should_sell(level, indicators):
                signals.append({
                    'action': 'SELL',
                    'price': level.price,
                    'size': level.position_size,
                    'indicators': indicators
                })
                print(f"Generated SELL signal at {level.price}")
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
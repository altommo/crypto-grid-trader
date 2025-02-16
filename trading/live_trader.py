import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.enums import *
from .strategy import GridStrategy

class LiveTrader:
    def __init__(self, config: Dict, client: Client):
        self.config = config
        self.client = client
        self.strategy = GridStrategy(config)
        self.bm = BinanceSocketManager(client)
        self.symbol = config['trading']['symbol']
        
        self.current_price = None
        self.positions = {}
        self.open_orders = {}
        self.historical_data = pd.DataFrame()
        self.is_running = False
        self.last_update = None
        
    async def initialize(self):
        """Initialize the trader with historical data and current state"""
        # Get historical data
        klines = self.client.get_historical_klines(
            self.symbol,
            Client.KLINE_INTERVAL_1HOUR,
            str(datetime.now() - timedelta(days=7))
        )
        
        self.historical_data = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignored'
        ])
        
        # Initialize strategy
        self.current_price = float(self.client.get_symbol_ticker(symbol=self.symbol)['price'])
        self.strategy.initialize_grid(self.current_price)
        
        # Get current positions
        self.update_positions()
        
        # Get open orders
        self.update_open_orders()
        
    def update_positions(self):
        """Update current positions"""
        account = self.client.get_account()
        self.positions = {}
        for balance in account['balances']:
            if float(balance['free']) > 0 or float(balance['locked']) > 0:
                self.positions[balance['asset']] = {
                    'free': float(balance['free']),
                    'locked': float(balance['locked'])
                }

    def update_open_orders(self):
        """Update open orders"""
        self.open_orders = {}
        open_orders = self.client.get_open_orders(symbol=self.symbol)
        for order in open_orders:
            self.open_orders[order['orderId']] = order

    def process_price_update(self, msg):
        """Process price update from websocket"""
        if msg['e'] == 'trade':
            self.current_price = float(msg['p'])
            self.last_update = datetime.now()
            
            # Update strategy
            signals = self.strategy.update(self.current_price, self.historical_data)
            
            # Process signals
            for signal in signals:
                self.execute_signal(signal)

    def execute_signal(self, signal: Dict):
        """Execute a trading signal"""
        try:
            price = signal['price']
            size = signal['size']
            action = signal['action']
            
            if action == 'BUY':
                order = self.client.create_order(
                    symbol=self.symbol,
                    side=SIDE_BUY,
                    type=ORDER_TYPE_LIMIT,
                    timeInForce=TIME_IN_FORCE_GTC,
                    quantity=size,
                    price=str(price)
                )
                self.open_orders[order['orderId']] = order
                
            elif action == 'SELL':
                order = self.client.create_order(
                    symbol=self.symbol,
                    side=SIDE_SELL,
                    type=ORDER_TYPE_LIMIT,
                    timeInForce=TIME_IN_FORCE_GTC,
                    quantity=size,
                    price=str(price)
                )
                self.open_orders[order['orderId']] = order
                
        except Exception as e:
            print(f"Error executing order: {e}")
            
    def process_order_update(self, msg):
        """Process order update from websocket"""
        if msg['e'] == 'executionReport':
            order_id = msg['i']
            
            if msg['X'] == 'FILLED':
                if order_id in self.open_orders:
                    del self.open_orders[order_id]
                self.update_positions()
            elif msg['X'] == 'CANCELED':
                if order_id in self.open_orders:
                    del self.open_orders[order_id]

    async def manage_orders(self):
        """Periodically manage and update orders"""
        while self.is_running:
            try:
                # Cancel stale orders
                current_time = datetime.now()
                for order_id, order in list(self.open_orders.items()):
                    order_time = datetime.fromtimestamp(order['time'] / 1000)
                    if (current_time - order_time).total_seconds() > 3600:  # 1 hour
                        self.client.cancel_order(
                            symbol=self.symbol,
                            orderId=order_id
                        )
                        
                # Update positions and orders
                self.update_positions()
                self.update_open_orders()
                
            except Exception as e:
                print(f"Error managing orders: {e}")
                
            await asyncio.sleep(60)  # Check every minute

    async def update_historical_data(self):
        """Periodically update historical data"""
        while self.is_running:
            try:
                klines = self.client.get_historical_klines(
                    self.symbol,
                    Client.KLINE_INTERVAL_1HOUR,
                    str(datetime.now() - timedelta(days=7))
                )
                
                self.historical_data = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                    'taker_buy_quote', 'ignored'
                ])
                
            except Exception as e:
                print(f"Error updating historical data: {e}")
                
            await asyncio.sleep(3600)  # Update every hour

    async def start(self):
        """Start the live trader"""
        await self.initialize()
        self.is_running = True
        
        # Start websocket connections
        self.bm.start_trade_socket(self.symbol, self.process_price_update)
        self.bm.start_user_socket(self.process_order_update)
        self.bm.start()
        
        # Start management tasks
        asyncio.create_task(self.manage_orders())
        asyncio.create_task(self.update_historical_data())
        
        print(f"Live trader started for {self.symbol}")
        
    async def stop(self):
        """Stop the live trader"""
        self.is_running = False
        self.bm.close()
        
        # Cancel all open orders
        for order_id in self.open_orders:
            try:
                self.client.cancel_order(
                    symbol=self.symbol,
                    orderId=order_id
                )
            except:
                pass
                
        print(f"Live trader stopped for {self.symbol}")

    def get_status(self) -> Dict:
        """Get current trading status"""
        return {
            'current_price': self.current_price,
            'positions': self.positions,
            'open_orders': len(self.open_orders),
            'last_update': self.last_update,
            'is_running': self.is_running,
            'grid_levels': [
                {'price': level.price, 'position_size': level.position_size}
                for level in self.strategy.grid_levels
            ]
        }
from flask import Flask, render_template, jsonify, request
import yaml
import pandas as pd
import numpy as np
from trading.strategy import GridStrategy
from trading.backtester import Backtester
from binance.client import Client
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Load configuration
with open('config.yaml') as f:
    config = yaml.safe_load(f)

# Add API credentials from environment variables
config['binance']['api_key'] = os.getenv('BINANCE_API_KEY')
config['binance']['api_secret'] = os.getenv('BINANCE_API_SECRET')

# Initialize Binance client
client = Client(
    config['binance']['api_key'],
    config['binance']['api_secret'],
    testnet=config['binance']['testnet']
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/strategy/parameters', methods=['GET'])
def get_strategy_parameters():
    """Get all strategy parameters"""
    try:
        return jsonify({
            'basic': {
                'symbol': config['trading']['symbol'],
                'gridSize': config['trading']['grid_size'],
                'gridSpacing': config['trading']['grid_spacing'] * 100,  # Convert to percentage
                'positionSize': config['trading']['position_size'],
                'maxPositions': config['trading']['max_positions'],
                'useBnbFees': config['binance']['use_bnb_fees']
            },
            'wolfpack': {
                'samplingPeriod': config['trading'].get('sampling_period', 27),
                'rangeMultiplier': config['trading'].get('range_multiplier', 1.0)
            },
            'risk': {
                'stopLoss': config['risk']['stop_loss'] * 100,  # Convert to percentage
                'takeProfit': config['risk']['take_profit'] * 100,  # Convert to percentage
                'minSuccessRate': config['risk'].get('min_success_rate', 0.4) * 100,  # Convert to percentage
                'minHoldTime': config['risk'].get('min_hold_time', 30)
            },
            'technical': {
                'rsiPeriod': config['technical'].get('rsi_period', 14),
                'shortTrendPeriod': config['technical'].get('short_trend_period', 3),
                'mediumTrendPeriod': config['technical'].get('medium_trend_period', 6),
                'minVolatility': config['technical'].get('min_volatility', 0.005) * 100,  # Convert to percentage
                'maxVolatility': config['technical'].get('max_volatility', 0.03) * 100  # Convert to percentage
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategy/parameters', methods=['POST'])
def update_strategy_parameters():
    """Update strategy parameters"""
    try:
        params = request.json
        
        # Update basic parameters
        if 'basic' in params:
            basic = params['basic']
            config['trading']['symbol'] = basic.get('symbol', config['trading']['symbol'])
            config['trading']['grid_size'] = int(basic.get('gridSize', config['trading']['grid_size']))
            config['trading']['grid_spacing'] = float(basic.get('gridSpacing', config['trading']['grid_spacing'])) / 100
            config['trading']['position_size'] = float(basic.get('positionSize', config['trading']['position_size']))
            config['trading']['max_positions'] = int(basic.get('maxPositions', config['trading']['max_positions']))
            config['binance']['use_bnb_fees'] = bool(basic.get('useBnbFees', config['binance']['use_bnb_fees']))
        
        # Update Wolfpack parameters
        if 'wolfpack' in params:
            wolfpack = params['wolfpack']
            config['trading']['sampling_period'] = int(wolfpack.get('samplingPeriod', 27))
            config['trading']['range_multiplier'] = float(wolfpack.get('rangeMultiplier', 1.0))
        
        # Update risk parameters
        if 'risk' in params:
            risk = params['risk']
            config['risk']['stop_loss'] = float(risk.get('stopLoss', config['risk']['stop_loss'])) / 100
            config['risk']['take_profit'] = float(risk.get('takeProfit', config['risk']['take_profit'])) / 100
            config['risk']['min_success_rate'] = float(risk.get('minSuccessRate', 40)) / 100
            config['risk']['min_hold_time'] = int(risk.get('minHoldTime', 30))
        
        # Update technical parameters
        if 'technical' in params:
            tech = params['technical']
            config['technical'] = {
                'rsi_period': int(tech.get('rsiPeriod', 14)),
                'short_trend_period': int(tech.get('shortTrendPeriod', 3)),
                'medium_trend_period': int(tech.get('mediumTrendPeriod', 6)),
                'min_volatility': float(tech.get('minVolatility', 0.5)) / 100,
                'max_volatility': float(tech.get('maxVolatility', 3.0)) / 100
            }
        
        # Save updated config
        with open('config.yaml', 'w') as f:
            yaml.dump(config, f)
        
        return jsonify({'status': 'success', 'message': 'Parameters updated successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    try:
        # Get parameters from request
        params = request.json
        print(f"Received parameters: {params}")  # Debug log
        
        symbol = params.get('symbol', config['trading']['symbol'])
        days = int(params.get('days', 30))  # Convert to integer
        
        # Update config with form parameters if provided
        if 'gridSize' in params:
            config['trading']['grid_size'] = int(params['gridSize'])
        if 'gridSpacing' in params:
            config['trading']['grid_spacing'] = float(params['gridSpacing']) / 100  # Convert from percentage
        if 'useBnbFees' in params:
            config['binance']['use_bnb_fees'] = bool(params['useBnbFees'])
            
        print(f"Using configuration: {config['trading']}")  # Debug log
        
        # Get historical data from Binance
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        print(f"Fetching data for {symbol} from {start_time} to {end_time}")  # Debug log
        
        klines = client.get_historical_klines(
            symbol,
            Client.KLINE_INTERVAL_1HOUR,
            str(int(start_time.timestamp() * 1000)),  # Convert to milliseconds
            str(int(end_time.timestamp() * 1000))
        )
        
        if not klines:
            return jsonify({
                'error': 'No data received from Binance',
                'total_return': 0,
                'total_trades': 0,
                'win_rate': 0
            })
        
        print(f"Received {len(klines)} candlesticks")  # Debug log
        
        # Convert to DataFrame
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignored'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        print(f"Data range: {df.index.min()} to {df.index.max()}")  # Debug log
        
        # Run backtest
        backtester = Backtester(config, df)
        results = backtester.run()
        
        print(f"Backtest results: {results}")  # Debug log
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Error in backtest: {str(e)}")  # Debug log
        return jsonify({
            'error': str(e),
            'total_return': 0,
            'total_trades': 0,
            'win_rate': 0
        })

@app.route('/api/grid/status', methods=['GET', 'POST'])
def grid_status():
    try:
        if request.method == 'POST':
            # Update grid parameters
            params = request.json
            print(f"Updating grid with parameters: {params}")  # Debug log
            
            if 'gridSize' in params:
                config['trading']['grid_size'] = int(params['gridSize'])
            if 'gridSpacing' in params:
                config['trading']['grid_spacing'] = float(params['gridSpacing']) / 100
            if 'useBnbFees' in params:
                config['binance']['use_bnb_fees'] = bool(params['useBnbFees'])
        
        strategy = GridStrategy(config)
        
        # Get current price
        ticker = client.get_symbol_ticker(symbol=config['trading']['symbol'])
        current_price = float(ticker['price'])
        
        # Initialize grid
        strategy.initialize_grid(current_price)
        
        grid_levels = [{'price': level.price, 
                       'position_size': level.position_size} 
                      for level in strategy.grid_levels]
        
        print(f"Grid status: {len(grid_levels)} levels around {current_price}")  # Debug log
        
        return jsonify({
            'current_price': current_price,
            'grid_levels': grid_levels,
            'config': {
                'grid_size': config['trading']['grid_size'],
                'grid_spacing': config['trading']['grid_spacing'],
                'use_bnb_fees': config['binance']['use_bnb_fees']
            }
        })
        
    except Exception as e:
        print(f"Error in grid status: {str(e)}")  # Debug log
        return jsonify({
            'error': str(e),
            'current_price': 0,
            'grid_levels': []
        })

if __name__ == '__main__':
    app.run(debug=True)
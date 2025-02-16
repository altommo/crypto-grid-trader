from flask import Flask, render_template, jsonify, request
import yaml
import pandas as pd
from trading.strategy import GridStrategy
from trading.backtester import Backtester
from binance.client import Client
from datetime import datetime, timedelta

app = Flask(__name__)

# Load configuration
with open('config.yaml') as f:
    config = yaml.safe_load(f)

# Initialize Binance client
client = Client(
    config['binance']['api_key'],
    config['binance']['api_secret'],
    testnet=config['binance']['testnet']
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    # Get parameters from request
    params = request.json
    symbol = params.get('symbol', config['trading']['symbol'])
    days = params.get('days', 30)
    
    # Get historical data from Binance
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    klines = client.get_historical_klines(
        symbol,
        Client.KLINE_INTERVAL_1HOUR,
        str(start_time),
        str(end_time)
    )
    
    # Convert to DataFrame
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
        'taker_buy_quote', 'ignored'
    ])
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
    
    # Run backtest
    backtester = Backtester(config, df)
    results = backtester.run()
    
    return jsonify(results)

@app.route('/api/grid/status')
def grid_status():
    strategy = GridStrategy(config)
    
    # Get current price
    ticker = client.get_symbol_ticker(symbol=config['trading']['symbol'])
    current_price = float(ticker['price'])
    
    # Initialize grid
    strategy.initialize_grid(current_price)
    
    return jsonify({
        'current_price': current_price,
        'grid_levels': [{'price': level.price, 
                        'position_size': level.position_size} 
                       for level in strategy.grid_levels]
    })

if __name__ == '__main__':
    app.run(debug=True)
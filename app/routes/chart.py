from flask import Blueprint, jsonify, request
import ccxt
from datetime import datetime, timedelta

chart_bp = Blueprint('chart', __name__)

def get_exchange():
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future'
        }
    })
    exchange.set_sandbox_mode(True)
    return exchange

TIMEFRAME_MAPPING = {
    '1m': '1m',
    '3m': '3m',
    '5m': '5m',
    '15m': '15m',
    '30m': '30m',
    '1h': '1h',
    '2h': '2h',
    '4h': '4h',
    '6h': '6h',
    '8h': '8h',
    '12h': '12h',
    '1d': '1D',
    '3d': '3D',
    '1w': '1W',
    '1M': '1M'
}

QUOTE_CURRENCIES = ['USDT', 'BUSD', 'USDC', 'BTC', 'ETH']

@chart_bp.route('/symbols')
def get_symbols():
    try:
        exchange = get_exchange()
        markets = exchange.load_markets()
        
        # Organize symbols by base/quote currency
        symbols = {}
        for symbol, market in markets.items():
            if market['active'] and market['future']:
                base = market['base']
                quote = market['quote']
                if quote in QUOTE_CURRENCIES:
                    if base not in symbols:
                        symbols[base] = []
                    symbols[base].append(quote)
        
        # Return structured symbol data
        return jsonify({
            'bases': list(symbols.keys()),
            'quotes': QUOTE_CURRENCIES,
            'pairs': symbols
        })
    except Exception as e:
        print(f"Error fetching symbols: {str(e)}")
        return jsonify({'error': str(e)}), 500

@chart_bp.route('/historical_data')
def get_historical_data():
    try:
        exchange = get_exchange()
        
        symbol = request.args.get('symbol', 'BTC/USDT')
        timeframe = request.args.get('timeframe', '1h')
        limit = int(request.args.get('limit', 1000))
        
        print(f"Fetching data for {symbol} ({timeframe})")
        
        if timeframe not in TIMEFRAME_MAPPING:
            return jsonify({'error': 'Invalid timeframe'}), 400
            
        ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME_MAPPING[timeframe], limit=limit)
        
        formatted_data = [{
            'time': candle[0] / 1000,
            'open': candle[1],
            'high': candle[2],
            'low': candle[3],
            'close': candle[4],
            'volume': candle[5]
        } for candle in ohlcv]
        
        print(f"Fetched {len(formatted_data)} candles")
        return jsonify(formatted_data)
        
    except Exception as e:
        print(f"Error fetching historical data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@chart_bp.route('/timeframes')
def get_timeframes():
    return jsonify(list(TIMEFRAME_MAPPING.keys()))
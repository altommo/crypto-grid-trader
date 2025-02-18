import ccxt
from flask import current_app

_exchange = None

def init_exchange(app):
    global _exchange
    with app.app_context():
        print("Initializing exchange connection...")
        config = app.config
        
        exchange_config = {
            'apiKey': config['binance']['api_key'],
            'secret': config['binance']['api_secret'],
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future'
            }
        }
        
        _exchange = ccxt.binance(exchange_config)
        
        if config['binance'].get('testnet', True):
            print("Setting up testnet mode")
            _exchange.set_sandbox_mode(True)
        
        print("Exchange initialization complete")

def get_exchange():
    if _exchange is None:
        raise RuntimeError("Exchange not initialized. Call init_exchange first.")
    return _exchange
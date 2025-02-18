import yaml
import os
from dotenv import load_dotenv

def load_config():
    load_dotenv()
    
    try:
        with open('config.yaml') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config = {
            'binance': {
                'api_key': '',
                'api_secret': '',
                'testnet': True
            },
            'trading': {
                'symbol': 'BTC/USDT',
                'grid_size': 10,
                'grid_spacing': 0.01,
                'position_size': 0.01,
                'max_positions': 5
            }
        }
    
    # Override with environment variables
    config['binance']['api_key'] = os.getenv('BINANCE_API_KEY', config['binance']['api_key'])
    config['binance']['api_secret'] = os.getenv('BINANCE_API_SECRET', config['binance']['api_secret'])
    
    return config
from app.core.exchange import get_exchange, fetch_ticker

class GridStrategy:
    def __init__(self, config):
        self.config = config
        self.exchange = get_exchange()
    
    def calculate_grid_levels(self):
        try:
            ticker = fetch_ticker(self.config['trading']['symbol'])
            current_price = float(ticker['last'])
            
            if 'lower_price' in self.config['trading'] and 'upper_price' in self.config['trading']:
                lower_price = float(self.config['trading']['lower_price'])
                upper_price = float(self.config['trading']['upper_price'])
            else:
                lower_price = current_price * 0.9
                upper_price = current_price * 1.1
            
            grid_levels = self.config['trading']['grid_size']
            step = (upper_price - lower_price) / (grid_levels - 1)
            
            return {
                'current_price': current_price,
                'grid_levels': [{'price': lower_price + i * step} for i in range(grid_levels)]
            }
        except Exception as e:
            raise Exception(f"Error calculating grid levels: {str(e)}")
    
    def update_parameters(self, params):
        self.config['trading'].update({
            'symbol': params['symbol'],
            'grid_size': int(params['gridSize']),
            'grid_spacing': float(params['gridSpacing']),
            'lower_price': float(params['lowerPrice']),
            'upper_price': float(params['upperPrice'])
        })
        return self.config['trading']
    
    def get_parameters(self):
        return {
            'symbol': self.config['trading']['symbol'],
            'gridSize': self.config['trading']['grid_size'],
            'gridSpacing': self.config['trading']['grid_spacing'],
            'lowerPrice': self.config['trading'].get('lower_price', 0),
            'upperPrice': self.config['trading'].get('upper_price', 0)
        }
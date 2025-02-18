# Crypto Grid Trader

A cryptocurrency grid trading application with advanced charting, multiple strategies, and backtesting capabilities.

## Current Features

### Overview Page
- Interactive price chart with multiple timeframes
- Symbol pair selection (Base/Quote currency)
- Grid trading parameter configuration
- Real-time status monitoring

### Chart Features
- Multiple timeframe support (1m to 1M)
- Loading overlay for data updates
- Responsive design
- Custom pair selection

## Recent Updates
- Added loading overlay for chart updates
- Implemented base/quote currency selection
- Extended timeframe options
- Modularized template structure
- Added navigation menu

## Next Steps
1. Implement Strategy Development Page
   - Custom indicator configuration
   - Entry/exit rule creation
   - Position sizing rules

2. Add Backtesting Features
   - Date range selection
   - Parameter optimization
   - Performance metrics

3. Enhance Grid Trading
   - Dynamic grid adjustment
   - Risk management parameters
   - Position tracking

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crypto-grid-trader.git
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run the application:
```bash
python run.py
```

## Project Structure
```
crypto-grid-trader/
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── main.py
│   │   ├── chart.py
│   │   └── strategy.py
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   │       ├── chart.js
│   │       └── overview.js
│   └── templates/
│       ├── base.html
│       └── index.html
├── requirements.txt
└── run.py
```

## Contributing
1. Create a feature branch
2. Make your changes
3. Update documentation
4. Submit a pull request

## License
MIT License - see LICENSE file for details
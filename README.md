# Crypto Grid Trader

Advanced cryptocurrency grid trading system with momentum indicators, backtesting, and web GUI.

## Features

- Grid trading with momentum confirmation
- RSI and MACD indicators
- Backtesting engine
- Web-based GUI
- Risk management system
- Binance integration

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `config.yaml` file with your settings:

```yaml
api_key: 'your_binance_api_key'
api_secret: 'your_binance_api_secret'
use_bnb_fees: true
```

## Running the System

1. Start the web interface:
```bash
python app.py
```

2. Access the dashboard at `http://localhost:5000`

## Documentation

See the `docs/` directory for detailed documentation on:
- Strategy parameters
- Backtesting
- Risk management
- API integration
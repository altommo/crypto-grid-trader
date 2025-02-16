
# Add this at the end of the file

@app.route('/api/historical_data')
def get_historical_data():
    try:
        symbol = config['trading']['symbol']
        timeframe = '1h'  # 1-hour candles
        limit = 1000  # Number of candles to fetch

        # Fetch historical data from the exchange
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

        # Format the data for the chart
        formatted_data = [{
            'time': candle[0] / 1000,  # Convert milliseconds to seconds
            'open': candle[1],
            'high': candle[2],
            'low': candle[3],
            'close': candle[4]
        } for candle in ohlcv]

        return jsonify(formatted_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

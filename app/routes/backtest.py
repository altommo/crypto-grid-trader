from flask import Blueprint, jsonify, request
from app.core.grid_strategy import GridStrategy

backtest_bp = Blueprint('backtest', __name__)

@backtest_bp.route('/', methods=['POST'])
def run_backtest():
    try:
        data = request.json
        days = data.get('days', 30)
        
        # TODO: Implement actual backtesting logic
        # This is a placeholder that returns dummy data
        return jsonify({
            'total_return': 0.05,
            'win_rate': 0.6,
            'total_trades': 100
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
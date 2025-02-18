from flask import Blueprint, jsonify, request

strategy_bp = Blueprint('strategy', __name__)

# Default strategy parameters
DEFAULT_STRATEGY = {
    'symbol': 'BTCUSDT',
    'gridSize': 10,
    'gridSpacing': 1,
    'lowerPrice': 0,
    'upperPrice': 0
}

@strategy_bp.route('/strategy/parameters', methods=['GET'])
def get_strategy_parameters():
    return jsonify(DEFAULT_STRATEGY)

@strategy_bp.route('/strategy/parameters', methods=['POST'])
def update_strategy_parameters():
    try:
        data = request.get_json()
        # Update the strategy parameters 
        for key, value in data.items():
            DEFAULT_STRATEGY[key] = value
        return jsonify({
            'status': 'success', 
            'message': 'Strategy parameters updated',
            'parameters': DEFAULT_STRATEGY
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
from flask import Flask
from app.core.exchange import init_exchange
from app.config.settings import load_config

def create_app():
    print("Creating Flask application...")
    
    app = Flask(__name__)
    
    # Load configuration
    print("Loading configuration...")
    config = load_config()
    app.config.update(config)
    
    # Initialize exchange
    print("Initializing exchange...")
    init_exchange(app)
    
    # Register blueprints
    print("Registering blueprints...")
    from app.routes.main import main_bp
    from app.routes.chart import chart_bp
    from app.routes.strategy import strategy_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(chart_bp, url_prefix='/api')
    app.register_blueprint(strategy_bp, url_prefix='/api')
    
    print(f"Registered routes: {[str(r) for r in app.url_map.iter_rules()]}")
    
    return app
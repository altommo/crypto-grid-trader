from flask import Flask
import os
import sys
from app.core.exchange import init_exchange
from app.config.settings import load_config

def create_app():
    print("Creating Flask application...")
    
    # Explicit and corrected frontend path
    frontend_dir = r'C:\Users\hp\Documents\crypto-grid-trader\crypto-grid-trader\frontend'
    template_dir = os.path.join(frontend_dir, 'templates')
    static_dir = os.path.join(frontend_dir, 'static')
    
    # Validate paths
    print(f"Frontend directory: {frontend_dir}")
    print(f"Template directory: {template_dir}")
    print(f"Static directory: {static_dir}")
    
    # Add more verbose path checking
    if not os.path.exists(frontend_dir):
        raise FileNotFoundError(f"Frontend directory not found: {frontend_dir}")
    
    if not os.path.exists(template_dir):
        raise FileNotFoundError(f"Template directory not found: {template_dir}")
    
    if not os.path.exists(static_dir):
        raise FileNotFoundError(f"Static directory not found: {static_dir}")
    
    # List directory contents for debugging
    print("\nTemplate directory contents:")
    try:
        print(os.listdir(template_dir))
    except Exception as e:
        print(f"Error listing template directory: {e}")
    
    print("\nStatic directory contents:")
    try:
        print(os.listdir(static_dir))
    except Exception as e:
        print(f"Error listing static directory: {e}")
    
    # Create Flask app with explicit template and static folders
    app = Flask(__name__, 
                template_folder=template_dir, 
                static_folder=static_dir)
    
    # Verify template and static folders
    print(f"\nActual template folder: {app.template_folder}")
    print(f"Actual static folder: {app.static_folder}")
    
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
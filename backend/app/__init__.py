from flask import Flask
import os
from app.core.exchange import init_exchange
from app.config.settings import load_config

def create_app():
    print("Creating Flask application...")
    
    # Determine frontend path
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(backend_dir)
    frontend_dir = os.path.join(project_root, 'frontend')
    template_dir = os.path.join(frontend_dir, 'templates')
    static_dir = os.path.join(frontend_dir, 'static')
    
    # Debug print full paths
    print(f"Backend directory: {backend_dir}")
    print(f"Project root: {project_root}")
    print(f"Frontend directory: {frontend_dir}")
    print(f"Template directory: {template_dir}")
    print(f"Static directory: {static_dir}")
    
    # Validate paths exist
    if not os.path.exists(template_dir):
        raise FileNotFoundError(f"Template directory not found: {template_dir}")
    if not os.path.exists(static_dir):
        raise FileNotFoundError(f"Static directory not found: {static_dir}")
    
    # Create Flask app with custom template and static folders
    app = Flask(__name__, 
                template_folder=template_dir, 
                static_folder=static_dir)
    
    # Verify template and static folders
    print(f"Actual template folder: {app.template_folder}")
    print(f"Actual static folder: {app.static_folder}")
    
    # List contents of template and static directories
    print("Template directory contents:")
    print(os.listdir(template_dir))
    print("\nStatic directory contents:")
    print(os.listdir(static_dir))
    
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
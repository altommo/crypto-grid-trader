import os
import sys
import time
import threading
import logging
from typing import Dict, Any, List

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app import create_app
from app.services.tradingview_client import TradingViewClient
from app.utils.validators import DataValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('trading_bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Debugging function to inspect paths
def debug_paths():
    print("\n--- PATH DEBUGGING ---")
    print(f"Current script path: {os.path.abspath(__file__)}")
    print(f"Current working directory: {os.getcwd()}")
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(os.path.dirname(project_root), 'frontend')
    template_dir = os.path.join(frontend_dir, 'templates')
    static_dir = os.path.join(frontend_dir, 'static')
    
    print(f"\nProject Root: {project_root}")
    print(f"Frontend Directory: {frontend_dir}")
    print(f"Template Directory: {template_dir}")
    print(f"Static Directory: {static_dir}")
    
    print("\nTemplate Directory Contents:")
    try:
        print(os.listdir(template_dir))
    except Exception as e:
        print(f"Error listing template directory: {e}")
    
    print("\nStatic Directory Contents:")
    try:
        print(os.listdir(static_dir))
    except Exception as e:
        print(f"Error listing static directory: {e}")
    print("--- END PATH DEBUGGING ---\n")

# Rest of the existing code remains the same
# ... [previous code content] ...

def main():
    """Main application entry point"""
    try:
        # Debugging paths
        debug_paths()
        
        # Create Flask app
        app = create_app()
        
        # Print debug information
        logger.info("Current working directory: %s", os.getcwd())
        logger.info("App template folder: %s", app.template_folder)
        logger.info("App static folder: %s", app.static_folder)
        
        # Rest of the function remains the same
        # ... [previous main function content] ...
        
    except Exception as e:
        logger.error(f"Application startup error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
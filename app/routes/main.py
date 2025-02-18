from flask import Blueprint, render_template
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    print("Rendering base template...")
    template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../templates/base.html'))
    print(f"Template path: {template_path}")
    print(f"Template exists: {os.path.exists(template_path)}")
    return render_template('base.html')
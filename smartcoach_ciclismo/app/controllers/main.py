from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Usa Flask render_template, pasándole HTML en duro temporalmente
    return render_template('base.html')
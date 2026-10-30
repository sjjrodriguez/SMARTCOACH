from datetime import date, timedelta

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.models.workout import Workout
from app.services.dashboard_service import build_dashboard_data

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    # 8 semanas cubren la serie semanal y las 4 semanas previas del semaforo
    since = date.today() - timedelta(days=7 * 8)
    workouts = (Workout.query
                .filter(Workout.user_id == current_user.id, Workout.date >= since)
                .order_by(Workout.date)
                .all())
    return render_template('dashboard/index.html', data=build_dashboard_data(workouts))
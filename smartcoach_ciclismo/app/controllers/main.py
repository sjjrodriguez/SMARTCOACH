from datetime import date, timedelta

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.models.workout import Workout
from app.services.dashboard_service import build_dashboard_data
from app.services.methodology_service import build_methodology_data
from app.services.routine_service import find_day

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
    return render_template('dashboard/index.html', data=build_dashboard_data(workouts),
                           today_plan=_today_session())


@main_bp.route('/phases')
def phases():
    """Public page 1 of 3: CRISP-DM / CRISP-ML(Q) phases."""
    return render_template('about/phases.html', data=build_methodology_data())


@main_bp.route('/architecture')
def architecture():
    """Public page 2 of 3: the 4-layer architecture."""
    return render_template('about/architecture.html', data=build_methodology_data())


@main_bp.route('/project-document')
def project_document():
    """Public page 3 of 3: models, evaluation and changes."""
    return render_template('about/project_document.html', data=build_methodology_data())


def _today_session():
    """Today's planned session and the plan-change suggestion, from the latest plan."""
    from app.controllers.plans import latest_plan, plan_snapshot
    plan = latest_plan(current_user.id)
    if plan is None:
        return None
    routine, review = plan_snapshot(plan)
    day = find_day(routine, date.today().isoformat())
    spec = routine['sessions'][day['key']] if day else None
    return {'plan_id': plan.id, 'day': day, 'spec': spec, 'level': routine['level_name'],
            'suggestion': review['suggestion']}

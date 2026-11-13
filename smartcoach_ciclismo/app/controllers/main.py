from datetime import date, timedelta

from flask import Blueprint, abort, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.models.workout import Workout
from app.services.crisp_content import PHASE_PAGES, STATUS_LABEL, class_distribution, get_phase, phase_menu
from app.services.dashboard_service import build_dashboard_data
from app.services.methodology_service import build_methodology_data
from app.services.routine_service import find_day

main_bp = Blueprint('main', __name__)


def _docs(**extra):
    """Context shared by the documentation pages (they use their own top bar)."""
    ctx = {'docs_mode': True, 'crisp_menu': phase_menu()}
    ctx.update(extra)
    return ctx


@main_bp.route('/')
def index():
    """The documentation comes first: the site opens on phase 1. The application is reached with "Open SmartCoach"."""
    return redirect(url_for('main.crisp_phase', slug=PHASE_PAGES[0]['slug']))


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
    """Old address of the phases page; the phases now live in the CRISP-DM menu."""
    return redirect(url_for('main.index'))


@main_bp.route('/crisp-dm/<slug>')
def crisp_phase(slug):
    """One page per CRISP-DM / CRISP-ML(Q) phase."""
    phase, prev_phase, next_phase = get_phase(slug)
    if phase is None:
        abort(404)
    return render_template('about/phase.html', **_docs(
        phase=phase, prev_phase=prev_phase, next_phase=next_phase,
        status_label=STATUS_LABEL, data=build_methodology_data(), class_dist=class_distribution()))


@main_bp.route('/architecture')
def architecture():
    """The 4-layer architecture."""
    return render_template('about/architecture.html', **_docs(data=build_methodology_data()))


@main_bp.route('/project-document')
def project_document():
    """Models, evaluation and the changes of this iteration."""
    return render_template('about/project_document.html', **_docs(data=build_methodology_data()))


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

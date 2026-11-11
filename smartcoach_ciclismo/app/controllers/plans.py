from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models.injury import InjuryCheckin
from app.models.plan import TrainingPlan
from app.models.workout import Workout
from app.services.ml_service import PLAN_DESCRIPTIONS, PLAN_LEVELS, ml_predictor
from app.services.progress_service import evaluate_plan
from app.services.routine_service import build_routine

plans_bp = Blueprint('plans', __name__, url_prefix='/plans')

PLAN_DAYS = 28
MIN_AGE, MAX_AGE = 10, 90

# (field, label, min, max, type). Age is not asked: it is calculated from the date of birth.
PLAN_FIELDS = [
    ('weight_kg', 'Weight (kg)', 30, 200, float),
    ('weekly_hours', 'Hours per week', 0.5, 40, float),
    ('resting_heart_rate', 'Resting heart rate (bpm)', 30, 120, int),
    ('tss_acumulado', 'Accumulated TSS', 0, 50000, float),
]


def age_on(born, today):
    """Whole years between a date of birth and a given day."""
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def _birth_limits():
    """Earliest / latest birth dates the form accepts (ages 90 and 10)."""
    t = date.today()
    def years_ago(n):
        try:
            return t.replace(year=t.year - n)
        except ValueError:  # Feb 29
            return t.replace(year=t.year - n, day=28)
    return {'min_birth': years_ago(MAX_AGE).isoformat(), 'max_birth': years_ago(MIN_AGE).isoformat()}


def _parse_birth_date(form):
    raw = (form.get('birth_date') or '').strip()
    try:
        born = date.fromisoformat(raw)
    except ValueError:
        return None, None, 'Date of birth: enter a valid date.'
    age = age_on(born, date.today())
    if born > date.today() or not MIN_AGE <= age <= MAX_AGE:
        return None, None, f'Your age must be between {MIN_AGE} and {MAX_AGE} years.'
    return born, age, None


def _parse_plan_form(form):
    values, errors = {}, []
    for name, label, lo, hi, cast in PLAN_FIELDS:
        raw = (form.get(name) or '').strip().replace(',', '.')
        try:
            v = cast(float(raw)) if cast is int else cast(raw)
        except ValueError:
            errors.append(f'{label}: enter a number.')
            continue
        if not lo <= v <= hi:
            errors.append(f'{label} must be between {lo} and {hi}.')
        values[name] = v
    return values, errors


def latest_plan(user_id):
    return (TrainingPlan.query.filter_by(user_id=user_id)
            .order_by(TrainingPlan.created_at.desc(), TrainingPlan.id.desc()).first())


def _plan_workouts(plan):
    return Workout.query.filter(Workout.user_id == plan.user_id, Workout.date >= plan.start_date,
                                Workout.date <= plan.end_date).all()


def routine_for_plan(plan, workouts=None):
    """Build the plan's routine; workouts logged on a planned date tick it off."""
    workouts = _plan_workouts(plan) if workouts is None else workouts
    return build_routine(plan, logged_dates={w.date for w in workouts})


def plan_snapshot(plan):
    """Routine + performance evaluation for a plan (one workouts query)."""
    workouts = _plan_workouts(plan)
    routine = routine_for_plan(plan, workouts)
    since = min(plan.start_date, date.today() - timedelta(days=14))
    checkins = InjuryCheckin.query.filter(InjuryCheckin.user_id == plan.user_id,
                                          InjuryCheckin.date >= since).all()
    return routine, evaluate_plan(plan, routine, workouts, checkins)


def _clone_plan(plan, level, reason=None):
    """A new 4-week plan that keeps the cyclist's data but changes level.

    This is the only way a plan changes after the first generation.
    """
    today = date.today()
    new = TrainingPlan(
        user_id=plan.user_id, start_date=today, end_date=today + timedelta(days=PLAN_DAYS),
        birth_date=plan.birth_date,
        age=age_on(plan.birth_date, today) if plan.birth_date else plan.age,
        weight_kg=plan.weight_kg, weekly_hours=plan.weekly_hours,
        resting_heart_rate=plan.resting_heart_rate, tss_acumulado=plan.tss_acumulado,
        plan_label=PLAN_LEVELS[level], description=PLAN_DESCRIPTIONS[level], change_reason=reason)
    db.session.add(new)
    db.session.commit()
    return new


@plans_bp.route('/')
@login_required
def current_plan():
    """Navbar entry: your plan if you have one, otherwise the generator."""
    plan = latest_plan(current_user.id)
    if plan:
        return redirect(url_for('plans.view_plan', plan_id=plan.id))
    return redirect(url_for('plans.generate_plan'))


@plans_bp.route('/generate', methods=['GET', 'POST'])
@login_required
def generate_plan():
    # The model builds your plan once. After that it only changes through the
    # performance review (see switch_plan / next_cycle).
    existing = latest_plan(current_user.id)
    if existing:
        flash('You already have a training plan. It changes only when your performance review suggests it.', 'info')
        return redirect(url_for('plans.view_plan', plan_id=existing.id))

    if request.method == 'GET':
        return render_template('plans/generate.html', values={}, **_birth_limits())

    values, errors = _parse_plan_form(request.form)
    born, age, err = _parse_birth_date(request.form)
    if err:
        errors.insert(0, err)
    if errors:
        for e in errors:
            flash(e, 'danger')
        return render_template('plans/generate.html', values=request.form, **_birth_limits()), 400

    try:
        _, label, description = ml_predictor.predict_training_plan(
            age=age, weight=values['weight_kg'],
            weekly_hours=values['weekly_hours'],
            resting_hr=values['resting_heart_rate'], tss=values['tss_acumulado'])
    except Exception as e:
        flash(f'Could not run the model: {e}', 'danger')
        return render_template('plans/generate.html', values=request.form, **_birth_limits()), 500

    plan = TrainingPlan(
        user_id=current_user.id, birth_date=born, age=age,
        start_date=date.today(), end_date=date.today() + timedelta(days=PLAN_DAYS),
        plan_label=label, description=description, **values)
    db.session.add(plan)
    db.session.commit()
    return redirect(url_for('plans.view_plan', plan_id=plan.id))


def _owned_plan_or_404(plan_id):
    plan = db.session.get(TrainingPlan, plan_id)
    if plan is None or plan.user_id != current_user.id:
        abort(404)
    return plan


@plans_bp.route('/<int:plan_id>')
@login_required
def view_plan(plan_id):
    plan = _owned_plan_or_404(plan_id)
    routine, review = plan_snapshot(plan)
    is_latest = latest_plan(current_user.id).id == plan.id
    # Link every ride to the log form, prefilled with that day's targets.
    for week in routine['weeks']:
        for day in week['days']:
            if not day['is_rest']:
                day['log_url'] = url_for('workouts.create_workout', plan_id=plan.id, date=day['date'])
    client = {k: routine[k] for k in ('weeks', 'sessions', 'selected')}
    return render_template('plans/view.html', plan=plan, routine=routine, client=client,
                           review=review, is_latest=is_latest, cycle_over=date.today() >= plan.end_date)


@plans_bp.route('/<int:plan_id>/switch', methods=['POST'])
@login_required
def switch_plan(plan_id):
    """Move one level up or down. Only allowed when the performance review says so."""
    plan = _owned_plan_or_404(plan_id)
    if latest_plan(current_user.id).id != plan.id:
        abort(404)
    _, review = plan_snapshot(plan)
    suggestion = review['suggestion']
    if not suggestion or suggestion['direction'] != request.form.get('direction'):
        flash('Your stats do not currently support a plan change.', 'warning')
        return redirect(url_for('plans.view_plan', plan_id=plan.id))

    reason = (f"Moved {suggestion['direction']} from the {suggestion['from_name']} plan on "
              f"{date.today():%b} {date.today().day}. {suggestion['reason']}")
    new = _clone_plan(plan, suggestion['to_level'], reason)
    flash(f"You are now on the {suggestion['to_name']} plan. A new 4-week cycle starts today.", 'success')
    return redirect(url_for('plans.view_plan', plan_id=new.id))


@plans_bp.route('/<int:plan_id>/next-cycle', methods=['POST'])
@login_required
def next_cycle(plan_id):
    """When the 4 weeks end, keep going at the same level (no new prediction)."""
    from app.services.routine_service import level_from_label
    plan = _owned_plan_or_404(plan_id)
    if latest_plan(current_user.id).id != plan.id or date.today() < plan.end_date:
        flash('Your current cycle is still in progress.', 'warning')
        return redirect(url_for('plans.view_plan', plan_id=plan.id))
    new = _clone_plan(plan, level_from_label(plan.plan_label))
    flash('A new 4-week cycle started at the same level.', 'success')
    return redirect(url_for('plans.view_plan', plan_id=new.id))

from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from app import db
from app.models.workout import Workout
from app.models.injury import InjuryCheckin
from app.models.plan import TrainingPlan
from app.services.injury_service import ValidationError, injury_predictor, parse_checkin
from app.services.routine_service import find_day

workouts_bp = Blueprint('workouts', __name__, url_prefix='/workouts')


def _owned_plan(plan_id):
    """The cyclist's own plan for ?plan_id=, or None."""
    try:
        plan = db.session.get(TrainingPlan, int(plan_id))
    except (TypeError, ValueError):
        return None
    return plan if plan and plan.user_id == current_user.id else None


def _planned_session(plan, iso_date):
    """Targets for a planned ride (used to prefill the log form), or None."""
    from app.controllers.plans import routine_for_plan
    routine = routine_for_plan(plan)
    day = find_day(routine, iso_date or '')
    if day is None or day['is_rest']:
        return None
    spec = routine['sessions'][day['key']]
    return {'plan_id': plan.id, 'date': day['date'], 'label': day['label'], 'title': spec['title'],
            'effort': spec['effort'], 'rpe': spec['rpe'], 'minutes': day['minutes'], 'km': day['km']}

def _check_data(form, duration_min, rpe, fatigue):
    """Inputs for the injury check, taken from the workout form.

    The check is no longer a separate page: it is filled in from the workout.
    Effort (RPE), duration and fatigue come from the workout itself, so the
    cyclist only answers recovery, sleep and (optionally) heart rate in the
    "Injury check" tab of the form.
    Returns None for sessions too short for the model (under 5 minutes).
    Raises ValidationError when an answer is missing or out of range.
    """
    if duration_min < 5:
        return None
    return parse_checkin({
        'recovery_score': form.get('recovery_score'),
        'sleep_quality': form.get('sleep_quality'),
        'heart_rate': form.get('heart_rate'),
        'fatigue_index': str(fatigue * 10),          # 1-10 fatigue -> 10-100 index
        'training_intensity': str(rpe),
        'training_duration': str(min(duration_min, 600)),
    })


def _run_daily_check(check_data, workout_date):
    """Predict injury risk and save the check-in. Returns the record or None."""
    try:
        level, probs = injury_predictor.predict(check_data)
        record = InjuryCheckin(
            user_id=current_user.id, date=workout_date, risk_level=level,
            prob_low=probs.get('Low'), prob_medium=probs.get('Medium'), prob_high=probs.get('High'),
            **check_data)
        db.session.add(record)
        db.session.commit()
        return record
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Could not run the daily injury check')
        return None


# 1. READ: List all workout entries for the current cyclist
@workouts_bp.route('/', methods=['GET'])
@login_required
def list_workouts():
    workouts = Workout.query.filter_by(user_id=current_user.id).order_by(Workout.date.desc()).all()
    return render_template('workouts/list.html', workouts=workouts)

# 2. CREATE: Record a new workout session
@workouts_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_workout():
    if request.method == 'POST':
        try:
            date_str = request.form.get('date')
            workout_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
            duration_min = int(request.form.get('duration_min'))
            distance_km = float(request.form.get('distance_km'))
            elevation_gain_m = float(request.form.get('elevation_gain_m') or 0.0)
            rpe = int(request.form.get('rpe'))
            fatigue = int(request.form.get('perceived_fatigue') or 1)
            notes = request.form.get('notes', '')
            # Validate the injury-check answers first so nothing is half saved.
            check_data = _check_data(request.form, duration_min, rpe, fatigue)

            new_workout = Workout(
                user_id=current_user.id,
                date=workout_date,
                duration_min=duration_min,
                distance_km=distance_km,
                elevation_gain_m=elevation_gain_m,
                rpe=rpe,
                perceived_fatigue=fatigue,
                notes=notes
            )
            db.session.add(new_workout)
            db.session.commit()

            flash('Training session logged successfully.', 'success')
            plan = _owned_plan(request.form.get('plan_id'))

            # Injury check, run automatically right after the workout is saved.
            record = _run_daily_check(check_data, workout_date) if check_data else None
            if record:
                return redirect(url_for('injury.result', checkin_id=record.id,
                                        plan_id=plan.id if plan else None))
            if check_data:
                flash('Your workout was saved, but the injury check could not be calculated.', 'warning')
            if plan:
                return redirect(url_for('plans.view_plan', plan_id=plan.id))
            return redirect(url_for('workouts.list_workouts'))
        except ValidationError as e:
            db.session.rollback()
            flash(str(e), 'danger')
        except (TypeError, ValueError):
            db.session.rollback()
            flash('Please check the values you entered and try again.', 'danger')
        except Exception:
            db.session.rollback()
            current_app.logger.exception('Error saving workout')
            flash('Could not save the workout. Please try again.', 'danger')

    plan = _owned_plan(request.values.get('plan_id'))
    planned = _planned_session(plan, request.values.get('date')) if plan else None
    if request.method == 'POST':
        values = request.form
    elif planned:
        values = {'date': planned['date'], 'duration_min': planned['minutes'],
                  'distance_km': planned['km'], 'rpe': planned['rpe']}
    else:
        values = {'date': date.today().isoformat()}
    return render_template('workouts/create.html', values=values, planned=planned)

# 3. UPDATE: Edit an existing workout session
@workouts_bp.route('/<int:workout_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    if workout.user_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        try:
            date_str = request.form.get('date')
            workout.date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else workout.date
            workout.duration_min = int(request.form.get('duration_min'))
            workout.distance_km = float(request.form.get('distance_km'))
            workout.elevation_gain_m = float(request.form.get('elevation_gain_m') or 0.0)
            workout.rpe = int(request.form.get('rpe'))
            workout.perceived_fatigue = int(request.form.get('perceived_fatigue') or 1)
            workout.notes = request.form.get('notes', '')

            db.session.commit()
            flash('Workout updated successfully.', 'success')
            return redirect(url_for('workouts.list_workouts'))
        except (TypeError, ValueError):
            db.session.rollback()
            flash('Please check the values you entered and try again.', 'danger')
        except Exception:
            db.session.rollback()
            current_app.logger.exception('Error updating workout')
            flash('Could not update the workout. Please try again.', 'danger')

    values = request.form if request.method == 'POST' else None
    return render_template('workouts/edit.html', workout=workout, values=values)

# 4. DELETE: Remove a workout entry
@workouts_bp.route('/<int:workout_id>/delete', methods=['POST'])
@login_required
def delete_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    if workout.user_id != current_user.id:
        abort(403)

    db.session.delete(workout)
    db.session.commit()
    flash('Workout deleted successfully.', 'info')
    return redirect(url_for('workouts.list_workouts'))
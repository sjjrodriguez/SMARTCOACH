from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.workout import Workout

workouts_bp = Blueprint('workouts', __name__, url_prefix='/workouts')

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
            elevation_gain_m = float(request.form.get('elevation_gain_m', 0.0))
            rpe = int(request.form.get('rpe'))
            fatigue = int(request.form.get('perceived_fatigue', 1))
            notes = request.form.get('notes', '')

            # Approximate TSS computation based on duration and RPE
            estimated_tss = (duration_min * rpe * 1.1) / 10[cite: 5]

            new_workout = Workout(
                user_id=current_user.id,
                date=workout_date,
                duration_min=duration_min,
                distance_km=distance_km,
                elevation_gain_m=elevation_gain_m,
                rpe=rpe,
                perceived_fatigue=fatigue,
                estimated_tss=round(estimated_tss, 2),
                notes=notes
            )
            db.session.add(new_workout)
            db.session.commit()

            flash('Training session logged successfully.', 'success')
            return redirect(url_for('workouts.list_workouts'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving workout: {str(e)}', 'danger')

    return render_template('workouts/create.html')

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
            workout.elevation_gain_m = float(request.form.get('elevation_gain_m', 0.0))
            workout.rpe = int(request.form.get('rpe'))
            workout.perceived_fatigue = int(request.form.get('perceived_fatigue', 1))
            workout.notes = request.form.get('notes', '')
            workout.estimated_tss = round((workout.duration_min * workout.rpe * 1.1) / 10, 2)[cite: 5]

            db.session.commit()
            flash('Workout updated successfully.', 'success')
            return redirect(url_for('workouts.list_workouts'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating workout: {str(e)}', 'danger')

    return render_template('workouts/edit.html', workout=workout)

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
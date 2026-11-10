from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models.plan import TrainingPlan
from app.services.ml_service import ml_predictor

plans_bp = Blueprint('plans', __name__, url_prefix='/plans')

# (field, label, min, max, type)
PLAN_FIELDS = [
    ('age', 'Age', 10, 90, int),
    ('weight_kg', 'Weight (kg)', 30, 200, float),
    ('weekly_hours', 'Hours per week', 0.5, 40, float),
    ('resting_heart_rate', 'Resting heart rate (bpm)', 30, 120, int),
    ('tss_acumulado', 'Accumulated TSS', 0, 50000, float),
]


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


@plans_bp.route('/generate', methods=['GET', 'POST'])
@login_required
def generate_plan():
    if request.method == 'GET':
        last = (TrainingPlan.query.filter_by(user_id=current_user.id)
                .order_by(TrainingPlan.created_at.desc()).first())
        return render_template('plans/generate.html', last=last, values={})

    values, errors = _parse_plan_form(request.form)
    if errors:
        for e in errors:
            flash(e, 'danger')
        return render_template('plans/generate.html', last=None, values=request.form), 400

    try:
        _, label, description = ml_predictor.predict_training_plan(
            age=values['age'], weight=values['weight_kg'],
            weekly_hours=values['weekly_hours'],
            resting_hr=values['resting_heart_rate'], tss=values['tss_acumulado'])
    except Exception as e:
        flash(f'Could not run the model: {e}', 'danger')
        return render_template('plans/generate.html', last=None, values=request.form), 500

    plan = TrainingPlan(
        user_id=current_user.id,
        start_date=date.today(), end_date=date.today() + timedelta(days=28),
        plan_label=label, description=description, **values)
    db.session.add(plan)
    db.session.commit()
    return redirect(url_for('plans.view_plan', plan_id=plan.id))


@plans_bp.route('/<int:plan_id>')
@login_required
def view_plan(plan_id):
    plan = db.session.get(TrainingPlan, plan_id)
    if plan is None or plan.user_id != current_user.id:
        abort(404)
    datos = {
        'Age': f'{plan.age} years',
        'Weight': f'{plan.weight_kg} kg',
        'Availability': f'{plan.weekly_hours} h/week',
        'Resting heart rate': f'{plan.resting_heart_rate} bpm',
        'Base TSS': plan.tss_acumulado,
    }
    return render_template('plans/view.html', recomendacion=plan.plan_label,
                           descripcion=plan.description, datos=datos, plan=plan)

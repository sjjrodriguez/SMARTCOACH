from datetime import date, timedelta
from flask import Blueprint, render_template, request, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models.injury import InjuryCheckin
from app.models.plan import TrainingPlan
from app.services.injury_service import (
    injury_predictor, ValidationError, RISK_TEXT, LEVEL_CSS)
from app.services.injury_cyclist_service import parse_profile, predict_injury

injury_bp = Blueprint('injury', __name__, url_prefix='/injury')


@injury_bp.route('/')
@login_required
def index():
    since = date.today() - timedelta(days=30)
    checkins = (InjuryCheckin.query
                .filter(InjuryCheckin.user_id == current_user.id, InjuryCheckin.date >= since)
                .order_by(InjuryCheckin.date.desc(), InjuryCheckin.id.desc()).all())
    chart = {
        'labels': [c.date.strftime('%b %d') for c in reversed(checkins)],
        'recovery': [c.recovery_score for c in reversed(checkins)],
        'fatigue': [c.fatigue_index for c in reversed(checkins)],
    }
    return render_template('injury/index.html', checkins=checkins, chart=chart,
                           risk_text=RISK_TEXT, level_css=LEVEL_CSS)


@injury_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Cyclist model: probability of a previous injury based on the profile."""
    if request.method == 'GET':
        return render_template('injury/profile.html', values={}, result=None)

    try:
        data = parse_profile(request.form)
        result = predict_injury(data)
    except ValidationError as e:
        flash(str(e), 'danger')
        return render_template('injury/profile.html', values=request.form, result=None), 400
    except Exception as e:
        flash(f'Could not calculate the profile result: {e}', 'danger')
        return render_template('injury/profile.html', values=request.form, result=None), 500
    return render_template('injury/profile.html', values=request.form, result=result)


@injury_bp.route('/<int:checkin_id>')
@login_required
def result(checkin_id):
    record = db.session.get(InjuryCheckin, checkin_id)
    if record is None or record.user_id != current_user.id:
        abort(404)
    label, message = RISK_TEXT[record.risk_level]
    data = {k: getattr(record, k) for k in
            ('recovery_score', 'fatigue_index', 'sleep_quality', 'training_intensity', 'training_duration')}
    # Coming from a plan's "Log this ride": offer a way back.
    plan = db.session.get(TrainingPlan, request.args.get('plan_id', type=int) or 0)
    back_plan_id = plan.id if plan and plan.user_id == current_user.id else None
    return render_template('injury/result.html', c=record, label=label, message=message,
                           back_plan_id=back_plan_id, css=LEVEL_CSS[record.risk_level],
                           tips=injury_predictor.recommendations(data))

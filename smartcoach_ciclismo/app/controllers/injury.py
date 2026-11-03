from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models.injury import InjuryCheckin
from app.services.injury_service import (
    injury_predictor, parse_checkin, ValidationError, RISK_TEXT, LEVEL_CSS)

injury_bp = Blueprint('injury', __name__, url_prefix='/injury')


@injury_bp.route('/')
@login_required
def index():
    since = date.today() - timedelta(days=30)
    checkins = (InjuryCheckin.query
                .filter(InjuryCheckin.user_id == current_user.id, InjuryCheckin.date >= since)
                .order_by(InjuryCheckin.date.desc(), InjuryCheckin.id.desc()).all())
    chart = {
        'labels': [c.date.strftime('%d/%m') for c in reversed(checkins)],
        'recovery': [c.recovery_score for c in reversed(checkins)],
        'fatigue': [c.fatigue_index for c in reversed(checkins)],
    }
    return render_template('injury/index.html', checkins=checkins, chart=chart,
                           risk_text=RISK_TEXT, level_css=LEVEL_CSS)


@injury_bp.route('/checkin', methods=['GET', 'POST'])
@login_required
def checkin():
    if request.method == 'GET':
        return render_template('injury/checkin.html', values={})

    try:
        data = parse_checkin(request.form)
        level, probs = injury_predictor.predict(data)
    except ValidationError as e:
        flash(str(e), 'danger')
        return render_template('injury/checkin.html', values=request.form), 400
    except Exception as e:
        flash(f'No se pudo calcular el riesgo: {e}', 'danger')
        return render_template('injury/checkin.html', values=request.form), 500

    record = InjuryCheckin(
        user_id=current_user.id, date=date.today(), risk_level=level,
        prob_low=probs.get('Low'), prob_medium=probs.get('Medium'), prob_high=probs.get('High'),
        **data)
    db.session.add(record)
    db.session.commit()
    return redirect(url_for('injury.result', checkin_id=record.id))


@injury_bp.route('/<int:checkin_id>')
@login_required
def result(checkin_id):
    record = db.session.get(InjuryCheckin, checkin_id)
    if record is None or record.user_id != current_user.id:
        abort(404)
    label, message = RISK_TEXT[record.risk_level]
    data = {k: getattr(record, k) for k in
            ('recovery_score', 'fatigue_index', 'sleep_quality', 'training_intensity', 'training_duration')}
    return render_template('injury/result.html', c=record, label=label, message=message,
                           css=LEVEL_CSS[record.risk_level],
                           tips=injury_predictor.recommendations(data))

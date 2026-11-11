from datetime import datetime
from app import db


class TrainingPlan(db.Model):
    __tablename__ = 'training_plans'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_volume_km = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(30), default='Active')

    # Datos que el ciclista ingresó al pedir el plan (los 5 del modelo)
    # Date of birth is what the cyclist enters; age is the snapshot used by the model.
    birth_date = db.Column(db.Date, nullable=True)
    age = db.Column(db.Integer, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    weekly_hours = db.Column(db.Float, nullable=False)
    resting_heart_rate = db.Column(db.Integer, nullable=False)
    tss_acumulado = db.Column(db.Float, nullable=False, default=0.0)

    # Resultado del modelo
    plan_label = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)
    # Set when this plan came from a performance-based change (not from the form).
    change_reason = db.Column(db.Text, nullable=True)

    daily_sessions = db.relationship('PlanDayDetail', backref='plan', lazy='dynamic')


class PlanDayDetail(db.Model):
    __tablename__ = 'plan_day_details'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('training_plans.id'), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False)
    session_type = db.Column(db.String(60), nullable=False)
    suggested_duration_min = db.Column(db.Integer, nullable=False)
    target_distance_km = db.Column(db.Float, default=0.0)
    is_completed = db.Column(db.Boolean, default=False)

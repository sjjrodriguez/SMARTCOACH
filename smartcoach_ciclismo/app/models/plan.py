from datetime import datetime
from app import db

class TrainingPlan(db.Model):
    __tablename__ = 'training_plans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_volume_km = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(30), default='Active')        # Active, Completed[cite: 4]

    daily_sessions = db.relationship('PlanDayDetail', backref='plan', lazy='dynamic', cascade='all, delete-orphan')

class PlanDayDetail(db.Model):
    __tablename__ = 'plan_day_details'

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('training_plans.id'), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False)     # Monday, Tuesday, etc.
    session_type = db.Column(db.String(60), nullable=False)    # Endurance, Intervals, Recovery, Rest[cite: 4]
    suggested_duration_min = db.Column(db.Integer, nullable=False)
    target_distance_km = db.Column(db.Float, default=0.0)
    is_completed = db.Column(db.Boolean, default=False)
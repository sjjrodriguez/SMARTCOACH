from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # 5 Datos Clave para el Plan de Entrenamiento
    age = db.Column(db.Integer, nullable=False, default=18)
    weight_kg = db.Column(db.Float, nullable=False, default=70.0)
    weekly_hours = db.Column(db.Float, nullable=False, default=5.0)
    resting_heart_rate = db.Column(db.Integer, nullable=False, default=60)
    tss_acumulado = db.Column(db.Float, nullable=False, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    workouts = db.relationship('Workout', backref='author', lazy='dynamic')
    training_plans = db.relationship('TrainingPlan', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(db.Model, UserMixin):
    """Cuenta de acceso: solo nombre, correo y contraseña.

    Los datos fisiológicos ya NO se piden al registrarse: se piden al generar
    un plan (se guardan en TrainingPlan) y al hacer el seguimiento de lesiones
    (se guardan en InjuryCheckin).
    """
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    workouts = db.relationship('Workout', backref='author', lazy='dynamic')
    training_plans = db.relationship('TrainingPlan', backref='user', lazy='dynamic')
    injury_checkins = db.relationship('InjuryCheckin', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

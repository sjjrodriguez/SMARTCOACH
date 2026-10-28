from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Biometric & Cycling Profiles
    age = db.Column(db.Integer, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    height_cm = db.Column(db.Float, nullable=True)
    discipline = db.Column(db.String(50), default='Road')     # Road, Track, MTB[cite: 4]
    level = db.Column(db.String(50), default='Amateur')       # Recreational, Amateur, Elite[cite: 4]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    workouts = db.relationship('Workout', backref='cyclist', lazy='dynamic', cascade='all, delete-orphan')
    plans = db.relationship('TrainingPlan', backref='cyclist', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.full_name} - {self.email}>"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
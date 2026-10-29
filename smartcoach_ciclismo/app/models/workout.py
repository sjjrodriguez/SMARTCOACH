from datetime import datetime
from app import db

class Workout(db.Model):
    __tablename__ = 'workouts'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    duration_min = db.Column(db.Integer, nullable=False)
    distance_km = db.Column(db.Float, nullable=False)
    elevation_gain_m = db.Column(db.Float, nullable=True, default=0.0)
    rpe = db.Column(db.Integer, nullable=False)
    perceived_fatigue = db.Column(db.Integer, nullable=True, default=1)
    estimated_tss = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Workout {self.date} - {self.distance_km}km>"
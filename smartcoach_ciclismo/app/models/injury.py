from datetime import date, datetime
from app import db


class InjuryCheckin(db.Model):
    """Chequeo de seguimiento: variables que más pesan en el modelo de lesiones."""
    __tablename__ = 'injury_checkins'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Estado diario (las 3 variables más importantes del dataset)
    recovery_score = db.Column(db.Integer, nullable=False)   # 0-100
    fatigue_index = db.Column(db.Integer, nullable=False)    # 0-100
    sleep_quality = db.Column(db.Float, nullable=False)      # 1-10

    # Sesión del día
    training_intensity = db.Column(db.Integer, nullable=False)  # RPE 1-10
    training_duration = db.Column(db.Integer, nullable=False)   # min
    heart_rate = db.Column(db.Integer, nullable=True)           # FC media (opcional)

    # Resultado
    risk_level = db.Column(db.String(10), nullable=False)       # Low / Medium / High
    prob_low = db.Column(db.Float)
    prob_medium = db.Column(db.Float)
    prob_high = db.Column(db.Float)

    @property
    def training_load(self):
        return self.training_intensity * self.training_duration

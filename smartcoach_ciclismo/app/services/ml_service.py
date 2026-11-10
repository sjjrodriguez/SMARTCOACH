import os
import joblib
import pandas as pd

ARTIFACTS = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ml_engine/model_artifacts'))

# Mismo orden y nombres con los que se entrenó el escalador (train_model.py)
FEATURES = ["age", "weight_kg", "weekly_hours", "resting_heart_rate", "tss_acumulado"]

PLAN_LEVELS = {
    0: "Beginner Plan - Base Conditioning",
    1: "Moderate Plan - Development and Threshold",
    2: "Advanced Plan - High Performance",
}

PLAN_DESCRIPTIONS = {
    0: "Focus on building an aerobic base. Easy-paced rides of 1 to 2 hours "
       "to get your body used to training and help prevent injuries.",
    1: "Focus on improving your cruising speed. Balances aerobic endurance "
       "(Zone 2) with lactate-threshold work.",
    2: "High-load structure. Includes 2 days of explosive intervals (VO2 Max) "
       "and rides of more than 4 hours.",
}


class MLService:
    """Clasificador de plan de entrenamiento (5 variables). Carga perezosa:
    si faltan los artefactos la app arranca igual y el error aparece al usarlo."""

    def __init__(self):
        self.model = None
        self.scaler = None

    def _load(self):
        if self.model is None or self.scaler is None:
            model_path = os.path.join(ARTIFACTS, 'model.joblib')
            scaler_path = os.path.join(ARTIFACTS, 'scaler.joblib')
            if not (os.path.exists(model_path) and os.path.exists(scaler_path)):
                raise FileNotFoundError("Training plan model files not found. Run ml_engine/train_model.py")
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)

    def predict_training_plan(self, age, weight, weekly_hours, resting_hr, tss):
        """Devuelve (clase, etiqueta, descripcion)."""
        self._load()
        features = pd.DataFrame([[age, weight, weekly_hours, resting_hr, tss]], columns=FEATURES)
        cls = int(self.model.predict(self.scaler.transform(features))[0])
        return cls, PLAN_LEVELS.get(cls, PLAN_LEVELS[0]), PLAN_DESCRIPTIONS.get(cls, PLAN_DESCRIPTIONS[0])


ml_predictor = MLService()

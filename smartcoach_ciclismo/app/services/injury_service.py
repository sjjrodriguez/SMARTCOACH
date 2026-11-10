"""Seguimiento y prevención de lesiones: predicción de riesgo + recomendaciones."""
import json
import os
import joblib
import pandas as pd

ARTIFACTS = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ml_engine/model_artifacts'))

# Rangos aceptados por el formulario (coinciden con los usados al entrenar)
LIMITS = {
    "recovery_score":     (0, 100),
    "fatigue_index":      (0, 100),
    "sleep_quality":      (1, 10),
    "training_intensity": (1, 10),
    "training_duration":  (5, 600),
    "heart_rate":         (30, 220),
}

# Field names shown to the user in validation messages
LABELS = {
    "recovery_score":     "Recovery",
    "fatigue_index":      "Fatigue",
    "sleep_quality":      "Sleep quality",
    "training_intensity": "Effort (RPE)",
    "training_duration":  "Duration",
    "heart_rate":         "Average heart rate",
}

RISK_TEXT = {
    "Low":    ("Low risk", "Today's condition matches your training load. Keep following your plan."),
    "Medium": ("Medium risk", "There are signs of overload. Reduce intensity and prioritize sleep and recovery."),
    "High":   ("High risk", "High probability of injury. Rest or do a very easy session, and consult your coach or physiotherapist if you feel any pain."),
}
LEVEL_CSS = {"Low": "low", "Medium": "med", "High": "high"}


class ValidationError(ValueError):
    pass


def parse_checkin(form):
    """Valida el formulario. Devuelve dict limpio o lanza ValidationError."""
    clean = {}
    for field, (lo, hi) in LIMITS.items():
        raw = (form.get(field) or "").strip()
        if raw == "":
            if field == "heart_rate":      # único opcional
                clean[field] = None
                continue
            raise ValidationError(f"{LABELS[field]} is required.")
        try:
            value = float(raw.replace(",", "."))
        except ValueError:
            raise ValidationError(f"{LABELS[field]}: enter a number.")
        if not lo <= value <= hi:
            raise ValidationError(f"{LABELS[field]} must be between {lo} and {hi}.")
        clean[field] = value if field == "sleep_quality" else int(round(value))
    return clean


class InjuryService:
    def __init__(self):
        self.model = None
        self.features = None
        self.classes = None

    def _load(self):
        if self.model is None:
            mp = os.path.join(ARTIFACTS, 'injury_model.joblib')
            fp = os.path.join(ARTIFACTS, 'injury_features.json')
            if not (os.path.exists(mp) and os.path.exists(fp)):
                raise FileNotFoundError("Injury model not found. Run ml_engine/train_injury_model.py")
            self.model = joblib.load(mp)
            with open(fp) as f:
                meta = json.load(f)
            self.features = meta["features"]
            self.classes = {int(k): v for k, v in meta["classes"].items()}

    def predict(self, data):
        """data: dict validado. Devuelve (nivel, {Low,Medium,High: prob})."""
        self._load()
        row = {
            "training_intensity": data["training_intensity"],
            "training_duration": data["training_duration"],
            "training_load": data["training_intensity"] * data["training_duration"],
            "heart_rate": data["heart_rate"] if data["heart_rate"] is not None else float("nan"),
            "sleep_quality": data["sleep_quality"],
            "recovery_score": data["recovery_score"],
            "fatigue_index": data["fatigue_index"],
        }
        X = pd.DataFrame([row])[self.features]
        proba = self.model.predict_proba(X)[0]
        probs = {self.classes[int(c)]: float(p) for c, p in zip(self.model.classes_, proba)}
        level = max(probs, key=probs.get)
        return level, probs

    @staticmethod
    def recommendations(data):
        """Consejos puntuales según las variables que más pesan en el modelo."""
        tips = []
        if data["recovery_score"] < 40:
            tips.append("Your perceived recovery is low: skip intervals today and focus on mobility and rest.")
        if data["fatigue_index"] > 70:
            tips.append("High fatigue: reduce the volume of your next session by 20-30%.")
        if data["sleep_quality"] < 5:
            tips.append("You slept poorly: aim for 7-9 hours tonight; short sleep is an injury risk factor.")
        if data["training_intensity"] >= 8 and data["training_duration"] >= 90:
            tips.append("Long, intense session: plan an easy day afterwards.")
        if not tips:
            tips.append("No specific alerts. Keep logging to spot trends.")
        return tips


injury_predictor = InjuryService()

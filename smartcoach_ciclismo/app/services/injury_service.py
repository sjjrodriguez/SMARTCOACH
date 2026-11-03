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

RISK_TEXT = {
    "Low":    ("Riesgo bajo", "Tu estado de hoy es compatible con tu carga. Mantén tu plan."),
    "Medium": ("Riesgo medio", "Hay señales de sobrecarga. Reduce intensidad y prioriza sueño y recuperación."),
    "High":   ("Riesgo alto", "Alta probabilidad de lesión. Descansa o haz una sesión muy suave y consulta a tu entrenador o fisioterapeuta si hay dolor."),
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
            raise ValidationError(f"Falta el campo: {field}")
        try:
            value = float(raw.replace(",", "."))
        except ValueError:
            raise ValidationError(f"Valor no numérico en: {field}")
        if not lo <= value <= hi:
            raise ValidationError(f"{field} debe estar entre {lo} y {hi}.")
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
                raise FileNotFoundError("Modelo de lesiones no encontrado. Ejecuta ml_engine/train_injury_model.py")
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
            tips.append("Tu recuperación percibida es baja: evita intervalos hoy y prioriza movilidad y descanso.")
        if data["fatigue_index"] > 70:
            tips.append("Fatiga alta: reduce el volumen de la próxima sesión entre 20% y 30%.")
        if data["sleep_quality"] < 5:
            tips.append("Dormiste mal: apunta a 7-9 h esta noche; el sueño corto es un factor de riesgo de lesión.")
        if data["training_intensity"] >= 8 and data["training_duration"] >= 90:
            tips.append("Sesión larga e intensa: planea un día suave después.")
        if not tips:
            tips.append("Sin alertas puntuales. Sigue registrando para detectar tendencias.")
        return tips


injury_predictor = InjuryService()

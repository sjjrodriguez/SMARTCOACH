import os
import joblib
import numpy as np

ARTIFACTS = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ml_engine/model_artifacts'))

PLAN_LEVELS = {
    0: "Plan Principiante - Acondicionamiento Base",
    1: "Plan Moderado - Desarrollo y Umbral",
    2: "Plan Avanzado - Alto Rendimiento",
}

PLAN_DESCRIPTIONS = {
    0: "Enfoque en construir base aeróbica. Salidas de 1 a 2 horas a ritmo suave "
       "para acostumbrar el cuerpo y prevenir lesiones.",
    1: "Enfoque en mejorar tu velocidad crucero. Balancea el fondo aeróbico "
       "(Zona 2) con estímulos al umbral de lactato.",
    2: "Estructura de alta carga. Incluye 2 días de intervalos explosivos (VO2 Max) "
       "y rodadas de más de 4 horas.",
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
                raise FileNotFoundError("Artefactos del plan no encontrados. Ejecuta ml_engine/train_model.py")
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)

    def predict_training_plan(self, age, weight, weekly_hours, resting_hr, tss):
        """Devuelve (clase, etiqueta, descripcion)."""
        self._load()
        features = np.array([[age, weight, weekly_hours, resting_hr, tss]])
        cls = int(self.model.predict(self.scaler.transform(features))[0])
        return cls, PLAN_LEVELS.get(cls, PLAN_LEVELS[0]), PLAN_DESCRIPTIONS.get(cls, PLAN_DESCRIPTIONS[0])


ml_predictor = MLService()

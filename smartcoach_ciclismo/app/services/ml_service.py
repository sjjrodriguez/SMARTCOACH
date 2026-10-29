import os
import joblib
import numpy as np

class MLService:
    def __init__(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ml_engine/model_artifacts'))
        self.model_path = os.path.join(base_dir, 'model.joblib')
        self.scaler_path = os.path.join(base_dir, 'scaler.joblib')
        self.model = None
        self.scaler = None
        self._load_artifacts()

    def _load_artifacts(self):
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
        else:
            raise FileNotFoundError("Artefactos no encontrados. Ejecuta train_model.py")

    def predict_training_plan(self, age, weight, weekly_hours, resting_hr, tss):
        if not self.model or not self.scaler:
            raise Exception("El modelo no está cargado correctamente.")

        # Array de 5 características exactas para el StandardScaler
        features = np.array([[age, weight, weekly_hours, resting_hr, tss]])
        
        scaled_features = self.scaler.transform(features)
        prediction = self.model.predict(scaled_features)
        
        niveles = {
            0: "Plan Principiante - Acondicionamiento Base", 
            1: "Plan Moderado - Desarrollo y Umbral", 
            2: "Plan Avanzado - Alto Rendimiento"
        }
        return niveles.get(prediction[0], "Plan Principiante - Acondicionamiento Base")

ml_predictor = MLService()

from pathlib import Path
import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = (
    BASE_DIR / "models" / "injury_model_cyclist.joblib"
)

_model = None


def load_model():
    global _model

    if _model is None:
        _model = joblib.load(MODEL_PATH)

    return _model


def predict_injury(data):
    """
    Recibe un diccionario con las variables
    utilizadas durante el entrenamiento.
    """

    model = load_model()

    if isinstance(data, dict):
        data = pd.DataFrame([data])

    prediction = model.predict(data)[0]
    probabilities = model.predict_proba(data)[0]

    return {
        "prediction": int(prediction),
        "probability": float(max(probabilities)),
        "message": (
            "Antecedente de lesión identificado"
            if prediction == 1
            else "Sin antecedente de lesión identificado"
        )
    }

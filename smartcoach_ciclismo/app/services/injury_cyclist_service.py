"""Modelo de ciclistas: estima la probabilidad de ANTECEDENTE de lesión a partir del perfil.

El modelo (ml_engine/train_cyclist_injury_model.py) espera 42 columnas del
cuestionario de DATA.xlsx. El formulario solo pregunta las más útiles; las demás
se envían como vacías (NaN) y el imputador del propio Pipeline las rellena con la
mediana / moda del entrenamiento.
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.services.injury_service import ValidationError

# ml_engine/models/injury_model_cyclist.joblib
# (antes apuntaba a app/services/models/, que no existe)
MODEL_PATH = Path(__file__).resolve().parents[2] / "ml_engine" / "models" / "injury_model_cyclist.joblib"

# Campo: (etiqueta, mínimo, máximo, obligatorio)
NUMERIC = {
    "Age":                ("Edad", 10, 90, True),
    "Height":             ("Estatura (cm)", 120, 220, True),
    "Bodymass":           ("Peso (kg)", 30, 200, True),
    "Frequency_cycling":  ("Salidas por semana", 1, 14, True),
    "Hours_week_cycling": ("Horas por semana", 0.5, 60, True),
    "Km_week":            ("Km por semana", 0, 2000, True),
    "Experience":         ("Años de experiencia", 0, 70, True),
    "Speed":              ("Velocidad media (km/h)", 5, 70, False),
    "TOTALKM":            ("Km semanales totales", 0, 3000, False),
}

# Campo: (etiqueta, códigos válidos). Códigos según la hoja "0.Information" de DATA.xlsx.
CHOICES = {
    "Gender":              ("Género", {0, 1}),
    "Discipline":          ("Disciplina", {1, 2, 3}),
    "Purpose":             ("Objetivo", {1, 2, 3}),
    "Terrain":             ("Terreno", {1, 2}),
    "Coach":               ("Entrenador", {0, 1}),
    "Bike_quality":        ("Calidad de la bici", {1, 2, 3}),
    "Comfort_saddle":      ("Comodidad del sillín", {2, 3}),
    "Comfort_posture":     ("Comodidad de la postura", {2, 3}),
}

# Casillas: marcada = 1, sin marcar = 0
CHECKS = ["Training_core", "Training_flexibility", "Training_strength"]

# Usuarios de la app: Colombia -> "4-Others" / "2-South-America" en el dataset.
FIXED = {"Country": 4, "Continent": 2}


_model = None


def load_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                "Modelo de ciclistas no encontrado. Ejecuta ml_engine/train_cyclist_injury_model.py")
        _model = joblib.load(MODEL_PATH)
    return _model


def parse_profile(form):
    """Valida el formulario. Devuelve dict limpio o lanza ValidationError."""
    data = {}
    for field, (label, lo, hi, required) in NUMERIC.items():
        raw = (form.get(field) or "").strip().replace(",", ".")
        if raw == "":
            if required:
                raise ValidationError(f"Falta el campo: {label}.")
            continue
        try:
            value = float(raw)
        except ValueError:
            raise ValidationError(f"{label}: ingresa un número.")
        if not lo <= value <= hi:
            raise ValidationError(f"{label} debe estar entre {lo} y {hi}.")
        data[field] = value

    for field, (label, allowed) in CHOICES.items():
        raw = (form.get(field) or "").strip()
        if raw == "":          # "No sé": queda vacío y lo imputa el modelo
            continue
        try:
            value = int(raw)
        except ValueError:
            value = None
        if value not in allowed:
            raise ValidationError(f"{label}: opción no válida.")
        data[field] = value

    for field in CHECKS:
        data[field] = 1 if form.get(field) else 0
    return data


def predict_injury(data):
    """data: dict de parse_profile. Devuelve dict con la predicción y su probabilidad."""
    model = load_model()
    columns = list(model.feature_names_in_)

    row = {c: np.nan for c in columns}
    row.update(FIXED)
    row.update(data)
    row["BMI"] = data["Bodymass"] / (data["Height"] / 100) ** 2

    X = pd.DataFrame([row])[columns]
    classes = list(model.classes_)
    prob_injury = float(model.predict_proba(X)[0][classes.index(1)])
    prediction = int(model.predict(X)[0])

    if prediction == 1:
        label = "Perfil con posible antecedente de lesión"
        message = ("Tu perfil se parece al de ciclistas que han tenido lesiones. Cuida el ajuste de la "
                   "bici, la recuperación y consulta a un profesional si sientes molestias.")
        css = "med"
    else:
        label = "Perfil sin antecedente de lesión probable"
        message = ("Tu perfil no se parece al de ciclistas con lesiones previas. "
                   "Mantén tu plan y sigue con tus chequeos diarios.")
        css = "low"

    return {"prediction": prediction, "prob_injury": prob_injury,
            "label": label, "message": message, "css": css}
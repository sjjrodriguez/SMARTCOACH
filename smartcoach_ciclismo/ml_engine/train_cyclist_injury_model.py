
import json
from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# Rutas
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "DATA.xlsx"
MODEL_DIR = BASE_DIR / "models"
METRICS_DIR = BASE_DIR / "metrics"

MODEL_DIR.mkdir(exist_ok=True)
METRICS_DIR.mkdir(exist_ok=True)

# 1. Cargar datos
df = pd.read_excel(
    DATA_PATH,
    sheet_name="1.ALL DATA FOR MODELS"
)

# 2. Preparar variable objetivo
target = "Injuries"

# Eliminar identificadores y variables de dolor,
# porque pueden revelar síntomas posteriores a la lesión.
excluded = [
    "Participant",
    "Paincycling",
    "Painnotcycling",
    target
]

X = df.drop(columns=excluded)
y = df[target].astype(int)

# 3. Identificar variables numéricas continuas
numeric_features = [
    "Age", "Height", "Bodymass", "BMI",
    "Frequency_cycling", "Hours_week_cycling",
    "Km_week", "TOTALKM", "Experience", "Speed"
]

categorical_features = [
    col for col in X.columns
    if col not in numeric_features
]

# 4. Preparar datos
numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median"))
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore"))
])

preprocessor = ColumnTransformer([
    ("numeric", numeric_pipeline, numeric_features),
    ("categorical", categorical_pipeline, categorical_features)
])

# 5. Crear modelo
model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        class_weight="balanced",
        random_state=42
    ))
])

# 6. Separar entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# 7. Entrenar y evaluar
model.fit(X_train, y_train)

predictions = model.predict(X_test)

metrics = {
    "accuracy": float(accuracy_score(y_test, predictions)),
    "precision": float(precision_score(y_test, predictions, zero_division=0)),
    "recall": float(recall_score(y_test, predictions, zero_division=0)),
    "f1_score": float(f1_score(y_test, predictions, zero_division=0)),
    "confusion_matrix": confusion_matrix(
        y_test, predictions
    ).tolist()
}

print("\n===== RESULTADOS DEL MODELO =====")
print(json.dumps(metrics, indent=4))

print("\n===== REPORTE DE CLASIFICACIÓN =====")
print(classification_report(y_test, predictions))

# 8. Reentrenar con todos los datos
model.fit(X, y)

# 9. Guardar modelo
model_path = MODEL_DIR / "injury_model_cyclist.joblib"
joblib.dump(model, model_path)

# 10. Guardar métricas de prueba
metrics_path = METRICS_DIR / "injury_metrics.json"

with open(metrics_path, "w", encoding="utf-8") as file:
    json.dump(metrics, file, indent=4)

print("\nEntrenamiento finalizado.")
print(f"Modelo guardado en: {model_path}")
print(f"Metricas guardadas en: {metrics_path}")

"""
Entrena el modelo de RIESGO DE LESION (Low / Medium / High) con
data/sports_injury_data.csv.

Solo usa las variables que el ciclista puede reportar en un chequeo diario
y que, segun la importancia de variables del modelo anterior, son las que
mas pesan: recovery_score, fatigue_index, sleep_quality y la carga de la
sesion (RPE, duracion, FC media).

Salida (ml_engine/model_artifacts/):
    injury_model.joblib   Pipeline (imputador + RandomForest balanceado)
    injury_features.json  orden de variables, rangos y clases
    injury_metrics.json   metricas en el set de prueba
"""
import json
import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "sports_injury_data.csv")
ARTIFACTS_DIR = os.path.join(BASE_DIR, "model_artifacts")

# Orden fijo: el servicio debe construir el vector en este mismo orden.
FEATURES = [
    "training_intensity",   # RPE de la sesion (1-10)
    "training_duration",    # minutos
    "training_load",        # RPE x minutos (se calcula, no se pregunta)
    "heart_rate",           # FC media de la sesion (lpm)
    "sleep_quality",        # 1-10
    "recovery_score",       # 0-100
    "fatigue_index",        # 0-100
]
TARGET = "injury_occurred"
CLASSES = {0: "Low", 1: "Medium", 2: "High"}

# El dataset trae fatigue_index hasta ~270; el formulario acepta 0-100.
CLIP = {"fatigue_index": (0, 100), "recovery_score": (0, 100),
        "sleep_quality": (1, 10), "training_intensity": (1, 10)}


def main():
    df = pd.read_csv(DATA_PATH)
    df = df[FEATURES + [TARGET]].copy()
    for col, (lo, hi) in CLIP.items():
        df[col] = df[col].clip(lo, hi)

    X, y = df[FEATURES], df[TARGET].astype(int)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)

    pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("rf", RandomForestClassifier(
            n_estimators=150, max_depth=10, min_samples_leaf=25,
            class_weight="balanced", random_state=42, n_jobs=-1)),
    ])

    cv = StratifiedKFold(5, shuffle=True, random_state=42)
    cv_f1 = cross_val_score(pipe, X_tr, y_tr, cv=cv, scoring="f1_macro")
    pipe.fit(X_tr, y_tr)
    pred = pipe.predict(X_te)

    print(classification_report(y_te, pred, target_names=list(CLASSES.values())))
    importances = dict(zip(FEATURES, pipe.named_steps["rf"].feature_importances_.round(4)))

    metrics = {
        "cv_macro_f1_mean": round(float(cv_f1.mean()), 4),
        "test_macro_f1": round(float(f1_score(y_te, pred, average="macro")), 4),
        "test_accuracy": round(float((pred == y_te).mean()), 4),
        "majority_class_baseline": round(float(y_te.value_counts(normalize=True).max()), 4),
        "confusion_matrix": confusion_matrix(y_te, pred).tolist(),
        "feature_importances": {k: float(v) for k, v in importances.items()},
        "n_train": int(len(X_tr)), "n_test": int(len(X_te)),
    }
    meta = {
        "features": FEATURES,
        "classes": {str(k): v for k, v in CLASSES.items()},
        "medians": {c: round(float(X_tr[c].median()), 3) for c in FEATURES},
        "model_type": "RandomForest(class_weight=balanced)",
    }

    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    joblib.dump(pipe, os.path.join(ARTIFACTS_DIR, "injury_model.joblib"))
    with open(os.path.join(ARTIFACTS_DIR, "injury_features.json"), "w") as f:
        json.dump(meta, f, indent=2)
    with open(os.path.join(ARTIFACTS_DIR, "injury_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()

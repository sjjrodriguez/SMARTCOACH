"""
SmartCoach Ciclismo - Injury risk model training (CRISP-DM).

"""
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, cross_val_predict
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBClassifier
except ImportError:  # XGBoost is optional
    XGBClassifier = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "sports_injury_data.csv")
ARTIFACTS_DIR = os.path.join(BASE_DIR, "model_artifacts")
RANDOM_STATE = 42

# FIXED ORDER: ml_service.py must pass the features exactly in this order.
# Each entry says where the app gets the value (form field / model field).
FEATURES = {
    "age": "cyclist age (profile)",
    "bmi": "weight(kg) / height(m)^2 (profile)",
    "training_intensity": "session rpe (1-10)",
    "training_duration": "session duracion_min",
    "training_load": "session load = rpe * duracion_min (sRPE)",
    "heart_rate": "session frecuencia_cardiaca_media",
    "sleep_quality": "daily check-in: sleep quality (2-10)",
    "recovery_score": "daily check-in: perceived recovery (25-98)",
    "fatigue_index": "daily check-in: fatigue (15-85)",
}
TARGET = "injury_occurred"
CLASSES = {0: "Low", 1: "Medium", 2: "High"}  # injury risk level
FEATURE_NAMES = list(FEATURES)


def load_data():
    df = pd.read_csv(DATA_PATH)
    missing = [c for c in FEATURE_NAMES + [TARGET, "athlete_id"] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in the dataset: {missing}")
    return df


def build_candidates():
    cands = {
        "RandomForest": RandomForestClassifier(
            n_estimators=200, min_samples_leaf=40, max_depth=12, class_weight="balanced",
            random_state=RANDOM_STATE, n_jobs=-1),
    }
    if XGBClassifier is not None:
        cands["XGBoost"] = XGBClassifier(
            n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8,
            random_state=RANDOM_STATE, n_jobs=-1)
    return cands


def train():
    df = load_data()
    X = df[FEATURE_NAMES].copy()
    y = df[TARGET].astype(int)
    groups = df["athlete_id"]

    # Medians used to impute missing values (the dataset has ~3 % missing)
    medians = X.median()
    X = X.fillna(medians)

    # Split BY ATHLETE: an athlete is never in both train and test
    # (otherwise the model could "recognize" the athlete and metrics would be inflated).
    tr, te = next(GroupShuffleSplit(test_size=0.2, random_state=RANDOM_STATE)
                  .split(X, y, groups))
    X_train, X_test, y_train, y_test = X.iloc[tr], X.iloc[te], y.iloc[tr], y.iloc[te]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # Class weights for the imbalance (64/21/15 %)
    class_w = len(y_train) / (3 * y_train.value_counts())
    sample_w = y_train.map(class_w).values

    # Model selection with grouped cross-validation, on the training set only
    results = {}
    for name, model in build_candidates().items():
        params = {"sample_weight": sample_w} if name == "XGBoost" else {}
        pred = cross_val_predict(model, X_train_s, y_train, groups=groups.iloc[tr],
                                 cv=GroupKFold(n_splits=5), params=params)
        results[name] = f1_score(y_train, pred, average="macro")
        print(f"CV macro-F1 {name}: {results[name]:.3f}")
    best_name = max(results, key=results.get)
    print(f"\n>> Selected model: {best_name}")

    model = build_candidates()[best_name]
    if best_name == "XGBoost":
        model.fit(X_train_s, y_train, sample_weight=sample_w)
    else:
        model.fit(X_train_s, y_train)

    # Final evaluation on athletes the model has never seen
    pred = model.predict(X_test_s)
    print("\nTest metrics (unseen athletes):")
    print(classification_report(y_test, pred, target_names=list(CLASSES.values())))
    cm = confusion_matrix(y_test, pred)
    print("Confusion matrix:\n", cm)

    # Export
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(ARTIFACTS_DIR, "model.joblib"))
    joblib.dump(scaler, os.path.join(ARTIFACTS_DIR, "scaler.joblib"))

    contract = {
        "features": FEATURE_NAMES,
        "feature_sources": FEATURES,
        "classes": {str(k): v for k, v in CLASSES.items()},
        "medians": {k: round(float(v), 4) for k, v in medians.items()},
        "ranges": {c: [round(float(df[c].min()), 3), round(float(df[c].max()), 3)]
                   for c in FEATURE_NAMES},
        "model_type": best_name,
        "sklearn_version": __import__("sklearn").__version__,
    }
    with open(os.path.join(ARTIFACTS_DIR, "features.json"), "w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, ensure_ascii=False)

    metrics = {
        "cv_macro_f1": {k: round(v, 4) for k, v in results.items()},
        "test_macro_f1": round(f1_score(y_test, pred, average="macro"), 4),
        "test_accuracy": round(float((pred == y_test).mean()), 4),
        "confusion_matrix": cm.tolist(),
        "feature_importances": dict(zip(
            FEATURE_NAMES, np.round(model.feature_importances_, 4).tolist())),
    }
    with open(os.path.join(ARTIFACTS_DIR, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print("\nArtifacts exported to:", ARTIFACTS_DIR)


if __name__ == "__main__":
    train()
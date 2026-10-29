import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_PATH = os.path.join(DATA_DIR, "ciclistas_planes.csv")
ARTIFACTS_DIR = os.path.join(BASE_DIR, "model_artifacts")

# Las 5 variables estables exactas que vienen de tu base de datos web
FEATURES = ["age", "weight_kg", "weekly_hours", "resting_heart_rate", "tss_acumulado"]
TARGET = "plan_type"
CLASSES = {0: "Principiante", 1: "Moderado", 2: "Avanzado"}

def generar_dataset_sintetico():
    """Genera 1000 registros lógicos de ciclistas si no existe el CSV"""
    os.makedirs(DATA_DIR, exist_ok=True)
    np.random.seed(42)
    n = 1000
    
    # Generar variables con distribuciones normales
    age = np.random.randint(18, 65, n)
    weight = np.random.normal(75, 10, n)
    
    # Lógica deportiva: 
    # Principiantes (0): pocas horas, FC alta, TSS bajo
    # Avanzados (2): muchas horas, FC baja, TSS alto
    planes = np.random.choice([0, 1, 2], n, p=[0.4, 0.4, 0.2])
    
    weekly_hours = np.where(planes == 0, np.random.uniform(2, 6, n),
                   np.where(planes == 1, np.random.uniform(6, 12, n),
                                         np.random.uniform(12, 25, n)))
    
    resting_hr = np.where(planes == 0, np.random.randint(65, 85, n),
                 np.where(planes == 1, np.random.randint(55, 70, n),
                                       np.random.randint(40, 55, n)))
    
    tss = np.where(planes == 0, np.random.uniform(0, 1500, n),
          np.where(planes == 1, np.random.uniform(1500, 5000, n),
                                np.random.uniform(5000, 15000, n)))

    df = pd.DataFrame({
        "age": age,
        "weight_kg": weight,
        "weekly_hours": weekly_hours,
        "resting_heart_rate": resting_hr,
        "tss_acumulado": tss,
        "plan_type": planes
    })
    
    df.to_csv(DATA_PATH, index=False)
    print(f"Dataset generado exitosamente en {DATA_PATH}")

def entrenar_modelo():
    if not os.path.exists(DATA_PATH):
        generar_dataset_sintetico()

    print("Cargando datos...")
    df = pd.read_csv(DATA_PATH)
    
    X = df[FEATURES]
    y = df[TARGET]

    # Separar en datos de entrenamiento (80%) y prueba (20%)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # 1. ESCALADOR: Ahora el StandardScaler aprenderá a escalar SOLO 5 variables
    print("Entrenando escalador y modelo...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 2. MODELO: Random Forest para clasificar los 3 planes
    modelo = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    modelo.fit(X_train_scaled, y_train)

    # Evaluar modelo
    predicciones = modelo.predict(X_test_scaled)
    print("\nReporte de Clasificación:")
    print(classification_report(y_test, predicciones, target_names=list(CLASSES.values())))

    # Exportar el modelo y el escalador de 5 variables
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    joblib.dump(modelo, os.path.join(ARTIFACTS_DIR, "model.joblib"))
    joblib.dump(scaler, os.path.join(ARTIFACTS_DIR, "scaler.joblib"))
    
    print(f"¡Éxito! Artefactos listos (model.joblib y scaler.joblib) exportados en {ARTIFACTS_DIR}")

if __name__ == "__main__":
    entrenar_modelo()
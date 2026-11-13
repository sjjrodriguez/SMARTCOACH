"""Content for the Methodology page: CRISP-DM / CRISP-ML(Q) phases and the 4-layer architecture.

Pure Python (no Flask, no database). The model metrics are read from the JSON files that the
training scripts in ml_engine/ write, so the page never shows numbers that are out of date.
If a file is missing the page still renders and shows "n/a" for that value.
"""
import json
import os

ML_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ml_engine'))

FEATURE_LABELS = {
    'recovery_score': 'Recovery',
    'sleep_quality': 'Sleep quality',
    'fatigue_index': 'Fatigue',
    'training_load': 'Training load (RPE x min)',
    'heart_rate': 'Average heart rate',
    'training_intensity': 'Effort (RPE)',
    'training_duration': 'Duration',
}

# status: done / partial / pending
PHASES = [
    {'n': 1, 'name': 'Business understanding', 'status': 'done',
     'did': ['Goal: give each cyclist a plan that fits their level and help prevent injuries by tracking load and recovery.',
             'Success: the cyclist gets a plan, logs workouts and sees an understandable injury risk (traffic light, probabilities, tips).'],
     'qa': 'The output is guidance, not a medical diagnosis. A false "low risk" is the costliest error, so probabilities are shown, not only the label.'},
    {'n': 2, 'name': 'Data understanding', 'status': 'done',
     'did': ['Three sources: datos.gov.co supported athletes (demographics only), the Kaggle Multimodal Sports Injury Dataset (15,420 rows) and a cyclist questionnaire (DATA.xlsx).',
             'Exploratory analysis and data-quality problems are documented in ml_engine/notebooks/exploratory_data.ipynb.'],
     'qa': 'Each source has a documentation sheet in the notebook. The injury classes are imbalanced (9,868 / 3,238 / 2,314).'},
    {'n': 3, 'name': 'Data preparation', 'status': 'done',
     'did': ['Cleaning and filtering of the national athletes registry down to cycling records.',
             'The injury model only uses variables a cyclist can report: RPE, duration, load, heart rate, sleep, recovery and fatigue.',
             'Missing values are imputed inside each scikit-learn Pipeline.'],
     'qa': 'A data-leakage check (splitting by athlete or not) is in the notebook, and the feature order is stored in injury_features.json so the app builds the same vector used in training.'},
    {'n': 4, 'name': 'Modeling', 'status': 'done',
     'did': ['Plan classifier: Random Forest (100 trees, depth 10), stratified 80/20 split.',
             'Injury risk: balanced Random Forest in a Pipeline, stratified 5-fold cross-validation.',
             'Cyclist profile: Random Forest with imputation and One-Hot encoding.'],
     'qa': 'Random Forest and XGBoost were compared in the notebook.'},
    {'n': 5, 'name': 'Evaluation', 'status': 'partial',
     'did': ['Injury risk and cyclist profile metrics are saved as JSON and shown below.',
             'Macro-F1 is used instead of accuracy because the classes are imbalanced.'],
     'qa': 'Limits are stated openly: the injury model accuracy is below the majority-class baseline, and the plan classifier was trained on synthetic data and has no saved metrics yet.'},
    {'n': 6, 'name': 'Deployment', 'status': 'done',
     'did': ['Models are exported with joblib and loaded lazily by the Flask services.',
             'PostgreSQL (Supabase) stores users, workouts, plans and injury checks; new columns are added safely at startup.'],
     'qa': 'Inputs are validated against fixed ranges, and a workout is always saved even if the injury model fails.'},
    {'n': 7, 'name': 'Monitoring and maintenance', 'status': 'pending', 'ml_q': True,
     'did': ['Every prediction is already stored (risk level and probabilities).',
             'Next: compare predictions with injuries actually reported, retrain with real data, version the model files and watch for data drift.'],
     'qa': 'This extra phase is what CRISP-ML(Q) adds to CRISP-DM. It is planned, not implemented yet.'},
]

STATUS_LABEL = {'done': 'Done', 'partial': 'Partial', 'pending': 'Planned'}

MODELS = [
    {'key': 'A', 'name': 'Plan classifier', 'output': 'Beginner / Moderate / Advanced',
     'data': '1,000 synthetic cyclist records', 'algo': 'Random Forest', 'used': 'Generate plan'},
    {'key': 'B', 'name': 'Injury risk', 'output': 'Low / Medium / High',
     'data': 'Kaggle sports injury dataset, 15,420 rows', 'algo': 'Balanced Random Forest', 'used': 'Workout injury check'},
    {'key': 'C', 'name': 'Cyclist profile', 'output': 'Probability of a previous injury',
     'data': 'Cyclist questionnaire (42 columns)', 'algo': 'Random Forest', 'used': 'Cyclist profile'},
]

LAYERS = [
    {'n': 1, 'name': 'Presentation', 'where': 'app/templates, app/static',
     'does': 'Shows data and collects forms.',
     'tech': 'Jinja2, Bootstrap 5, Chart.js',
     'example': 'The workout form with its Workout and Injury check tabs.', 'color': 'primary'},
    {'n': 2, 'name': 'Application / Control', 'where': 'app/controllers',
     'does': 'HTTP routes, user session and orchestration of each use case.',
     'tech': 'Flask blueprints: auth, main, workouts, plans, injury',
     'example': 'create_workout saves the workout and triggers the injury check.', 'color': 'low'},
    {'n': 3, 'name': 'Business logic', 'where': 'app/services, ml_engine',
     'does': 'Rules, validation and predictions, independent of Flask.',
     'tech': 'scikit-learn, pandas, joblib',
     'example': 'InjuryService.predict() and the weekly load traffic light.', 'color': 'med'},
    {'n': 4, 'name': 'Data', 'where': 'app/models, config.py, ml_engine/data',
     'does': 'Persistence and data access.',
     'tech': 'SQLAlchemy, PostgreSQL (Supabase), .joblib files',
     'example': 'Tables users, workouts, training_plans and injury_checkins.', 'color': 'none'},
]

FLOW = [
    ('Presentation', 'The cyclist fills in the Workout tab and the Injury check tab.'),
    ('Control', 'workouts.create_workout validates the form.'),
    ('Business logic', 'RPE, duration and fatigue come from the workout; the model predicts the risk.'),
    ('Data', 'The workout and its injury check are saved, then the result is shown.'),
]


def _load_json(*parts):
    try:
        with open(os.path.join(ML_DIR, *parts), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _injury_metrics():
    m = _load_json('model_artifacts', 'injury_metrics.json')
    if not m:
        return None
    out = {
        'macro_f1': m.get('test_macro_f1'),
        'accuracy': m.get('test_accuracy'),
        'baseline': m.get('majority_class_baseline'),
        'cv_f1': m.get('cv_macro_f1_mean'),
        'high_recall': None,
        'features': [],
    }
    cm = m.get('confusion_matrix')
    try:
        row = cm[2]
        out['high_recall'] = row[2] / sum(row)
    except (TypeError, IndexError, ZeroDivisionError):
        pass
    out['confusion'] = _confusion_rows(cm)
    imp = m.get('feature_importances') or {}
    top = sorted(imp.items(), key=lambda kv: kv[1], reverse=True)[:5]
    if top:
        biggest = top[0][1] or 1
        out['features'] = [{'label': FEATURE_LABELS.get(k, k), 'pct': round(v * 100, 1),
                            'width': round(v / biggest * 100)} for k, v in top]
    return out


def _confusion_rows(cm, labels=('Low', 'Medium', 'High')):
    """Rows of the confusion matrix with the share of each cell inside its real class (row)."""
    try:
        rows = []
        for i, row in enumerate(cm):
            total = sum(row) or 1
            rows.append({'label': labels[i], 'total': sum(row),
                         'cells': [{'n': n, 'share': n / total} for n in row]})
        return {'labels': list(labels), 'rows': rows}
    except (TypeError, IndexError):
        return None


def _algo_compare():
    """Cross-validated macro-F1 of each algorithm in the earlier version of the injury model."""
    m = _load_json('model_artifacts', 'metrics.json')
    cv = (m or {}).get('cv_macro_f1')
    if not isinstance(cv, dict):
        return None
    names = {'RandomForest': 'Random Forest', 'XGBoost': 'XGBoost'}
    return [{'name': names.get(k, k), 'score': v} for k, v in cv.items()]


def _profile_metrics():
    m = _load_json('metrics', 'injury_metrics.json')
    if not m:
        return None
    return {'accuracy': m.get('accuracy'), 'f1': m.get('f1_score')}


def build_methodology_data():
    return {
        'phases': PHASES, 'status_label': STATUS_LABEL, 'models': MODELS,
        'layers': LAYERS, 'flow': FLOW,
        'injury': _injury_metrics(), 'profile': _profile_metrics(), 'algo_compare': _algo_compare(),
    }

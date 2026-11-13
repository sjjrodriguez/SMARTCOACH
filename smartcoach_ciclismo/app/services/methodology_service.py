"""Content for the Architecture and Project document pages: the three models and the 4-layer architecture.

The CRISP-DM / CRISP-ML(Q) phases live in crisp_content.py.

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

MODELS = [
    {'key': 'A', 'name': 'Plan classifier', 'question': 'Which plan level fits me?',
     'output': 'Beginner / Moderate / Advanced',
     'inputs': ['Age', 'Weight', 'Hours per week', 'Resting heart rate', 'Accumulated TSS'],
     'data': '1,000 synthetic cyclist records',
     'data_plain': 'Made-up cyclists generated from simple rules for each level.',
     'algo': 'Random Forest',
     'algo_plain': '100 decision trees vote on the level.',
     'used': 'Generate plan', 'used_endpoint': 'plans.generate_plan',
     'trust': {'label': 'Prototype', 'tone': 'warn',
               'note': 'It learned from synthetic data, so it repeats the rules used to create it, not real cyclists. No metrics are saved yet.'}},
    {'key': 'B', 'name': 'Injury risk', 'question': 'How risky is today\'s training?',
     'output': 'Low / Medium / High',
     'inputs': ['Effort (RPE)', 'Duration', 'Load (RPE x min)', 'Heart rate (optional)', 'Sleep quality', 'Recovery', 'Fatigue'],
     'data': 'Kaggle sports injury dataset, 15,420 rows',
     'data_plain': 'Records of athletes from several sports (not only cycling) with load, sleep, recovery and injury risk.',
     'algo': 'Balanced Random Forest',
     'algo_plain': '150 decision trees vote. Rare classes get extra weight so they are not ignored.',
     'used': 'Workout injury check', 'used_endpoint': 'workouts.create_workout',
     'trust': {'label': 'Guidance only', 'tone': 'warn',
               'note': 'Weak signal: accuracy is below the "always answer Low" baseline. Its strength is catching high-risk cases.'}},
    {'key': 'C', 'name': 'Cyclist profile', 'question': 'Does my profile look like injured cyclists?',
     'output': 'Probability of a previous injury',
     'inputs': ['Age', 'Height', 'Weight', 'Rides, hours and km per week', 'Years of experience', 'Optional: bike, terrain, coach, comfort'],
     'data': 'Cyclist questionnaire (739 cyclists, 42 questions)',
     'data_plain': 'Answers of real cyclists, including whether they had been injured before.',
     'algo': 'Random Forest',
     'algo_plain': '300 decision trees vote. Unanswered questions are filled in automatically.',
     'used': 'Cyclist profile', 'used_endpoint': 'injury.profile',
     'trust': {'label': 'Guidance only', 'tone': 'warn',
               'note': 'Small sample and modest scores. It tells you whether your profile resembles that of injured cyclists, nothing more.'}},
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
    out = {'accuracy': m.get('accuracy'), 'f1': m.get('f1_score'),
           'precision': m.get('precision'), 'recall': m.get('recall'), 'n_test': None, 'baseline': None}
    try:
        cm = m['confusion_matrix']
        total = sum(sum(row) for row in cm)
        out['n_test'] = total
        out['baseline'] = max(sum(row) for row in cm) / total
    except (KeyError, TypeError, ZeroDivisionError):
        pass
    return out


def build_methodology_data():
    return {
        'models': MODELS, 'layers': LAYERS, 'flow': FLOW,
        'injury': _injury_metrics(), 'profile': _profile_metrics(), 'algo_compare': _algo_compare(),
    }

"""Content of the CRISP-DM / CRISP-ML(Q) documentation: one page per phase.

Pure Python (no Flask, no database). Everything written here was checked against the code, the exploratory
notebook and the metrics files of this repository. Numbers that come from the trained models (macro-F1,
accuracy, importances, confusion matrix) are NOT written here: the Evaluation page reads them from the JSON
files through methodology_service, so they never go out of date.

Each phase has: glance (key facts), what (generic explanation), blocks (what was done in SmartCoach),
delivers (what the phase produced), terms (key vocabulary), files and qa (CRISP-ML(Q) quality check).

Block kinds, rendered in order: {'h': heading, 'lead': intro sentence} plus ONE of
  'p' (paragraph or list of paragraphs), 'ul', 'ol', 'table', 'cards', 'flow', 'callout', 'special'.
"""

PHASE_PAGES = [
    # ------------------------------------------------------------------ 1
    {
        'slug': 'business-understanding', 'n': 1, 'name': 'Business understanding', 'status': 'done',
        'short': 'Define the problem, the goal and what success looks like.',
        'what': 'The first phase defines the problem from the point of view of the people who will use the result. '
                'Before touching any data, the team decides what success means and what could go wrong.',
        'glance': [('3', 'models to build'), ('1', 'golden rule: guidance, not diagnosis'), ('2', 'main outputs: weekly plan and injury risk')],
        'blocks': [
            {'h': 'The problem',
             'p': ['Planning cycling training means balancing volume (hours, distance, climbing) against effort and recovery. '
                   'When these variables are tracked separately, or not tracked at all, it is hard to see the accumulated load, '
                   'notice fatigue and adjust the sessions in time. Amateur and recreational cyclists often end up with scattered '
                   'records and subjective impressions.',
                   'The guiding question of the project: how can a web platform be designed and built that joins the cyclist '
                   'profile and the training log with a machine learning model, to recommend personalized weekly sessions from '
                   'load and fatigue variables?']},
            {'h': 'Goal, success and scope',
             'cards': [{'t': 'Business goal', 'x': 'Give each cyclist a training plan that fits their level and help prevent injuries by tracking load and recovery.'},
                       {'t': 'Success looks like', 'x': 'The cyclist gets a plan, logs workouts and receives an understandable injury risk: a traffic light, probabilities and tips.'},
                       {'t': 'Scope', 'x': 'A Flask web application with accounts, a workout log, a weekly dashboard, training plans and injury risk.'}]},
            {'h': 'From each need to a model', 'lead': 'Every question a cyclist asks became one model.',
             'cards': [{'tag': 'Model A', 't': 'Which plan level fits me?', 'x': 'The plan classifier answers Beginner, Moderate or Advanced.'},
                       {'tag': 'Model B', 't': 'How risky is today\'s training?', 'x': 'The injury model answers Low, Medium or High, with probabilities.'},
                       {'tag': 'Model C', 't': 'Does my profile look like injured cyclists?', 'x': 'The profile model estimates the probability of a previous injury.'}]},
            {'h': 'Requirements and risks',
             'callout': {'tone': 'warn', 't': 'Guidance, not a medical diagnosis',
                         'x': 'This wording is already shown on the dashboard. A false "low risk" is the costliest error, so the application shows the probabilities and not only the label.'}},
            {'ul': ['Only variables a cyclist can realistically report are used as inputs.',
                    'Open data from datos.gov.co is used only after checking its content and license.']},
        ],
        'delivers': ['A written problem statement and guiding question', 'Success criteria and scope', 'A list of requirements and risks', 'The mapping from needs to the three models'],
        'terms': [('Business goal', 'What the project must achieve for its users, stated without technical words.'),
                  ('Success criteria', 'Concrete, checkable conditions that tell the team the goal was reached.'),
                  ('Guidance vs diagnosis', 'Guidance suggests and warns; a diagnosis is a medical statement. SmartCoach only gives guidance.')],
        'files': ['static/docs/Propuesta_SmartCoach.docx (project proposal)'],
        'qa': 'Requirements and risks are written down before modelling: guidance only, and the costliest error is a false "low risk".',
    },
    # ------------------------------------------------------------------ 2
    {
        'slug': 'data-understanding', 'n': 2, 'name': 'Data understanding', 'status': 'done',
        'short': 'Collect and explore the data sources and find their problems.',
        'what': 'This phase collects the available data, describes it and explores it. The goal is to learn what the data can and '
                'cannot answer, and to find quality problems before they reach a model.',
        'glance': [('4', 'data origins'), ('15,420', 'injury records (Kaggle)'), ('3', 'imbalanced risk classes')],
        'blocks': [
            {'h': 'Four data origins', 'lead': 'No single source has everything, so each model learns from a different one.',
             'cards': [{'tag': 'Context', 't': 'datos.gov.co registry', 'x': 'Supported athletes and para-athletes, 2021-2022. 60,000 rows, 2,150 of them cyclists (track, BMX and road). Demographic variables only.'},
                       {'tag': 'Model B', 't': 'Kaggle injury dataset', 'x': 'Multimodal Sports Injury Dataset: 15,420 rows and 29 columns with load, heart rate, sleep, recovery, fatigue and an injury-risk label.'},
                       {'tag': 'Model C', 't': 'Cyclist questionnaire', 'x': 'DATA.xlsx: answers of cyclists in 42 columns, including previous injuries.'},
                       {'tag': 'Model A', 't': 'Synthetic cyclists', 'x': '1,000 records generated by train_model.py from rules for each level: age, weight, weekly hours, resting heart rate and accumulated TSS.'}]},
            {'h': 'Imbalanced injury classes', 'lead': 'Number of examples of each risk level in the Kaggle dataset.',
             'special': 'class_dist'},
            {'h': 'What the exploration found',
             'cards': [{'tone': 'warn', 't': 'The registry cannot train a model', 'x': 'It has cyclists but no load, RPE, fatigue or injury data, so it is not used to train anything.'},
                       {'tone': 'warn', 't': 'The Kaggle data is not about cyclists', 'x': 'It covers soccer, basketball, track and other sports. Its results cannot be assumed to represent Colombian cyclists, and the report states this.'},
                       {'tone': 'ok', 't': 'Which variables matter', 'x': 'Recovery, sleep, fatigue and training load are the variables most related to risk. This is why the workout form has an Injury check tab.'}]},
            {'h': 'Quality problems found',
             'ul': ['The ID and year columns of the registry are stored as text with a thousands separator ("129,719", "2,021").',
                    'The age-range column is corrupted: the range 10-14 was converted into a date by Excel and shows up as 41913 or as a date.',
                    'In the Kaggle data, training load is about RPE × duration (the session-RPE method), and the application uses exactly that formula.']},
        ],
        'delivers': ['An inventory of sources with a documentation sheet for each', 'The list of data quality problems', 'The decision about which source feeds which model', 'The limits of each source, written for the report'],
        'terms': [('Class imbalance', 'When some classes have many more examples than others. A model can look accurate just by predicting the biggest class.'),
                  ('Documentation sheet', 'A short record of a source: origin, link, version, license, columns and download date.'),
                  ('Synthetic data', 'Data created by rules instead of measured on real people. Useful for a prototype, but it reflects the rules, not reality.'),
                  ('sRPE', 'Session RPE: training load computed as perceived effort (RPE) multiplied by minutes.')],
        'files': ['ml_engine/notebooks/exploratory_data.ipynb', 'ml_engine/data/datos_gov_ciclismo_raw.csv', 'ml_engine/data/sports_injury_data.csv',
                  'ml_engine/data/DATA.xlsx', 'ml_engine/data/ciclistas_planes.csv'],
        'qa': 'Each source has a documentation sheet in the notebook. The download date of each source must be filled in before submitting.',
    },
    # ------------------------------------------------------------------ 3
    {
        'slug': 'data-preparation', 'n': 3, 'name': 'Data preparation', 'status': 'done',
        'short': 'Clean the data and build the inputs each model will receive.',
        'what': 'Data preparation turns raw data into the exact table each model is trained on: cleaning, selecting variables, '
                'filling gaps and scaling. In practice this is where most of the work happens.',
        'glance': [('60,000 → 2,150', 'registry rows cut to cycling'), ('7', 'variables a cyclist can report'), ('1', 'saved column order, shared with the app')],
        'blocks': [
            {'h': 'The preparation steps', 'lead': 'The same chain of steps runs in training and inside the application.',
             'flow': [{'t': 'Select', 'x': 'Keep only the rows and columns the model needs.'},
                      {'t': 'Clean', 'x': 'Fix text columns that hold numbers and corrupted values.'},
                      {'t': 'Fill gaps', 'x': 'Missing values are imputed inside the Pipeline.'},
                      {'t': 'Scale / encode', 'x': 'Scale numbers or One-Hot encode categories, depending on the model.'},
                      {'t': 'Save the order', 'x': 'The column order is stored so the app builds the same vector.'}]},
            {'h': 'What each model receives',
             'table': {'head': ['Model', 'Inputs', 'Preparation'],
                       'rows': [['A. Plan classifier', 'age, weight_kg, weekly_hours, resting_heart_rate, tss_acumulado', 'StandardScaler over the 5 variables'],
                                ['B. Injury risk', 'training_intensity (RPE), training_duration, training_load, heart_rate, sleep_quality, recovery_score, fatigue_index', 'training_load = RPE × minutes. Missing values are imputed inside the Pipeline.'],
                                ['C. Cyclist profile', 'The most useful questions of the questionnaire', 'The remaining columns are sent empty; the Pipeline imputes them and encodes categories with One-Hot.']]}},
            {'h': 'A design decision that shapes the application',
             'callout': {'tone': 'info', 't': 'Only variables a cyclist can report',
                         'x': 'RPE, duration and fatigue come from the workout itself. Recovery, sleep and, optionally, heart rate cannot be deduced from the workout, so the person answers them. That is why the workout form has an Injury check tab and why the check is created automatically on save. An earlier version also used age and BMI; the current model keeps the seven variables above.'}},
            {'h': 'A note on accumulated TSS',
             'p': 'The application no longer estimates TSS for each workout: load is always RPE × minutes. The plan classifier keeps accumulated TSS as an input variable, because removing it would require retraining that model.'},
        ],
        'delivers': ['Clean training tables for each model', 'The chosen input variables', 'Scaler, imputer and encoder stored inside each Pipeline', 'injury_features.json, the saved column order'],
        'terms': [('Imputation', 'Filling a missing value with a replacement learned from the training data, so a blank answer does not break the model.'),
                  ('Scaling (StandardScaler)', 'Rescaling numbers to a common scale so that large units (like minutes) do not dominate small ones.'),
                  ('One-Hot encoding', 'Turning a category into several 0/1 columns, one per option.'),
                  ('Pipeline', 'A chain of steps (impute, scale, predict) saved as one object, so training and the application behave identically.'),
                  ('Data leakage', 'When information from the test set sneaks into training and makes results look better than they are.')],
        'files': ['ml_engine/model_artifacts/injury_features.json', 'ml_engine/train_model.py', 'ml_engine/train_injury_model.py', 'ml_engine/train_cyclist_injury_model.py'],
        'qa': 'A data-leakage check compares a random split with a split by athlete; the difference was small. The column order is stored in injury_features.json, so the application builds exactly the same vector used in training.',
    },
    # ------------------------------------------------------------------ 4
    {
        'slug': 'modeling', 'n': 4, 'name': 'Modeling', 'status': 'done',
        'short': 'Choose, train and compare the algorithms.',
        'what': 'Modeling chooses the algorithms, trains them on the prepared data and compares the options. The result is a trained '
                'model, not yet a verdict on whether it is good enough.',
        'glance': [('3', 'trained models'), ('100', 'trees in the plan classifier'), ('5-fold', 'cross-validation for injury risk')],
        'blocks': [
            {'h': 'The three models',
             'cards': [{'tag': 'Model A', 't': 'Plan classifier', 'x': 'Random Forest with 100 trees and maximum depth 10. Stratified 80/20 split. Answers Beginner, Moderate or Advanced.'},
                       {'tag': 'Model B', 't': 'Injury risk', 'x': 'Balanced Random Forest inside a Pipeline (imputer + classifier). Stratified 5-fold cross-validation. Answers Low, Medium or High with probabilities.'},
                       {'tag': 'Model C', 't': 'Cyclist profile', 'x': 'Random Forest with a ColumnTransformer (imputation + One-Hot). Answers with the probability of a previous injury.'}]},
            {'h': 'Why a Random Forest',
             'p': 'A Random Forest handles numeric and categorical variables with little tuning and reports how much each variable matters. '
                  'That second property is used in the Evaluation phase to explain the injury result. "Balanced" means the classes are weighted, because the injury classes are imbalanced.'},
            {'h': 'Comparing algorithms',
             'p': 'The notebook compares Random Forest and XGBoost and selects by macro-F1 in cross-validation, not by accuracy. In the earlier version of the injury model both were almost the same, so the Random Forest was kept.',
             'special': 'algo_compare'},
        ],
        'delivers': ['Three trained models exported as .joblib files', 'A comparison of Random Forest and XGBoost', 'The training scripts that reproduce every model'],
        'terms': [('Random Forest', 'Many decision trees that vote together. Each tree sees a different sample of the data.'),
                  ('Cross-validation', 'Training and testing several times on different slices of the data, to get a steadier score than a single split.'),
                  ('Stratified split', 'A split that keeps the proportion of each class equal in the training and test sets.'),
                  ('Class weights', 'Giving rare classes more importance so the model does not ignore them.')],
        'files': ['ml_engine/train_model.py', 'ml_engine/train_injury_model.py', 'ml_engine/train_cyclist_injury_model.py', 'ml_engine/model_artifacts/injury_model.joblib', 'ml_engine/models/injury_model_cyclist.joblib'],
        'qa': 'Results are compared with cross-validation and not with a single split. The files metrics.json and features.json belong to an earlier model version and are kept as history.',
    },
    # ------------------------------------------------------------------ 5
    {
        'slug': 'evaluation', 'n': 5, 'name': 'Evaluation', 'status': 'partial',
        'short': 'Measure the models honestly against the business goal.',
        'what': 'Evaluation asks two questions: how well does each model perform, and does that performance serve the goal defined in '
                'the first phase? A model can score well and still be useless for the business.',
        'glance': None,   # built from the metrics files in the template
        'blocks': [
            {'h': 'Why macro-F1',
             'p': 'The injury classes are imbalanced, so plain accuracy is misleading: a model that always answers the most common class already scores well. '
                  'Macro-F1 gives the same weight to each class, so it shows whether the rare, important classes are being detected.'},
            {'h': 'Results of the injury model', 'special': 'metrics'},
            {'h': 'Where the model is right and wrong', 'lead': 'Confusion matrix on the test set: rows are the real level, columns the predicted one.', 'special': 'confusion'},
            {'h': 'The other models', 'special': 'other_models'},
            {'h': 'Honest reading of the results',
             'callout': {'tone': 'warn', 't': 'Guidance only',
                         'x': 'For the injury model, accuracy is lower than the baseline of always predicting the most common class, so macro-F1 is the right metric and the result is guidance, not a diagnosis. The predictive signal is weak, and the Kaggle data is not about cyclists.'}},
            {'ul': ['Where it does help: it finds most of the high-risk cases, which is the costliest error to miss.',
                    'The plan classifier was trained on synthetic data built from rules for each level, so its results reflect those rules and not real cyclists.',
                    'Business criterion: besides the models, the application uses explainable rules (the weekly load traffic light and plan progress) that do not depend on these metrics.']},
        ],
        'delivers': ['Metrics saved as JSON and shown in this page', 'A confusion matrix and the feature importances', 'A written list of the limits of every model'],
        'terms': [('Accuracy', 'The share of predictions that were correct. Misleading when classes are imbalanced.'),
                  ('Macro-F1', 'The average F1 score of every class, counting each class equally.'),
                  ('Baseline', 'The score of a trivial strategy, such as always answering the most common class. A model must beat it to be worth using.'),
                  ('Recall', 'Of all real cases of a class, the share the model found.'),
                  ('Feature importance', 'How much each input variable contributes to the model\'s decisions.')],
        'files': ['ml_engine/model_artifacts/injury_metrics.json', 'ml_engine/metrics/injury_metrics.json'],
        'qa': 'Limits are stated openly: the injury model accuracy is below the majority-class baseline, and the plan classifier was trained on synthetic data and has no saved metrics yet.',
    },
    # ------------------------------------------------------------------ 6
    {
        'slug': 'deployment', 'n': 6, 'name': 'Deployment', 'status': 'done',
        'short': 'Put the models inside the web application, safely.',
        'what': 'Deployment makes the models useful: they are placed inside the application so that cyclists use them without knowing '
                'anything about machine learning.',
        'glance': [('3', 'models served by the app'), ('PostgreSQL', 'database (Supabase)'), ('0', 'workouts lost if a model fails')],
        'blocks': [
            {'h': 'From a trained model to a screen',
             'flow': [{'t': 'Export', 'x': 'Each training script saves its model with joblib (.joblib files).'},
                      {'t': 'Load lazily', 'x': 'The Flask services load the files on first use. If one is missing, the app still starts.'},
                      {'t': 'Validate', 'x': 'Every input is checked against fixed ranges before reaching a model.'},
                      {'t': 'Predict', 'x': 'The service builds the feature vector and the model answers.'},
                      {'t': 'Save and show', 'x': 'The result is stored in the database and shown to the cyclist.'}]},
            {'h': 'Where the cyclist uses each model',
             'cards': [{'tag': 'Model A', 't': 'Generate plan', 'x': 'Assigns the plan level.'},
                       {'tag': 'Model B', 't': 'Log workout, Injury check tab', 'x': 'Calculates the injury risk when the workout is saved.'},
                       {'tag': 'Model C', 't': 'Cyclist profile', 'x': 'Estimates the probability of a previous injury.'},
                       {'tag': 'Rules', 't': 'Dashboard', 'x': 'Explainable rules, not a model, give the weekly load traffic light.'}]},
            {'h': 'Data and safety',
             'ul': ['The data lives in PostgreSQL (Supabase). Tables are created at startup, and new columns are added without deleting existing data.',
                    'If the model fails, the workout is still saved and the user is notified.']},
            {'h': 'Architecture', 'p': 'The code is organized in four layers (presentation, control, business logic and data). See the Architecture page.'},
        ],
        'delivers': ['Exported .joblib models loaded by Flask services', 'Database tables for users, workouts, plans and injury checks', 'Input validation and error handling'],
        'terms': [('Serialization (joblib)', 'Saving a trained model to a file so another program can load it later.'),
                  ('Lazy loading', 'Loading something only when it is first needed, not when the application starts.'),
                  ('Input validation', 'Checking that every value is inside a sensible range before using it.'),
                  ('Schema update', 'Adding new database columns at startup without deleting the existing data.')],
        'files': ['app/services/ml_service.py', 'app/services/injury_service.py', 'app/services/injury_cyclist_service.py', 'app/services/schema_service.py', 'config.py'],
        'qa': 'Strict input validation (ranges in injury_service.LIMITS) and error handling that never loses a workout.',
    },
    # ------------------------------------------------------------------ 7
    {
        'slug': 'monitoring-maintenance', 'n': 7, 'name': 'Monitoring and maintenance', 'status': 'pending', 'ml_q': True,
        'short': 'Keep the models reliable once real people use them. Planned.',
        'what': 'CRISP-ML(Q) adds this phase to CRISP-DM because a deployed model slowly gets worse: people and data change. '
                'Monitoring detects the drop, and maintenance fixes it.',
        'glance': [('Planned', 'status: proposal, not in the code yet'), ('1', 'building block already in place'), ('4', 'next steps')],
        'blocks': [
            {'h': 'Roadmap', 'lead': 'What exists today and what comes next.',
             'flow': [{'t': 'Store predictions', 'x': 'Every injury check keeps its level and probabilities in the injury_checkins table.', 'status': 'done'},
                      {'t': 'Compare with reality', 'x': 'Check the stored predictions against injuries cyclists actually report.', 'status': 'next'},
                      {'t': 'Watch for drift', 'x': 'For example, compare the users\' average recovery score with the training dataset.', 'status': 'next'},
                      {'t': 'Retrain and version', 'x': 'Retrain with enough real records and version the files, for example injury_model_v2.joblib.', 'status': 'next'},
                      {'t': 'Save plan metrics', 'x': 'Store the evaluation metrics of the plan classifier, which are missing today.', 'status': 'next'}]},
            {'callout': {'tone': 'info', 't': 'Honest status',
                         'x': 'This phase is a proposal. It is not implemented in the code yet, and the documentation says so on purpose.'}},
        ],
        'delivers': ['A monitoring and maintenance proposal', 'The raw material for monitoring: stored predictions'],
        'terms': [('Data drift', 'When the data the model sees in real use slowly stops resembling the data it was trained on.'),
                  ('Retraining', 'Training the model again with newer data.'),
                  ('Model versioning', 'Keeping numbered copies of the model files, so a change can be traced or undone.'),
                  ('Ground truth', 'What really happened, for example an injury that the cyclist reports later.')],
        'files': ['app/models (InjuryCheckin table)', 'ml_engine/metrics/'],
        'qa': 'This extra phase is what CRISP-ML(Q) adds to CRISP-DM. It is planned, not implemented yet.',
    },
]

STATUS_LABEL = {'done': 'Done', 'partial': 'Partial', 'pending': 'Planned'}

# Injury dataset class sizes (Low, Medium, High), documented in the exploratory notebook
CLASS_DIST = [('Low', 9868), ('Medium', 3238), ('High', 2314)]


def get_phase(slug):
    for index, page in enumerate(PHASE_PAGES):
        if page['slug'] == slug:
            prev_page = PHASE_PAGES[index - 1] if index > 0 else None
            next_page = PHASE_PAGES[index + 1] if index + 1 < len(PHASE_PAGES) else None
            return page, prev_page, next_page
    return None, None, None


def phase_menu():
    """Light list used by the CRISP-DM drop-down menu and the step chips."""
    return [{'slug': p['slug'], 'n': p['n'], 'name': p['name']} for p in PHASE_PAGES]


def class_distribution():
    total = sum(n for _, n in CLASS_DIST)
    biggest = max(n for _, n in CLASS_DIST)
    return [{'label': label, 'n': n, 'pct': round(n / total * 100), 'width': round(n / biggest * 100)} for label, n in CLASS_DIST]

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please sign in to continue.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def create_app(config_object=None):
    # Read the variables of the .env file (DATABASE_URL, SECRET_KEY...) before config.py uses them.
    load_dotenv()

    from config import Config, DEFAULT_SECRET_KEY

    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    if app.config['SECRET_KEY'] == DEFAULT_SECRET_KEY:
        app.logger.warning('SECRET_KEY is not set: using the development key. Set it in your .env file.')

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from app.models.user import User
        from app.models.workout import Workout
        from app.models.plan import TrainingPlan, PlanDayDetail
        from app.models.injury import InjuryCheckin

        # First run: create every table in the configured database.
        db.create_all()
        from app.services.schema_service import ensure_columns
        ensure_columns(db, app.logger)

    from app.controllers.main import main_bp
    from app.controllers.auth import auth_bp
    from app.controllers.workouts import workouts_bp
    from app.controllers.plans import plans_bp
    from app.controllers.injury import injury_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(workouts_bp)
    app.register_blueprint(plans_bp)
    app.register_blueprint(injury_bp)

    return app

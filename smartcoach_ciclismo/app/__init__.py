from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = 'dev-key-secreta'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartcoach.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from app.models.user import User
        from app.models.workout import Workout 
        from app.models.plan import TrainingPlan, PlanDayDetail
        db.create_all()

    from app.controllers.main import main_bp
    from app.controllers.auth import auth_bp
    from app.controllers.workouts import workouts_bp
    from app.controllers.plans import plans_bp  
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(workouts_bp)
    app.register_blueprint(plans_bp)            

    return app
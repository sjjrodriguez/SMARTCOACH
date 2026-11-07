import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Inicia sesión para continuar.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return db.session.get(User, int(user_id))

def create_app():
    # Carga las variables del archivo .env (incluyendo tu DATABASE_URL de Supabase)
    load_dotenv()  
    
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-secreta')
    
    # Toma la URL de Supabase. Si no encuentra el .env, usará sqlite localmente.
    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+psycopg://postgres.sjsmwccpkrgkcgsdashw:TANIABELTRAN1864@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from app.models.user import User
        from app.models.workout import Workout 
        from app.models.plan import TrainingPlan, PlanDayDetail
        from app.models.injury import InjuryCheckin
        
        # Al ejecutar la app por primera vez, esto creará automáticamente 
        # todas estas tablas directamente en tu proyecto de Supabase
        db.create_all()

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
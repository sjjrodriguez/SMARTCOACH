from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('workouts.list_workouts'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        if User.query.filter_by(email=email).first():
            flash('El correo ya está registrado.')
            return redirect(url_for('auth.register'))
            
        new_user = User(
            full_name=request.form.get('full_name'),
            email=email,
            age=int(request.form.get('age', 18)),
            weight_kg=float(request.form.get('weight_kg', 70.0)),
            weekly_hours=float(request.form.get('weekly_hours', 5.0)),
            resting_heart_rate=int(request.form.get('resting_heart_rate', 60)),
            tss_acumulado=float(request.form.get('tss_acumulado', 0.0))
        )
        new_user.set_password(request.form.get('password'))
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('workouts.list_workouts'))
        
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('workouts.list_workouts'))
        
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('workouts.list_workouts'))
        flash('Correo o contraseña incorrectos.')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
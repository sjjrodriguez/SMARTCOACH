from urllib.parse import urlparse
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

MIN_PASSWORD = 8

def _safe_next(target):
    """Solo permite redirigir a rutas internas (evita open redirect).

    Browsers treat "\\" like "/", so "/\\evil.com" would leave the site: it is rejected too.
    """
    if (target and target.startswith('/') and not target.startswith('//')
            and '\\' not in target and not urlparse(target).netloc):
        return target
    return url_for('main.dashboard')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        full_name = (request.form.get('full_name') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''

        if not full_name or '@' not in email:
            flash('Please enter your full name and a valid email.', 'danger')
        elif len(password) < MIN_PASSWORD:
            flash(f'Password must be at least {MIN_PASSWORD} characters long.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('This email is already registered.', 'danger')
        else:
            user = User(full_name=full_name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Account created! Generate your plan to get started.', 'success')
            return redirect(url_for('plans.generate_plan'))

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(request.form.get('password') or ''):
            login_user(user)
            return redirect(_safe_next(request.args.get('next')))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/logout', methods=['POST'])
def logout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('auth.login'))
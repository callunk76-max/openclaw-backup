from flask import Blueprint, render_template, request, redirect, url_for, session, flash

auth_bp = Blueprint('auth', __name__, url_prefix='')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        from models import User
        user = User.query.filter_by(username=username, is_active=True).first()
        if user and user.check_password(password):
            session['user_id'] = user.id_user
            session['user_nama'] = user.nama
            session['user_role'] = user.role
            return redirect(url_for('dashboard.index'))
        flash('Username atau password salah!', 'error')
        return render_template('login.html')
    if session.get('user_id'):
        return redirect(url_for('dashboard.index'))
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

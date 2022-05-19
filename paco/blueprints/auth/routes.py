from datetime import datetime

from flask import render_template, redirect, url_for, request, flash, Blueprint
from paco import bcrypt, db
from paco.api.email import send_email
from flask_login import login_user, current_user, logout_user, login_required

from paco.blueprints.auth.forms import LoginForm, UserRegistrationForm, RequestResetPasswordForm, PasswordResetForm
from paco.models import User
from paco.tokens import generate_confirmation_token, confirm_token, generate_reset_token, verify_reset_token
from paco.utils import flash_form_errors

auth = Blueprint('auth', __name__, template_folder='templates', url_prefix='/auth')


@auth.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('user.dashboard'))
        else:
            flash('Email and password don\'t match. Please try again', 'danger')
    flash_form_errors(form)
    return render_template("login.html", form=form, title='Login')


@auth.route('/signup', methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = UserRegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
        )
        db.session.add(user)
        db.session.commit()

        flash('Your account has been created! Please verify your email', 'success')

        login_user(user, remember=True)

        return redirect(url_for('auth.verify_email'))
    else:
        flash_form_errors(form)
        return render_template("signup.html", form=form, title='Sign Up')


@auth.route('/logout', methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth.route('/verify_email', methods=["GET", "POST"])
@login_required
def verify_email():
    if not current_user.email_confirmed:
        # Generate confirmation email
        token = generate_confirmation_token(current_user.email)
        send_email([current_user.email],
                   'Please confirm your email',
                   render_template('emails/verification_email.html',
                                   confirm_url=url_for('auth.confirm_email', token=token, _external=True)))
        return render_template("verify_email.html", title="Verify Email")
    else:
        return redirect(url_for('user.dashboard'))


@auth.route('/verify_email/<token>', methods=["GET"])
def confirm_email(token):
    email = ''
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired', 'danger')
    user = User.query.filter_by(email=email).first_or_404()
    if user.email_confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.email_confirmed = True
        user.date_email_confirmed = datetime.utcnow()
        db.session.add(user)
        db.session.commit()
        flash('You successfully verified your account! Please log in.', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/reset_password', methods=["GET", "POST"])
def request_reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    form = RequestResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        print(user)
        if user:
            token = generate_reset_token(user)
            send_email([user.email],
                       'Please reset your password',
                       render_template('emails/reset_password_email.html',
                                       reset_url=url_for('auth.reset_password', token=token, _external=True)))
        return render_template('next_reset_password.html', current_user=current_user, title='Reset password', email=form.email.data)
    return render_template("request_reset_password.html", form=form, title='Reset password')

@auth.route('/reset_password/<token>', methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
    user = verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('main.request_reset_password'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('auth.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

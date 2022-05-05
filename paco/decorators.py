from flask_login.utils import current_user
from werkzeug.local import LocalProxy
from functools import wraps
from flask import redirect, url_for, flash


def email_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user.email_confirmed:
            return func(*args, **kwargs)
        else:
            flash('Before continuing, we need you to verify your email', 'danger')
            return redirect(url_for('verify_email'), code=303)

    return decorated_view

def driver_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user.is_driver:
            return func(*args, **kwargs)
        else:
            flash('Before continuing, you need to sign up as driver', 'danger')
            return redirect(url_for('become_driver'), code=303)

    return decorated_view
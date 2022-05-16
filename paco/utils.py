import os
import secrets

from PIL import Image
from flask_login.utils import current_user
from functools import wraps
from flask import redirect, url_for, flash

from paco import app


def email_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user.email_confirmed:
            return func(*args, **kwargs)
        else:
            flash('Before continuing, we need you to verify your email', 'danger')
            return redirect(url_for('auth.verify_email'), code=303)

    return decorated_view


def driver_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user.is_driver:
            return func(*args, **kwargs)
        else:
            flash('Before continuing, you need to sign up as driver', 'danger')
            return redirect(url_for('driver.create'), code=303)

    return decorated_view


def car_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user.get_license_plates():
            return func(*args, **kwargs)
        else:
            flash('Before continuing, you need to add a car', 'danger')
            return redirect(url_for('driver.add_car'), code=303)

    return decorated_view


def flash_form_errors(form):
    for elem in form:
        if elem.errors:
            for error in elem.errors:
                flash('{}: {}'.format(elem.label.text, error), "danger")


def human_readable_time(seconds):
    if (seconds - 60) < 0:
        # seconds
        return '{} s'.format(seconds)
    elif (seconds - 3600) < 0:
        # minutes
        minutes = int(seconds / 60)
        return '{} min, {} s'.format(minutes, seconds - minutes * 60)
    else:
        # hours
        hours = int(seconds / 3600)
        minutes = int(seconds / 60) - hours * 60
        return '{} h, {} min, {} s'.format(hours, minutes, seconds - hours * 3600 - minutes * 60)


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (150, 150)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

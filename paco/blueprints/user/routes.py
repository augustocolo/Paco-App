from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required

from paco import db
from paco.blueprints.driver.forms import DriverUpdateForm
from paco.blueprints.user.forms import UserUpdateForm
from paco.utils import email_required, flash_form_errors, save_picture

user = Blueprint('user', __name__, template_folder='templates', url_prefix='/user')


@user.route('/settings', methods=["GET"])
@login_required
@email_required
def settings():
    user_info_form = UserUpdateForm(
        username=current_user.username,
        email=current_user.email
    )
    driver_info_form = None
    driver = current_user.get_driver_info()
    if current_user.is_driver:
        driver_info_form = DriverUpdateForm(
            name=driver.name,
            surname=driver.surname,
            gender=driver.gender,
            date_of_birth=driver.date_of_birth,
            town_of_birth=driver.town_of_birth,
            country_of_birth=driver.country_of_birth,
            fiscal_code=driver.fiscal_code,
            phone_number=driver.phone_number,
            address_street=driver.address_street,
            address_town=driver.address_town,
            address_zip_code=driver.address_zip_code,
            address_country=driver.address_country,
            license_code =driver.license_number,
            license_expiration=driver.license_expiration,
            license_issuing_authority=driver.license_issuing_authority
        )
    return render_template('user_settings.html', title='Settings', current_user=current_user, user_info_form=user_info_form, driver_info_form=driver_info_form)




@user.route('/update', methods=["POST"])
@login_required
@email_required
def update():
    form = UserUpdateForm()
    if form.validate_on_submit():
        if current_user.username != form.username.data:
            current_user.username = form.username.data
        if current_user.email != form.email.data:
            current_user.email = form.email.data
            current_user.email_confirmed = False
            current_user.date_email_confirmed = None
        if form.image_file.data:
            filename = save_picture(form.image_file.data)
            current_user.image_file=filename
        db.session.commit()

    flash_form_errors(form)
    return redirect(url_for('user.settings'))

from flask import render_template, redirect, url_for, request, flash, json, abort
from paco import app, db, bcrypt
from paco.forms import *
from paco.models import *
from paco.email import send_email
from flask_login import login_user, current_user, logout_user, login_required
from flask_googlemaps import Map
from paco.tokens import *
from datetime import datetime
from paco.directions import get_distance_between
from paco.pricing import get_price
from paco.decorators import email_required, driver_required
from paco.api import license_plates


def flash_form_errors(form):
    for elem in form:
        if elem.errors:
            for error in elem.errors:
                flash('{}: {}'.format(elem.label.text, error), "danger")


@app.route('/')
def index():
    form = SendParcelFormIntro()
    towns = set()
    for locker in db.session.query(Locker.town):
        towns.add(locker[0])
    return render_template("landing_user.html", title='Home', current_user=current_user, towns=towns, form=form)


# USER AUTHENTICATION ACTIONS

@app.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('show_dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('show_dashboard'))
    return render_template("authentication/login.html", form=form, title='Login')


@app.route('/signup', methods=["GET", "POST"])
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

        return redirect(url_for('verify_email'))
    else:
        flash_form_errors(form)
        return render_template("authentication/signup.html", form=form, title='Sign Up')


@app.route('/logout', methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/verify_email', methods=["GET", "POST"])
@login_required
def verify_email():
    if not current_user.email_confirmed:
        # Generate confirmation email
        token = generate_confirmation_token(current_user.email)
        confirm_url = url_for('confirm_email', token=token, _external=True)
        html = render_template('emails/confirmation_email.html', confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email(current_user.email, subject, html)
        return render_template("authentication/verify_email.html", title="Verify Email")
    else:
        return redirect(url_for('show_dashboard'))


@app.route('/verify_email/<token>', methods=["GET"])
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
    return redirect(url_for('login'))


@app.route('/driver/create', methods=["GET", "POST"])
@login_required
@email_required
def become_driver():
    if current_user.is_driver:
        flash('You are already a driver', 'danger')
        return redirect(url_for('show_dashboard'))
    form = DriverSignupForm()
    if form.validate_on_submit():
        driver = DriverInfo(
            id=current_user.id,
            name=form.name.data,
            surname=form.surname.data,
            gender=bool(form.gender.data),
            date_of_birth=form.date_of_birth.data,
            town_of_birth=form.town_of_birth.data,
            country_of_birth=form.country_of_birth.data,
            fiscal_code=form.fiscal_code.data,
            phone_number=form.phone_number.data,
            address_street=form.address_street.data,
            address_town=form.address_town.data,
            address_zip_code=form.address_zip_code.data,
            address_country=form.address_country.data,
            license_number=form.license_code.data,
            license_expiration=form.license_expiration.data,
            license_issuing_authority=form.license_issuing_authority.data
        )
        current_user.is_driver = True
        db.session.add(driver)
        db.session.commit()
        flash('You succesfully signed up as driver. Now insert your car\'s information', 'success')
        return redirect(url_for('add_car'))

    flash_form_errors(form)

    return render_template("authentication/signup_driver.html", title="Become a driver", form=form)


@app.route('/driver/car/add', methods=["GET", "POST"])
@login_required
@email_required
@driver_required
def add_car():
    form = CarInfoAddForm()
    if form.validate_on_submit():
        info = license_plates.get_car_info(form.license_plate.data)
        if info:
            form2 = CarInfoConfirmForm(
                license_plate=form.license_plate.data,
                car_make=info['CarMake']['CurrentTextValue'],
                car_model=info['CarModel']['CurrentTextValue'],
                fuel_type=info['FuelType']['CurrentTextValue'],
                power_cv=info['PowerCV'],
                registration_year=int(info['RegistrationYear'])
            )
            return render_template('car/confirm.html', title='Confirm car', form=form2, car_image=info['ImageUrl'])
        else:
            flash('Please insert a valid license plate', 'danger')
    flash_form_errors(form)
    return render_template('car/add.html', title='Add a car', form=form)

@app.route('/driver/car/confirm', methods=["POST"])
@login_required
@email_required
@driver_required
def confirm_car():
    form = CarInfoConfirmForm()
    if form.validate_on_submit():
        car = CarInfo(
            license_plate=form.license_plate.data,
            driver_id=current_user.id,
            car_make=form.car_make.data,
            car_model=form.car_model.data,
            fuel_type=form.fuel_type.data,
            registration_year=form.registration_year.data,
            power_cv=form.power_cv.data
        )
        db.session.add(car)
        db.session.commit()
        flash('You succesfully added {} to your cars'.format(form.license_plate.data), 'success')
    flash_form_errors(form)
    return redirect(url_for('show_dashboard'))


# DASHBOARD ACTIONS

@app.route('/dashboard')
@login_required
@email_required
def show_dashboard():
    deliveries = current_user.get_deliveries_sent()
    total_spent = current_user.get_spent_last_month()
    delivery_count = current_user.get_delivery_count_last_month()

    return render_template("dashboard.html", title="Dashboard",
                           current_user=current_user, deliveries=deliveries,
                           total_spent_last_month=Delivery.format_price(total_spent),
                           delivery_count_last_month=delivery_count)


# CREATE DELIVERY ACTIONS

@app.route('/delivery/create', methods=['GET', 'POST'])
@login_required
@email_required
def create_delivery():
    form = SendParcelFormIntro()
    if form.validate_on_submit():
        # prendi locker in città
        send_from_lockers = Locker.query.filter_by(town=form.send_from.data).all()
        send_to_lockers = Locker.query.filter_by(town=form.send_to.data).all()

        # Create Google Maps
        gmap_style = "width:100%;margin:0;height:200px"
        map_from = Map(
            identifier='map_from',
            lat=send_from_lockers[0].latitude,
            lng=send_from_lockers[0].longitude,
            markers=[{'lat': locker.latitude,
                      'lng': locker.longitude,
                      'label': str(locker.id),
                      'infobox': '<b>{}</b><br>{}<br>{}<br>{} {}<br>Italy<br><br><a href="{}" target="_blank" '
                                 'rel="noopener noreferrer">Get directions</a>'.format(locker.name, locker.address,
                                                                                       locker.zip_code, locker.town,
                                                                                       locker.province,
                                                                                       locker.get_google_maps_directions())}
                     for locker in send_from_lockers],
            fit_markers_to_bounds=True,
            style=gmap_style,
            zoom_control=False,
            maptype_control=False,
            streetview_control=False,
            rotate_control=False,
            fullscreen_control=False
        )

        map_to = Map(
            identifier='map_to',
            lat=send_to_lockers[0].latitude,
            lng=send_to_lockers[0].longitude,
            markers=[{'lat': locker.latitude,
                      'lng': locker.longitude,
                      'label': str(locker.id),
                      'infobox': '<b>{}</b><br>{}<br>{}<br>{} {}<br>Italy<br><br><a href="{}" target="_blank" '
                                 'rel="noopener noreferrer">Get directions</a>'.format(locker.name, locker.address,
                                                                                       locker.zip_code, locker.town,
                                                                                       locker.province,
                                                                                       locker.get_google_maps_directions())}
                     for locker in send_to_lockers],
            fit_markers_to_bounds=True,
            style=gmap_style,
            zoom_control=False,
            maptype_control=False,
            streetview_control=False,
            rotate_control=False,
            fullscreen_control=False,
        )

        form2 = SendParcelFormLockerChoice(sender_id=current_user.id, weight=form.weight.data,
                                           dimension=form.box_size.data)
        form2.locker_source_id.choices = [(locker.id, locker.name) for locker in send_from_lockers]
        form2.locker_destination_id.choices = [(locker.id, locker.name) for locker in send_to_lockers]

        return render_template("delivery/create/create_delivery_choose_lockers.html",
                               title="Choose Lockers", current_user=current_user, form=form2,
                               from_town=form.send_from.data,
                               to_town=form.send_to.data,
                               text_dimension=Delivery.dimension_from_int_to_text(form.box_size.data),
                               map_from=map_from, map_to=map_to)
    else:
        flash_form_errors(form)
        towns = set()
        for locker in db.session.query(Locker.town):
            towns.add(locker[0])
        return render_template("delivery/create/create_delivery.html", title="Create Delivery",
                               current_user=current_user, towns=towns,
                               form=form)


@app.route('/delivery/create/locker_choice', methods=['POST'])
@login_required
def send_locker_choice():
    form = SendParcelFormLockerChoice()
    lockers = Locker.query.all()
    form.locker_source_id.choices = [(locker.id, locker.name) for locker in lockers]
    form.locker_destination_id.choices = [(locker.id, locker.name) for locker in lockers]

    if form.validate_on_submit():
        locker_source = Locker.query.filter_by(id=form.locker_source_id.data).first()
        locker_destination = Locker.query.filter_by(id=form.locker_destination_id.data).first()

        distance = get_distance_between(
            origin=(locker_source.latitude, locker_source.longitude),
            destination=(locker_destination.latitude, locker_destination.longitude)
        )

        price = get_price(distance, int(form.dimension.data), int(form.weight.data))
        form2 = SendParcelFormConfirmation(
            sender_id=form.sender_id.data,
            locker_source_id=form.locker_source_id.data,
            locker_destination_id=form.locker_destination_id.data,
            weight=form.weight.data,
            dimension=form.dimension.data,
            distance=distance,
            price=price
        )

        return render_template("delivery/create/create_delivery_confirm.html",
                               title="Choose Lockers", current_user=current_user, form=form2,
                               from_locker='{} - {}'.format(locker_source.town, locker_source.name),
                               to_locker='{} - {}'.format(locker_destination.town, locker_destination.name),
                               text_dimension=Delivery.dimension_from_int_to_text(form.dimension.data),
                               distance='{} km'.format(int(distance / 1000)),
                               price=Delivery.format_price(price))
    else:
        flash_form_errors(form)
        form2 = SendParcelFormIntro()
        towns = set()
        for locker in db.session.query(Locker.town):
            towns.add(locker[0])
        return render_template("delivery/create/create_delivery.html", title="Create Delivery",
                               current_user=current_user, towns=towns,
                               form=form2)


@app.route('/delivery/create/confirm', methods=["POST"])
@login_required
def confirm_delivery():
    form = SendParcelFormConfirmation()

    if form.validate_on_submit():
        delivery = Delivery(
            sender_id=form.sender_id.data,
            locker_source_id=form.locker_source_id.data,
            locker_destination_id=form.locker_destination_id.data,
            weight=form.weight.data,
            dimension=form.dimension.data,
            distance=form.distance.data,
            price=form.price.data
        )
        db.session.add(delivery)
        db.session.commit()

        return redirect(url_for('show_dashboard'))
    else:
        flash("There was an error while processing your request. Try again!", "danger")
        return redirect(url_for('create_delivery'))


# Locker management

@app.route('/locker/<int:id>/qr', methods=["GET"])
def show_locker_qr(id):
    locker = Locker.query.filter_by(id=id).first()

    qr_info = {
        'app': 'paco',
        'token': generate_locker_qr(locker.id)
    }

    return render_template("locker_qr.html",
                           title="Locker {}".format(locker.name), locker=locker, qr_info=json.dumps(qr_info))


# Tracking

@app.route('/delivery/track/<int:id>')
@login_required
def track_delivery(id):
    delivery = Delivery.query.filter_by(id=id).first()

    gmap_style = "width:100%;margin:0;height:200px"
    map = Map(
        identifier='map',
        lat=delivery.get_locker_source().latitude,
        lng=delivery.get_locker_source().longitude,
        markers=[{'lat': delivery.get_locker_source().latitude,
                  'lng': delivery.get_locker_source().longitude,
                  'label': 'O',
                  'infobox': '<b>{}</b><br>{}<br>{}<br>{} {}<br>Italy'.format(delivery.get_locker_source().name,
                                                                              delivery.get_locker_source().address,
                                                                              delivery.get_locker_source().zip_code,
                                                                              delivery.get_locker_source().town,
                                                                              delivery.get_locker_source().province)},
                 {'lat': delivery.get_locker_destination().latitude,
                  'lng': delivery.get_locker_destination().longitude,
                  'label': 'D',
                  'infobox': '<b>{}</b><br>{}<br>{}<br>{} {}<br>Italy'.format(delivery.get_locker_destination().name,
                                                                              delivery.get_locker_destination().address,
                                                                              delivery.get_locker_destination().zip_code,
                                                                              delivery.get_locker_destination().town,
                                                                              delivery.get_locker_destination().province)},
                 ],
        fit_markers_to_bounds=True,
        style=gmap_style,
        zoom_control=False,
        maptype_control=False,
        streetview_control=False,
        rotate_control=False,
        fullscreen_control=False
    )

    print(delivery)
    if delivery:
        return render_template("delivery/track.html", title='Tracking', delivery=delivery, map=map)
    else:
        return abort(404)

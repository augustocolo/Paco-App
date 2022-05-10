from flask import Blueprint, flash, redirect, url_for, render_template
from flask_googlemaps import Map
from flask_login import login_required, current_user

from paco import db, gmaps
from paco.api import license_plates
from paco.api.optimization import solve_session_knapsack
from paco.blueprints.driver.forms import CarInfoAddForm, CarInfoConfirmForm, DriverSignupForm, SessionStartForm, \
    SessionConfirmForm
from paco.models import DriverInfo, CarInfo, Locker, Delivery, DriverSession, DriverSessionDelivery
from paco.utils import email_required, driver_required, flash_form_errors, human_readable_time

driver = Blueprint('driver', __name__, template_folder='templates', url_prefix='/driver')


@driver.route('/create', methods=["GET", "POST"])
@login_required
@email_required
def create():
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
        return redirect(url_for('driver.add_car'))

    flash_form_errors(form)

    return render_template("signup_driver.html", title="Become a driver", form=form)


@driver.route('/car/add', methods=["GET", "POST"])
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


@driver.route('/car/confirm', methods=["POST"])
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
        return redirect(url_for('show_dashboard'))

    flash_form_errors(form)
    return redirect(url_for('driver.add_car'))


@driver.route('/session/start', methods=["GET", "POST"])
@login_required
@email_required
@driver_required
def start_session():
    if current_user.is_in_driving_session():
        flash('You cannot start a new driving session! Please complete the one you\'ve started', 'danger')
        return redirect(url_for('show_dashboard'))
    form = SessionStartForm()
    license_plates = current_user.get_license_plates()
    form.license_plate.choices = [
        (car.license_plate, '{} {} ({})'.format(car.car_make, car.car_model, car.license_plate)) for car in
        license_plates]
    if form.validate_on_submit():
        # Get start point
        from_coords = []
        from_address_geocoded = gmaps.geocode(form.from_location.data)
        from_coords = [from_address_geocoded[0]['geometry']['location']['lat'],
                       from_address_geocoded[0]['geometry']['location']['lng']]

        lockers_near_source = Locker.get_lockers_near_source(
            from_coords[0],
            from_coords[1]
        )

        if not lockers_near_source:
            flash('There are no deliveries available near your starting point.', 'danger')
            return redirect(url_for('show_dashboard'))

        # Get end point
        to_address_geocoded = gmaps.geocode(form.to_location.data)
        to_coords = [to_address_geocoded[0]['geometry']['location']['lat'],
                     to_address_geocoded[0]['geometry']['location']['lng']]

        lockers_near_destination = Locker.get_lockers_near_destination(
            to_coords[0],
            to_coords[1]
        )

        if not lockers_near_destination:
            flash('There are no deliveries available near your arrival.', 'danger')
            return redirect(url_for('show_dashboard'))

        # Get deliveries in route

        route_deliveries = Delivery.query.filter(
            Delivery.locker_source_id.in_([locker.id for locker in lockers_near_source]),
            Delivery.locker_destination_id.in_([locker.id for locker in lockers_near_destination]),
            Delivery.sender_id != current_user.id,
            Delivery.driver_id == None,
            Delivery.status == 1
        ).all()

        if not route_deliveries:
            flash('There are no deliveries available at the moment.', 'danger')
            return redirect(url_for('show_dashboard'))

        # Get set of deliveries, maximize for price, bound is max capacity
        max_price = 0
        solution = []

        for source_locker in lockers_near_source:
            for destination_locker in lockers_near_destination:
                deliveries = Delivery.query.filter(
                    Delivery.locker_source_id == source_locker.id,
                    Delivery.locker_destination_id == destination_locker.id,
                    Delivery.sender_id != current_user.id,
                    Delivery.driver_id == None,
                    Delivery.status == 1
                ).all()

                if deliveries:
                    sol, price, used_cap = solve_session_knapsack(deliveries, form.liters_available.data)
                    if price > max_price:
                        max_price = price
                        solution = sol
        if solution:
            form_deliveries_string = ''
            for elem in solution:
                form_deliveries_string += str(elem.id) + ','
            form2 = SessionConfirmForm(
                license_plate=form.license_plate.data,
                from_location_geocoded=from_address_geocoded[0]['formatted_address'],
                to_location_geocoded=to_address_geocoded[0]['formatted_address'],
                deliveries=form_deliveries_string
            )

            # Get car info
            car_info = CarInfo.query.filter_by(license_plate=form.license_plate.data).first()

            # Calculate reward
            reward_to_driver = 0
            for parcel in solution:
                reward_to_driver += int(parcel.price * car_info.get_price_percentage())

            # Get map
            gmap_style = "width:100%;margin:0;height:200px"
            map = Map(
                identifier='map',
                lat=solution[0].get_locker_source().latitude,
                lng=solution[0].get_locker_source().longitude,
                markers=[{'lat': solution[0].get_locker_source().latitude,
                          'lng': solution[0].get_locker_source().longitude,
                          'label': '2',
                          'infobox': '<b>{}</b><br>{}<br>{}<br>{} {}<br>Italy'.format(
                              solution[0].get_locker_source().name,
                              solution[0].get_locker_source().address,
                              solution[0].get_locker_source().zip_code,
                              solution[0].get_locker_source().town,
                              solution[0].get_locker_source().province)},
                         {'lat': solution[0].get_locker_destination().latitude,
                          'lng': solution[0].get_locker_destination().longitude,
                          'label': '3',
                          'infobox': '<b>{}</b><br>{}<br>{}<br>{} {}<br>Italy'.format(
                              solution[0].get_locker_destination().name,
                              solution[0].get_locker_destination().address,
                              solution[0].get_locker_destination().zip_code,
                              solution[0].get_locker_destination().town,
                              solution[0].get_locker_destination().province)},
                         {'lat': from_coords[0],
                          'lng': from_coords[1],
                          'label': '1',
                          'infobox': from_address_geocoded[0]['formatted_address']},
                         {'lat': to_coords[0],
                          'lng': to_coords[1],
                          'label': '4',
                          'infobox': to_address_geocoded[0]['formatted_address']}
                         ],
                fit_markers_to_bounds=True,
                style=gmap_style,
                zoom_control=False,
                maptype_control=False,
                streetview_control=False,
                rotate_control=False,
                fullscreen_control=False
            )

            # Directions
            directions = gmaps.directions(
                from_coords,
                to_coords,
                waypoints=[
                    [solution[0].get_locker_source().latitude, solution[0].get_locker_source().longitude],
                    [solution[0].get_locker_destination().latitude, solution[0].get_locker_destination().longitude]
                ],
                mode='driving',
                alternatives=False,
                units='metric'
            )
            total_duration = 0
            total_distance = 0
            for leg in directions[0]['legs']:
                total_distance += leg['distance']['value']
                total_duration += leg['duration']['value']

            return render_template('session/confirm.html', title="Confirm driving session", current_user=current_user,
                                   form=form2,
                                   formatted_car='{} {} ({})'.format(car_info.car_make, car_info.car_model,
                                                                     car_info.license_plate),
                                   from_locker='Locker {}: {}'.format(solution[0].get_locker_source().id,
                                                                      solution[0].get_locker_source().name),
                                   to_locker='Locker {}: {}'.format(solution[0].get_locker_destination().id,
                                                                    solution[0].get_locker_destination().name),
                                   reward_to_driver=Delivery.format_price(reward_to_driver),
                                   solution=solution,
                                   map=map,
                                   total_distance=int(total_distance / 1000),
                                   total_duration=human_readable_time(total_duration)
                                   )
        else:
            flash('There are no deliveries available for you at the moment.', 'danger')
            return redirect(url_for('show_dashboard'))

    flash_form_errors(form)
    return render_template('session/start.html', current_user=current_user, title="Start driving session", form=form)


@driver.route('/session/confirm', methods=["POST"])
@login_required
@email_required
@driver_required
def confirm_session():
    form = SessionConfirmForm()
    if form.validate_on_submit():
        deliveries = []
        # GET CAR INFO
        car_info = CarInfo.query.filter_by(license_plate=form.license_plate.data).first()
        # UPDATE DELIVERY
        for delivery_string in form.deliveries.data.split(',')[:-1]:
            delivery = Delivery.query.filter_by(id=delivery_string).first()
            delivery.driver_id = current_user.id
            deliveries.append(delivery)
        # CREATE DRIVER SESSION
        session = DriverSession(
            driver_id=current_user.id,
            license_plate=form.license_plate.data,
            start_address=form.from_location_geocoded.data,
            end_address=form.to_location_geocoded.data
        )
        db.session.add(session)
        db.session.commit()

        # LINK DELIVERY TO DRIVER SESSION
        for delivery in deliveries:
            delivery_session = DriverSessionDelivery(
                session_id=session.id,
                delivery_id=delivery.id,
                earned_amount=int(delivery.price * car_info.get_price_percentage())
            )
            db.session.add(delivery_session)

        db.session.commit()
        return redirect(url_for('driver.next_step_session'))

    flash_form_errors(form)
    return redirect(url_for('driver.start_session'))


@driver.route('/session/next', methods=["GET"])
@login_required
@email_required
@driver_required
def next_step_session():
    session = current_user.get_active_session()
    if session:
        deliveries = session.get_deliveries()

        # Get map
        gmap_style = "width:100%;margin:0;height:200px"
        map = Map(
            identifier='map',
            lat=deliveries[0].get_locker_source().latitude,
            lng=deliveries[0].get_locker_source().longitude,
            markers=[{'lat': deliveries[0].get_locker_source().latitude,
                      'lng': deliveries[0].get_locker_source().longitude,
                      'label': 'O',
                      'infobox': '<b>{}</b><br>{}<br>{}<br>{} {}<br>Italy'.format(
                          deliveries[0].get_locker_source().name,
                          deliveries[0].get_locker_source().address,
                          deliveries[0].get_locker_source().zip_code,
                          deliveries[0].get_locker_source().town,
                          deliveries[0].get_locker_source().province)},
                     {'lat': deliveries[0].get_locker_destination().latitude,
                      'lng': deliveries[0].get_locker_destination().longitude,
                      'label': 'D',
                      'infobox': '<b>{}</b><br>{}<br>{}<br>{} {}<br>Italy'.format(
                          deliveries[0].get_locker_destination().name,
                          deliveries[0].get_locker_destination().address,
                          deliveries[0].get_locker_destination().zip_code,
                          deliveries[0].get_locker_destination().town,
                          deliveries[0].get_locker_destination().province)},
                     ],
            fit_markers_to_bounds=True,
            style=gmap_style,
            zoom_control=False,
            maptype_control=False,
            streetview_control=False,
            rotate_control=False,
            fullscreen_control=False
        )
        if deliveries[0].status == 1:
            return render_template('session/next.html', current_user=current_user, title='Go to {}'.format(deliveries[0].get_locker_source().name),
                                   session=session, deliveries=deliveries, map=map)
            pass
        elif deliveries[0].status == 2:
            # Go to second locker
            pass
        else:
            flash('This session is not valid.', 'danger')
            return redirect(url_for('show_dashboard'))

    else:
        flash('It looks like you don\'t have an active session, please start one.', 'danger')
        return redirect(url_for(start_session))

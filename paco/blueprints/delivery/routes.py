from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_googlemaps import Map
from flask_login import login_required, current_user

from paco import db, gmaps
from paco.api.email import send_email
from paco.api.pricing import get_price
from paco.blueprints.delivery.forms import SendParcelFormIntro, SendParcelFormLockerChoice, SendParcelFormConfirmation
from paco.models import Locker, Delivery
from paco.utils import email_required, flash_form_errors

delivery = Blueprint('delivery', __name__, template_folder='templates', url_prefix='/delivery')


@delivery.route('/create', methods=['GET', 'POST'])
@login_required
@email_required
def create():
    form = SendParcelFormIntro()
    if form.validate_on_submit():
        # Get lockers in selected towns
        send_from_lockers_all = Locker.query.filter_by(town=form.send_from.data).all()
        send_to_lockers_all = Locker.query.filter_by(town=form.send_to.data).all()

        # Filter lockers with available spaces
        send_from_lockers = []
        for locker in send_from_lockers_all:
            if locker.has_space_free(form.box_size.data):
                send_from_lockers.append(locker)

        send_to_lockers = []
        for locker in send_to_lockers_all:
            if locker.has_space_free(form.box_size.data):
                send_to_lockers.append(locker)


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

        return render_template("create/create_delivery_choose_lockers.html",
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
        return render_template("create/create_delivery.html", title="Create Delivery",
                               current_user=current_user, towns=towns,
                               form=form)


@delivery.route('/create/locker_choice', methods=['POST'])
@login_required
def create_locker_choice():
    form = SendParcelFormLockerChoice()
    lockers = Locker.query.all()
    form.locker_source_id.choices = [(locker.id, locker.name) for locker in lockers]
    form.locker_destination_id.choices = [(locker.id, locker.name) for locker in lockers]

    if form.validate_on_submit():
        locker_source = Locker.query.filter_by(id=form.locker_source_id.data).first()
        locker_destination = Locker.query.filter_by(id=form.locker_destination_id.data).first()

        directions = gmaps.directions(
            [locker_source.latitude, locker_source.longitude],
            [locker_destination.latitude, locker_destination.longitude],
            mode='driving',
            alternatives=False,
            units='metric'
        )
        distance = directions[0]['legs'][0]['distance']['value']


        price = get_price(distance, int(form.dimension.data), int(form.weight.data), fragile=bool(form.fragile.data))
        form2 = SendParcelFormConfirmation(
            sender_id=form.sender_id.data,
            locker_source_id=form.locker_source_id.data,
            locker_destination_id=form.locker_destination_id.data,
            weight=form.weight.data,
            dimension=form.dimension.data,
            distance=distance,
            price=price,
            fragile=form.fragile.data
        )

        return render_template("create/create_delivery_confirm.html",
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
        return redirect(url_for('delivery.create'))


@delivery.route('/create/confirm', methods=["POST"])
@login_required
def confirm():
    form = SendParcelFormConfirmation()

    if form.validate_on_submit():
        # Add delivery
        email_recipient = form.email_recipient.data if form.email_recipient.data else None
        delivery = Delivery(
            sender_id=form.sender_id.data,
            locker_source_id=form.locker_source_id.data,
            locker_destination_id=form.locker_destination_id.data,
            weight=form.weight.data,
            dimension=form.dimension.data,
            distance=form.distance.data,
            price=form.price.data,
            email_recipient=email_recipient,
            tracking_id=Delivery.generate_tracking_id(),
            fragile=form.fragile.data
        )
        db.session.add(delivery)
        db.session.commit()

        # Reserve space
        delivery.get_locker_source().reserve_space(delivery)
        delivery.get_locker_destination().reserve_space(delivery)
        db.session.commit()

        # Send email
        mail_recipients = [delivery.get_sender().email]
        if delivery.email_recipient:
            mail_recipients.append(delivery.email_recipient)
        send_email(mail_recipients,
                   'Paco - Delivery {} created'.format(delivery.tracking_id),
                   render_template('emails/delivery_update_created.html', delivery=delivery))

        return redirect(url_for('user.dashboard'))
    else:
        flash("There was an error while processing your request. Try again!", "danger")
        return redirect(url_for('delivery.create'))

@delivery.route('/track/<string:tracking_id>')
def track(tracking_id):
    delivery = Delivery.query.filter_by(tracking_id=tracking_id).first()
    if delivery:
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

        return render_template("track.html", title='Tracking', delivery=delivery, map=map)
    else:
        return abort(404)
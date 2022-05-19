import json

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, AnonymousUserMixin, UserMixin
from datetime import datetime
from paco import app, db
from paco.api.email import send_email
from paco.blueprints.locker.forms import LockerPickUpForm

from paco.models import Locker, Delivery, LockerSpace
from paco.tokens import generate_locker_qr, confirm_qr
from paco.utils import flash_form_errors

locker = Blueprint('locker', __name__, template_folder='templates', url_prefix='/locker')


@locker.route('/qr/show/<int:id>', methods=["GET"])
def show_locker_qr(id):
    locker = Locker.query.filter_by(id=id).first()
    token = generate_locker_qr(locker.id)
    qr_info = '{}locker/qr/{}'.format(request.host_url, token)

    return render_template("locker_qr.html",
                           title="Locker {}".format(locker.name), locker=locker, qr_info=qr_info, debug=app.debug)


@locker.route('/qr/<string:token>', methods=["GET"])
def process_qr_locker(token):
    # This function redirects to process delivery with a string indicating the deliveries assigned to that user/driver.
    # if the user/driver doesn't have deliveries in the locker
    locker_id = confirm_qr(token)
    delivery_string = ''
    if locker_id:
        if isinstance(current_user, UserMixin):
            # Get deliveries
            sender_deliveries = Delivery.query.filter(
                (Delivery.locker_source_id == locker_id) & (Delivery.sender_id == current_user.id) & (
                        Delivery.status == 0)
            ).all()

            driver_deliveries = Delivery.query.filter(
                ((Delivery.locker_source_id == locker_id) | (Delivery.locker_destination_id == locker_id)) & (
                        Delivery.driver_id == current_user.id) & ((Delivery.status == 1) | (Delivery.status == 2))
            ).all()

            if len(sender_deliveries) + len(driver_deliveries) > 0:
                for delivery in sender_deliveries:
                    delivery_string += str(delivery.id) + ","
                for delivery in driver_deliveries:
                    delivery_string += str(delivery.id) + ","
            return redirect(url_for('locker.process_deliveries', locker_id=locker_id, delivery_string=delivery_string))
        else:
            return redirect(url_for('locker.locker_pickup', locker_id=locker_id))

    flash('Please scan again the locker QR code.', 'danger')
    return redirect(url_for('main.scan_qr'))


@locker.route('/process')
def process_deliveries():
    locker_id = int(request.args.get('locker_id'))
    delivery_string = request.args.get('delivery_string')
    if locker_id:
        if delivery_string:
            delivery_ids = delivery_string.split(",")[:-1]
            delivery_id = int(delivery_ids.pop(0))
            delivery = Delivery.query.filter_by(id=delivery_id).first()
            if delivery:
                mail_recipients = [delivery.get_sender().email]
                if delivery.email_recipient:
                    mail_recipients.append(delivery.email_recipient)
                locker_space_source = LockerSpace.query.filter_by(delivery_id=delivery_id, locker_id=delivery.get_locker_source().id).first()
                locker_space_destination = LockerSpace.query.filter_by(delivery_id=delivery_id, locker_id=delivery.get_locker_destination().id).first()
                delivery_string = ''
                if isinstance(current_user, UserMixin):
                    for id in delivery_ids:
                        delivery_string += str(id) + ','
                    if delivery.status == 0 and delivery.sender_id == current_user.id:
                        # sender delivers package to source locker
                        # change delivery status
                        delivery.status = 1
                        delivery.date_source_arrived = datetime.utcnow()
                        db.session.commit()
                        # send mail
                        send_email(mail_recipients,
                                   'Paco - Delivery {} update'.format(delivery.tracking_id),
                                   render_template('emails/delivery_update_arrived_at_source_locker.html', delivery=delivery))
                        # show message
                        return render_template('process.html', title='Process delivery', current_user=current_user,
                                               action_string='put', locker_space=locker_space_source, delivery_string=delivery_string, delivery=delivery, locker_id=locker_id)
                    elif delivery.status == 1 and delivery.driver_id == current_user.id:
                        # driver picks up package from source locker
                        # change delivery status
                        delivery.status = 2
                        delivery.date_source_departed = datetime.utcnow()
                        # free locker space
                        locker_space_source.free_space()
                        db.session.commit()
                        # send mail
                        send_email(mail_recipients,
                                   'Paco - Delivery {} update'.format(delivery.tracking_id),
                                   render_template('emails/delivery_update_picked_up_by_driver.html',
                                                   delivery=delivery))
                        return render_template('process.html', title='Process delivery', current_user=current_user,
                                               action_string='pick up', locker_space=locker_space_source,
                                               delivery_string=delivery_string, delivery=delivery, locker_id=locker_id)
                    elif delivery.status == 2 and delivery.driver_id == current_user.id:
                        # driver delivers package to destination locker
                        # change delivery status
                        delivery.status = 3
                        delivery.date_destination_arrived = datetime.utcnow()
                        # close driver session
                        if not Delivery.query.filter_by(driver_id=current_user.id, status=2).all():
                            current_user.get_active_session().date_ended = datetime.utcnow()
                        db.session.commit()
                        # send mail
                        send_email(mail_recipients,
                                   'Paco - Delivery {} update'.format(delivery.tracking_id),
                                   render_template('emails/delivery_update_arrived_at_destination_locker.html',
                                                   delivery=delivery))
                        return render_template('process.html', title='Process delivery', current_user=current_user,
                                               action_string='put', locker_space=locker_space_destination,
                                               delivery_string=delivery_string, delivery=delivery, locker_id=locker_id)

                    elif delivery.status == 3 and current_user.id not in [delivery.sender_id, delivery.driver_id]:
                        # recipient (which is an user, not sender or driver) picks up package from destination locker
                        # change delivery status
                        delivery.status = 4
                        delivery.date_destination_picked = datetime.utcnow()
                        # free locker space
                        locker_space_destination.free_space()

                        # send mail
                        send_email(mail_recipients,
                                   'Paco - Delivery {} update'.format(delivery.tracking_id),
                                   render_template('emails/delivery_update_picked_up_by_recipient.html',
                                                   delivery=delivery))
                        return render_template('process.html', title='Process delivery', current_user=current_user,
                                               action_string='pick up', locker_space=locker_space_destination,
                                               delivery_string=delivery_string, delivery=delivery, locker_id=locker_id)
                    else:
                        # error
                        flash('There was an error while processing your request', 'danger')
                        return redirect(url_for('main.scan_qr'))

                elif delivery.status == 3:
                    # recipient (not an user) picks up package from destination locker
                    # change delivery status
                    delivery.status = 4
                    delivery.date_destination_picked = datetime.utcnow()
                    # free locker space
                    locker_space_destination.free_space()
                    # send mail
                    send_email(mail_recipients,
                               'Paco - Delivery {} update'.format(delivery.tracking_id),
                               render_template('emails/delivery_update_picked_up_by_recipient.html',
                                               delivery=delivery))
                    return render_template('process.html', title='Process delivery', current_user=current_user,
                                           action_string='pick up', locker_space=locker_space_destination,
                                           delivery_string=delivery_string, delivery=delivery, locker_id=locker_id)

            else:
                flash('There was an error while processing your request, please try again', 'danger')
                return redirect(url_for('main.scan_qr'))

        # redirect to pickup
        return redirect(url_for('locker.locker_pickup', locker_id=locker_id))

    flash('There was an error while processing your request, please try again', 'danger')
    return redirect(url_for('main.scan_qr'))


@locker.route('/pickup', methods=['GET', 'POST'])
def locker_pickup():
    locker_id = int(request.args.get('locker_id'))
    form = LockerPickUpForm(
        locker_id=locker_id
    )
    if form.validate_on_submit():
        delivery = Delivery.query.filter_by(locker_destination_id=locker_id, tracking_id=form.tracking_id.data).first()
        if delivery:
            return redirect(url_for('locker.process_deliveries', locker_id=locker_id, delivery_string='{},'.format(delivery.id)))
        else:
            flash('Please insert a valid tracking id', 'danger')

    flash_form_errors(form)
    return render_template('locker_pickup.html', title='Insert tracking code', form=form, current_user=current_user)

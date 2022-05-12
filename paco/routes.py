from flask import render_template, json
from paco.blueprints.delivery.forms import SendParcelFormIntro
from paco.models import *
from flask_login import current_user, login_required
from paco.tokens import *
from paco.utils import email_required


@app.route('/')
def index():
    form = SendParcelFormIntro()
    towns = set()
    for locker in db.session.query(Locker.town):
        towns.add(locker[0])
    return render_template("landing_user.html", title='Home', current_user=current_user, towns=towns, form=form)


@app.route('/dashboard')
@login_required
@email_required
def show_dashboard():
    deliveries_sent = current_user.get_deliveries_sent()
    total_spent = current_user.get_spent_last_month()
    deliveries_sent_count = current_user.get_deliveries_sent_count_last_month()

    deliveries_delivered = current_user.get_deliveries_delivered()
    total_earned = current_user.get_earned_last_month()
    deliveries_delivered_count = current_user.get_deliveries_delivered_count_last_month()

    return render_template("dashboard.html", title="Dashboard",
                           current_user=current_user, deliveries_sent=deliveries_sent,
                           total_spent_last_month=Delivery.format_price(total_spent),
                           deliveries_sent_count_last_month=deliveries_sent_count,
                           deliveries_delivered=deliveries_delivered,
                           total_earned_last_month=Delivery.format_price(total_earned),
                           deliveries_delivered_count_last_month=deliveries_delivered_count)


@app.route('/qr')
def scan_qr():
    return render_template('qr.html', current_user=current_user, title="Scan QR")

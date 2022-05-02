from paco import db, login_manager
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask_login import UserMixin
from sqlalchemy.sql import functions


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    is_driver = db.Column(db.Boolean, nullable=False, default=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    email_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    date_email_confirmed = db.Column(db.DateTime)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

    def is_email_confirmed(self):
        return self.email_confirmed

    def get_deliveries_sent(self):
        return Delivery.query.filter_by(sender_id=self.id).all()

    def get_spent_last_month(self):
        date = datetime.utcnow() + relativedelta(months=-1)
        spent = db.session.query(functions.sum(Delivery.price)).filter(
            (Delivery.sender_id == self.id) & (Delivery.date_created > date)).scalar()
        return spent if spent else 0

    def get_delivery_count_last_month(self):
        date = datetime.utcnow() + relativedelta(months=-1)
        return db.session.query(functions.count(Delivery.id)).filter(
            (Delivery.sender_id == self.id) & (Delivery.date_created > date)).scalar()


class Locker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    address = db.Column(db.String(60), unique=True, nullable=False)
    zip_code = db.Column(db.String(10), nullable=False)
    town = db.Column(db.String(40), nullable=False)
    province = db.Column(db.String(2), nullable=False)
    region = db.Column(db.String(20), nullable=False)
    latitude = db.Column(db.Numeric, nullable=False)
    longitude = db.Column(db.Numeric, nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Locker('{self.id}', '{self.name}')"

    def get_google_maps_directions(self):
        return 'https://maps.google.com?saddr=Current+Location&daddr={},{}'.format(self.latitude, self.longitude)


class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Dates
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_source_arrived = db.Column(db.DateTime)
    date_source_departed = db.Column(db.DateTime)
    date_destination_arrived = db.Column(db.DateTime)
    date_destination_picked = db.Column(db.DateTime)

    # Lockers
    locker_source_id = db.Column(db.Integer, db.ForeignKey('locker.id'), nullable=False)
    locker_destination_id = db.Column(db.Integer, db.ForeignKey('locker.id'), nullable=False)
    # Package information
    weight = db.Column(db.Integer, nullable=False)
    dimension = db.Column(db.Integer, nullable=False)  # 1 -> small 2 -> medium 3 -> large
    fragile = db.Column(db.Boolean, nullable=False, default=False)

    # Route Information
    distance = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)

    def dimension_from_int_to_text(dimension):
        dimension_coding = {
            1: "small (max 25cm x 20 cm x 15cm)",
            2: "medium (max 45cm x 30 cm x 25cm)",
            3: "large (max 70cm x 70 cm x 70 cm)"
        }
        return dimension_coding[int(dimension)]

    def get_dimension_from_int_to_text(self):
        dimension_coding = {
            1: "small (max 25cm x 20 cm x 15cm)",
            2: "medium (max 45cm x 30 cm x 25cm)",
            3: "large (max 70cm x 70 cm x 70 cm)"
        }
        return dimension_coding[self.dimension]

    def get_formatted_price(self):
        price_string = str(self.price)
        while len(price_string) < 3:
            price_string = price_string + "0"
        return "{},{}€".format(price_string[:-2], price_string[-2:])

    def format_price(price):
        price_string = str(price)
        while len(price_string) < 3:
            price_string = price_string + "0"
        return "{},{}€".format(price_string[:-2], price_string[-2:])

    def get_status(self):
        if self.date_destination_picked:
            # Delivery is done
            return 4
        elif self.date_destination_arrived:
            # Waiting for pickup
            return 3
        elif self.date_source_departed:
            # En route
            return 2
        elif self.date_source_arrived:
            # Waiting for driver to pick up
            return 1
        else:
            # Waiting for sender to get to locker
            return 0

    def format_status(self):
        format_status_dict = {
            0: 'Confirmed',
            1: 'Waiting',
            2: 'En route',
            3: 'Collect package',
            4: 'Completed'
        }
        return format_status_dict[self.get_status()]

    def get_status_action(self):
        format_status_dict = {
            0: 'Open locker',
            1: 'Open tracking',
            2: 'Open tracking',
            3: 'Open tracking',
            4: 'Open invoice'
        }
        return format_status_dict[self.get_status()]

    def get_locker_source(self):
        return Locker.query.filter_by(id=self.locker_source_id).first()

    def get_locker_destination(self):
        return Locker.query.filter_by(id=self.locker_destination_id).first()

    def get_distance_km(self):
        return int(self.distance / 1000)

    def get_sender(self):
        return User.query.filter_by(id=self.sender_id).first()

    def get_driver(self):
        return User.query.filter_by(id=self.driver_id).first()

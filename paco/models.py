import string
import random

from paco import db, login_manager
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask_login import UserMixin
from sqlalchemy.sql import functions
from geopy import distance


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default_user_image.jpg')
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
        return Delivery.query.filter_by(sender_id=self.id).order_by(Delivery.date_created.desc()).all()

    def get_deliveries_delivered(self):
        return Delivery.query.filter_by(sender_id=self.id).order_by(Delivery.date_created.desc()).all()

    def get_spent_last_month(self):
        date = datetime.utcnow() + relativedelta(months=-1)
        spent = db.session.query(functions.sum(Delivery.price)).filter(
            (Delivery.sender_id == self.id) & (Delivery.date_created > date)).scalar()
        return spent if spent else 0

    def get_earned_last_month(self):
        if self.is_driver:
            date = datetime.utcnow() + relativedelta(months=-1)
            sessions = DriverSession.query.filter(
                (DriverSession.driver_id == self.id) &
                (DriverSession.date_created > date)
            ).all()
            amount = 0
            for session in sessions:
                if not session.is_active():
                    amount += session.get_total_earned()
            return amount
        else:
            return 0

    def get_driving_sessions_count_last_month(self):
        date = datetime.utcnow() + relativedelta(months=-1)
        res = db.session.query(functions.count(Delivery.id)).filter(
            (Delivery.sender_id == self.id) & (Delivery.date_created > date)).scalar()
        return res if res else 0

    def get_deliveries_sent_count_last_month(self):
        date = datetime.utcnow() + relativedelta(months=-1)
        res = db.session.query(functions.count(Delivery.id)).filter(
            (Delivery.sender_id == self.id) & (Delivery.date_created > date)).scalar()
        return res if res else 0

    def get_deliveries_delivered_count_last_month(self):
        date = datetime.utcnow() + relativedelta(months=-1)
        res = db.session.query(functions.count(Delivery.id)).filter(
            (Delivery.driver_id == self.id) & (Delivery.date_created > date)).scalar()
        return res if res else 0

    def get_license_plates(self):
        if self.is_driver:
            return CarInfo.query.filter_by(driver_id=self.id).all()
        else:
            return None

    def is_in_driving_session(self):
        sessions = DriverSession.query.filter_by(driver_id=self.id).all()
        if sessions:
            for session in sessions:
                if session.is_active():
                    return True
        return False

    def get_active_session(self):
        sessions = DriverSession.query.filter_by(driver_id=self.id).all()
        if sessions:
            for session in sessions:
                if session.is_active():
                    return session
        return None

    def get_driver_info(self):
        if self.is_driver:
            return DriverInfo.query.filter_by(id=self.id).first()
        return None


class Locker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    address = db.Column(db.String(60), unique=True, nullable=False)
    zip_code = db.Column(db.String(10), nullable=False)
    town = db.Column(db.String(40), nullable=False)
    province = db.Column(db.String(2), nullable=False)
    region = db.Column(db.String(20), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Locker('{self.id}', '{self.name}')"

    def get_google_maps_directions(self):
        return 'https://maps.google.com?saddr=Current+Location&daddr={},{}'.format(self.latitude, self.longitude)

    @staticmethod
    def get_lockers_near_source(latitude, longitude):
        res = []
        source_lockers = [item[0] for item in
                          db.session.query(Delivery.locker_source_id).filter(Delivery.driver_id == None).all()]
        locker_list = Locker.query.filter(Locker.id.in_(source_lockers)).all()
        for locker in locker_list:
            distance_from_locker = distance.distance(
                (locker.latitude, locker.longitude),
                (latitude, longitude)
            ).m
            if distance_from_locker <= 25000:
                res.append(locker)
        return res

    @staticmethod
    def get_lockers_near_destination(latitude, longitude):
        res = []
        destination_lockers = [item[0] for item in db.session.query(Delivery.locker_destination_id).filter(
            Delivery.driver_id == None).all()]
        locker_list = Locker.query.filter(Locker.id.in_(destination_lockers)).all()
        for locker in locker_list:
            distance_from_locker = distance.distance(
                (locker.latitude, locker.longitude),
                (latitude, longitude)
            ).m
            if distance_from_locker <= 25000:
                res.append(locker)
        return res

    def has_space_free(self, dimension):
        locker_spaces_available = LockerSpace.query.filter_by(locker_id=self.id, dimension=dimension,
                                                              delivery_id=None).all()
        return True if locker_spaces_available else False

    def get_available_space(self, dimension):
        locker_space_available = LockerSpace.query.filter_by(locker_id=self.id, dimension=dimension,
                                                             delivery_id=None).first()
        return locker_space_available

    def reserve_space(self, delivery):
        locker_space = LockerSpace.query.filter_by(locker_id=self.id, dimension=delivery.dimension,
                                                   delivery_id=None).first()
        locker_space.delivery_id = delivery.id


class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver_info.id'))
    status = db.Column(db.Integer, nullable=False, default=0)
    email_recipient = db.Column(db.String(120))
    tracking_id = db.Column(db.String(8), unique=True, nullable=False)

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

    @staticmethod
    def dimension_from_int_to_text(dimension):
        dimension_coding = {
            1: "small (max 40cm x 20 cm x 20cm)",
            2: "medium (max 40cm x 40cm x 40cm)",
            3: "large (max 80cm x 40 cm x 40cm)"
        }
        return dimension_coding[int(dimension)]

    def get_dimension_from_int_to_text(self):
        dimension_coding = {
            1: "small (max 40cm x 20cm x 20cm)",
            2: "medium (max 40cm x 40cm x 40cm)",
            3: "large (max 80cm x 40cm x 40cm)"
        }
        return dimension_coding[self.dimension]

    def get_volume(self):
        volume_coding = [0, 16, 64, 128]
        return volume_coding[self.dimension]

    def get_formatted_price(self):
        price_string = str(self.price)
        while len(price_string) < 3:
            price_string = price_string + "0"
        return "{},{}€".format(price_string[:-2], price_string[-2:])

    @staticmethod
    def format_price(price):
        price_string = str(price)
        while len(price_string) < 3:
            price_string = price_string + "0"
        return "{},{}€".format(price_string[:-2], price_string[-2:])

    def format_status(self):
        format_status_dict = {
            0: 'Confirmed',
            1: 'Waiting for driver',
            2: 'En route',
            3: 'Collect package at destination locker',
            4: 'Completed'
        }
        return format_status_dict[self.status]

    def get_status_action(self):
        format_status_dict = {
            0: 'Open locker',
            1: 'Open tracking',
            2: 'Open tracking',
            3: 'Open tracking',
            4: 'Open invoice'
        }
        return format_status_dict[self.status]

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

    @staticmethod
    def generate_tracking_id():
        ran = 'PACOFIRS'
        while Delivery.query.filter_by(tracking_id=ran).first():
            ran = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return ran


class DriverInfo(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Personal Info
    name = db.Column(db.String(60), nullable=False)
    surname = db.Column(db.String(60), nullable=False)
    gender = db.Column(db.Boolean, nullable=False)  # 0->male 1->female
    date_of_birth = db.Column(db.Date, nullable=False)
    town_of_birth = db.Column(db.String(60), nullable=False)
    country_of_birth = db.Column(db.String(60), nullable=False)
    fiscal_code = db.Column(db.String(16), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)

    # Address
    address_street = db.Column(db.String(60), nullable=False)
    address_town = db.Column(db.String(60), nullable=False)
    address_zip_code = db.Column(db.String(60), nullable=False)
    address_country = db.Column(db.String(60), nullable=False)

    # Drivers License
    license_number = db.Column(db.String(60), nullable=False)
    license_expiration = db.Column(db.Date, nullable=False)
    license_issuing_authority = db.Column(db.String(60), nullable=False)

    def get_sessions(self):
        return DriverSession.query.filter_by(driver_id=self.id).order_by(DriverSession.date_created.desc()).all()



class CarInfo(db.Model):
    license_plate = db.Column(db.String(7), primary_key=True, nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver_info.id'), nullable=False)
    car_make = db.Column(db.String(60), nullable=False)
    car_model = db.Column(db.String(60), nullable=False)
    fuel_type = db.Column(db.String(60), nullable=False)
    registration_year = db.Column(db.Integer, nullable=False)
    power_cv = db.Column(db.Integer)

    def get_price_percentage(self):
        price_percentage = 0.7
        if self.fuel_type in ['Electric', 'Elettrica']:
            price_percentage = 0.9
        elif self.fuel_type in ['Hybrid', 'Ibrida']:
            price_percentage = 0.8

        return price_percentage


class DriverSession(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver_info.id'), nullable=False)
    license_plate = db.Column(db.String(7), db.ForeignKey('car_info.license_plate'))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_ended = db.Column(db.DateTime)
    start_address = db.Column(db.String(128), nullable=False)
    end_address = db.Column(db.String(128), nullable=False)

    def get_total_earned(self):
        return db.session.query(functions.sum(DriverSessionDelivery.earned_amount)).filter(
            (DriverSessionDelivery.session_id == self.id)).scalar()

    def get_formatted_total_earned(self):
        total_earned = self.get_total_earned()
        return Delivery.format_price(total_earned)

    def get_deliveries(self):
        return [session_delivery.get_delivery() for session_delivery in
                DriverSessionDelivery.query.filter(DriverSessionDelivery.session_id == self.id).all()]

    def is_active(self):
        return self.date_ended is None


class DriverSessionDelivery(db.Model):
    session_id = db.Column(db.Integer, db.ForeignKey('driver_session.id'), primary_key=True, nullable=False)
    delivery_id = db.Column(db.Integer, db.ForeignKey('delivery.id'), primary_key=True, nullable=False)
    earned_amount = db.Column(db.Integer, nullable=False)

    def get_delivery(self):
        return Delivery.query.filter_by(id=self.delivery_id).first()


class LockerSpace(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    locker_id = db.Column(db.Integer, db.ForeignKey('locker.id'), primary_key=True, nullable=False)
    delivery_id = db.Column(db.Integer, db.ForeignKey('delivery.id'))
    dimension = db.Column(db.Integer, nullable=False)

    def free_space(self):
        self.delivery_id = None

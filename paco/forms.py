import json
import os
import re

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DecimalField, SelectField, IntegerField, \
    RadioField, DateField
from wtforms.widgets import HiddenInput, ListWidget, html_params, Input
from markupsafe import Markup
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from paco.models import User, Locker, CarInfo
from codicefiscale import codicefiscale
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class ButtonCheckInput(object):
    def __init__(self, html_tag='div'):
        self.html_tag = html_tag

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        html = ['<%s %s>' % (self.html_tag, html_params(**kwargs))]
        for subfield in field:
            html.append(
                '<input id="{}" name="{}" value="{}" class="btn-check" type="radio"></input><label class="btn btn-outline-primary">{}: {}</label>'.format(
                    subfield.id, subfield.name, subfield.data, subfield.data, subfield.label))
        html.append('</%s>' % self.html_tag)
        return Markup(''.join(html))


class UserRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password', message="Passwords must match!")])
    terms_of_contract = BooleanField('I agree to the Terms of Contract', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Login')


class SendParcelFormIntro(FlaskForm):
    send_from = StringField('You want to send it from...', validators=[DataRequired()])
    send_to = StringField('You want it to arrive in...', validators=[DataRequired()])
    weight = IntegerField('Weight', validators=[DataRequired(), NumberRange(min=1, max=15)])
    box_size = SelectField('Box size',
                           choices=[(1, 'Small (max 25cm x 20 cm x 15cm)'), (2, 'Medium (max 45cm x 30 cm x 25cm)'),
                                    (3, 'Large (max 70cm x 70 cm x 70 cm)')], validators=[DataRequired()])
    submit = SubmitField('Send it now')

    def validate_send_from(self, send_from):
        locker = Locker.query.filter_by(town=send_from.data).first()
        if not locker:
            raise ValidationError(
                'The town you want to send your parcel from is not in our system. Please choose a valid town!')

    def validate_send_to(self, send_to):
        locker = Locker.query.filter_by(town=send_to.data).first()
        if not locker:
            raise ValidationError(
                'The town you want to send your parcel to is not in our system. Please choose a valid town!')

    ''' INUTILE FINO A QUANDO NON AGGIORNERANNO FLASK-WTF
    def validate_different_cities(self):
        print(self.send_to.data)
        print(self.send_from.data)
        if self.send_to.data == self.send_from.data:
            raise ValidationError('We do not support same city shipping. Please choose two different cities as your origin and destination!')
            '''


class SendParcelFormLockerChoice(FlaskForm):
    sender_id = IntegerField(widget=HiddenInput(), validators=[DataRequired()])
    weight = IntegerField(widget=HiddenInput(), validators=[DataRequired()])
    dimension = IntegerField(widget=HiddenInput(), validators=[DataRequired()])
    locker_source_id = SelectField('Locker', widget=ButtonCheckInput(), validators=[DataRequired()])
    locker_destination_id = SelectField('Locker', widget=ButtonCheckInput(), validators=[DataRequired()])
    submit = SubmitField('Confirm choice')


class SendParcelFormConfirmation(FlaskForm):
    sender_id = IntegerField(widget=HiddenInput(), validators=[DataRequired()])
    weight = IntegerField(widget=HiddenInput(), validators=[DataRequired()])
    dimension = IntegerField(widget=HiddenInput(), validators=[DataRequired()])
    locker_source_id = IntegerField('Locker', widget=HiddenInput(), validators=[DataRequired()])
    locker_destination_id = IntegerField('Locker', widget=HiddenInput(), validators=[DataRequired()])
    price = IntegerField(widget=HiddenInput(), validators=[DataRequired()])
    distance = IntegerField(widget=HiddenInput(), validators=[DataRequired()])
    submit = SubmitField('Confirm delivery and pay')


class DriverSignupForm(FlaskForm):
    _countries = [country['name_alt_en'] for country in json.load(open('data/countries.json')) if country['name_alt_en'] != '']
    _countries.sort()
    _countries.insert(0, 'Italy')

    name = StringField('Name', validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[(0, 'Male'), (1, 'Female')])
    date_of_birth = DateField('Date of birth', validators=[DataRequired()])
    town_of_birth = StringField('Town of birth', validators=[DataRequired()])
    country_of_birth = SelectField('Country of birth', choices=_countries, validators=[DataRequired()])
    fiscal_code = StringField('Fiscal code', validators=[DataRequired()])
    phone_number = StringField('Phone number',widget=Input(input_type="tel"), validators=[DataRequired()])
    address_street = StringField('Street', validators=[DataRequired()])
    address_town = StringField('Town', validators=[DataRequired()])
    address_zip_code = StringField('Zip code', validators=[DataRequired()])
    address_country = SelectField('Country', validators=[DataRequired()], choices=_countries)
    license_code = StringField('Number', validators=[DataRequired()])
    license_expiration = DateField('Expiration date', validators=[DataRequired()])
    license_issuing_authority = StringField('Issuing authority', validators=[DataRequired()])
    terms_of_contract = BooleanField('I agree to the Terms of Contract', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def validate_fiscal_code(self, fiscal_code):
        if not codicefiscale.is_valid(fiscal_code.data):
            raise ValidationError('Insert a valid fiscal code.')

    def validate_phone_number(self, phone_number):
        if not re.match("^(\+|00)[1-9][0-9 \-\(\)\.]{7,32}$", phone_number.data):
            raise ValidationError('Insert a valid phone number.')

    def validate_date_of_birth(self, date_of_birth):
        eighteen_years_ago = datetime.now() - relativedelta(years=18)
        if datetime(date_of_birth.data.year, date_of_birth.data.month, date_of_birth.data.day) > eighteen_years_ago:
            raise ValidationError('You have to be over the age of 18 in order to drive with Paco')

    def validate_license_expiration(self, license_expiration):
        if license_expiration.data < date.today():
            raise ValidationError('Your license must not be expired')

class CarInfoAddForm(FlaskForm):
    license_plate = StringField('License plate', validators=[DataRequired(), Length(max=7)])
    submit = SubmitField('Submit')

    def validate_license_plate(self, license_plate):
        car = CarInfo.query.filter_by(license_plate=license_plate.data).first()
        if car:
            raise ValidationError('This car is already in our system')


class CarInfoConfirmForm(FlaskForm):
    license_plate = StringField('License plate', validators=[DataRequired(), Length(max=7)], widget=HiddenInput())
    car_make = StringField('CarMake', validators=[DataRequired()], widget=HiddenInput())
    car_model = StringField('CarModel', validators=[DataRequired()], widget=HiddenInput())
    fuel_type = StringField('FuelType', validators=[DataRequired()], widget=HiddenInput())
    power_cv = IntegerField('PowerCV', validators=[DataRequired()], widget=HiddenInput())
    registration_year = IntegerField('RegistrationYear', validators=[DataRequired()], widget=HiddenInput())
    submit = SubmitField('Confirm and add car')



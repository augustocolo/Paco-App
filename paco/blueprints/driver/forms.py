import json
import re
from datetime import datetime, date

from codicefiscale import codicefiscale
from dateutil.relativedelta import relativedelta
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, ValidationError, Length, NumberRange
from wtforms.widgets import Input, HiddenInput

from paco import gmaps
from paco.models import CarInfo


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


class SessionStartForm(FlaskForm):
    license_plate = SelectField('License plate', validators=[DataRequired(), Length(max=7)])
    from_location = StringField('You\'re going to start from', validators=[DataRequired()])
    to_location = StringField('You\'re going to arrive in', validators=[DataRequired()])
    liters_available = IntegerField('Space available', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Check availability')

    def validate_from_location(self, from_location):
        if gmaps.geocode(from_location.data):
            pass
        else:
            raise ValidationError('This address is not valid')

    def validate_to_location(self, to_location):
        if gmaps.geocode(to_location.data):
            pass
        else:
            raise ValidationError('This address is not valid')


class SessionConfirmForm(FlaskForm):
    license_plate = StringField('License plate', validators=[DataRequired(), Length(max=7)], widget=HiddenInput())
    from_location_geocoded = StringField('You\'re going to start from', validators=[DataRequired()], widget=HiddenInput())
    to_location_geocoded = StringField('You\'re going to arrive in', validators=[DataRequired()], widget=HiddenInput())
    deliveries = StringField('Deliveries', validators=[DataRequired()], widget=HiddenInput())
    submit = SubmitField('Confirm and start driving')


class DriverUpdateForm(FlaskForm):
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
    submit = SubmitField('Update')

    def validate_fiscal_code(self, fiscal_code):
        if current_user.get_driver_info().fiscal_code != fiscal_code.data:
            if not codicefiscale.is_valid(fiscal_code.data):
                raise ValidationError('Insert a valid fiscal code.')

    def validate_phone_number(self, phone_number):
        if current_user.get_driver_info().phone_number != phone_number.data:
            if not re.match("^(\+|00)[1-9][0-9 \-\(\)\.]{7,32}$", phone_number.data):
                raise ValidationError('Insert a valid phone number.')

    def validate_date_of_birth(self, date_of_birth):
        if current_user.get_driver_info().date_of_birth != date_of_birth.data:
            eighteen_years_ago = datetime.now() - relativedelta(years=18)
            if datetime(date_of_birth.data.year, date_of_birth.data.month, date_of_birth.data.day) > eighteen_years_ago:
                raise ValidationError('You have to be over the age of 18 in order to drive with Paco')

    def validate_license_expiration(self, license_expiration):
        if current_user.get_driver_info().license_expiration != license_expiration.data:
            if license_expiration.data < date.today():
                raise ValidationError('Your license must not be expired')








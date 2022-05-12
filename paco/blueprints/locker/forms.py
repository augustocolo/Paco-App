from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Length, ValidationError

from paco.models import Delivery


class LockerPickUpForm(FlaskForm):
    tracking_id = StringField('Tracking code', validators=[DataRequired(), Length(min=8, max=8)])
    locker_id = IntegerField('Locker id', validators=[DataRequired()], widget=HiddenField())
    submit = SubmitField('Get parcel')

    def validate_tracking_id(self, tracking_id):
        delivery = Delivery.query.filter_by(tracking_id=tracking_id.data).first()
        if not delivery:
            raise ValidationError('Tracking code not valid! Please insert a valid one.')



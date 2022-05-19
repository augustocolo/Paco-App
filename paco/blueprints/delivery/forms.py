from flask_wtf import FlaskForm
from markupsafe import Markup
from wtforms import StringField, IntegerField, SelectField, SubmitField, EmailField, BooleanField
from wtforms.validators import DataRequired, NumberRange, ValidationError
from wtforms.widgets import HiddenInput, html_params

from paco.models import Locker


class ButtonCheckInput(object):
    def __init__(self, html_tag='div'):
        self.html_tag = html_tag

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        html = ['<%s %s>' % (self.html_tag, html_params(**kwargs))]
        for subfield in field:
            html.append(
                '<input id="{}" name="{}" value="{}" class="btn-check" type="radio"></input><label class="btn '
                'btn-outline-primary">{}: {}</label>'.format(
                    subfield.id, subfield.name, subfield.data, subfield.data, subfield.label))
        html.append('</%s>' % self.html_tag)
        return Markup(''.join(html))


class SendParcelFormIntro(FlaskForm):
    send_from = StringField('You want to send it from', validators=[DataRequired()])
    send_to = StringField('You want it to arrive in', validators=[DataRequired()])
    weight = IntegerField('Weight', validators=[DataRequired(), NumberRange(min=1, max=15)])
    box_size = SelectField('Box size',
                           choices=[(1, 'Small (max 40cm x 20 cm x 20cm)'), (2, 'Medium (max 40cm x 40cm x 40cm)'),
                                    (3, 'Large (max 80cm x 40 cm x 40cm)')], validators=[DataRequired()])
    submit = SubmitField('Send it now')

    def validate_send_from(self, send_from):
        lockers = Locker.query.filter_by(town=send_from.data).all()
        if not lockers:
            raise ValidationError(
                'The town you want to send your parcel from is not in our system. Please choose a valid town!')

        valid = False
        for locker in lockers:
            if locker.has_space_free(self.box_size.data):
                valid = True
                break
        if not valid:
            raise ValidationError(
                'There are no available lockers in {}. Please try again at another time.'.format(self.send_from.data)
            )

    def validate_send_to(self, send_to):
        lockers = Locker.query.filter_by(town=send_to.data).all()
        if not lockers:
            raise ValidationError(
                'The town you want to send your parcel to is not in our system. Please choose a valid town!')
        if send_to.data == self.send_from.data:
            raise ValidationError(
                'You have to choose two different towns'
            )

        valid = False
        for locker in lockers:
            if locker.has_space_free(self.box_size.data):
                valid = True
                break
        if not valid:
            raise ValidationError(
                'There are no available lockers in {}. Please try again at another time.'.format(self.send_to.data))
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
    fragile = BooleanField('Is this parcel fragile?')
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
    fragile = BooleanField(widget=HiddenInput())
    email_recipient = EmailField('Recipient email')
    submit = SubmitField('Confirm delivery and pay')

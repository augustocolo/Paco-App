import os

from flask_mail import Mail

from paco import app


# Email
app.config['MAIL_SERVER'] = os.environ.get('EMAIL_SERVER')
app.config['MAIL_PORT'] = os.environ.get('EMAIL_PORT')
app.config['MAIL_USE_TLS'] = bool(int(os.environ.get('EMAIL_TLS')))
app.config['MAIL_USE_SSL'] = bool(int(os.environ.get('EMAIL_SSL')))
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('EMAIL_USER')
mail = Mail(app)


import os

from flask_mail import Mail

from paco import app


# Email
app.config['MAIL_SERVER'] = 'smtp.libero.it'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
app.config['MAIL_DEFAULT_SENDER'] = 'pacodelivery@libero.it'
mail = Mail(app)


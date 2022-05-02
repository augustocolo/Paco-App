import os

from flask import Flask
from flask_assets import Bundle, Environment
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_googlemaps import GoogleMaps
from flask_qrcode import QRcode

app = Flask(__name__)

# Configure database
app.config['SECRET_KEY'] = 'Cambiarelasecretkeynonappenapubblico'
app.config['SECURITY_PASSWORD_SALT'] = 'Cambiarelasaltkeynonappenapubblico'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///paco.db'
db = SQLAlchemy(app)

# Authentication stuff
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Email
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
app.config['MAIL_DEFAULT_SENDER'] = 'smillacipolla@gmail.com'
mail = Mail(app)

# Maps API
app.config['GOOGLEMAPS_KEY'] = os.environ.get('GOOGLE_MAPS_API_KEY')
GoogleMaps(app)

# QR Codes
QRcode(app)


from paco import models

db.create_all()

# Create assets environment
assets = Environment(app)
assets.url = app.static_url_path

# Bundle JS files
js = Bundle(
    "assets/node_modules/jquery/dist/jquery.min.js",
    "assets/node_modules/@popperjs/core/dist/umd/popper.js",
    "assets/node_modules/bootstrap/dist/js/bootstrap.js",
    filters="jsmin",
    output="js/generated.js"
)
assets.register("js_all", js)

# Bundle Scss files
scss = Bundle(
    "assets/main.scss",  # 1. will read this scss file and generate a css file based on it
    filters="libsass",   # 2. using this filter: https://webassets.readthedocs.io/en/latest/builtin_filters.html#libsass
    output="css/scss-generated.css"  # 3. and output the generated .css file in the static/css folder
)
assets.register("scss_all", scss)  # 4. register the generated css file, to be used in Jinja templates (see base.html)


from paco import routes


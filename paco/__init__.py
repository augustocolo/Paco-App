import os

from flask import Flask
from flask_assets import Bundle, Environment
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_googlemaps import GoogleMaps
from flask_qrcode import QRcode
import googlemaps
from loadenv import load_env

load_env()

app = Flask(__name__)

# Configure database
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('FLASK_SALT_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///paco.db'
db = SQLAlchemy(app)

# Authentication stuff
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Embedded Maps API
app.config['GOOGLEMAPS_KEY'] = os.environ.get('GOOGLE_MAPS_API_KEY')
GoogleMaps(app)

# Google Maps Services
gmaps = googlemaps.Client(key=os.environ.get('GOOGLE_MAPS_API_KEY'))

# QR Codes
QRcode(app)

from paco import models

# Create assets environment
assets = Environment(app)
assets.url = app.static_url_path

# Bundle JS files
js = Bundle(
    "assets/node_modules/jquery/dist/jquery.min.js",
    "assets/node_modules/@popperjs/core/dist/umd/popper.js",
    "assets/node_modules/bootstrap/dist/js/bootstrap.js",
    "assets/js/geolocation.js",
    "assets/js/main_page_fill.js",
    filters="jsmin",
    output="js/generated.js"
)
assets.register("js_all", js)

# Bundle Scss files
scss = Bundle(
    "assets/main.scss",
    filters="libsass",
    output="css/scss-generated.css"
)
assets.register("scss_all", scss)

from paco.api import mail

from paco.blueprints.auth.routes import auth
from paco.blueprints.delivery.routes import delivery
from paco.blueprints.driver.routes import driver
from paco.blueprints.locker.routes import locker
from paco.blueprints.user.routes import user
from paco.blueprints.main.routes import main

app.register_blueprint(auth)
app.register_blueprint(delivery)
app.register_blueprint(driver)
app.register_blueprint(locker)
app.register_blueprint(user)
app.register_blueprint(main)

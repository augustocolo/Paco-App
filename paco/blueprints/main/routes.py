from flask import render_template, Blueprint
from flask_googlemaps import Map

from paco.blueprints.delivery.forms import SendParcelFormIntro
from paco.models import *
from flask_login import current_user

main = Blueprint('main', __name__, template_folder='templates')


@main.route('/')
@main.route('/landing/user')
def index():
    form = SendParcelFormIntro()
    towns = set()
    for locker in db.session.query(Locker.town):
        towns.add(locker[0])
    return render_template("landing_user.html", title='Send parcels', current_user=current_user, towns=towns, form=form)

@main.route('/landing/driver')
def landing_driver():
    return render_template("landing_driver.html", title="Drive your car", current_user=current_user)

@main.route('/our_vision')
def our_vision():
    return render_template("our_vision.html", title="Our vision", current_user=current_user)

@main.route('/locations')
def locations():
    lockers = Locker.query.all()
    gmap_style = "width:100%;margin:0;height:500px"
    map = Map(
        identifier='map_to',
        lat=lockers[0].latitude,
        lng=lockers[0].longitude,
        markers=[{'lat': locker.latitude,
                  'lng': locker.longitude,
                  'label': str(locker.id),
                  'infobox': '<b>{}</b><br>{}<br>{}<br>{} {}<br>Italy<br><br><a href="{}" target="_blank" '
                             'rel="noopener noreferrer">Get directions</a>'.format(locker.name, locker.address,
                                                                                   locker.zip_code, locker.town,
                                                                                   locker.province,
                                                                                   locker.get_google_maps_directions())}
                 for locker in lockers],
        fit_markers_to_bounds=True,
        style=gmap_style,
        zoom_control=False,
        maptype_control=False,
        streetview_control=False,
        rotate_control=False,
        fullscreen_control=False,
    )
    return render_template("locations.html", title="Locations", current_user=current_user, map=map)




@main.route('/qr')
def scan_qr():
    return render_template('qr.html', current_user=current_user, title="Scan QR")
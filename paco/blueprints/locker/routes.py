import json

from flask import Blueprint, render_template

from paco.models import Locker
from paco.tokens import generate_locker_qr

locker = Blueprint('locker', __name__, template_folder='templates', url_prefix='/locker')


@locker.route('/locker/<int:id>/qr', methods=["GET"])
def show_locker_qr(id):
    locker = Locker.query.filter_by(id=id).first()

    qr_info = {
        'app': 'paco',
        'token': generate_locker_qr(locker.id)
    }

    return render_template("qr.html",
                           title="Locker {}".format(locker.name), locker=locker, qr_info=json.dumps(qr_info))



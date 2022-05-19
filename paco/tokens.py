from itsdangerous import URLSafeTimedSerializer

from paco import app
from paco.models import User


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email


def generate_locker_qr(id):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(str(id), salt=app.config['SECURITY_PASSWORD_SALT'])


def confirm_qr(token, expiration=65):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        id = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
        res = int(id)
    except:
        return False
    return res


def generate_reset_token(user):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps({'user_id': user.id}, salt=app.config['SECURITY_PASSWORD_SALT'])


def verify_reset_token(token, expiration=1800):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        user_id = s.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )['user_id']
    except:
        return None
    return User.query.filter_by(id=user_id)

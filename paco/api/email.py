from flask_mail import Message

from paco import app, mail


def send_email(to, subject, template):
    for email in to:
        msg = Message(
            subject,
            recipients=[email],
            html=template,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)

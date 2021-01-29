from celery import Celery
# from bbs import app
from flask_mail import Message
from excit import mail
from flask import Flask
import config

app = Flask(__name__)

mail.init_app(app)


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=config.CELERY_BROKER_URL,
        broker=config.CELERY_RESULT_BACKEND
        # backend=app.config['CELERY_RESULT_BACKEND'],
        # broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery(app)


@celery.task
def send_mail(subject, recipients, body):
    message = Message(subject=subject, recipients=recipients, body=body)
    mail.send(message)


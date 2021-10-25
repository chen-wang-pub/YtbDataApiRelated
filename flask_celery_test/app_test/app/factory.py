from flask import Flask
import os
from .celery_utils import init_celery
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

PKG_NAME = os.path.dirname(os.path.realpath(__file__)).split("/")[-1]

def create_app(app_name=PKG_NAME, **kwargs):
    app = Flask(app_name)
    if kwargs.get("celery"):
        init_celery(kwargs.get("celery"), app)
    from app.all import bp
    from app.paid_user import paid_user
    from app.config import Config
    app.register_blueprint(bp)
    app.register_blueprint(paid_user)

    app.config.from_object(Config)
    #db = SQLAlchemy(app)
    #migrate = Migrate(app, db)

    #from app import models
    return app
from flask import Flask
import os
from .celery_utils import init_celery
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

PKG_NAME = os.path.dirname(os.path.realpath(__file__)).split("/")[-1]
db = SQLAlchemy()
login = LoginManager()
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
    from app import models

    db.init_app(app)
    login.init_app(app)
    login.login_view = 'paid_user.login'
    migrate = Migrate(app, db)

    @app.shell_context_processor
    def make_shell_context():
        return {'db':db}
    return app
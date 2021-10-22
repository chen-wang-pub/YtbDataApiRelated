import logging

from app import factory
import app

if __name__ == "__main__":
    app = factory.create_app(celery=app.celery)
    app.logger.setLevel(logging.INFO)
    app.run()
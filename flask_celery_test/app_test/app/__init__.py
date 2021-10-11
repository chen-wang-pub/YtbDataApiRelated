from celery import Celery

def make_celery(app_name = __name__):
    celery = Celery(
        app_name,
        backend='redis://localhost:6379',
        broker='redis://localhost:6379',
    )
    return celery

celery = make_celery()
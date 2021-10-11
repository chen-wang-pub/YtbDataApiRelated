from celery import Celery

app = Celery('app', backend='redis://localhost', broker='pyamqp://guest@localhost//')

@app.task
def add(x, y):
    return x + y


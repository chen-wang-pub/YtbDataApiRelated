from celery import Celery

app = Celery('celery_tutorial', backend='redis://localhost', broker='pyamqp://guest@localhost//')

@app.task
def add(x, y):
    return x + y

result = add.delay(4,4)
print(result.get())
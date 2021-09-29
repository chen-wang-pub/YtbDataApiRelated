from celery import Celery

app = Celery('celery_tutorial', backend='redis://localhost', broker='pyamqp://guest@localhost//',
             include=['celery_test.tasks'])

# Optional configuration, see the application user guide.
app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
    app.start()
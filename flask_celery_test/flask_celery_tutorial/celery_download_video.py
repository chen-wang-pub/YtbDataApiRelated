from celery import Celery
from flask import Flask, request
from pytube import YouTube


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(flask_app)

@celery.task
def download_video(ytb_id):
    ytb_base_url = 'https://www.youtube.com/watch?v='
    download_url = '{}{}'.format(ytb_base_url, ytb_id)
    yt = YouTube(download_url)
    all_stream = yt.streams.filter(only_audio=True)
    best_quality = all_stream[-1]  # last in list
    stream = yt.streams.get_by_itag(best_quality.itag)
    stream.download(output_path='', filename=ytb_id)


@flask_app.route('/')
def queue_download():
    video_ids = request.args.get('id', default='', type=str)
    video_ids = video_ids.split(',')
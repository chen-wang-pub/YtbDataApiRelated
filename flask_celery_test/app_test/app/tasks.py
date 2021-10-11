from app import celery
from pytube import YouTube
from flask import current_app
def on_complete(stream, file_handle):
    """

    :param file_handle:
    :return:
    """
    current_app.logger.debug('{} download finished'.format(file_handle))



@celery.task
def download_video(ytb_id):
    ytb_base_url = 'https://www.youtube.com/watch?v='
    download_url = '{}{}'.format(ytb_base_url, ytb_id)
    yt = YouTube(download_url, on_complete_callback=on_complete)
    all_stream = yt.streams.filter(only_audio=True)
    best_quality = all_stream[-1]  # last in list
    stream = yt.streams.get_by_itag(best_quality.itag)
    stream.download(output_path='', filename=yt.title)
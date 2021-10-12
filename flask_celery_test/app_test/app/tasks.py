from app import celery
from pytube import YouTube
from celery.utils.log import get_task_logger
import os
import subprocess

logger = get_task_logger((__name__))

def on_complete(stream, file_handle):
    """

    :param file_handle:
    :return:
    """
    logger.info('{} download finished'.format(file_handle))
    convert_audio(file_handle, '{}.mp3'.format(stream.title))
    logger.info('{} conversion finished'.format(stream.title))
    os.remove(file_handle)
    logger.info('{} removed'.format(file_handle))


def convert_audio( source_file, result_file):
    """
    convert the downloaded file to mp3
    :param source_file: path to the file to be converted
    :param result_file: should be path to the file with .mp3 extension
    :return:
    """
    ffmpeg_path = 'ffmpeg-static/ffmpeg'
    ffmpeg_real_path = os.path.join(os.path.dirname(__file__), ffmpeg_path)

    command = '{} -i "{}" "{}"'.format(ffmpeg_real_path, source_file, result_file)
    # app.logger.debug(command)
    completed = subprocess.run(command, capture_output=True, shell=True, text=True, input="y")
    # app.logger.debug(completed.stdout)
    # app.logger.debug(completed.stderr)
    return completed.returncode

@celery.task
def download_video(ytb_id):
    ytb_base_url = 'https://www.youtube.com/watch?v='
    download_url = '{}{}'.format(ytb_base_url, ytb_id)
    yt = YouTube(download_url, on_complete_callback=on_complete)
    all_stream = yt.streams.filter(only_audio=True)
    best_quality = all_stream[-1]  # last in list
    stream = yt.streams.get_by_itag(best_quality.itag)
    stream.download(output_path='', filename=yt.title)

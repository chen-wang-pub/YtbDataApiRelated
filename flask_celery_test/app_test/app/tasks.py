from app import celery
from pytube import YouTube
from celery.utils.log import get_task_logger
import os
import subprocess
import json

import time
import requests
import traceback

from app.utils.db_document_related import upload_if_not_exist, generate_doc, refresh_status
from app.const import update_url, read_url, write_url
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
    doc = generate_doc(ytb_id)
    read_payload = {'read_filter': {'item_id': ytb_id}}
    try:
        if not upload_if_not_exist(doc, read_payload, read_url, write_url):
            refresh_status(read_payload, read_url, update_url)
    except:
        logger.error(traceback.format_exc())
    logger.info('{} wrote to db'.format(ytb_id))

    ytb_base_url = 'https://www.youtube.com/watch?v='
    download_url = '{}{}'.format(ytb_base_url, ytb_id)
    yt = YouTube(download_url, on_complete_callback=on_complete)
    all_stream = yt.streams.filter(only_audio=True)
    best_quality = all_stream[-1]  # last in list
    stream = yt.streams.get_by_itag(best_quality.itag)
    stream.download(output_path='', filename=yt.title)

    data = {'update_filter': {'item_id': ytb_id},
            'update_aggregation': [
                {'$set': {'status': 'ready', 'ready_time': time.time(), 'title': yt.title}}]}
    response = requests.put(url=update_url, data=json.dumps(data),
                            headers={'content-type': 'application/json'})
    response_dict = json.loads(response.content)
    # logger.debug('update status is {}'.format(response_dict['update_status']))
    logger.info('update status is {}'.format(response_dict['update_status']))
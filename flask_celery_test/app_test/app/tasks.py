from app import celery
from pytube import YouTube
from celery.utils.log import get_task_logger
import os
import subprocess
import json
from celery.schedules import crontab

import time
import requests
import traceback

from app.utils.db_document_related import upload_if_not_exist, generate_doc, refresh_status
from app.const import update_url, read_url, write_url, delete_url
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
    # app.logger.info(command)
    completed = subprocess.run(command, capture_output=True, shell=True, text=True, input="y")
    # app.logger.info(completed.stdout)
    # app.logger.info(completed.stderr)
    return completed.returncode


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, periodic_the_main_thread.s(), name='Check queued video every 10 sec')


@celery.task
def download_video(ytb_id, download_dir):
    doc = generate_doc(ytb_id)
    read_payload = {'read_filter': {'item_id': ytb_id}}
    try:
        if not upload_if_not_exist(doc, read_payload, read_url, write_url):
            refresh_status(read_payload, read_url, update_url)
    except:
        logger.error(traceback.format_exc())
    logger.info('{} wrote to db'.format(ytb_id))
    # above block for testing only

    # update status to downloading
    data = {'update_filter': {'item_id': doc['item_id']},
            'update_aggregation': [{'$set': {'status': 'downloading'}}]}
    response = requests.put(url=update_url, data=json.dumps(data),
                            headers={'content-type': 'application/json'})
    response_dict = json.loads(response.content)
    logger.info('update status is {}'.format(response_dict['update_status']))

    ytb_base_url = 'https://www.youtube.com/watch?v='
    download_url = '{}{}'.format(ytb_base_url, ytb_id)
    yt = YouTube(download_url, on_complete_callback=on_complete)
    all_stream = yt.streams.filter(only_audio=True)
    best_quality = all_stream[-1]  # last in list
    stream = yt.streams.get_by_itag(best_quality.itag)
    stream.download(output_path=download_dir, filename=yt.title)

    data = {'update_filter': {'item_id': ytb_id},
            'update_aggregation': [
                {'$set': {'status': 'ready', 'ready_time': time.time(), 'title': yt.title}}]}
    response = requests.put(url=update_url, data=json.dumps(data),
                            headers={'content-type': 'application/json'})
    response_dict = json.loads(response.content)
    # logger.info('update status is {}'.format(response_dict['update_status']))
    logger.info('update status is {}'.format(response_dict['update_status']))


@celery.task
def periodic_the_main_thread():
    #logger.info('periodic task is running {}'.format(time.time()))
    temp_dir_loc = os.path.join(os.path.dirname(__file__), 'temp_storage')
    read_payload = {'read_filter': {'status': 'queued'}}
    response = requests.post(url=read_url, data=json.dumps(read_payload),
                             headers={'content-type': 'application/json'})
    doc_list = response.json()['response']
    # logger.info('{} new download waiting to be started'.format(len(doc_list)))
    for doc in doc_list:
        # check if it's expired
        current_sec = time.time()
        if (current_sec - int(doc['queued_time'])) > 600:
            data = {'delete_filter': {'item_id': doc['item_id']}}

            response = requests.delete(url=delete_url, data=json.dumps(data),
                                       headers={'content-type': 'application/json'})
            response_dict = json.loads(response.content)
            logger.info('delete status is {}'.format(response_dict['delete_status']))
            continue

        new_temp_dir = r'{}/{}'.format(temp_dir_loc, doc['item_id'])
        try:
            os.makedirs(new_temp_dir)

        except OSError as err:
            if err.errno == 17:
                logger.info('directory {} already created'.format(new_temp_dir))
            else:
                logger.info('something wrong when creating directory {}'.format(new_temp_dir))

        if os.path.isdir(new_temp_dir):
            # INSERT STARTING DOWNLOADING THREAD HERE
            download_video.delay(doc['item_id'], new_temp_dir)
            continue
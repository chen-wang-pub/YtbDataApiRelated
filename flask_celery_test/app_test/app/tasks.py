import shutil

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
from app.const import update_url, read_url, write_url, delete_url, MAX_TIMEOUT, TEMP_DIR_LOC
logger = get_task_logger((__name__))



def on_complete(stream, file_handle):
    """

    :param file_handle:
    :return:
    """
    logger.info('{} download finished'.format(file_handle))
    last_back_slash_index = file_handle.rfind('/')
    convert_audio(file_handle, os.path.join(file_handle[:last_back_slash_index], '{}.mp3'.format(stream.title)))
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
    sender.add_periodic_task(30.0, periodic_cleaner_thread.s(), name='Clean up every 30 sec')

@celery.task
def download_video(ytb_id, download_dir):
    """doc = generate_doc(ytb_id)
    read_payload = {'read_filter': {'item_id': ytb_id}}
    try:
        if not upload_if_not_exist(doc, read_payload, read_url, write_url):
            refresh_status(read_payload, read_url, update_url)
    except:
        logger.error(traceback.format_exc())"""
    logger.info('{} wrote to db'.format(ytb_id))
    # above block for testing only

    # update status to downloading
    data = {'update_filter': {'item_id': ytb_id},
            'update_aggregation': [{'$set': {'status': 'downloading'}}]}
    response = requests.put(url=update_url, data=json.dumps(data),
                            headers={'content-type': 'application/json'})
    response_dict = json.loads(response.content)
    logger.info('update status is {}'.format(response_dict['update_status']))

    ytb_base_url = 'https://www.youtube.com/watch?v='
    download_url = '{}{}'.format(ytb_base_url, ytb_id)
    try:
        yt = YouTube(download_url, on_complete_callback=on_complete)
        all_stream = yt.streams.filter(only_audio=True)
        best_quality = all_stream[-1]  # last in list
        stream = yt.streams.get_by_itag(best_quality.itag)
        stream.download(output_path=download_dir, filename=yt.title)
    except:
        logger.error(traceback.format_exc())
        logger.error('download for ytb item {} failed'.format(ytb_id))
        data = {'update_filter': {'item_id': ytb_id},
                'update_aggregation': [
                    {'$set': {'status': 'error', 'ready_time': time.time()}}]}
        response = requests.put(url=update_url, data=json.dumps(data),
                                headers={'content-type': 'application/json'})
        response_dict = json.loads(response.content)
        # logger.debug('update status is {}'.format(response_dict['update_status']))
        logger.debug('update status is {}'.format(response_dict['update_status']))
        logger.debug('Error when downloading {}'.format(ytb_id))
        return

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

        new_temp_dir = r'{}/{}'.format(TEMP_DIR_LOC, doc['item_id'])
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


@celery.task
def clean_ready_records(record_list, current_time):
    # TODO: delete record in db, then delete local files
    for doc in record_list:
        if current_time - doc['ready_time'] > MAX_TIMEOUT:
            data = {'delete_filter': {'item_id': doc['item_id']}}

            response = requests.delete(url=delete_url, data=json.dumps(data),
                                       headers={'content-type': 'application/json'})
            response_dict = json.loads(response.content)
            logger.debug('delete status for {} is {}'.format(doc['item_id'],
                                                             response_dict['delete_status']))

            dir_to_delete = r'{}/{}'.format(TEMP_DIR_LOC, doc['item_id'])
            if os.path.isdir(dir_to_delete):
                try:
                    shutil.rmtree(dir_to_delete)
                    logger.debug('{} is deleted'.format(dir_to_delete))
                except OSError as e:
                    logger.error('Error when deleting {}'.format(dir_to_delete))
                    logger.error(traceback.format_exc())


@celery.task
def clean_error_records(record_list, current_time):
    for doc in record_list:
        if current_time - doc['ready_time'] > MAX_TIMEOUT:
            data = {'delete_filter': {'item_id': doc['item_id']}}

            response = requests.delete(url=delete_url, data=json.dumps(data),
                                       headers={'content-type': 'application/json'})
            response_dict = json.loads(response.content)
            logger.debug('delete status is {}'.format(response_dict['delete_status']))

            dir_to_delete = r'{}/{}'.format(TEMP_DIR_LOC, doc['item_id'])
            if os.path.isdir(dir_to_delete):
                try:
                    shutil.rmtree(dir_to_delete)
                    logger.debug('{} is deleted due to error status'.format(dir_to_delete))
                except OSError as e:
                    logger.error('Error when deleting {}'.format(dir_to_delete))
                    logger.error(traceback.format_exc())

@celery.task
def periodic_cleaner_thread():
    logger.debug('the cleaner thread is running!!!!')
    # TODO: The loop should be run every 1 - 5 minutes
    # TODO: When receiving request, the server will also check records in ready status to see if it's in there,
    #  if so, set the ready_time to the current time to avoid the record being cleaned up
    read_payload = {'read_filter': {'status': 'ready'}}
    response = requests.post(url=read_url, data=json.dumps(read_payload),
                             headers={'content-type': 'application/json'})
    ready_list = response.json()['response']
    # logger.debug(len(ready_list))
    clean_ready_records.delay(ready_list, time.time())
    read_payload = {'read_filter': {'status': 'error'}}
    response = requests.post(url=read_url, data=json.dumps(read_payload),
                             headers={'content-type': 'application/json'})
    error_list = response.json()['response']
    # logger.debug(len(error_list))
    clean_error_records.delay(error_list, time.time())

import math
import re
import shutil

from app import celery
from pytube import YouTube
from celery.utils.log import get_task_logger
import os
import subprocess
import json
from lxml import html
from celery.schedules import crontab

import time
import requests
import traceback

from app.utils.db_document_related import upload_if_not_exist, generate_doc, refresh_status
from app.const import update_url, read_url, write_url, delete_url, MAX_TIMEOUT, TEMP_DIR_LOC, generate_db_access_obj, spotify_db, ytb_playlist_db
from app.utils.celery_task_utils import get_song_info
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


@celery.task(bind=True)
def check_queued_list(self, item_id_list):
    """
    Since it seems that without using socket, the frontend need to poll result from the backend to check celery task
    status. then maybe just start a celery task that starts downloading all the item requested.
    The view that starts this task will return the task id back to the client.
    The client then use the task id in view to retrieve update of this task.
    """
    """celery_task_id_list = []
    for ytb_id in item_id_list:
        doc = generate_doc(ytb_id)
        read_payload = {'read_filter': {'item_id': ytb_id}}
        try:
            if not upload_if_not_exist(doc, read_payload, read_url, write_url):
                refresh_status(read_payload, read_url, update_url)
        except:
            logger.error(traceback.format_exc())

        celery_task = download_video.delay(ytb_id)
        celery_task_id_list.append(celery_task.task_id)"""
    status_dict = {}
    while len(item_id_list) > 0:
        for i in range(len(item_id_list)-1, -1, -1):
            read_payload = {'read_filter': {'item_id': item_id_list[i]}}
            response = requests.post(url=read_url, data=json.dumps(read_payload),
                                     headers={'content-type': 'application/json'})
            doc_list = response.json()['response']
            if len(doc_list) != 1:
                logger.error('sth went wrong in check_queued_list for item {}'.format(item_id_list[i]))
                logger.error(traceback.format_exc())
                return {"status_dict": status_dict, "status": "ERROR"}
            if doc_list[0]['status'] == 'ready' or doc_list[0]['status'] == 'error':
                status_dict[item_id_list[i]] = doc_list[0]['status']
                del item_id_list[i]
            else:
                status_dict[item_id_list[i]] = doc_list[0]['status']
        self.update_state(state='PROGRESS', meta={"status_dict": status_dict, "status": "PROGRESS"})
        logger.info('status sent from check_queued_list {}'.format(status_dict))
        time.sleep(30)
    return {"status_dict": status_dict, "status": "SUCCESS"}


@celery.task
def extract_spotify_playlist(playlist_id):
    """
    This function takes the spotify playlist id as argument.
    It will first try simulate a get request with headers to the playlist url to get access_token.
    Then it will use the spotify api, the access_token on a utility function to get all song's info from the list
    It returns 1) a dict obj contains the populated db access dict 2) a list of dict obj of all songs info
    """
    spotify_url = 'https://open.spotify.com/playlist/{}'.format(playlist_id)
    api_prefix = 'https://api.spotify.com/v1/playlists'
    database_name = 'spotify_playlist'
    collection_name = playlist_id
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"}
    response = requests.get(spotify_url, headers=headers, timeout=10)
    html_content = html.fromstring(response.content)
    playlist_name = html_content.findtext('.//title')

    logger.info("Spotify playlist title is {}".format(playlist_name))

    access_token_obj_str = html_content.xpath('//*[@id="config"]/text()')[0]
    access_token_obj = json.loads(access_token_obj_str)
    access_token = access_token_obj['accessToken']
    headers['Authorization'] = 'Bearer {}'.format(access_token)

    logger.debug("The access token for {} is {}".format(playlist_id, access_token))


    total_songs = html_content.xpath("//meta[@property='music:song_count']/@content")[0]
    logger.debug('total {} songs in the list {}'.format(total_songs, playlist_id))
    total_request = math.ceil(int(total_songs) / 100)
    logger.debug(total_request)
    list_suffix = html_content.xpath("//meta[@property='og:url']/@content")[0].split('/')[-1]
    logger.debug('song list url suffix: {}'.format(list_suffix))
    api_url = '{}/{}'.format(api_prefix, list_suffix)
    logger.debug('api url for the playlist {} is {}'.format(playlist_id, api_url))


    spotify_song_docs = get_song_info(api_url, headers, is_first_page=True)

    logger.debug(len(spotify_song_docs))

    playlist_db_access = generate_db_access_obj(spotify_db, collection_name)

    return {'playlist_db_access': playlist_db_access, 'spotify_song_docs': spotify_song_docs}


@celery.task
def search_for_ytb_items_from_spotify_list(dbaccess_songinfo_dict):
    logger.debug('placeholder task, argument is {}'.format(dbaccess_songinfo_dict))

    time.sleep(30)

    return ['A8RCCDzykHU', 'iUEhr8GE6Bo', 'NZc__Hhi4L8', 'kKqsV3t94PY']
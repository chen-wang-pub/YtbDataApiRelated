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

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from app.utils.db_document_related import upload_if_not_exist, generate_doc, refresh_status
from app.const import update_url, read_url, write_url, delete_url, MAX_TIMEOUT, TEMP_DIR_LOC, generate_db_access_obj, spotify_db, ytb_playlist_db, command_executor
from app.utils.celery_task_utils import get_song_info, generate_ytb_item_doc
from app.utils.YoutubeDataApiCaller import YoutubeDataApiCaller
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
        cleaned_filename = yt.title.replace('/','')
        all_stream = yt.streams.filter(only_audio=True)
        best_quality = all_stream[-1]  # last in list
        stream = yt.streams.get_by_itag(best_quality.itag)
        stream.download(output_path=download_dir, filename=cleaned_filename)
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
                {'$set': {'status': 'ready', 'ready_time': time.time(), 'title': cleaned_filename}}]}
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
    status_list = []
    while len(item_id_list) > 0:
        for i in range(len(item_id_list)-1, -1, -1):
            read_payload = {'read_filter': {'item_id': item_id_list[i]}}
            response = requests.post(url=read_url, data=json.dumps(read_payload),
                                     headers={'content-type': 'application/json'})
            doc_list = response.json()['response']
            if len(doc_list) != 1:
                logger.error('sth went wrong in check_queued_list for item {}'.format(item_id_list[i]))
                logger.error(traceback.format_exc())
                return {"used_for_template_rendering": status_list, "status": "ERROR"}
            if doc_list[0]['status'] == 'ready':
                status_dict[item_id_list[i]] = doc_list[0]['title']
                #status_list.append([item_id_list[i], doc_list[0]['title']])
                del item_id_list[i]
            elif doc_list[0]['status'] == 'error':
                status_dict[item_id_list[i]] = doc_list[0]['status']
                del item_id_list[i]
            else:
                status_dict[item_id_list[i]] = doc_list[0]['status']
                #status_list.append([item_id_list[i], doc_list[0]['status']])
            status_list = [[k, v] for k, v in status_dict.items()]
        self.update_state(state='PROGRESS', meta={"used_for_template_rendering": status_list, "status": "PROGRESS"})
        logger.info('status sent from check_queued_list {}'.format(status_list))
        time.sleep(30)
    return {"used_for_template_rendering": status_list, "status": "SUCCESS"}


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
    #database_name = 'spotify_playlist'
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
    logger.info('placeholder task, argument is {}'.format(dbaccess_songinfo_dict))
    result_list = []
    ytb_api_caller = YoutubeDataApiCaller()
    for doc in dbaccess_songinfo_dict['spotify_song_docs']:
        for_query = "{} {}".format(doc['name'], ' '.join(doc['artists']))
        duration_ms = doc['duration_ms']
        try:
            respond = ytb_api_caller.search_query(for_query, check_existing=True)
            item_id = YoutubeDataApiCaller.rank_documents(respond, duration_ms)
            result_list.append(item_id)
        except Exception:
            logger.error(traceback.format_exc())
            return {'item_id_list': result_list}

    return {'item_id_list': result_list}


@celery.task
def extract_ytb_channel_videos(channel_id):
    channel_videos_url = "https://www.youtube.com/channel/{}/videos".format(channel_id)
    user_videos_url = "https://www.youtube.com/{}/videos".format(channel_id)
    logger.info('The url of the youtube channel is {}'.format(channel_videos_url))
    logger.info('The url of the youtube  is {}'.format(user_videos_url))
    driver = webdriver.Remote(command_executor, desired_capabilities=DesiredCapabilities.FIREFOX)
    driver.get(channel_videos_url)

    item_xpath = '//*[@id="video-title"]'
    try:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, item_xpath)))
    except TimeoutException:
        driver.get(user_videos_url)
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, item_xpath)))

    total_music = len(driver.find_elements_by_xpath(item_xpath))
    flag = False
    while not flag:
        driver.execute_script(
            "window.scrollBy(0,document.body.scrollHeight || document.documentElement.scrollHeight)")

        max_wait = 30
        while max_wait > 0:
            time.sleep(0.5)
            temp_total = len(driver.find_elements_by_xpath(item_xpath))
            if temp_total != total_music:
                total_music = temp_total
                break
            # height = driver.execute_script("return document.body.scrollHeight")
            # print('current scroll height is {}'.format(height))

            max_wait -= 1
        if max_wait == 0:
            flag = True
    # print(driver.page_source)

    logger.info(total_music)
    playlist_owner = driver.find_element_by_xpath('//*[@id="text-container"]/*[@id="text"]').text
    logger.info(playlist_owner)
    all_link = driver.find_elements_by_xpath('//div[@id="dismissible"]')
    logger.info(len(all_link))
    ytb_doc_list = []
    for a_link in all_link:
        # print(a_link.get_attribute('innerHTML'))
        title = a_link.find_element_by_xpath('.//*[@id="video-title-link"]').get_attribute('title')
        href = a_link.find_element_by_xpath('.//*[@id="video-title-link"]').get_attribute('href')
        duration = a_link.find_element_by_xpath('.//span[@id="text"]').text
        try:
            view = a_link.find_element_by_xpath('.//*[@id="metadata-line"]/span[1]').text
        except:
            view = "unknown views"
        ytb_item_doc = generate_ytb_item_doc(href, title, duration, view)
        logger.debug(ytb_item_doc)
        ytb_doc_list.append(ytb_item_doc)
    driver.quit()

    ytb_channel_db_access_dict = generate_db_access_obj(ytb_playlist_db, channel_id)

    logger.info('This ytb channel db access dict is: {}'.format(ytb_channel_db_access_dict))

    item_id_list = []
    used_for_template_rendering = []
    number_added_doc = 0
    for doc in ytb_doc_list:
        item_id_list.append(doc['item_id'])
        read_payload = {'read_filter': {'item_id': doc['item_id']}}
        used_for_template_rendering.append([doc['item_id'], doc['title']])
        if upload_if_not_exist(doc, read_payload, ytb_channel_db_access_dict['read'], ytb_channel_db_access_dict['write']):
            number_added_doc += 1
    return {'ytb_channel_db_access_dict': ytb_channel_db_access_dict, 'item_id_list': item_id_list, 'used_for_template_rendering': used_for_template_rendering}


@celery.task
def extracted_data_processor(result_dict):
    assert 'item_id_list' in result_dict
    for video_id in result_dict['item_id_list']:

        doc = generate_doc(video_id)
        read_payload = {'read_filter': {'item_id': video_id}}
        try:
            if not upload_if_not_exist(doc, read_payload, read_url, write_url):
                refresh_status(read_payload, read_url, update_url)
        except:
            logger.error(traceback.format_exc())
        logger.info('{} wrote to db'.format(video_id))
        logger.info('{} is queued for downloading'.format(video_id))
    return result_dict['item_id_list']

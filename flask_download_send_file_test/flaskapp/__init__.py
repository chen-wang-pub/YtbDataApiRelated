import threading
import os
import time
import json
import requests
import logging
import traceback
from flask import Flask
from pytube import YouTube

from queue_request import queue_request
#from the_thread import TheThread
from logging.config import dictConfig
def create_app(test_config=None):
    # create and configure the
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }},
        'loggers': {
            'root': {  # root logger
                'handlers': ['wsgi'],
                'level': 'DEBUG',
            },
            'the_thread': {
                'handlers': ['wsgi'],
                'level': 'DEBUG',
            },
            '__main__': {  # if __name__ == '__main__'
                'handlers': ['wsgi'],
                'level': 'DEBUG',
            },
        }
    })
    app = Flask('flaskapp', instance_relative_config=True)


    app.logger.debug('flask app started')
    app.register_blueprint(queue_request)


    #app.register_blueprint(send_file)
    class TheThread(threading.Thread):
        """
        record status in db: queued, downloading, ready,
        max time before expiring should be around 5-10min
        """

        def __init__(self):
            super(TheThread, self).__init__()
            db_info_dict = {
                'db_url': '172.17.0.4',
                'db_port': '27017',
                'db_name': 'ytb_temp_file',
                'col_name': 'id_timestamp_status'
            }
            self.read_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/read'.format(db_info_dict['db_url'],
                                                                                            db_info_dict['db_port'],
                                                                                            db_info_dict['db_name'],
                                                                                            db_info_dict['col_name'])
            self.update_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/update'.format(db_info_dict['db_url'],
                                                                                                db_info_dict['db_port'],
                                                                                                db_info_dict['db_name'],
                                                                                                db_info_dict[
                                                                                                    'col_name'])
            self.delete_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/delete'.format(db_info_dict['db_url'],
                                                                                                db_info_dict['db_port'],
                                                                                                db_info_dict['db_name'],
                                                                                                db_info_dict[
                                                                                                    'col_name'])
            self.temp_dir_loc = os.path.join(os.path.dirname(__file__), 'temp_storage')
            self.thread_name = 'main_thread'
            self.timeout = 600

        def create_folder_start_download(self, item_id):
            """
            Check if dir exist, if not, create it, and start the download thread with timeout,
            item_id, use item_id as thread name, dir location
            :param item_id:
            :return:
            """

        def run(self):
            app.logger.debug('the main thread is running!!!!')
            while True:
                read_playload = {'read_filter': {'status': 'queued'}}
                response = requests.post(url=self.read_url, data=json.dumps(read_playload),
                                         headers={'content-type': 'application/json'})
                doc_list = response.json()['response']
                # logger.debug('{} new download waiting to be started'.format(len(doc_list)))
                for doc in doc_list:
                    # check if it's expired
                    current_sec = time.time()
                    if (current_sec - int(doc['queued_time'])) > 600:
                        data = {'delete_filter': {'item_id': doc['item_id']}}

                        response = requests.delete(url=self.delete_url, data=json.dumps(data),
                                                   headers={'content-type': 'application/json'})
                        response_dict = json.loads(response.content)
                        app.logger.debug('delete status is {}'.format(response_dict['delete_status']))
                        continue

                    new_temp_dir = r'{}/{}'.format(self.temp_dir_loc, doc['item_id'])
                    try:
                        os.makedirs(new_temp_dir)

                    except OSError as err:
                        if err.errno == 17:
                            app.logger.debug('directory {} already created'.format(new_temp_dir))
                        else:
                            app.logger.debug('something wrong when creating directory {}'.format(new_temp_dir))

                    if os.path.isdir(new_temp_dir):
                        # INSERT STARTING DOWNLOADING THREAD HERE
                        download_thread = PytubeThread(doc['item_id'], new_temp_dir, self.update_url)
                        download_thread.start()
                        data = {'update_filter': {'item_id': doc['item_id']},
                                'update_aggregation': [{'$set': {'status': 'downloading'}}]}
                        response = requests.put(url=self.update_url, data=json.dumps(data),
                                                headers={'content-type': 'application/json'})
                        response_dict = json.loads(response.content)
                        app.logger.debug('update status is {}'.format(response_dict['update_status']))
                        continue

                time.sleep(10)

    class PytubeThread(threading.Thread):
        ytb_base_url = 'https://www.youtube.com/watch?v='

        def __init__(self, itemid, dirlocation, update_url):
            super(PytubeThread, self).__init__()
            self.download_url = '{}{}'.format(self.ytb_base_url, itemid)
            self.download_dir = dirlocation
            self.item_id = itemid
            self.update_url = update_url

        def on_complete(self, stream, file_handle):
            """

            :param file_handle:
            :return:
            """

            data = {'update_filter': {'item_id': self.item_id},
                    'update_aggregation': [
                        {'$set': {'status': 'ready', 'ready_time': time.time(), 'title': self.title}}]}
            response = requests.put(url=self.update_url, data=json.dumps(data),
                                    headers={'content-type': 'application/json'})
            response_dict = json.loads(response.content)
            # logger.debug('update status is {}'.format(response_dict['update_status']))
            app.logger.debug('update status is {}'.format(response_dict['update_status']))

        def download_best_audio(self):
            yt = YouTube(self.download_url, on_complete_callback=self.on_complete)
            self.title = yt.title
            # logger.debug('about to download {} from url: {}'.format(yt.title, self.download_url))
            all_stream = yt.streams.filter(only_audio=True)
            best_quality = all_stream[-1]  # last in list
            stream = yt.streams.get_by_itag(best_quality.itag)
            return stream.download(output_path=self.download_dir, filename=self.item_id)

        def run(self):
            app.logger.debug('Starting the download of {}'.format(self.item_id))
            try:
                self.download_best_audio()
                app.logger.debug(('Download of {} is finished.'.format(self.item_id)))
            except:
                app.logger.debug(traceback.format_exc())

                data = {'update_filter': {'item_id': self.item_id},
                        'update_aggregation': [
                            {'$set': {'status': 'error'}}]}
                response = requests.put(url=self.update_url, data=json.dumps(data),
                                        headers={'content-type': 'application/json'})
                response_dict = json.loads(response.content)
                # logger.debug('update status is {}'.format(response_dict['update_status']))
                app.logger.debug('update status is {}'.format(response_dict['update_status']))
                app.logger.debug('Error when downloading {}'.format(self.item_id))

    TheThread().start()
    return app
if __name__ == '__main__':
    #logging.basicConfig(filename='error.log',level=logging.DEBUG)
    print('flask running!!!')
    app = create_app()
    #TheThread().start()

    app.run(debug=True, use_reloader=False, port=5005, host='localhost')
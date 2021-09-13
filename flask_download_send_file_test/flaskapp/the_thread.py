import threading
import os
import time
import json
import requests

from flask import current_app

class TheThread(threading.Thread):
    """
    record status in db: queued, downloading, ready,
    max time before expiring should be around 5-10min
    """
    def __init__(self):
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
        self.write_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/update'.format(db_info_dict['db_url'],
                                                                                     db_info_dict['db_port'],
                                                                                     db_info_dict['db_name'],
                                                                                     db_info_dict['col_name'])
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
        while True:
            time.sleep(20)

            read_playload = {'read_filter': {'status': 'queued'}}
            response = requests.post(url=self.read_url, data=json.dumps(read_playload),
                                     headers={'content-type': 'application/json'})
            doc_list = response.json()['response']
class PytubeThread(threading.Thread):
    ytb_base_url = 'https://www.youtube.com/watch?v='
    def __init__(self, threadname, itemid, timeout, dirlocation):

        pass

    def run(self):

        pass
if __name__ == '__main__':
    db_info_dict = {
        'db_url': '172.17.0.4',
        'db_port': '27017',
        'db_name': 'ytb_temp_file',
        'col_name': 'id_timestamp_status'
    }
    read_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/read'.format(db_info_dict['db_url'],
                                                                               db_info_dict['db_port'],
                                                                               db_info_dict['db_name'],
                                                                               db_info_dict['col_name'])
    delete_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/delete'.format(db_info_dict['db_url'],
                                                                               db_info_dict['db_port'],
                                                                               db_info_dict['db_name'],
                                                                               db_info_dict['col_name'])
    read_playload = {'read_filter': {'status': 'queued'}}
    response = requests.post(url=read_url, data=json.dumps(read_playload),
                             headers={'content-type': 'application/json'})
    doc_list = response.json()['response']
    for doc in doc_list:
        print(doc['item_id'])
        print(doc['total_sec'])
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
                                                                                     db_info_dict['col_name'])
        self.delete_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/delete'.format(db_info_dict['db_url'],
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
            current_app.debug('{} new download waiting to be started'.format(len(doc_list)))
            for doc in doc_list:
                # check if it's expired
                current_sec = time.time()
                if (current_sec - int(doc['total_sec'])) > 600:
                    data = {'delete_filter': {'item_id': doc['item_id']}}

                    response = requests.delete(url=self.delete_url, data=json.dumps(data),
                                               headers={'content-type': 'application/json'})
                    response_dict = json.loads(response.content)
                    print('delete status is {}'.format(response_dict['delete_status']))
                    continue

                new_temp_dir = r'{}/{}'.format(self.temp_dir_loc, doc['item_id'])
                try:
                    os.makedirs(new_temp_dir)

                except OSError as err:
                    if err.errno == 17:
                        print('directory {} already created'.format(new_temp_dir))
                    else:
                        print('something wrong when creating directory {}'.format(new_temp_dir))

                if os.path.isdir(new_temp_dir):
                    # INSERT STARTING DOWNLOADING THREAD HERE
                    PytubeThread(doc['item_id'], self.timeout, new_temp_dir).start()

                    data = {'update_filter': {'item_id': doc['item_id']},
                            'update_aggregation': [{'$set': {'status': 'downloading'}}]}
                    response = requests.put(url=self.update_url, data=json.dumps(data),
                                            headers={'content-type': 'application/json'})
                    response_dict = json.loads(response.content)
                    print('update status is {}'.format(response_dict['update_status']))
                    continue


class PytubeThread(threading.Thread):
    ytb_base_url = 'https://www.youtube.com/watch?v='
    def __init__(self, itemid, timeout, dirlocation):
        super(PytubeThread, self).__init__()
        self.timeout = 60
        self.start_time = time.time()
        pass

    def run(self):

        pass


if __name__ == '__main__':
    """db_info_dict = {
        'db_url': '172.17.0.4',
        'db_port': '27017',
        'db_name': 'ytb_temp_file',
        'col_name': 'id_timestamp_status'
    }
    temp_dir_loc = os.path.join(os.path.dirname(__file__), 'temp_storage')
    read_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/read'.format(db_info_dict['db_url'],
                                                                               db_info_dict['db_port'],
                                                                               db_info_dict['db_name'],
                                                                               db_info_dict['col_name'])
    delete_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/delete'.format(db_info_dict['db_url'],
                                                                               db_info_dict['db_port'],
                                                                               db_info_dict['db_name'],
                                                                               db_info_dict['col_name'])
    update_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/update'.format(db_info_dict['db_url'],
                                                                               db_info_dict['db_port'],
                                                                               db_info_dict['db_name'],
                                                                               db_info_dict['col_name'])
    time_out = 600

    read_playload = {'read_filter': {'status': 'queued'}}
    response = requests.post(url=read_url, data=json.dumps(read_playload),
                             headers={'content-type': 'application/json'})
    doc_list = response.json()['response']
    for doc in doc_list:
        # check if it's expired
        current_sec = time.time()
        if (current_sec - int(doc['total_sec'])) > 600:
            data = {'delete_filter': {'item_id': doc['item_id']}}

            response = requests.delete(url=delete_url, data=json.dumps(data),
                                       headers={'content-type': 'application/json'})
            response_dict = json.loads(response.content)
            print('delete status is {}'.format(response_dict['delete_status']))
            continue

        new_temp_dir = r'{}/{}'.format(temp_dir_loc, doc['item_id'])
        try:
            os.makedirs(new_temp_dir)

        except OSError as err:
            if err.errno == 17:
                print('directory {} already created'.format(new_temp_dir))
            else:
                print('something wrong when creating directory {}'.format(new_temp_dir))

        if os.path.isdir(new_temp_dir):
            # INSERT STARTING DOWNLOADING THREAD HERE
            PytubeThread(doc['item_id'], time_out, new_temp_dir).start()

            data = {'update_filter': {'item_id': doc['item_id']},
                    'update_aggregation': [{'$set': {'status': 'downloading'}}]}
            response = requests.put(url=update_url, data=json.dumps(data),
                                    headers={'content-type': 'application/json'})
            response_dict = json.loads(response.content)
            print('update status is {}'.format(response_dict['update_status']))
            continue"""
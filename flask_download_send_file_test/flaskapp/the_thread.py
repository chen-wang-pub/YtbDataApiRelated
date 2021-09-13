import threading
import os
import time


class TheThread(threading.Thread):
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

    def run(self):
        while True:
            time.sleep(20)


class PytubeThread(threading.Thread):
    def __init__(self, itemid, timeout, dirlocation):

        pass

    def run(self):

        pass

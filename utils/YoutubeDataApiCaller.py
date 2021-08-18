from pymongo import MongoClient, DESCENDING
from pymongo.errors import DuplicateKeyError
import requests
import json
import datetime
import logging

logging.basicConfig(level=logging.DEBUG)
api_key_pool_dict = {
    'db_url': 'localhost',
    'db_port': 1024,
    'db_name': 'KeyPool',
    'col_name': 'YoutubeDataApi',
}


class YoutubeDataApiCaller:
    """
    This class is for calling youtubedataapi
    The aim of this class is to manage the quota limit from youtube api key
    It expects an api key pool dedicated for youtubedataapi search query stored in mongodb
    The document schema of the api key stored in mongodb should be as the following
    {
        'key':'xxxx'
        'in_use': True/False
        'quota_exceeded' : True/False
        'last_update_date': 'xxxx-xx-xx'
    }


    The class will first pull certain number of api key from the database upon creation
        error handling is needed for insufficient api key

    The class will then use the pulled api keys sequentially till the quota of the key runs out for the day,
    it then will then update the in_use and last_update_date status of the api key in the db.

    Whenever a key's quota runs out while making an api call, it updates to the db about the quota-exceeded status,
    then it will retry the api call with the next available api key

    When all the api key pulled from db exceeded the quota, it will release and update the status of the key to db,
    then it will try pull new keys from db.

    When the class ends, it will release and update the status of the key to db.

    According to google's document, the quota of the key refreshes everyday 0:00 pacific time,
    the db should be in maintenance to update the quota status of all keys / the class will update the quota info base
    on the last_update_date


    """
    _documents_to_update = []
    _available_keys = []
    _ytbApiUrlTemplate = "https://youtube.googleapis.com/youtube/v3/search?q={}&key={}"

    def __init__(self, db_url, db_port, db_name, col_name, number_of_keys=3):
        self.db_client = MongoClient(db_url, db_port)
        self.db = self.db_client[db_name]
        self.col = self.db[col_name]
        self._max_key = number_of_keys
        self._pull_api_key()

    @property
    def max_key(self):
        return self._max_key

    @max_key.setter
    def max_key(self, number_of_keys):
        self._max_key = number_of_keys

    @property
    def ytb_api_url_template(self):
        return self._ytbApiUrlTemplate

    @ytb_api_url_template.setter
    def ytb_api_url_template(self, url):
        self._ytbApiUrlTemplate = url

    def search_query(self, query_string):

        pass

    def _pull_api_key(self):
        temp_keys = self.col.find({'in_use': False, 'quota_exceeded': False, }, limit=self.max_key)
        if temp_keys == 0:
            return False
        else:
            self._available_keys = temp_keys
            for key in temp_keys:
                temp_doc = YoutubeDataApiCaller.generate_document(key, True, False, datetime.datetime.now())
                self._update_key_status(temp_doc)  # should check if the status is success or not
            return len(self._available_keys)

    def _retry_search(self, query_string):
        pass

    def _update_key_status(self, docs_for_update):
        result = self.col.update_one({'key': docs_for_update['key']},
               {"$set": {'in_use': docs_for_update['in_use'], 'quota_exceeded': docs_for_update['quota_exceeded'],
                         'last_update_date': docs_for_update['last_update_date']}}
               )

        if result.modified_count == 1:
            return True
        else:
            return False

    @staticmethod
    def generate_document(key, in_use, quota_exceeded, last_update_date):

        if not isinstance(key, str) or not isinstance(in_use, bool) or\
                not isinstance(quota_exceeded, bool) or not isinstance(last_update_date, datetime.datetime):
            return False
        datetime_str_format = '%Y-%m-%d'
        doc_dict = {'key': key, 'in_use': in_use, 'quota_exceeded': quota_exceeded,
                    'last_update_date': last_update_date.strftime(datetime_str_format)}

        return doc_dict

    def __del__(self):
        pass


def add_keys_to_db(api_keys, db_url, db_port, db_name, col_name):
    db_client = MongoClient(db_url, db_port)
    db = db_client[db_name]
    col = db[col_name]
    col.create_index([('key', DESCENDING)], unique=True)

    failed_keys = []

    for api_key in api_keys:
        doc_dict = YoutubeDataApiCaller.generate_document(api_key, False, False, datetime.datetime.now())
        try:
            col.insert_one(doc_dict)
            logging.debug('record added')
        except DuplicateKeyError:
            logging.debug(('name already in database for {}'.format(doc_dict)))
            failed_keys.append(api_key)

    return failed_keys


def update_db_keys_status(key_to_update, db_url, db_port, db_name, col_name):
    db_client = MongoClient(db_url, db_port)
    db = db_client[db_name]
    col = db[col_name]

    result = col.update_one({'key': key_to_update['key']},
               {"$set": {'in_use': key_to_update['in_use'], 'quota_exceeded': key_to_update['quota_exceeded'],
                         'last_update_date': key_to_update['last_update_date']}}
               )

    if result.modified_count == 1:
        return True
    else:
        return False


if __name__ == '__main__':
    test = YoutubeDataApiCaller(**api_key_pool_dict)#'localhost', 1024, 'KeyPool', 'YoutubeDataApi')
    a = YoutubeDataApiCaller.generate_document('tewatwearew', False, False, datetime.datetime.now())
    logging.debug(a)
    import yaml

    with open('api_keys.yaml', 'r') as f:
        doc = yaml.load(f, Loader=yaml.BaseLoader)

    for api in doc['YTB_API_POOL']:
        logging.debug(api)
        #db_doc = YoutubeDataApiCaller.generate_document(api, False, False, datetime.datetime.now())
    failed_keys = add_keys_to_db(doc['YTB_API_POOL'], **api_key_pool_dict)#'localhost', 1024, 'KeyPool', 'YoutubeDataApi')
    if failed_keys:
        logging.debug(failed_keys)

from pymongo import MongoClient, DESCENDING
from pymongo.errors import DuplicateKeyError
import requests
import json
import datetime
import logging
from enum import Enum, unique

from StoreSearchResponse import storeSearchResponse, get_all_doc_contains_query_string

logging.basicConfig(level=logging.DEBUG)
api_key_pool_dict = {
    'db_url': 'localhost',
    'db_port': 27017,
    'db_name': 'KeyPool',
    'col_name': 'YoutubeDataApi',
}


@unique
class YtbApiErrorEnum(Enum):
    UNDEFINED_ERROR = 0
    QUOTA_EXCEEDED = 1


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
    _available_keys = []
    _ytbApiUrlTemplate = "https://youtube.googleapis.com/youtube/v3/search?q={}&key={}"
    _error_msg_identifier_dict = {'QUOTA_EXCEEDED': 'you have exceeded your',}

    def __init__(self, db_url, db_port, db_name, col_name, number_of_keys=3):
        self.db_client = MongoClient(db_url, db_port)
        self.db = self.db_client[db_name]
        self.col = self.db[col_name]
        self._max_key = number_of_keys
        #self._pull_api_key()

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

    @property
    def has_available_keys(self):
        if self._available_keys:
            return True
        return False

    def _check_error(self, api_reply_json):
        """
        Check if pre determined error exists in the response
        return the pre-set enum error obj if exists, or enum undefined error obj, or False when no error
        :param api_reply_json:
        :return:
        """
        if 'error' in api_reply_json:
            # error_code = api_reply_json['error']['code']
            error_message = api_reply_json['error']['message']

            for k, v in self._error_msg_identifier_dict.items():
                if v in error_message:
                    return YtbApiErrorEnum[k]
            return YtbApiErrorEnum.UNDEFINED_ERROR
        return False

    def _parse_ytb_api_response(self, api_reply_json, query_string):
        doc_list = []
        searched_items = api_reply_json['items']
        for item in searched_items:
            etag = item['etag']
            kind = item['id']['kind']
            if 'videoId' in item['id']:
                item_id = item['id']['videoId']
            elif 'channelId' in item['id']:
                item_id = item['id']['channelId']
            elif 'playlistId' in item['id']:
                item_id = item['id']['playlistId']
            record_doc = {'etag': etag, 'kind': kind, 'item_id': item_id, 'query_string': [query_string]}
            doc_list.append(record_doc)
        return doc_list

    def search_query(self, query_string, check_existing=False):

        if check_existing:
            existed_list = get_all_doc_contains_query_string(query_string)
            if existed_list:
                return existed_list

        if not self.has_available_keys:
            result = self._pull_api_key()
            if not result:
                logging.error('error when pulling api keys while executing search_query')
                return False

        # TODO: Search in the storeSearchResponse database to check if the query_string has been used for searching.

        #result = checkStoredSearchResponse(query_string)
        #if result:
        #   return result

        try:
            final_url = self._ytbApiUrlTemplate.format(query_string, self._available_keys[0])
            payload = {}
            headers = {}
            response = requests.request("GET", final_url, headers=headers, data=payload)
            ytb_result = json.loads(response.text)

            error_obj = self._check_error(ytb_result)
            if error_obj:
                return self._retry_search(query_string, error_obj)

            doc_list = self._parse_ytb_api_response(ytb_result, query_string)
            # TODO: Queue this method in a thread in background
            storeSearchResponse(doc_list)

            return doc_list

        except requests.exceptions.RequestException:
            logging.error('error in requests module')
            return False
        finally:
            self._release_all_key()

    def _pull_api_key(self):
        documents = self.col.find({'in_use': False, 'quota_exceeded': False, }, limit=self.max_key)
        temp_keys = [a_doc['key'] for a_doc in documents]
        logging.debug('temp keys:{}'.format(temp_keys))
        logging.debug(list(documents))
        if not temp_keys:
            return False
        else:
            self._available_keys = temp_keys
            for key in temp_keys:
                temp_doc = YoutubeDataApiCaller.generate_document(key, True, False, datetime.datetime.now())
                self._update_key_status(temp_doc)  # should check if the status is success or not
            return len(self._available_keys)

    def _retry_search(self, query_string, error_obj):
        if error_obj.value == YtbApiErrorEnum.QUOTA_EXCEEDED.value:
            doc_quota_exceeded = self.generate_document(self._available_keys[0], False, True, datetime.datetime.now())
            result = self._update_key_status(doc_quota_exceeded)
            if not result:
                logging.error('Error when updating document to database in _retry_search')
                return False
            self._available_keys.pop(0)
            if len(self._available_keys) == 0:
                pull_result = self._pull_api_key()
                if not pull_result:
                    logging.error('Error when pulling new api key in _retry_search')
                    return False
            return self.search_query(query_string)
        if error_obj.value == YtbApiErrorEnum.UNDEFINED_ERROR.value:
            logging.error('Unhandled error in _retry_search')
            return False

    def _update_key_status(self, docs_for_update):
        logging.debug(docs_for_update)
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
        logging.debug('api key document generated: {}'.format(doc_dict))
        return doc_dict

    def _release_all_key(self):

        failed_released_key = []
        for key in self._available_keys:
            update_doc = self.generate_document(key, False, False, datetime.datetime.now())
            update_result = self._update_key_status(update_doc)
            if update_result:
                failed_released_key.append(key)
        if failed_released_key:
            logging.error('error when releasing keys, total {} keys, the keys are {}'.format(
                len(failed_released_key), failed_released_key))

    """def __del__(self):
        self._release_all_key()"""


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
    import yaml

    with open('api_keys.yaml', 'r') as f:
        doc = yaml.load(f, Loader=yaml.BaseLoader)

    for api in doc['YTB_API_POOL']:
        logging.debug(api)
        #db_doc = YoutubeDataApiCaller.generate_document(api, False, False, datetime.datetime.now())
    #failed_keys = add_keys_to_db(doc['YTB_API_POOL'], **api_key_pool_dict)#'localhost', 27017, 'KeyPool', 'YoutubeDataApi')
    #if failed_keys:
        #logging.debug(failed_keys)

    test = YoutubeDataApiCaller(**api_key_pool_dict)#'localhost', 27017, 'KeyPool', 'YoutubeDataApi')
    a = YoutubeDataApiCaller.generate_document('tewatwearew', False, False, datetime.datetime.now())
    logging.debug(a)

    respond = test.search_query('wef', check_existing=True)
    logging.debug(respond)

    respond = test.search_query('sef', check_existing=True)
    logging.debug(respond)

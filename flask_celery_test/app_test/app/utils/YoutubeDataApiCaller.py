from pymongo import MongoClient, DESCENDING
from pymongo.errors import DuplicateKeyError
import requests
import json
import datetime
import logging
from enum import Enum, unique


logging.basicConfig(level=logging.DEBUG)
api_key_pool_dict = {
    'db_url': 'localhost',
    'db_port': 27017,
    'db_name': 'KeyPool',
    'col_name': 'YoutubeDataApi',
}
db_info_dict = {
                'db_url': '172.17.0.4',
                'db_port': '27017',
                'db_name': 'ytb_temp_file',
                'col_name': 'id_timestamp_status'
            }
dynamic_db_url_template = {
    'read':'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/read'.format(db_info_dict['db_url'],
                                                                                            db_info_dict['db_port'],
                                                                                            '{}',
                                                                                            '{}'),
    'delete':'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/delete'.format(db_info_dict['db_url'],
                                                                                                db_info_dict['db_port'],
                                                                                       '{}',
                                                                                       '{}'),
    'update':'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/update'.format(db_info_dict['db_url'],
                                                                                        db_info_dict['db_port'],
                                                                                        '{}',
                                                                                        '{}'),
    'write':'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/write'.format(db_info_dict['db_url'],
                                                                             db_info_dict['db_port'],
                                                                                     '{}',
                                                                                     '{}'),
    'createindex':'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/createindex'.format(db_info_dict['db_url'],
                                                                             db_info_dict['db_port'],
                                                                                     '{}',
                                                                                     '{}')
}
def generate_db_access_obj(db_name, collection_name):
    new_db_access_obj = dynamic_db_url_template.copy()
    new_db_access_obj['read'] = new_db_access_obj['read'].format(db_name, collection_name)
    new_db_access_obj['delete'] = new_db_access_obj['delete'].format(db_name, collection_name)
    new_db_access_obj['update'] = new_db_access_obj['update'].format(db_name, collection_name)
    new_db_access_obj['write'] = new_db_access_obj['write'].format(db_name, collection_name)
    return new_db_access_obj

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

    def __init__(self, db_name='YtbDataApiSearched', col_name='YtbSearchRecord', number_of_keys=3):
        self.db_dict = generate_db_access_obj(db_name, col_name)
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
                    return YtbApiErrorEnum['k']
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
            elif 'channelId':
                item_id = item['id']['channelId']
            elif 'playlistId':
                item_id = item['id']['playlistId']
            record_doc = {'etag': etag, 'kind': kind, 'item_id': item_id, 'query_string': [query_string]}
            doc_list.append(record_doc)
        return doc_list

    def search_query(self, query_string, check_existing=False):

        if check_existing:
            existed_list = self.get_all_doc_contains_query_string(query_string)
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
            self.storeSearchResponse(doc_list)

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

    def storeSearchResponse(self, doc_list):
        """
        Expecting youtube data api response in json format as the example at the end of the file

        stored mongo db collection schema:
        {
            "query_string": ['xxx']
                All query strings used for querying the youtube data api, it is an array of
                        query_string historically used to get this result
            "etag": 'xxx'
                The item's etag that is used as the unique identifier used by youtube data api
            "kind": 'xxx'
                The item's kind field in the resopnse body
            "item_id": 'xxx'
                The video id or channel id of the item. It's the suffix of the youtube video
        }

        api example: https://youtube.googleapis.com/youtube/v3/search?q=xxxx&key=xxxx
        https://developers.google.com/youtube/v3/docs/search#resource
        :param API_reply_json:
        :param db_url:
        :param db_port:
        :param db_name:
        :return:
        """
        # TODO: Need to split the response handle with the document upload
        payload = {'index_pairs': [('etag', 'DESCENDING')],
        'index_kwargs': {"unique": True}}
        response = requests.post(url=self.db_dict['createindex'], data=json.dumps(payload),
                                 headers={'content-type': 'application/json'})
        logging.debug(response.content)

        for doc_record in doc_list:
            # TODO: need to rewrite the following part with the $addtoset updateone upsert, and add test to it
            # TODO: Add check that the insert succeeded and return the result
            # TODO: Add error handling and add testing
            query_string = doc_record['query_string']
            payload = {'read_filter': {'etag': doc_record['etag']}, 'read_projection': {'query_string': 1, '_id': 0}}
            response = requests.post(url=self.db_dict['read'], data=json.dumps(payload),
                                     headers={'content-type': 'application/json'})

            doc = json.loads(response.content.decode('UTF-8'))['response']
            if doc:
                current_queries = doc[0]['query_string']
                if query_string not in current_queries:
                    current_queries.append(query_string)
            else:
                current_queries = [query_string]
            final_record = {'etag': doc_record['etag'],
                            'kind': doc_record['kind'], 'item_id': doc_record['item_id'], 'query_string': current_queries}

            payload = {'update_filter': {"etag": doc_record['etag']}, 'update_aggregation': [{'$set': final_record}], 'update_options':{'upsert': True}}
            response = requests.put(url=self.db_dict['update'], data=json.dumps(payload),
                                    headers={'content-type': 'application/json'})
            logging.debug(response.content)
    def get_all_doc_contains_query_string(self, query_string):
        """
        Search in the search record collection and return all the documents that contains the query string

        :param query_string:
        :param db_url:
        :param db_port:
        :param db_name:
        :param col_name:
        :return:
        """


        doc_list = []
        payload = {'read_filter': {'query_string': [query_string]}}
        response = requests.post(url=self.db_dict['read'], data=json.dumps(payload),
                                 headers={'content-type': 'application/json'})

        docs = json.loads(response.content.decode('UTF-8'))['response']


        for document in docs:
            doc = {'etag': document['etag'], 'kind': document['kind'], 'item_id': document['item_id'],
                   'query_string': [query_string]}
            doc_list.append(doc)
        return doc_list


def add_keys_to_db(api_keys, db_name, col_name):
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
    failed_keys = add_keys_to_db(doc['YTB_API_POOL'], **api_key_pool_dict)#'localhost', 27017, 'KeyPool', 'YoutubeDataApi')
    if failed_keys:
        logging.debug(failed_keys)

    test = YoutubeDataApiCaller(**api_key_pool_dict)#'localhost', 27017, 'KeyPool', 'YoutubeDataApi')
    a = YoutubeDataApiCaller.generate_document('tewatwearew', False, False, datetime.datetime.now())
    logging.debug(a)

    respond = test.search_query('test4', check_existing=True)
    logging.debug(respond)

    respond = test.search_query('Whats Going On Astro Nito Onna', check_existing=True)
    logging.debug(respond)
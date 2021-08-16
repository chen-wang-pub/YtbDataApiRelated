from pymongo import MongoClient
import requests
import json

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
        'last_update_date': 'xxxx-xx-xx'/None
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
    def __init__(self, db_url, db_port, db_name, col_name, number_of_keys=5):
        self.db_client = MongoClient(db_url, db_port)
        self.db = self.db_client[db_name]
        self.col = self.db[col_name]
        self._max_key = number_of_keys
        pass
    @property
    def max_key(self):
        return self._max_key
    @max_key.setter
    def max_key(self, number_of_keys):
        self._max_key = number_of_keys
    @property
    def ytbApiUrlTemplate(self):
        return self._ytbApiUrlTemplate
    @ytbApiUrlTemplate.setter
    def ytbApiUrlTemplate(self, url):
        self._ytbApiUrlTemplate = url

    def search_query(self, query_string):
        pass
    def _pull_api_key(self, number_of_keys):
        pass
    def _retry_search(self, query_string):
        pass
    def _update_key_status(self, docs_for_update):
        pass
    def _generate_document(self, key, in_use, quota_exceeded, last_update_date):
        pass
    def __del__(self):
        pass

def add_keys_to_db(api_keys):
    pass
def update_db_keys_status():
    pass

if __name__ == '__main__':
    test = YoutubeDataApiCaller('localhost', 1024, 'KeyPool', 'YoutubeDataApi')

from flask import Flask, request, json, Response
from pymongo import MongoClient
import logging

logging.basicConfig(level=logging.DEBUG)

api_search_record_db_dict = {
    'db_url': 'localhost',
    'db_port': 1024,
    'db_name': 'YtbDataApiSearched',
    'col_name': 'YtbSearchRecord',
}


class YtbSearchRecordDBAPI_V0:
    """
    This class is created for the CRUD interactions on the database collection
    that stores the cached Ytb data api search records
    """

    def __init__(self, payload, db_url='localhost', db_port=1024,
                 db_name='YtbDataApiSearched', col_name='YtbSearchRecord'):
        client = MongoClient(db_url, db_port)
        db = client[db_name]
        self.collection = db[col_name]
        self.payload = payload
    # TODO: Need error handling when query failed
    def read(self):
        doc_filter, doc_projection = self._get_read_parameters()
        documents = self.collection.find(doc_filter, doc_projection)
        record_list = [{field: doc[field] for field in doc} for doc in documents]

        return record_list

    def _transfer_load(self, payload_key, output_dict):
        """
        This function is used to check if certain dict_data exists in the payload
        If exists, it will check the item in the payload dict data,
        and transfer all the valid key-value to the output dict
        :param payload_key:
        :param output_dict:
        :return:
        """
        if self.payload[payload_key]:
            temp_read_filter = self.payload[payload_key]
            for k, v in temp_read_filter.items():
                #TODO: field check can be added here
                output_dict[k] = v
        else:
            logging.debug('Payload key {} does not exist in payload data'.format(payload_key))
            return False

        return True

    def _get_read_parameters(self):
        """
        The parameters should be checked
        :return:
        """
        doc_filter = {}
        doc_projection = {'_id': 0}

        self._transfer_load('read_filter', doc_filter)
        self._transfer_load('read_projection', doc_projection)

        return doc_filter, doc_projection

    def write(self):
        pass

    def update(self):
        pass

    def delete(self):
        pass



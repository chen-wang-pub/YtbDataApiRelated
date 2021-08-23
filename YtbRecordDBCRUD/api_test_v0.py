from flask import Flask, request, json, Response
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import BulkWriteError
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
        self._payload = payload
    # TODO: Need error handling when query failed

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, new_payload):
        logging.debug('switching payload')
        self._payload = new_payload

    def read(self, read_limit=10000):
        doc_filter, doc_projection, doc_sort_list = self._get_read_parameters()

        if doc_sort_list:
            documents = self.collection.find(doc_filter, doc_projection).sort(doc_sort_list).limit(read_limit)
        else:
            documents = self.collection.find(doc_filter, doc_projection).limit(read_limit)
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

        :return:
        """
        doc_filter = {}
        doc_projection = {'_id': 0}
        doc_sort_list = []
        """
        sort list example:
        col.find().sort([
        ('field1', pymongo.ASCENDING),
        ('field2', pymongo.DESCENDING)])
        please refer to https://pymongo.readthedocs.io/en/stable/api/pymongo/cursor.html#pymongo.cursor.Cursor.limit
        for more example
        """

        self._transfer_load('read_filter', doc_filter)
        self._transfer_load('read_projection', doc_projection)
        temp_dict = {}
        self._transfer_load('read_sort', temp_dict)
        for k, v in temp_dict:
            doc_sort_list.append((k, v))

        return doc_filter, doc_projection, doc_sort_list

    def write(self):

        docs_to_write = self.payload['write_docs']  # expecting it to be a list of documents
        try:
            response = self.collection.insert_many(docs_to_write)
        except BulkWriteError:
            #  code 11000 is for duplicate key error
            errors_to_worry = filter(lambda x: x['code'] != 11000, BulkWriteError.details['writeErrors'])
            if len(errors_to_worry) > 0:
                logging.error('Errors need to be handled when writing to the database')
                return False
        logging.debug('Total {} new document inserted into db'.format(len(response['insertedIds'])))
        return True

    def _check_update_aggregation(self, update_aggregation):
        pass

    def update(self):
        update_filter = {}
        update_aggregation = self.payload['update_aggregation']
        self._check_update_aggregation(update_aggregation)
        update_options = {}

        self._transfer_load('update_filter', update_filter)
        self._transfer_load('update_options', update_options)

        response = self.collection.update_many(update_filter, update_aggregation, **update_options)
        logging.debug('Response from update operation. acknowledged: {}, matchedCount: {}, modifiedCount: {}'.format(
            response.acknowledged, response.matched_count, response.modified_count))
        if response.modified_count > 0:
            return True
        else:
            return False

    def delete(self):
        delete_filter = {}
        delete_option = {}
        self._transfer_load('delete_filter', delete_filter)
        self._transfer_load('delete_option', delete_option)

        response = self.collection.delete_many(delete_filter, **delete_option)
        logging.debug('Response from delete operation. acknowledged: {}, deletedCount: {}'.format(
            response.acknowledged, response.deleted_count))

        if response.deleted_count > 0:
            return True
        else:
            return False

if __name__ == '__main__':
    payload = {

    }

    db_obj = YtbSearchRecordDBAPI_V0(payload)

import pymongo.errors
from pymongo import MongoClient, ASCENDING, DESCENDING, GEO2D, GEOHAYSTACK, GEOSPHERE, HASHED, TEXT
from pymongo.errors import BulkWriteError, OperationFailure
import logging

logging.basicConfig(level=logging.DEBUG)

api_search_record_db_dict = {
    'db_url': 'thismongo',
    'db_port': 27017,
    'db_name': 'YtbDataApiSearched',
    'col_name': 'YtbSearchRecord',
}
"""api_search_record_db_dict = {
    'db_url': 'thismongo',
    'db_port': 27017,
    'db_name': 'YtbDataApiSearched',
    'col_name': 'YtbSearchRecord',
}"""

class YtbSearchRecordDBAPI_V0:
    """
    This class is created for the CRUD interactions on the database collection
    that stores the cached Ytb data api search records
    """

    def __init__(self, payload, db_url=api_search_record_db_dict['db_url'],
                 db_port=api_search_record_db_dict['db_port'],
                 db_name='YtbDataApiSearched', col_name='YtbSearchRecord'):
        client = MongoClient("mongodb://{}:{}".format(db_url, db_port))
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

        return {'response': record_list}

    def _transfer_load(self, payload_key, output_dict):
        """
        This function is used to check if certain dict_data exists in the payload
        If exists, it will check the item in the payload dict data,
        and transfer all the valid key-value to the output dict
        :param payload_key:
        :param output_dict:
        :return:
        """
        if payload_key in self.payload:
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
        except BulkWriteError as bwe:
            #  code 11000 is for duplicate key error
            error_list = bwe.details['writeErrors']
            errors_to_worry = filter(lambda x: x['code'] != 11000, error_list)
            if len(list(errors_to_worry)) > 0:
                logging.error('Errors need to be handled when writing to the database')
                return False
            logging.debug('Duplicated key error. Total {} new document inserted into db'.format(bwe.details['nInserted']))
            return True
        logging.debug('Total {} new document inserted into db'.format(len(response.inserted_ids)))
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


    def createIndex(self):
        index_pairs, index_kwargs = self._process_index_arguments(self.payload['index_pairs'], self.payload['index_kwargs'])
        try:
            response = self.collection.create_index(index_pairs, **index_kwargs)
        except OperationFailure as of:
            logging.error("error when creating index with pairs {} and kwargs {}".format(index_pairs, index_kwargs))
            logging.error("error details: {}".format(of.details))
            return False
        logging.debug('Response from create index operation. names: {}'.format(response))
        return True


    def _process_index_arguments(self, index_pairs, index_kwargs):
        index_related_dict = {
            'ASCENDING': ASCENDING,
            'DESCENDING': DESCENDING,
            'GEO2D': GEO2D,
            'GEOHAYSTACK': GEOHAYSTACK,
            'GEOSPHERE': GEOSPHERE,
            'HASHED': HASHED,
            'TEXT': TEXT,
            'True': True,
            'False': False
        }
        processed_pairs = []
        processed_kwargs = {}
        for pair in index_pairs:
            new_pair = (pair[0], index_related_dict[pair[1]])
            processed_pairs.append(new_pair)
        for key in index_kwargs:
            if index_kwargs[key] in index_related_dict:
                processed_kwargs[key] = index_related_dict[key]
            else:
                processed_kwargs[key] = index_kwargs[key]
        return processed_pairs, processed_kwargs



if __name__ == '__main__':
    payload = {
        'write_docs': [{'query_string': ['test0','test1','test4'], 'etag': 'e12340', 'kind':'video', 'item_id':'1121210'},
                       {'query_string': ['test2'], 'etag': 'e12341', 'kind':'channel', 'item_id':'1121211'},
                       {'query_string': ['test3'], 'etag': 'e12342', 'kind':'playlist', 'item_id':'1121212'},
                       {'query_string': ['test4'], 'etag': 'e12343', 'kind':'video', 'item_id':'1121213'}],
        'read_filter': {'query_string': 'test4'},
        'read_projection': {'item_id': 1},
        'update_filter': {'kind': {'$in': ['channel', 'playlist']}},
        'update_aggregation': [{'$set': {'kind': 'not video'}}],
        'delete_filter': {'etag': 'e12342'},
        'index_pairs': [('etag', 'ASCENDING')],
        'index_kwargs': {"unique": True}
    }
    logging.info('testing create index')
    db_obj = YtbSearchRecordDBAPI_V0(payload)
    db_obj.createIndex()
    input('pause teset')
    logging.info('testing basic write')
    clean_up = YtbSearchRecordDBAPI_V0({'delete_filter':{}})
    clean_up.delete()

    db_obj = YtbSearchRecordDBAPI_V0(payload)
    db_obj.collection.create_index([('etag', DESCENDING)], unique=True)
    db_obj.write()

    logging.info('testing write with duplicate entry')
    db_obj.write()

    logging.info('testing read')
    logging.debug(db_obj.read())

    logging.info('testing update')
    db_obj.update()
    db_obj.payload['read_filter'] = {}
    db_obj.payload['read_projection'] = {}
    logging.debug(db_obj.read())


    logging.info('testing delete')
    db_obj.delete()
    db_obj.payload['read_filter'] = {}
    db_obj.payload['read_projection'] = {}
    logging.debug(db_obj.read())
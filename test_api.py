import logging
import requests
import json

from pymongo import DESCENDING

from YtbRecordDBCRUD.api_test_v0 import YtbSearchRecordDBAPI_V0

logging.basicConfig(level=logging.DEBUG)


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
        'delete_filter': {'etag': 'e12342'}
    }

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


    base_url = 'http://localhost:5000/ytbrecordapi/v0/{}'

    logging.info('testing restapi read')
    data = {'read_filter': {}}

    response = requests.get(url=base_url.format('read'), data=json.dumps(data), headers={'content-type': 'application/json'})
    logging.debug(response.content)

    logging.info('testing restapi delete')
    data = {'delete_filter':{}}

    response = requests.delete(url=base_url.format('delete'), data=json.dumps(data), headers={'content-type': 'application/json'})
    logging.debug(response.content)
    logging.debug(db_obj.read())

    logging.info('testing restapi write')
    data = {'write_docs': [{'query_string': ['test0','test1','test4'], 'etag': 'e12340', 'kind':'video', 'item_id':'1121210'},
                       {'query_string': ['test2'], 'etag': 'e12341', 'kind':'channel', 'item_id':'1121211'},
                       {'query_string': ['test3'], 'etag': 'e12342', 'kind':'playlist', 'item_id':'1121212'},
                       {'query_string': ['test4'], 'etag': 'e12343', 'kind':'video', 'item_id':'1121213'}]}

    response = requests.post(url=base_url.format('write'), data=json.dumps(data), headers={'content-type': 'application/json'})
    logging.debug(response.content)
    logging.debug(db_obj.read())

    logging.info('testing restapi update')

    data = {'update_filter': {'kind': {'$in': ['channel', 'playlist']}},
            'update_aggregation': [{'$set': {'kind': 'not video'}}]}
    response = requests.put(url=base_url.format('update'), data=json.dumps(data), headers={'content-type': 'application/json'})
    logging.debug(response.content)
    logging.debug(db_obj.read())



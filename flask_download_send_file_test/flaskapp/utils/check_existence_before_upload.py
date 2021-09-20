import requests
import json
import logging
import time
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)

def upload_if_not_exist(doc_to_upload, read_payload, rest_read_url, rest_write_api):
    """
    This function is used for checking if the single document generated from scraping result already exist in the
    database, collection. If not, insert the document

    The read method and write method are connected via post method

    :param doc_to_upload: The document to be write to the collection, Should be in dictionary form
    :param read_payload: The dictionary object used for passing read_filter, read_projection... It is used when calling
    the rest api read function. read_filter should be mandatory, the read_projection can be optional
    example of a read_payload:
    {'read_filter': {'ip': '1.1.1.1', 'port': '1111', 'country': 'Canada'}, 'read_projection': {'country_code': 1}}
    :param rest_read_url: the url of the restapi read
    :param rest_write_api:
    :return: True when the function wrote the doc to the col,
    False when the doc already exist
    """
    #TODO: add error handling
    response = requests.post(url=rest_read_url, data=json.dumps(read_payload),
                             headers={'content-type': 'application/json'})
    doc_list = response.json()['response']
    #logger.debug(doc_list)
    if len(doc_list) < 1:
        # logger.debug('found doc')
        payload = {'write_docs': [doc_to_upload]}
        response = requests.post(url=rest_write_api, data=json.dumps(payload),
                                 headers={'content-type': 'application/json'})
        #logger.debug(response.content)
        return True
    return False


def refresh_status(read_payload, rest_read_url, rest_update_api):
    """
    This function is used to update the record in DB when the status is ready.
    The constant running cleaner thread will delete all record in ready & error status based on the ready_time. When the
    cleaner detects the record in a 'ready to be deleted' status, it will compare the difference between the current
    time and the ready_time. The record will be deleted when the difference exceeds certain threshold.
    This function was designed to be used by the request queuing function that when users request an item that is
    already in
    1) ready status, the ready_time will be extended to the current time.
    2) error status, the status will be changed to queued, and the queued_time will be updated tp the current time
    :param read_payload: read_payload should contain the item_id and one item_id only
    :param rest_read_url:
    :param rest_update_api:
    :return:
    """
    response = requests.post(url=rest_read_url, data=json.dumps(read_payload),
                             headers={'content-type': 'application/json'})
    doc_list = response.json()['response']
    doc = doc_list[0]
    if doc['status'] == 'ready':
        data = {'update_filter': {'item_id': doc['item_id']},
                'update_aggregation': [
                    {'$set': {'ready_time': time.time()}}]}
    elif doc['status'] == 'error':
        data = {'update_filter': {'item_id': doc['item_id']},
                'update_aggregation': [
                    {'$set': {'status': 'queued', 'queued_time': time.time()}}]}
    response = requests.put(url=rest_update_api, data=json.dumps(data),
                            headers={'content-type': 'application/json'})
    response_dict = json.loads(response.content)
    #logger.debug('update status is {}'.format(response_dict['update_status']))
    return response_dict['update_status']


if __name__ == '__main__':
    db_url = '172.17.0.4'
    db_port = 27017
    database_name = 'test_db'
    collectoin_name = 'test_col'

    write_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/write'.format(db_url, db_port, database_name,
                                                                                   collectoin_name)
    read_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/read'.format(db_url, db_port, database_name,
                                                                               collectoin_name)
    delete_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/delete'.format(db_url, db_port, database_name,
                                                                                   collectoin_name)

    test_doc = {'doc_id': 111, 'doc_name': 'for testing', 'doc_content': 'yup'}
    read_payload = {'read_filter': {'doc_id': 111}}
    delete_payload = {'delete_filter': {}}
    response = requests.post(url=delete_url, data=json.dumps(delete_payload),
                             headers={'content-type': 'application/json'})
    assert upload_if_not_exist(test_doc, read_payload, read_url, write_url)

    assert not upload_if_not_exist(test_doc, read_payload, read_url, write_url)

import logging
import requests
import json

from pymongo import DESCENDING

from YtbRecordDBCRUD.api_test_v0 import YtbSearchRecordDBAPI_V0

logging.basicConfig(level=logging.DEBUG)


if __name__ == '__main__':
    server_host = 'http://localhost:5005'
    get_url = '/ytbaudiodownload/v0/queuebyvideoid?id={}'
    post_url = '/ytbaudiodownload/v0/queuebyurl'

    video_id = 'YFWeLuq4nJU'
    ytb_url = 'https://www.youtube.com/watch?v=bB2-9BY92xU'

    get_url = '{}{}'.format(server_host, get_url.format(video_id))
    post_url = '{}{}'.format(server_host, post_url)
    post_data = {'url': ytb_url}

    logging.info('testing queue video get')
    response = requests.get(url=get_url, headers={'content-type': 'application/json'})
    logging.debug(response.content)

    logging.info('testing queue video post')

    response = requests.post(url=post_url, data=json.dumps(post_data), headers={'content-type': 'application/json'})
    logging.debug(response.content)


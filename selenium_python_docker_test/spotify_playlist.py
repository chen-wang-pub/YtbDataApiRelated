
import logging
import requests
from lxml import html
import json
import math
import re
from selenium_python_docker_test.utils.check_existence_before_upload import upload_if_not_exist
from selenium_python_docker_test.utils.proxy_extractor import ProxyExtractor

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)



def generate_spotify_doc(name, duration_ms, album_name, artists):
    return {'name': name, 'duration_ms': duration_ms, 'album_name': album_name, 'artists': artists}


def get_song_info(source_url, header, is_first_page=False, proxy_dict={}):
    """
    A recursive function that scrape the link till no next page. The final return is a list of dictionary obj of the
    song info document
    :param proxy_dict:
    :param source_url:
    :param header:
    :param is_first_page:
    :return:
    """
    record_list = []
    if proxy_dict:
        response = requests.get(source_url, headers=header, proxies=proxy_dict, timeout=10)
    else:
        response = requests.get(source_url, headers=header, timeout=10)
    if not response.text:
        logger.error('Failed when trying to get api info from url {}'.format(source_url))
        return []
    parsed_data = json.loads(response.text)
    if is_first_page:
        tracks = parsed_data['tracks']
    else:
        tracks = parsed_data
    items = tracks['items']
    logger.debug('total {} items in this trac json string'.format(len(items)))
    for item in items:
        song = item['track']
        # print(song)
        song_name = song['name']
        song_duration_ms = song['duration_ms']
        song_album_name = song['album']['name']
        song_artists = []
        for artist in song['artists']:
            song_artists.append(artist['name'])
        spotify_record = generate_spotify_doc(name=song_name, duration_ms=song_duration_ms, album_name=song_album_name,
                                              artists=song_artists)
        record_list.append(spotify_record)

    logger.debug('this api url is {}'.format(tracks['href']))
    if 'next' in tracks:
        if tracks['next']:
            logger.debug('next api url is {}'.format(tracks['next']))

            record_list.extend(get_song_info(tracks['next'], header, proxy_dict=proxy_dict))
    return record_list

#TODO: Use proxy when sending requests, refactor the code so that it has a proper status indicator

def extract_spotify_playlist(play_list_id='0dRizWkhzplGjqvULihR72', country_code='CA'):

    proxy_extractor = ProxyExtractor(country_code)
    proxy_extractor.get_all_proxies()
    proxy_dict_list = proxy_extractor.parse_proxies_for_requests()
    current_proxy_dict_index = 0
    all_proxy_failed = True

    spotify_url = 'https://open.spotify.com/playlist/{}'.format(play_list_id)
    api_prefix = 'https://api.spotify.com/v1/playlists'
    db_url = '172.17.0.3'
    db_port = 27017
    database_name = 'spotify_playlist'
    collection_name = ''#play_list_id

    #command_executor = 'http://localhost:4445/wd/hub'
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"}

    for i in range(0, len(proxy_dict_list)):
        current_proxy_dict_index = i
        try:
            response = requests.get(spotify_url, headers=headers, proxies=proxy_dict_list[i], timeout=10)
            if response.status_code == 200:
                all_proxy_failed = False
                break
        except:
            logger.debug('proxy: {} failed'.format(proxy_dict_list[i]))
        """
        Had ValueError: check_hostname requires server_hostname
        work around
        https://stackoverflow.com/questions/66642705/why-requests-raise-this-exception-check-hostname-requires-server-hostname
        """

    if all_proxy_failed:
        logger.error('all proxy failed. proxy dict list is: {}'.format(proxy_dict_list))
        return False
    html_content = html.fromstring(response.content)
    playlist_name = html_content.findtext('.//title')
    playlist_name = re.sub('[^0-9a-zA-Z]+', '_', playlist_name)
    if not collection_name:
        collection_name = playlist_name
        logger.debug('collection name will be: {}'.format(playlist_name))

    access_token_obj_str = html_content.xpath('//*[@id="config"]/text()')[0]
    access_token_obj = json.loads(access_token_obj_str)
    access_token = access_token_obj['accessToken']
    headers['Authorization'] = 'Bearer {}'.format(access_token)

    logger.debug(access_token)

    total_songs = html_content.xpath("//meta[@property='music:song_count']/@content")[0]
    logger.debug('total {} songs in the list'.format(total_songs))
    total_request = math.ceil(int(total_songs) / 100)
    logger.debug(total_request)
    list_suffix = html_content.xpath("//meta[@property='og:url']/@content")[0].split('/')[-1]
    logger.debug('song list url suffix: {}'.format(list_suffix))
    api_url = '{}/{}'.format(api_prefix, list_suffix)
    logger.debug('api url for the playlist is {}'.format(api_url))

    for i in range(current_proxy_dict_index, len(proxy_dict_list)):
        try:
            spotify_song_docs = get_song_info(api_url, headers, is_first_page=True,
                                              proxy_dict=proxy_dict_list[current_proxy_dict_index])
            break
        except:
            logger.debug('sth went wrong with proxy: {}'.format(proxy_dict_list[i]))
    logger.debug(len(spotify_song_docs))
    logger.debug(spotify_song_docs)

    write_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/write'.format(db_url,db_port,database_name,collection_name)
    read_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/read'.format(db_url,db_port,database_name,collection_name)
    delete_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/delete'.format(db_url,db_port,database_name,collection_name)
    logger.debug('write url is: {}'.format(write_url))
    logger.debug('read url is: {}'.format(read_url))
    logger.debug('delete url is: {}'.format(delete_url))

    number_added_doc = 0
    for doc in spotify_song_docs:
        read_payload = {'read_filter': {'name': doc['name'], 'duration_ms': doc['duration_ms'],
                                         'album_name': doc['album_name'], 'artists': doc['artists']}}
        if upload_if_not_exist(doc, read_payload, read_url,write_url):
            number_added_doc += 1
    return number_added_doc

if __name__ == '__main__':
    logger.info(extract_spotify_playlist())
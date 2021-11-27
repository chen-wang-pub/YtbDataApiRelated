import requests
import logging
import json
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)


def generate_spotify_doc(name, duration_ms, album_name, artists):
    return {'name': name, 'duration_ms': duration_ms, 'album_name': album_name, 'artists': artists}


def generate_ytb_item_doc(video_url, video_title, video_duration, video_view):
    video_id = video_url.replace('https://www.youtube.com/watch?v=', '')
    #  naming it as item_id is to keep consistency with the data got from youtube data api
    return {'item_id': video_id, 'title': video_title, 'duration': video_duration, 'view': video_view}


def get_song_info(source_url, header, is_first_page=False, proxy_dict={}):
    """
    {'name': 'Foolish', 'duration_ms': 177626, 'album_name': 'Shang-Chi and The Legend of The Ten Rings: The Album', 'artists': ["Rich Brian", "Warren Hue", "Guapdad 4000"]}
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
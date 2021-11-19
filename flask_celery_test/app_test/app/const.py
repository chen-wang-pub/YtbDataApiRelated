from os.path import join, dirname
db_info_dict = {
                'db_url': '172.17.0.4',
                'db_port': '27017',
                'db_name': 'ytb_temp_file',
                'col_name': 'id_timestamp_status'
            }
read_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/read'.format(db_info_dict['db_url'],
                                                                                            db_info_dict['db_port'],
                                                                                            db_info_dict['db_name'],
                                                                                            db_info_dict['col_name'])
update_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/update'.format(db_info_dict['db_url'],
                                                                                                db_info_dict['db_port'],
                                                                                                db_info_dict['db_name'],
                                                                                                db_info_dict[
                                                                                                    'col_name'])
delete_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/delete'.format(db_info_dict['db_url'],
                                                                                                db_info_dict['db_port'],
                                                                                                db_info_dict['db_name'],
                                                                                                db_info_dict[
                                                                                                    'col_name'])
write_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/write'.format(db_info_dict['db_url'],
                                                                             db_info_dict['db_port'],
                                                                             db_info_dict['db_name'],
                                                                             db_info_dict['col_name'])

createindex_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/createindex'.format(db_info_dict['db_url'],
                                                                             db_info_dict['db_port'],
                                                                             db_info_dict['db_name'],
                                                                             db_info_dict['col_name'])
MAX_TIMEOUT = 2400

TEMP_DIR_LOC = join(dirname(__file__), 'temp_storage')


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

spotify_db = 'spotify_playlist'

ytb_playlist_db = 'ytb_playlist_from_selenium'

command_executor = 'http://localhost:4444/wd/hub'

db_info_dict = {
                'db_url': '172.17.0.3',
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
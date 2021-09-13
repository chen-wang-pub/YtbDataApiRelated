import os
import time
from flask import Blueprint, Response, request, json, redirect, current_app

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
write_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/write'.format(db_info_dict['db_url'],
                                                                             db_info_dict['db_port'],
                                                                             db_info_dict['db_name'],
                                                                             db_info_dict['col_name'])
temp_dir_loc = os.path.join(os.path.dirname(__file__), 'temp_storage')
access_request = Blueprint('access_request', __name__)


"""
Workflow:
1. check in db if the record exist, if not, return record not exist, return the item queuing url to user
2. if exist, check if the status is file ready for transfer, if so, check if the file exist in local storage, if so, start the file transfer process
3. after step 2 check the time stamp to see if it's expired. If so, clean the local storage, set the status of the record to 'expired'

There should be a thread that constantly scans the db for record in queuing status, 
and create temp folder in the temp_storage, then start download process, set timeout in download process, 
and update the record from queuing to downloaidng, when download finished, set it as ready status
"""


@access_request.route('/ytbaudiodownload/v0/retrieveguide')
def retrieve_guide_page():
    html_str = """<head>To retrieve the queued audio downloading task, please use one of the following 2 methods:</head>
<div class="method">
   <p>Use GET or POST method on url /ytbaudiodownload/v0/retrievebyvideoid</p>
   <p>When using GET method, Use with argument ?id=ytbvideoid. The youtbue video's id is the part after the '=' sign</p>
   <p>When using POST method, Use with data {'item_id': 'ytb_video_id'}. The youtbue video's id is the part after the '=' sign</p>
</div>
"""
    return html_str


@access_request.route('/ytbaudiodownload/v0/retrievebyid', methods=['GET', 'POST'])
def retrieve_video_id():
    if request.method == 'GET':
        video_id = request.args.get('id', default='', type=str)
    elif request.method == 'GET':
        data = request.json
        if 'item_id' not in data:
            video_id = ''
        elif 'item_id' in data:
            video_id = data['item_id']
    if not video_id:
        return redirect('/ytbaudiodownload/v0/retrieveguide')


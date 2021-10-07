import os
import time
from flask import Blueprint, Response, request, json, redirect, current_app
import traceback
from utils.check_existence_before_upload import upload_if_not_exist, refresh_status

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
write_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/write'.format(db_info_dict['db_url'],
                                                                             db_info_dict['db_port'],
                                                                             db_info_dict['db_name'],
                                                                             db_info_dict['col_name'])
update_url = 'http://localhost:5001/ytbrecordapi/v0/{}/{}/{}/{}/update'.format(db_info_dict['db_url'],
                                                                             db_info_dict['db_port'],
                                                                             db_info_dict['db_name'],
                                                                             db_info_dict['col_name'])
temp_dir_loc = os.path.join(os.path.dirname(__file__), 'temp_storage')
queue_request = Blueprint('queue_request', __name__)

"""
The workflow of the download & sending ytb audio should be as following

client send api request via prefix/download/ytb_video_url
Then server verifies ytb_video_url and create a temp url for it prefix/download/temp_url_based_on_ytb_video_id, and send the url back to the client, and queue the corresponding tasks needed for downloading the video
The client then can use the temp url received from the server to check status of the downloading and retrieve the downloaded file
When the download of the file is not finished, the temp url will send back the 'downloading' status, otherwise, the temp url will send back the file
The tempurl will self destroy after certain time (5min?) from once the task is queued

There can be 2 servers, one is used for handling request, the other one is used for downloading and sending file

There can be multiple downloading & sending file server deployed.
The request handling server can queue the task to certain downloading & sending file server based on load, locations, etc.
"""
def verify_video_id(video_id):
    if video_id:
        return True
    return False

def retrieve_video_id(url):
    video_id = url.replace('https://www.youtube.com/watch?v=', '')
    return video_id

def generate_doc(item_id):
    return {'item_id': item_id, 'title': '', 'status': 'queued', 'queued_time': time.time(), 'ready_time': 0,
            'queued_timezone': 'PDT'}

@queue_request.route('/ytbaudiodownload/v0/howto')
def user_guide_page():
    html_str = """<head>To queue a download task for the audio part of a youtube video, please use one of the following 2 methods:</head>
<div class="method">
   <p>Use GET method on url /ytbaudiodownload/v0/queuebyvideoid with argument ?id=ytbvideoid</p>
   <p>The youtbue video's id is the part after the '=' sign</p>
</div>
<div class="method">
   <p>Use POST method on url /ytbaudiodownload/v0/queuebyurl with data in the format of {'url': 'ytb_video_url'}</p>
   <p>Just use the whole youtube video url</p>
</div>"""
    return html_str


@queue_request.route('/')
def default_page():
    #current_app.logger.debug('logging test from default page')
    #current_app.logger.info('logging test from default page')
    return redirect('ytbaudiodownload/v0/howto')


@queue_request.route('/ytbaudiodownload/v0/queuebyvideoid', methods=['GET'])
def handling_get_download_request():
    video_id = request.args.get('id', default='', type=str)
    if not video_id:
        return redirect('ytbaudiodownload/v0/howto')

    if verify_video_id(video_id):
        """new_temp_dir = r'{}/{}'.format(temp_dir_loc, video_id)
        try:
            os.makedirs(new_temp_dir)
        except OSError as err:
            if err.errno == 17:
                return Response(response=json.dumps({"Succeeded": "Download for {} is already queued. "
                                                                  "Please use "
                                                                  "/ytbaudiodownload/v0/downloadbyvideoid/{} "
                                                                  "for checking status and "
                                                                  "retrieving the file".format(video_id, video_id)}),
                                status=200,
                                mimetype='application/json')
            else:
                current_app.logger.error('Error when making temp directory for {}'.format(video_id))
                return Response(response=json.dumps({"Error": "Error when queuing the task"}),
                                status=400,
                                mimetype='application/json')"""
        doc = generate_doc(video_id)
        read_payload = {'read_filter': {'item_id': video_id}}
        try:
            if not upload_if_not_exist(doc, read_payload, read_url, write_url):
                refresh_status(read_payload, read_url,update_url)
            return Response(response=json.dumps({"Succeeded": "Download for {} is queued. "
                                                              "Please use "
                                                              "/ytbaudiodownload/v0/downloadbyvideoid/{} "
                                                              "for checking status and "
                                                              "retrieving the file".format(video_id, video_id)}),
                            status=200,
                            mimetype='application/json')
        except:
            current_app.logger.error(traceback.format_exc())
            return Response(response=json.dumps({"Error": "Error when queuing request into database"}),
                            status=400,
                            mimetype='application/json')

    return Response(response=json.dumps({"Error": "Video ID error"}),
                    status=400,
                    mimetype='application/json')


@queue_request.route('/ytbaudiodownload/v0/queuebyurl', methods=['POST'])
def handling_post_download_request():
    data = request.json
    if 'url' not in data:
        return redirect('ytbaudiodownload/v0/howto')
    video_id = retrieve_video_id(data['url'])
    if verify_video_id(video_id):
        doc = generate_doc(video_id)
        read_payload = {'read_filter': {'item_id': video_id}}
        try:
            if not upload_if_not_exist(doc, read_payload, read_url, write_url):
                refresh_status(read_payload, read_url, update_url)
            return Response(response=json.dumps({"Succeeded": "Download for {} is queued. "
                                                              "Please use "
                                                              "/ytbaudiodownload/v0/downloadbyvideoid/{} "
                                                              "for checking status and "
                                                              "retrieving the file".format(video_id, video_id)}),
                            status=200,
                            mimetype='application/json')
        except:
            return Response(response=json.dumps({"Error": "Error when queuing request into database"}),
                            status=400,
                            mimetype='application/json')

    return Response(response=json.dumps({"Error": "Video ID error"}),
                    status=400,
                    mimetype='application/json')
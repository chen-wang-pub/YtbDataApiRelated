from flask import Blueprint, Response, request, json

import pytube

mongodbrestapi = Blueprint('download_file', __name__)

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
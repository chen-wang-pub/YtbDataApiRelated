from flask import Blueprint, request, current_app, Response, json
import os
from .tasks import download_video
bp = Blueprint("all", __name__)

@bp.route("/")
def queue_download():
    video_ids = request.args.get('id', default='', type=str)
    video_ids = video_ids.split(',')
    for video_id in video_ids:
        download_video.delay(video_id)
        #celery.send_task('app_test.app.celery_tasks.download_video')
        current_app.logger.debug('{} is queued for downloading'.format(video_id))
    return Response(response=json.dumps({"Succeeded": "Download for {} is queued. ".format(video_ids)}),
                    status=200,
                    mimetype='application/json')
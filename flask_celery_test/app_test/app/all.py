import time
from flask import Blueprint, request, current_app, Response, json
import os
import traceback
from app.tasks import download_video, check_queued_list
from app.utils.db_document_related import upload_if_not_exist, generate_doc, refresh_status
from app.const import update_url, read_url, write_url, delete_url
from app import celery
bp = Blueprint("all", __name__)

@bp.route("/")
def queue_download():
    video_ids = request.args.get('id', default='', type=str)
    video_ids = video_ids.split(',')
    for video_id in video_ids:
        download_video.delay(video_id, '')
        #celery.send_task('app_test.app.celery_tasks.download_video')
        current_app.logger.info('{} is queued for downloading'.format(video_id))
    return Response(response=json.dumps({"Succeeded": "Download for {} is queued. ".format(video_ids)}),
                    status=200,
                    mimetype='application/json')

@bp.route("/queue")
def queue_id():
    video_ids = request.args.get('id', default='', type=str)
    video_ids = video_ids.split(',')
    for video_id in video_ids:

        doc = generate_doc(video_id)
        read_payload = {'read_filter': {'item_id': video_id}}
        try:
            if not upload_if_not_exist(doc, read_payload, read_url, write_url):
                refresh_status(read_payload, read_url, update_url)
        except:
            current_app.logger.error(traceback.format_exc())
        current_app.logger.info('{} wrote to db'.format(video_id))

        #celery.send_task('app_test.app.celery_tasks.download_video')
        current_app.logger.info('{} is queued for downloading'.format(video_id))
    return Response(response=json.dumps({"Succeeded": "Download for {} is queued. ".format(video_ids)}),
                    status=200,
                    mimetype='application/json')

@bp.route("/queueall")
def queue_all():
    video_ids = request.args.get('id', default='', type=str)
    video_ids = video_ids.split(',')
    for video_id in video_ids:

        doc = generate_doc(video_id)
        read_payload = {'read_filter': {'item_id': video_id}}
        try:
            if not upload_if_not_exist(doc, read_payload, read_url, write_url):
                refresh_status(read_payload, read_url, update_url)
        except:
            current_app.logger.error(traceback.format_exc())
        current_app.logger.info('{} wrote to db'.format(video_id))

        #celery.send_task('app_test.app.celery_tasks.download_video')
        current_app.logger.info('{} is queued for downloading'.format(video_id))
    celery_task = check_queued_list.delay(video_ids)
    return Response(response=json.dumps({"uuid": celery_task.task_id}),
                    status=200,
                    mimetype='application/json')


@bp.route("/retrievetask/<uuid>")
def retrieve_task(uuid):
    current_app.logger.info('uuid from route is {}'.format(uuid))
    task_result = celery.AsyncResult(uuid)
    if task_result:
        return Response(response=json.dumps({"task_result":task_result.info }),
                        status=200,
                        mimetype='application/json')
    else:
        return Response(response=json.dumps({"error": "invalid uuid"}),
                        status=200,
                        mimetype='application/json')

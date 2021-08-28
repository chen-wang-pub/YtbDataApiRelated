from flask import Blueprint, Response, request, json

from .mongodbapi import YtbSearchRecordDBAPI_V0

mongodbrestapi = Blueprint('mongodbrestapi', __name__)





@mongodbrestapi.route('/ytbrecordapi/v0/readall', methods=['GET'])
def ytb_record_db_api_readall():

    db_obj = YtbSearchRecordDBAPI_V0({})
    return_data = db_obj.read()

    return Response(response=json.dumps(return_data),
                    status=200,
                    mimetype='application/json')


@mongodbrestapi.route('/ytbrecordapi/v0/read', methods=['POST'])
def ytb_record_db_api_read():
    data = request.json
    if not data:
        return Response(response=json.dumps({"Error": "Please provide connection information"}),
                        status=400,
                        mimetype='application/json')
    db_obj = YtbSearchRecordDBAPI_V0(data)
    return_data = db_obj.read()

    return Response(response=json.dumps(return_data),
                    status=200,
                    mimetype='application/json')


@mongodbrestapi.route('/ytbrecordapi/v0/write', methods=['POST'])
def ytb_record_db_api_write():
    data = request.json
    if not data:
        return Response(response=json.dumps({"Error": "Please provide connection information"}),
                        status=400,
                        mimetype='application/json')
    db_obj = YtbSearchRecordDBAPI_V0(data)
    write_status = db_obj.write()
    return Response(response=json.dumps({'write_status': write_status}),
                    status=200,
                    mimetype='application/json')


@mongodbrestapi.route('/ytbrecordapi/v0/update', methods=['PUT'])
def ytb_record_db_api_update():
    data = request.json
    if not data:
        return Response(response=json.dumps({"Error": "Please provide connection information"}),
                        status=400,
                        mimetype='application/json')
    db_obj = YtbSearchRecordDBAPI_V0(data)
    update_status = db_obj.update()
    return Response(response=json.dumps({'update_status': update_status}),
                    status=200,
                    mimetype='application/json')


@mongodbrestapi.route('/ytbrecordapi/v0/delete', methods=['DELETE'])
def ytb_record_db_api_delete():
    data = request.json
    if not data:
        return Response(response=json.dumps({"Error": "Please provide connection information"}),
                        status=400,
                        mimetype='application/json')
    db_obj = YtbSearchRecordDBAPI_V0(data)
    delete_status = db_obj.delete()
    return Response(response=json.dumps({'delete_status': delete_status}),
                    status=200,
                    mimetype='application/json')

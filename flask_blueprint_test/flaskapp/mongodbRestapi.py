from flask import Blueprint, Response, request, json

from .mongodbapi import YtbSearchRecordDBAPI_V0

mongodbrestapi = Blueprint('mongodbrestapi', __name__)


# TODO: modify the route to /ytbrecordapi/v0/{db_url}/{db_col}/readall|read|write|update|delete
def verify_db_access(db_url, db_port, db_name, col_name, access_level=None):
    if not access_level:
        pass


@mongodbrestapi.route('/ytbrecordapi/v0/readall', methods=['GET'])
def ytb_record_db_api_readall_legacy():

    db_obj = YtbSearchRecordDBAPI_V0({})
    return_data = db_obj.read()

    return Response(response=json.dumps(return_data),
                    status=200,
                    mimetype='application/json')


@mongodbrestapi.route('/ytbrecordapi/v0/<string:db_url>/<int:db_port>/<string:db_name>/<string:col_name>/readall',
                      methods=['GET'])
def ytb_record_db_api_readall(db_url, db_port, db_name, col_name):
    verify_db_access(db_url, db_port, db_name, col_name)

    db_obj = YtbSearchRecordDBAPI_V0({}, db_url=db_url, db_port=db_port, db_name=db_name, col_name=col_name)
    return_data = db_obj.read()

    return Response(response=json.dumps(return_data),
                    status=200,
                    mimetype='application/json')


@mongodbrestapi.route('/ytbrecordapi/v0/read', methods=['POST'])
def ytb_record_db_api_read_legacy():
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


@mongodbrestapi.route('/ytbrecordapi/v0/<string:db_url>/<int:db_port>/<string:db_name>/<string:col_name>/read',
                      methods=['POST'])
def ytb_record_db_api_read(db_url, db_port, db_name, col_name):
    data = request.json
    if not data:
        return Response(response=json.dumps({"Error": "Please provide connection information"}),
                        status=400,
                        mimetype='application/json')
    verify_db_access(db_url, db_port, db_name, col_name)

    db_obj = YtbSearchRecordDBAPI_V0(data, db_url=db_url, db_port=db_port, db_name=db_name, col_name=col_name)
    return_data = db_obj.read()

    return Response(response=json.dumps(return_data),
                    status=200,
                    mimetype='application/json')


@mongodbrestapi.route('/ytbrecordapi/v0/write', methods=['POST'])
def ytb_record_db_api_write_legacy():
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


@mongodbrestapi.route('/ytbrecordapi/v0/<string:db_url>/<int:db_port>/<string:db_name>/<string:col_name>/write',
                      methods=['POST'])
def ytb_record_db_api_write(db_url, db_port, db_name, col_name):
    data = request.json
    if not data:
        return Response(response=json.dumps({"Error": "Please provide connection information"}),
                        status=400,
                        mimetype='application/json')
    verify_db_access(db_url, db_port, db_name, col_name)

    db_obj = YtbSearchRecordDBAPI_V0(data, db_url=db_url, db_port=db_port, db_name=db_name, col_name=col_name)
    write_status = db_obj.write()
    return Response(response=json.dumps({'write_status': write_status}),
                    status=200,
                    mimetype='application/json')


@mongodbrestapi.route('/ytbrecordapi/v0/update', methods=['PUT'])
def ytb_record_db_api_update_legacy():
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


@mongodbrestapi.route('/ytbrecordapi/v0/<string:db_url>/<int:db_port>/<string:db_name>/<string:col_name>/update',
                      methods=['PUT'])
def ytb_record_db_api_update(db_url, db_port, db_name, col_name):
    data = request.json
    if not data:
        return Response(response=json.dumps({"Error": "Please provide connection information"}),
                        status=400,
                        mimetype='application/json')
    verify_db_access(db_url, db_port, db_name, col_name)

    db_obj = YtbSearchRecordDBAPI_V0(data, db_url=db_url, db_port=db_port, db_name=db_name, col_name=col_name)
    update_status = db_obj.update()
    return Response(response=json.dumps({'update_status': update_status}),
                    status=200,
                    mimetype='application/json')


@mongodbrestapi.route('/ytbrecordapi/v0/delete', methods=['DELETE'])
def ytb_record_db_api_delete_legacy():
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


@mongodbrestapi.route('/ytbrecordapi/v0/<string:db_url>/<int:db_port>/<string:db_name>/<string:col_name>/delete',
                      methods=['DELETE'])
def ytb_record_db_api_delete(db_url, db_port, db_name, col_name):
    data = request.json
    if not data:
        return Response(response=json.dumps({"Error": "Please provide connection information"}),
                        status=400,
                        mimetype='application/json')
    verify_db_access(db_url, db_port, db_name, col_name)

    db_obj = YtbSearchRecordDBAPI_V0(data, db_url=db_url, db_port=db_port, db_name=db_name, col_name=col_name)
    delete_status = db_obj.delete()
    return Response(response=json.dumps({'delete_status': delete_status}),
                    status=200,
                    mimetype='application/json')
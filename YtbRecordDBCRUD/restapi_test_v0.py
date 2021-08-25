from flask import json, Response, request
from flask import Flask

from YtbRecordDBCRUD import api_test_v0

app = Flask(__name__)

# TODO: Modify the db api to include detailed error msg in response instead of just a single T/F status
# TODO: Need log on server side for dealing with request
# TODO: Error handling

@app.route('/')
def homepage():
    return Response(response=json.dumps({"Status": "homepage WIP"}),
                    status=200,
                    mimetype='application/json')


@app.route('/ytbrecordapi/v0/read', methods=['GET'])
def ytb_record_db_api_read():
    data = request.json
    if not data:
        return Response(response=json.dumps({"Error": "Please provide connection information"}),
                        status=400,
                        mimetype='application/json')
    db_obj = api_test_v0.YtbSearchRecordDBAPI_V0(data)
    return_data = db_obj.read()

    return Response(response=json.dumps(return_data),
                    status=200,
                    mimetype='application/json')


@app.route('/ytbrecordapi/v0/write', methods=['POST'])
def ytb_record_db_api_write():
    data = request.json
    if not data:
        return Response(response=json.dumps({"Error": "Please provide connection information"}),
                        status=400,
                        mimetype='application/json')
    db_obj = api_test_v0.YtbSearchRecordDBAPI_V0(data)
    write_status = db_obj.write()
    return Response(response=json.dumps({'write_status': write_status}),
                    status=200,
                    mimetype='application/json')


@app.route('/ytbrecordapi/v0/update', methods=['PUT'])
def ytb_record_db_api_update():
    data = request.json
    if not data:
        return Response(response=json.dumps({"Error": "Please provide connection information"}),
                        status=400,
                        mimetype='application/json')
    db_obj = api_test_v0.YtbSearchRecordDBAPI_V0(data)
    update_status = db_obj.update()
    return Response(response=json.dumps({'update_status': update_status}),
                    status=200,
                    mimetype='application/json')


@app.route('/ytbrecordapi/v0/delete', methods=['DELETE'])
def ytb_record_db_api_delete():
    data = request.json
    if not data:
        return Response(response=json.dumps({"Error": "Please provide connection information"}),
                        status=400,
                        mimetype='application/json')
    db_obj = api_test_v0.YtbSearchRecordDBAPI_V0(data)
    delete_status = db_obj.delete()
    return Response(response=json.dumps({'delete_status': delete_status}),
                    status=200,
                    mimetype='application/json')


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='localhost')
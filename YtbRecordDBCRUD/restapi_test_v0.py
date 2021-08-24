from flask import json, Response
from flask import Flask

app = Flask(__name__)
from YtbRecordDBCRUD import api_test_v0

@app.route('/')
def homepage():
    return Response(response=json.dumps({"Status": "homepage WIP"}),
                    status=200,
                    mimetype='application/json')
@app.route('/YtbRecordDBCRUD/v0/test', methods=['GET'])
def mongodb_read():
    return Response(response=json.dumps({"Status": "Read api WIP"}),
                    status=200,
                    mimetype='application/json')
@app.route('/YtbRecordDBCRUD/v0/test', methods=['POST'])
def mongodb_write():
    return Response(response=json.dumps({"Status": "Write api WIP"}),
                    status=200,
                    mimetype='application/json')
@app.route('/YtbRecordDBCRUD/v0/test', methods=['PUT'])
def mongodb_update():
    return Response(response=json.dumps({"Status": "Update api WIP"}),
                    status=200,
                    mimetype='application/json')
@app.route('/YtbRecordDBCRUD/v0/test', methods=['DELETE'])
def mongodb_delete():
    return Response(response=json.dumps({"Status": "Delete api WIP"}),
                    status=200,
                    mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='localhost')
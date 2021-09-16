from flask import Flask

from queue_request import queue_request
from the_thread import TheThread
import sys
def create_app(test_config=None):
    # create and configure the

    app = Flask('flaskapp', instance_relative_config=True)


    app.register_blueprint(queue_request)
    main_thread = TheThread()
    main_thread.start()
    #app.register_blueprint(send_file)

    return app
app = create_app()
if __name__ == '__main__':
    #logging.basicConfig(filename='error.log',level=logging.DEBUG)

    app = create_app()
    app.run(debug=True, port=5005, host='localhost')
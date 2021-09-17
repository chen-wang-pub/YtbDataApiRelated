from flask import Flask

from queue_request import queue_request
from the_thread import TheThread
from logging.config import dictConfig
def create_app(test_config=None):
    # create and configure the
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }},
        'loggers': {
            'root': {  # root logger
                'handlers': ['wsgi'],
                'level': 'DEBUG',
            },
            'the_thread': {
                'handlers': ['wsgi'],
                'level': 'DEBUG',
            },
            '__main__': {  # if __name__ == '__main__'
                'handlers': ['wsgi'],
                'level': 'DEBUG',
            },
        }
    })
    app = Flask('flaskapp', instance_relative_config=True)


    app.register_blueprint(queue_request)
    #app.register_blueprint(send_file)

    return app
if __name__ == '__main__':
    #logging.basicConfig(filename='error.log',level=logging.DEBUG)
    print('flask running!!!')
    app = create_app()
    TheThread().start()

    app.run(debug=True, use_reloader=False, port=5005, host='localhost')
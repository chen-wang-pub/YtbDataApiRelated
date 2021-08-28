from flask import Flask
from .mongodbRestapi import mongodbrestapi
def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.register_blueprint(mongodbrestapi)

    return app
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001, host='localhost')
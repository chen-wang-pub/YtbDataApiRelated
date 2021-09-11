import flaskapp
if __name__ == '__main__':
    app = flaskapp.create_app()
    app.run(debug=True, port=5005, host='localhost')
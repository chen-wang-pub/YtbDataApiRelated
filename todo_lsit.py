objective_queue = [
    'Learn how to use selenium webdrive with python in docker',
    'Collect proxy info from https://sslproxies.org/ via selenium in docker',
    'Run a web scraping script using python requests in docker',
    'Deploy a flask server that takes in web-scraping scripts, stores in db, executes them based on requests', # it's better to use a message queue for this objective https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xxii-background-jobs
    'Optional: try deploy a scrapy project in docker',
    'Deploy a flask server that makes use of pytube, download audio & video upon request and transfer it to the client',
    'Try deploy a format convertor that converts webm format to mp3 in docker',
    'Deploy a server that takes a webm file, convert it to mp3 then send it back',
    'Learn python message queue',
    'Refactor part of or the whole project using message queue',
]

new_objective_queue = [
    #'try use ffmpeg in docker for file conversion', #scratched this one cuz it seems the ffmpeg in docker only handles files with public address, but I want it to convert file locally stored in the server
    'better server debug log',
    'a deployment plan for the server (in a linux vm maybe)',
    'better flask viewpoint',
    'sync the post and get method for the server',
    'can split the queuing and file sending routes',
]

another_server = [
    'a server that stores session data from users about what item they requested',
    'it stores if the user wants to convert a spotify list, or ytb playlist, or just some ytb items'
]
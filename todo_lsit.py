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

new_thought = """
1) The downloading thread can/should be replaced by multiprocessing or flask celery

2) The server that deals with client's request for downloading spotify list, ytber's list, ytb item, 
involves transmitting multiple files from server to the client.
After some search online, the workflow of the whole process should be described as below

1. client send request for downloading multiple files  --> 
2. server receives request, queues all the item for downloading --> 
3 - 1. server starts a celery task that monitors the downloading status for all the item requested by the client 
when all item are in finished status, either ready or error, the celery task will send the data back to the client,
consists of downloading links to all the items that are ready to download, and items that are in error status.  -->

The good part is that this seems easy to implement. 
The issue with this approach is that the client might experience a long wait time for the server finishing downloading all requested files

3 - 2. Server uses websocket to update any requested files that are ready for download to the client. THe socket will close when all requested item is in finished status.

What's good is that the overall wait time for the client should be the shortest comparing with all other method.
The bad part is that it will increase the complexity of the server. 

3 - 3. the server can just generate all the download link and send it back to the client right away, then let the client constantly polling the result from the DB for download attempts,

The issue with this approach is that it will cause performance issue when there is a large number of users.

4. the client then can download the ready item one by one (Not zipping items cuz the same item might be requested by multiple users)

3) Session or cookie should be used, in case users accidentally closed the browser and send the request again. 

3-1 and 3-2 should be implemented, with 3-2 being the paid feature :)

The next task is to find working example for flask celery, flask websocket, flask session. After learning from the example, try building the server with those tools
"""
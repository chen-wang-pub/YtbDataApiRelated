FROM python:3.8-slim-buster



COPY ["requirements.txt", "./"]
COPY ["setup.py", "./"]

RUN pip3 install -r requirements.txt

COPY ./flaskapp /flaskapp



ENV FLASK_APP=flaskapp
ENV FLASK_RUN_PORT=5001

CMD [ "flask", "run", "--host=0.0.0.0"]

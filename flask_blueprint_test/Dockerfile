FROM python:3.8-slim-buster



COPY ["requirements.txt", "./"]

RUN pip3 install -r requirements.txt

COPY ./flaskapp /flaskapp


CMD [ "python", "-m", "flaskapp" ]

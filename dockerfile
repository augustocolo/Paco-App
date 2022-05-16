# syntax=docker/dockerfile:1

FROM python:3.7.13

WORKDIR /app

ENV FLASK_APP=run.py

ENV EMAIL_PASS=P@co2022
ENV EMAIL_USER=pacodelivery@libero.it
ENV GOOGLE_MAPS_API_KEY=AIzaSyDhYxH0M83iVLoATS7Zt9HJku7s7Ylubz0
ENV TARGA_USERNAME=demos

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

RUN rm paco/paco.db

RUN python3 createdb.py

CMD python -m flask run -h 0.0.0.0 -p 80


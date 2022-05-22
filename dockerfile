# syntax=docker/dockerfile:1

FROM nikolaik/python-nodejs

WORKDIR /app

ENV FLASK_APP=run.py
ENV EMAIL_PASS=P@co2022
ENV EMAIL_USER=pacodelivery@libero.it
ENV GOOGLE_MAPS_API_KEY=AIzaSyDhYxH0M83iVLoATS7Zt9HJku7s7Ylubz0
ENV TARGA_USERNAME=dawwas

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

RUN python3 createdb.py

WORKDIR paco/static/assets

RUN npm install

WORKDIR /app

CMD python -m flask run -h 0.0.0.0 -p 80


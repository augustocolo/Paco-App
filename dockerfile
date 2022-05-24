# syntax=docker/dockerfile:1

FROM nikolaik/python-nodejs

WORKDIR /app

ENV FLASK_APP=run.py
ENV EMAIL_PASS=P@co2022
ENV EMAIL_PORT=465
ENV EMAIL_SERVER=smtp.libero.it
ENV EMAIL_SSL=1
ENV EMAIL_TLS=0
ENV EMAIL_USER=pacodelivery@libero.it
ENV FLASK_SALT_KEY=fR2F3gu7z77ku0OY
ENV FLASK_SECRET_KEY=KhLnxo9UZxwGqnGI
ENV GOOGLE_MAPS_API_KEY=AIzaSyDhYxH0M83iVLoATS7Zt9HJku7s7Ylubz0
ENV SQLALCHEMY_DATABASE_URI=sqlite:///paco.db
ENV TARGA_USERNAME=sjdnmx



COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .

RUN python3 createdb.py

WORKDIR paco/static/assets

RUN npm install

WORKDIR /app

CMD python -m flask run -h 0.0.0.0 -p 80


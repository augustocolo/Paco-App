# syntax=docker/dockerfile:1

FROM nikolaik/python-nodejs

WORKDIR /app

ENV FLASK_APP=run.py

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .

RUN python3 createdb.py

WORKDIR paco/static/assets

RUN npm install

WORKDIR /app

CMD python -m flask run -h 0.0.0.0 -p 80


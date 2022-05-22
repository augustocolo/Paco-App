import requests
import os
from lxml.etree import fromstring
import json

_endpoint = 'https://www.regcheck.org.uk/api/reg.asmx/CheckItaly'


def get_car_info(license_plate):
    req = requests.get(_endpoint, params={
        'RegistrationNumber': license_plate,
        'username': os.environ.get('TARGA_USERNAME')
    })
    if req.status_code == 200:
        string = req.text
        response = fromstring(string.encode('utf-8'))
        json_vehicle = response.getchildren()[0].text
        json_info = json.loads(json_vehicle)
        return json_info
    else:
        return None

import requests
import os
from pprint import pprint


def get_distance_between(origin, destination):
    params = {
        'destination': '{},{}'.format(str(destination[0]), str(destination[1])),
        'origin': '{},{}'.format(str(origin[0]), str(origin[1])),
        'key': os.environ.get('GOOGLE_MAPS_API_KEY')
    }
    r = requests.get('https://maps.googleapis.com/maps/api/directions/json', params=params)
    distance = r.json()['routes'][0]['legs'][0]['distance']['value']
    return distance

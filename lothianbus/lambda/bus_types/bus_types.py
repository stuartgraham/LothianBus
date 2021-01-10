import boto3
import simplejson as json
import requests
import pprint
import os

# Environment Variables
data_assets_bucket = os.environ['DATA_ASSETS_BUCKET']

# boto3 objects
S3 = boto3.resource('s3')

# Constants and tweakables
STOPIDS = ['6200204700', '6200204380', '6200243655', '6200243375', '6200243600']
STOP_TYPE_URL = 'https://tfeapp.com/api/website/stop.php?id='

def refresh_bus_data(stopid):
    response = requests.get(f'{STOP_TYPE_URL}{stopid}')
    try:
        return response.json()
    except:
        print('ERROR: No valid JSON returned from the API')
        return 'error'

def handler(event, context):
    for stopid in STOPIDS:
        filepath = 'bustypes_' + stopid + '.json'
        s3object = S3.Object(data_assets_bucket, filepath)
        result = refresh_bus_data(stopid)
        if not result == 'error':
            s3object.put(Body=(bytes(json.dumps(result).encode('UTF-8'))))

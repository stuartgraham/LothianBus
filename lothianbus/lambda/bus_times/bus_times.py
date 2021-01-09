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
STOPIDS = ['6200204700', '6200204380']
STOP_TIME_URL = 'https://tfeapp.com/api/website/stop_times.php?stop_id='

def refresh_stop_data(stopid):
    response = requests.get(f'{STOP_TIME_URL}{stopid}')
    return response.json()

def lambda_handler(event, context):
    for stopid in STOPIDS:
        filepath = 'bustimes_' + stopid + '.json'
        s3object = S3.Object(data_assets_bucket, filepath)
        result = refresh_stop_data(stopid)
        s3object.put(Body=(bytes(json.dumps(result).encode('UTF-8'))))

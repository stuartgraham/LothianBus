import boto3
import simplejson as json
from decimal import Decimal
import requests
import os

# Environment Variables
BUS_TIMES_TABLE = os.environ['BUS_TIMES_TABLE'] 

# boto3 objects
DYNAMODB = boto3.resource('dynamodb')

# Constants and tweakables
STOP_IDS = ['6200204700', '6200204380', '6200243655', '6200243375', '6200243600', '6200245540']
STOP_TIME_URL = 'https://tfeapp.com/api/website/stop_times.php?stop_id='

def refresh_stop_data(stop_id):
    response = requests.get(f'{STOP_TIME_URL}{stop_id}')
    try:
        result_json = response.json()
        result_json = json.loads(json.dumps(result_json), parse_float=Decimal)
        return result_json
    except:
        print(f'ERROR: No valid JSON returned from the API when processing stop:{stop_id}')
        return 'error'

def dynamo_write(input_json):
    bus_times_json = input_json
    stop_id = input_json['stop']['id']
    table = DYNAMODB.Table(BUS_TIMES_TABLE)
    table.put_item(Item={'stop_id': stop_id, 'services': bus_times_json['services']})


def handler(event, context):
    for stop_id in STOP_IDS:
        result = refresh_stop_data(stop_id)
        if not result == 'error':
            dynamo_write(result)
            print(f'DATAPROCESS: Processed stop:{stop_id} successfully')
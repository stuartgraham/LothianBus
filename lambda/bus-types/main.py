import boto3
import simplejson as json
from decimal import Decimal
import requests
import os
from pprint import pprint

# Environment Variables
BUS_TYPES_TABLE = os.environ['BUS_TYPES_TABLE']

# boto3 objects
DYNAMODB = boto3.resource('dynamodb')


# Constants and tweakables
STOP_IDS = ['6200204700', '6200204380', '6200243655', '6200243375', '6200243600', '6200245540', '6200245600']
STOP_TYPE_URL = 'https://tfeapp.com/api/website/stop.php?id='

def refresh_bus_data(stop_id):
    response = requests.get(f'{STOP_TYPE_URL}{stop_id}')
    try:
        result_json = response.json()
        result_json = json.loads(json.dumps(result_json), parse_float=Decimal)
        return result_json
    except:
        print(f'ERROR: No valid JSON returned from the API when processing stop: {stop_id}')
        return 'error'

def dynamo_write(input_json):
    bus_type_json = input_json
    stop_id = input_json['stop']['id']
    table = DYNAMODB.Table(BUS_TYPES_TABLE)
    table.put_item(Item={'stop_id': stop_id, 'stop': bus_type_json['stop']})

def handler(event, context):
    for stop_id in STOP_IDS:   
        result = refresh_bus_data(stop_id)
        if not result == 'error':
            dynamo_write(result)
            print(f'DATAPROCESS: Processed stop:{stop_id} successfully')

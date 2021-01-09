import boto3
import simplejson as json
import requests
import pprint
import os

# Boto3 Objects

# Constants and Tweakables

def get_location_data():
    return ''

def get_bus_data():
    return ''

def handler(context, event):
    path_params = event['pathParameters']
    print(path_params)
    location_data = get_location_data()
    items = get_bus_data()

    return {
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': str(json.dumps(items)),
        'statusCode': '200'
    }
import boto3
import simplejson as json
import pprint
import os
from jinja2 import Environment, FileSystemLoader

# Boto3 Objects

# Constants and Tweakables

def get_location_data():
    return ''

def get_bus_data():
    return ''

def gen_html():
    content = 'This is about page'
    file_loader = FileSystemLoader('templates')
    env = Environment(loader=file_loader)
    template = env.get_template('stopdetail.html')
    output = template.render(content=content)
    return output

def handler(context, event):
    path_params = event['pathParameters']
    print(path_params)
    location_data = get_location_data()
    html = gen_html()
    
    return {
        'headers': {
            'Content-Type': 'text/html',
        },
        'body': html,
        'statusCode': '200'
    }

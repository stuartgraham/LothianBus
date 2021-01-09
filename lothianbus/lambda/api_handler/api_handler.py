import boto3
import simplejson as json
import pprint
import os
import jinja2

# Boto3 Objects

# Constants and Tweakables

def get_location_data():
    return ''

def get_bus_data():
    return ''

def gen_html():
    content = 'test'
    file_loader = jinja2.FileSystemLoader('templates')
    env = jinja2.Environment(loader=file_loader)
    template = env.get_template('stopdetail.html')
    output = template.render(content=content)
    return output

def handler(event, context):
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

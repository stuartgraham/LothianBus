import boto3
import simplejson as json
import pprint
import os
import jinja2
from time import time
from operator import itemgetter

# Boto3 Objects
data_assets_bucket = os.environ['DATA_ASSETS_BUCKET']
S3 = boto3.resource('s3')

# Constants and Tweakables
STOP_LOCATIONS = [
    {'location': 'default', 'stops' : {'stop1' : {'id' : '6200204700', 'walk_time' : 10}, 'stop2' : {'id' : '6200204380', 'walk_time' : 5}}},
    {'location': 'waverley', 'stops' : {'stop1' : {'id' : '6200243375', 'walk_time' : 5}}},
    {'location': 'boots', 'stops' : {'stop1' : {'id' : '6200243655', 'walk_time' : 5}}},
    {'location': 'hanover', 'stops' : {'stop1' : {'id' : '6200243600', 'walk_time' : 5}}}
]

VIA_DETAILS  = [
    {"via Dean Bridge & Waverley" : ["19", "37", "113","37","N37"]},
    {"via Stockbridge & Fountainbridge" : ["24"]},
    {"via Stockbridge & Waverley" : ["29", "X29"]},
    {"via Retail Park & Murrayfield" : ["38"]},
    {"via Dean Bridge & Fountainbridge" : ["47", "X47"]},
    {"via Stockbridge & Hanover St" : ["42"]}
]

# Function will grab a curated list of service form an anchor stop
def get_valid_services():
    global valid_services
    valid_services = []
    time_file_path = 'bustypes_6200204700.json'
    s3_object = S3.Object(data_assets_bucket, time_file_path)
    page_data = s3_object.get()['Body'].read().decode('utf-8')
    page_json = json.loads(page_data)
    for service in page_json['stop']['services']:
        valid_services.append(service)

# Curate services in the chosen vicinity ordered by time
def order_bus_data(location_data):
    unordered_services = []
    processed_services = []
    for k, stop_details in location_data['stops'].items():
        stop_id = stop_details['id']
        time_file_path = 'bustimes_' + stop_id + '.json'
        s3_object = S3.Object(data_assets_bucket, time_file_path)
        page_data = s3_object.get()['Body'].read().decode('utf-8')
        page_json = json.loads(page_data)

        for service in page_json['services']:
            for departure in service['departures']:
                
                if departure['service_name'] in processed_services:
                    # Do not process if already seen this service on another stop - stops duplicates
                    continue
                elif float(departure['departure_time_unix']) - time() <0:
                    # Only want future buses
                    continue
                else:
                    service_data = {}
                    service_data.update({'service_name' : departure['service_name']})
                    service_data.update({'destination' : departure['destination']})
                    service_data.update({'departure_time' : departure['departure_time']})
                    service_data.update({'departure_time_unix' : departure['departure_time_unix']})
                    service_data.update({'stop_id' : stop_id})

                    # Add via data to default only
                    if location_data['location'] == 'default':
                        via_data = get_via_detail(departure['service_name'])
                        service_data.update({'via' : via_data })
                    else:
                        service_data.update({'via' : ''})

                    # Determine if realtime data is working
                    if departure['real_time'] == True:
                        service_data.update({'time_status' : 'Live'})
                    else:
                        service_data.update({'time_status' : 'Schedule'})

                    # Determine walking delta times
                    timedelta = int((float(departure['departure_time_unix']) - time())/60)
                    walk_time = stop_details['walk_time']
                    timedelta = timedelta - walk_time
                    service_data.update({'time_delta' : timedelta})
                    # Delta time label
                    if timedelta < 0:
                        service_data.update({'time_delta_status' : 'Make up '})
                    else:
                        service_data.update({'time_delta_status' : 'Leave in '})

                    # Add data to processing lists
                    unordered_services.append(service_data)
                    processed_services.append(departure['service_name'])
    
    # Reorder list on departure time
    ordered_services = sorted(unordered_services, key=itemgetter('departure_time_unix')) 
    print(ordered_services)
    return ordered_services

# Curate a list of stops relative to the location
def get_location_data(path_param):
    for stop_location in STOP_LOCATIONS:
        if path_param == stop_location['location']:
            return stop_location
    return STOP_LOCATIONS[0]

# Provide via data to the service
def get_via_detail(service_name):
    for via_detail in VIA_DETAILS:
        for destination, service_names in via_detail.items():
            if service_name in service_names:
                return destination
    return ''

# Generate HTML for response
def gen_html(bus_services):
    file_loader = jinja2.FileSystemLoader('templates')
    env = jinja2.Environment(loader=file_loader)
    template = env.get_template('stopdetail.html')
    output = template.render(bus_services=bus_services)
    return output

# Lambda handler
def handler(event, context):
    path_params = event['pathParameters']
    print(path_params)
    get_valid_services()
    print(valid_services)
    location_data = get_location_data(path_params['location'])
    bus_services = order_bus_data(location_data)
    html = gen_html(bus_services)
    
    return {
        'headers': {
            'Content-Type': 'text/html',
        },
        'body': html,
        'statusCode': '200'
    }

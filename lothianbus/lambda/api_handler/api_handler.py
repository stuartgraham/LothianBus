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


def get_via_detail(service_name):
    viaservices = [
        ["19","via Dean Bridge & Waverley"],
        ["37","via Dean Bridge & Waverley"],
        ["113","via Dean Bridge & Waverley"],
        ["X37","via Dean Bridge & Waverley"],
        ["N37","via Dean Bridge & Waverley"],
        ["24","via Stockbridge & Fountainbridge"],
        ["29","via Stockbridge & Waverley"],
        ["X29","via Stockbridge & Waverley"],
        ["38","via Retail Park & Murrayfield"],
        ["47","via Dean Bridge & Fountainbridge"],
        ["X47","via Dean Bridge & Fountainbridge"],
        ["42", "via Stockbridge & Hanover St"]
    ]
    for viaservice in viaservices:
        if viaservice[0] == service_name:
            return viaservice[1]
    return ''

def order_bus_data(location_data):
    listofservices = []
    unordered_services = []
    processed_services = []
    for k, stop_details in location_data['stops'].items():
        stop_id = stop_details['id']
        timefilepath = 'bustimes_' + stop_id + '.json'
        s3object = S3.Object(data_assets_bucket, timefilepath)
        pagedata = s3object.get()['Body'].read().decode('utf-8')
        pagejson = json.loads(pagedata)
        print(pagejson['services'])

        for service in pagejson['services']:
            for departure in service['departures']:
                
                if departure['service_name'] in processed_services:
                    # Do not process if already seen this service on another stop - stops duplicates
                    continue
                elif float(departure['departure_time_unix']) - time() <0:
                    # Only want future buses
                    continue
                else:
                    servicedata = []
                    service_data = {}
                    # servicedata attr 0
                    servicedata.append(departure['service_name'])
                    service_data.update({'service_name' : departure['service_name']})
                    # servicedata attr 1
                    servicedata.append(departure['destination'])
                    service_data.update({'destination' : departure['destination']})
                    # servicedata attr 2
                    if location_data['location'] == 'default':
                        servicedata.append(get_via_detail(departure['service_name']))
                        service_data.update({'via' : get_via_detail(departure['service_name'])})
                    else:
                        servicedata.append('')
                        service_data.update({'via' : ''})
                    # servicedata attr 3
                    servicedata.append(departure['departure_time'])
                    service_data.update({'departure_time' : departure['departure_time']})
                    # servicedata attr 4
                    if departure['real_time'] == True:
                        servicedata.append('Live Time')
                        service_data.update({'time_status' : 'Live'})
                    else:
                        servicedata.append('Schedule')
                        service_data.update({'time_status' : 'Schedule'})
                    # servicedata attr 5
                    servicedata.append(departure['departure_time_unix'])
                    service_data.update({'departure_time_unix' : departure['departure_time_unix']})
                    # servicedata attr 6
                    servicedata.append(stop_id)
                    service_data.update({'stop_id' : stop_id})
                    # servicedata attr 7
                    timedelta = int((float(departure['departure_time_unix']) - time())/60)
                    walk_time = stop_details['walk_time']
                    timedelta = timedelta - walk_time
                    servicedata.append(timedelta)
                    service_data.update({'time_delta' : timedelta})
                    # servicedata attr 8
                    if timedelta < 0:
                        servicedata.append('Make up ')
                        service_data.update({'time_delta_status' : 'Make up '})
                    else:
                        servicedata.append('Leave in ')
                        service_data.update({'time_delta_status' : 'Leave in '})
                    # Appended to array of arrays (listofservices)
                    listofservices.append(servicedata)
                    unordered_services.append(service_data)
                    processed_services.append(departure['service_name'])
    
    orderlistofservices = sorted(listofservices, key=itemgetter(5))
    ordered_services = sorted(unordered_services, key=itemgetter('departure_time_unix')) 
    print(ordered_services)
    return orderlistofservices


def get_location_data(path_param):
    for stop_location in STOP_LOCATIONS:
        if path_param == stop_location['location']:
            return stop_location
    return STOP_LOCATIONS[0]


def gen_html(bus_services):
    file_loader = jinja2.FileSystemLoader('templates')
    env = jinja2.Environment(loader=file_loader)
    template = env.get_template('stopdetail.html')
    output = template.render(bus_services=bus_services)
    return output

def handler(event, context):
    path_params = event['pathParameters']
    print(path_params)
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

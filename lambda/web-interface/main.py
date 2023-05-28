import boto3
import simplejson as json
import os
import jinja2
from time import time
from operator import itemgetter

# Environment Variables
BUS_TYPES_TABLE = os.environ['BUS_TYPES_TABLE']
BUS_TIMES_TABLE = os.environ['BUS_TIMES_TABLE'] 

# boto3 objects
DYNAMODB = boto3.resource('dynamodb')
SSM = boto3.client('ssm')

# Constants and Tweakables
ANCHOR_STOPS = ['6200204700', '6200245540', '6200245600']

STOP_LOCATIONS_DATA = [
    {'location': 'default', 'stops' : {'stop1' : {'id' : '6200204700', 'walk_time' : 10, 'friendly_name' : 'Crewe Road Cemetery'},
        'stop2' : {'id' : '6200204380', 'walk_time' : 5, 'friendly_name' : 'Craigleith Hill Road North Side'},
        'stop3' : {'id' : '6200245540', 'walk_time' : 5, 'friendly_name' : 'Craigleith Hill Road South Side'}}},
    {'location': 'waverley', 'stops' : {'stop1' : {'id' : '6200243375', 'walk_time' : 5, 'friendly_name' : 'Princes St Waverley Steps'}}},
    {'location': 'boots', 'stops' : {'stop1' : {'id' : '6200243655', 'walk_time' : 5, 'friendly_name' : 'Princes St Boots'}}},
    {'location': 'hanover', 'stops' : {'stop1' : {'id' : '6200243600', 'walk_time' : 5,'friendly_name' : 'Hanover St'}}}
]

VIA_DETAILS  = [
    {"via Dean Bridge & Waverley" : ["19", "37", "113","37","N37"]},
    {"via Stockbridge & Fountainbridge" : ["24"]},
    {"via Stockbridge & Waverley" : ["29", "X29"]},
    {"via Retail Park & Murrayfield" : ["38"]},
    {"via Dean Bridge & Fountainbridge" : ["47", "X47", "22"]}
]

IGNORED_SERVICES = [
    {'service_name': '38', 'stop_id': '6200204380'},
    {'service_name': '104', 'stop_id': '*'}
]


# Grab valid services based on services passing through anchor stops
def get_valid_services():
    valid_services = []
    for stop in ANCHOR_STOPS:
        times_table = DYNAMODB.Table(BUS_TIMES_TABLE)
        response = times_table.get_item(Key={
            'stop_id': stop
        })
        for service in response['Item']['services']:
            if service['service_name'] not in valid_services:
                valid_services.append(service['service_name'])
    return valid_services


# Get bus times based on bus stop
def get_bus_times(stop_id):
    bus_times_table = DYNAMODB.Table(BUS_TIMES_TABLE)
    response = bus_times_table.get_item(Key={
        'stop_id': stop_id
    })
    return response

# Get bus types based on bus stop
def get_bus_types(stop_id):
    bus_times_table = DYNAMODB.Table(BUS_TYPES_TABLE)
    response = bus_times_table.get_item(Key={
        'stop_id': stop_id
    })
    return response

# Check if service is on ignored list
def ignored_service(service_name, stop_id):
    for ignored_service in IGNORED_SERVICES:
        if ignored_service['service_name'] == service_name and ignored_service['stop_id'] == stop_id:
            return True
        if ignored_service['service_name'] == service_name and ignored_service['stop_id'] == '*':
            return True
    return False

# Curates service detail to downselect only valuable data
def curated_service_detail(departure, bus_type_data, stop_location, walk_time):
    service_data = {}

    # Selected service detail
    service_data.update({'service_name' : departure['service_name']})
    service_data.update({'destination' : departure['destination']})
    service_data.update({'departure_time' : departure['departure_time']})
    service_data.update({'departure_time_unix' : departure['departure_time_unix']})
    service_data.update({'stop_id' : departure['stop_id']})

    # Get service colours
    for service in bus_type_data['Item']['stop']['services']:
        if service['name'] == departure['service_name']:
            service_data.update({'back_colour' : service['color']})
            service_data.update({'text_colour' : service['text_color']})

    # Add via data to default only
    if stop_location == 'default':
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
    timedelta = timedelta - walk_time
    service_data.update({'time_delta' : timedelta})
    # Delta time label
    if timedelta < 0:
        service_data.update({'time_delta_status' : 'Make up '})
    else:
        service_data.update({'time_delta_status' : 'Leave in '})

    return service_data


# Get an ordered list of services we care about based on location
def order_bus_data(stop_location_data, valid_services):
    unordered_services = []
    processed_services = []

    # Take stop details from location data passed
    for _, stop_details in stop_location_data['stops'].items():
        stop_id = stop_details['id']
        bus_time_data = get_bus_times(stop_id)
        bus_type_data = get_bus_types(stop_id)
        bus_time_data = bus_time_data['Item']
        print(bus_time_data['services'])
        for service in bus_time_data['services']:
            for departure in service['departures']:
                # Example response
                # departure: {'occupancy_rate': None, 'diverted': False, 'service_name': '19', 'minutes': Decimal('7'), 
                # 'stop_id': '36232869', 'real_time': True, 'destination': 'Leith Street', 'journey_id': '4005', 
                # 'departure_time': '21:50', 'vehicle_id': '638', 'departure_time_unix': Decimal('1672696231'), 
                # 'departure_time_iso': '2023-01-02T21:50:31+00:00'}
                validated_service = []

                # Check service goes to anchor
                if departure['service_name'] in valid_services:
                    validated_service.append(True)
                else:
                    validated_service.append(False)
                
                # Check service is not on ignore list
                if ignored_service(departure['service_name'], departure['stop_id']):
                    validated_service.append(False)
                else:
                    validated_service.append(True)

                # Check if service in processed list
                if departure['service_name'] in processed_services:
                    validated_service.append(False)
                else:
                    validated_service.append(True)

                # Check future bus only and not in past
                if float(departure['departure_time_unix']) - time() < 0:
                    validated_service.append(False)
                else:
                    validated_service.append(True)

                # Check if service is validated, curate service detail if so
                if all(validated_service):
                    service_detail = curated_service_detail(
                        departure, bus_type_data, stop_location_data['location'], stop_details['walk_time'])
                    # Add data to processing lists
                    unordered_services.append(service_detail)
                    processed_services.append(departure['service_name'])

    # Reorder list on departure time
    ordered_services = sorted(unordered_services, key=itemgetter('departure_time_unix')) 
    print(ordered_services)
    return ordered_services


# Get location from path
def get_location(raw_path):
    if raw_path == '/':
        return 'default'
    else:
        return raw_path.strip('/')


# Curate a list of stops relative to the location
def get_location_data(location):
    for stop_location_data in STOP_LOCATIONS_DATA:
        if location == stop_location_data['location']:
            return stop_location_data


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

# Get build number
def get_build_number():
    build_number = SSM.get_parameter(Name='/lothianbus/buildnumber')
    print(build_number)
    return build_number

# Lambda handler
def handler(event, context):
    print(event)
    location = get_location(event['rawPath'])
    stop_location_data = get_location_data(location)
    valid_services = get_valid_services()
    bus_services = order_bus_data(stop_location_data, valid_services)
    html = gen_html(bus_services)
    
    return {
        'headers': {
            'Content-Type': 'text/html',
        },
        'body': html,
        'statusCode': '200'
    }

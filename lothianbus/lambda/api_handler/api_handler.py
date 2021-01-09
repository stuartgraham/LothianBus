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
STOPIDS = ['6200204700', '6200204380']
STOPIDSTIMES = [['6200204700', 10],['6200204380', 5]]

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

def order_bus_data():
    listofservices = []
    processedservices = []
    for stopid in STOPIDS:
        timefilepath = 'bustimes_' + stopid + '.json'
        s3object = S3.Object(data_assets_bucket, timefilepath)
        pagedata = s3object.get()['Body'].read().decode('utf-8')
        pagejson = json.loads(pagedata)
    
        for service in pagejson['services']:
            for departure in service['departures']:
                
                if departure['service_name'] in processedservices:
                    # Do not process if already seen this service on another stop - stops duplicates
                    continue
                elif float(departure['departure_time_unix']) - time() <0:
                    # Only want future buses
                    continue
                else:
                    servicedata = []
                    # servicedata attr 0
                    servicedata.append(departure['service_name'])
                    # servicedata attr 1
                    servicedata.append(departure['destination'])
                    # servicedata attr 2
                    servicedata.append(get_via_detail(departure['service_name']))
                    # servicedata attr 3
                    servicedata.append(departure['departure_time'])
                    # servicedata attr 4
                    if departure['real_time'] == True:
                        servicedata.append('Live Time')
                    else:
                        servicedata.append('Schedule')
                    # servicedata attr 5
                    servicedata.append(departure['departure_time_unix'])
                    # servicedata attr 6
                    servicedata.append(stopid)
                    # servicedata attr 7
                    timedelta = int((float(departure['departure_time_unix']) - time())/60)
                    walktime = 0
                    for stopidtime in STOPIDSTIMES:
                        if stopid == stopidtime[0]:
                            walktime = stopidtime[1]
                    timedelta = timedelta - walktime
                    servicedata.append(timedelta)
                    # servicedata attr 8
                    if timedelta < 0:
                        servicedata.append('Make up ')
                    else:
                        servicedata.append('Leave in ')
                    # Appended to array of arrays (listofservices)
                    listofservices.append(servicedata)
                    processedservices.append(departure['service_name'])
    
    orderlistofservices = sorted(listofservices, key=itemgetter(5))
    #pprint(orderlistofservices)
    return orderlistofservices




def get_location_data():
    return ''

def get_bus_data():
    return ''

def gen_html(bus_services):
    file_loader = jinja2.FileSystemLoader('templates')
    env = jinja2.Environment(loader=file_loader)
    template = env.get_template('stopdetail.html')
    output = template.render(bus_services=bus_services)
    return output

def handler(event, context):
    path_params = event['pathParameters']
    print(path_params)
    location_data = get_location_data()
    bus_services = order_bus_data()
    html = gen_html(bus_services)
    
    return {
        'headers': {
            'Content-Type': 'text/html',
        },
        'body': html,
        'statusCode': '200'
    }

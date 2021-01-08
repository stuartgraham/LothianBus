import urllib.request 
import json
import boto3
import parameters 

S3 = boto3.resource('s3')

def refreshBusData(stopid):
    with urllib.request.urlopen("https://tfeapp.com/api/website/stop.php?id=" + stopid) as url:
        bustypes = json.loads(url.read().decode())
        print('HTTPCODE:' + str(url.getcode()))
    return bustypes

def lambda_handler(event, context):
    for stopid in parameters.STOPIDS:
        filepath = 'bustypes_' + stopid + '.json'
        s3object = S3.Object(parameters.S3BUCKET, filepath)
        result = refreshBusData(stopid)
        s3object.put(Body=(bytes(json.dumps(result).encode('UTF-8'))))

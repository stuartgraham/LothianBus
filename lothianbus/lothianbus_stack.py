from os import path
from aws_cdk import core
import aws_cdk.aws_lambda as lmb
import aws_cdk.aws_lambda_event_sources as lmb_events
import aws_cdk.aws_apigatewayv2 as apigw2
import aws_cdk.aws_apigatewayv2_integrations as apigw2int
import aws_cdk.aws_dynamodb as dynamodb
import aws_cdk.aws_sqs as sqs
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_s3_deployment as s3deploy
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as eb_targets


class ApplicationStage(core.Stage):
    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        service = ApplicationStack(self, 'LothianBus')
        #self.url_output = service.url_output


class ApplicationStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        this_dir = path.dirname(__file__)
        
        # Dynamo DB Tables
        dynamo_bus_times_table = dynamodb.Table(self, 'bus_times',
            partition_key=dynamodb.Attribute(name='lb_stop', type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
            )
        
        
        # Lambda Layers
        lambda_layer_requests = lmb.LayerVersion(self, 'Layer-Requests',
            code = lmb.Code.from_asset(path.join(this_dir, 'lambda/layers/requests.zip')),
            compatible_runtimes = [lmb.Runtime.PYTHON_3_8],
        )
        lambda_layer_simplejson = lmb.LayerVersion(self, 'Layer-SimpleJSON',
            code = lmb.Code.from_asset(path.join(this_dir, 'lambda/layers/simplejson.zip')),
            compatible_runtimes = [lmb.Runtime.PYTHON_3_8],
        )


        # Lambda
        ## Lambda - Get Bus Times
        lambda_bus_times = lmb.Function(self, 'Bus-Times',
            runtime=lmb.Runtime.PYTHON_3_8,
            handler='bus_times.handler',
            layers=[lambda_layer_requests, lambda_layer_simplejson],
            code=lmb.Code.from_asset(path.join(this_dir, 'lambda/bus_times'))
        )
        ### Grants
        dynamo_bus_times_table.grant_read_write_data(lambda_bus_times)

        ## Lambda - Get Bus Types
        lambda_bus_types = lmb.Function(self, 'Bus-Types',
            runtime=lmb.Runtime.PYTHON_3_8,
            handler='bus_types.handler',
            layers=[lambda_layer_requests, lambda_layer_simplejson],
            code=lmb.Code.from_asset(path.join(this_dir, 'lambda/bus_types'))
        )
        ### Grants
        dynamo_bus_times_table.grant_read_write_data(lambda_bus_types)


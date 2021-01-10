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
import aws_cdk.aws_events_targets as targets


class ApplicationStage(core.Stage):
    def __init__(self, scope: core.Construct, id: str, lb_env='', **kwargs):
        super().__init__(scope, id, **kwargs)
        self.lb_env = lb_env
        print(lb_env)

        service = ApplicationStack(self, 'LothianBus', lb_env=self.lb_env)
        #self.url_output = service.url_output


class ApplicationStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, lb_env='', **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        this_dir = path.dirname(__file__)

        print(lb_env)
        
        # S3 Buckets
        s3_bucket_assets = s3.Bucket(self, 'Assets')
        
        
        # Lambda Layers
        lambda_layer_requests = lmb.LayerVersion(self, 'Layer-Requests',
            code = lmb.Code.from_asset(path.join(this_dir, 'lambda/layers/requests.zip')),
            compatible_runtimes = [lmb.Runtime.PYTHON_3_8],
        )
        lambda_layer_simplejson = lmb.LayerVersion(self, 'Layer-SimpleJSON',
            code = lmb.Code.from_asset(path.join(this_dir, 'lambda/layers/simplejson.zip')),
            compatible_runtimes = [lmb.Runtime.PYTHON_3_8],
        )
        lambda_layer_jinja2 = lmb.LayerVersion(self, 'Layer-Jinja2',
            code = lmb.Code.from_asset(path.join(this_dir, 'lambda/layers/jinja2.zip')),
            compatible_runtimes = [lmb.Runtime.PYTHON_3_8],
        )


        # Lambda
        ## Lambda - Get Bus Times
        lambda_bus_times = lmb.Function(self, 'Bus-Times',
            timeout=core.Duration.seconds(360),
            memory_size=512,
            runtime=lmb.Runtime.PYTHON_3_8,
            handler='bus_times.handler',
            layers=[lambda_layer_requests, lambda_layer_simplejson],
            code=lmb.Code.from_asset(path.join(this_dir, 'lambda/bus_times')),
            environment={
                'DATA_ASSETS_BUCKET': s3_bucket_assets.bucket_name
            }
        )
        ### Grants
        s3_bucket_assets.grant_read_write(lambda_bus_times)

        ## Lambda - Get Bus Types
        lambda_bus_types = lmb.Function(self, 'Bus-Types',
            timeout=core.Duration.seconds(360),
            memory_size=512,
            runtime=lmb.Runtime.PYTHON_3_8,
            handler='bus_types.handler',
            layers=[lambda_layer_requests, lambda_layer_simplejson],
            code=lmb.Code.from_asset(path.join(this_dir, 'lambda/bus_types')),
            environment={
                'DATA_ASSETS_BUCKET': s3_bucket_assets.bucket_name
            }
        )
        ### Grants
        s3_bucket_assets.grant_read_write(lambda_bus_types)

        ## Lambda - API Handler
        lambda_api_handler = lmb.Function(self, 'API-Handler',
            timeout=core.Duration.seconds(360),
            memory_size=512,
            runtime=lmb.Runtime.PYTHON_3_8,
            handler='api_handler.handler',
            layers=[lambda_layer_simplejson, lambda_layer_jinja2],
            code=lmb.Code.from_asset(path.join(this_dir, 'lambda/api_handler')),
            environment={
                'DATA_ASSETS_BUCKET': s3_bucket_assets.bucket_name
            }
        )
        ### Grants
        s3_bucket_assets.grant_read(lambda_api_handler)


        # CW Events
        lambda_target_bus_times = targets.LambdaFunction(lambda_bus_times)
        lambda_target_bus_types = targets.LambdaFunction(lambda_bus_types)

        bus_time_refresh_mins = 5
        bus_type_refresh_mins = 30
        if lb_env == 'Production':
            bus_time_refresh_mins = 1
            bus_type_refresh_mins = 10
            
        events.Rule(self, "Every1Mins",
            schedule=events.Schedule.rate(core.Duration.minutes(bus_time_refresh_mins)),
            targets=[lambda_target_bus_times]
        )

        events.Rule(self, "Every10Mins",
            schedule=events.Schedule.rate(core.Duration.minutes(bus_type_refresh_mins)),
            targets=[lambda_target_bus_types]
        )

        # APIGW
        apigw_lothianbus = apigw2.HttpApi(self, 'LothianBus-APIGW-Http')

        # APIGW Integrations
        ## Lambda Integrations
        lambda_int_lambda_api_handler = apigw2int.LambdaProxyIntegration(
            handler=lambda_api_handler
        )

        apigw_lothianbus.add_routes(
            path='/{location}',
            methods=[apigw2.HttpMethod.GET],
            integration=lambda_int_lambda_api_handler
        )

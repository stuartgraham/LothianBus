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
        self.url_output = service.url_output


class ApplicationStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        this_dir = path.dirname(__file__)
        
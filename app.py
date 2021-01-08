#!/usr/bin/env python3

from aws_cdk import core

from lothianbus.pipeline_stack import PipelineStack

app = core.App()
PipelineStack(app, 'LothianBusPipeline', env={
    'account': '811799881965',
    'region': 'eu-west-1'
})

app.synth()

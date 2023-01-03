#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { LothianBusStackUsEast1, LothianBusStackEuWest1 } from '../lib/lothian-bus-stack';

const app = new cdk.App();
new LothianBusStackEuWest1(app, 'LothianBusStackEuWest1', {
  env: { account: process.env.AWS_ACCOUNT_NUMBER!, region: 'eu-west-1' },
});

new LothianBusStackUsEast1(app, 'LothianBusStackUsEast1', {
  env: { account: process.env.AWS_ACCOUNT_NUMBER!, region: 'us-east-1' },
});
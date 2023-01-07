import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as path from 'path';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as events from 'aws-cdk-lib/aws-events';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import { LambdaFunction } from 'aws-cdk-lib/aws-events-targets';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as ssmcross from '@pepperize/cdk-ssm-parameters-cross-region';
import * as ssm from 'aws-cdk-lib/aws-ssm';


export class LothianBusStackEuWest1 extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Dynamo Table - bus types
    const busTypesTable = new dynamodb.Table(this, "BusTypesTable", {
      partitionKey: {
        name: "stop_id",
        type: dynamodb.AttributeType.STRING
      },
      billingMode: dynamodb.BillingMode.PROVISIONED,
      readCapacity: 1,
      writeCapacity: 1,
    })


    // Dynamo Table - bus times
    const busTimesTable = new dynamodb.Table(this, "BusTimesTable", {
      partitionKey: {
        name: "stop_id",
        type: dynamodb.AttributeType.STRING
      },
      billingMode: dynamodb.BillingMode.PROVISIONED,
      readCapacity: 1,
      writeCapacity: 1,
    })


    // SimpleJSON layer
    const simpleJsonLayer = new lambda.LayerVersion(this, 'SimpleJsonLayer', {
      compatibleRuntimes: [
        lambda.Runtime.PYTHON_3_9
      ],
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/layers/simplejson.zip'))
    });

    // Requests layer
    const requestsLayer = new lambda.LayerVersion(this, 'RequestsLayer', {
      compatibleRuntimes: [
        lambda.Runtime.PYTHON_3_9
      ],
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/layers/requests.zip'))
    });

    // Jinja2 layer
    const jinja2Layer = new lambda.LayerVersion(this, 'jinja2Layer', {
      compatibleRuntimes: [
        lambda.Runtime.PYTHON_3_9
      ],
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/layers/jinja2.zip'))
    });


    // Policy - Put Item Bus Type Table
    const dynamoDbPutItemBusType = new iam.PolicyStatement({
      actions: [
        "dynamodb:PutItem"
    ],
      resources: [
        busTypesTable.tableArn
    ]
    });

    // Policy - Put Item Bus Times Table
    const dynamoDbPutItemBusTimes = new iam.PolicyStatement({
      actions: [
        "dynamodb:PutItem"
    ],
      resources: [
        busTimesTable.tableArn
    ]
    });

    // Policy - Read Items from Bus Times and Bus Types Table
    const dynamoDbReadItemBusTables = new iam.PolicyStatement({
      actions: [
        "dynamodb:GetItem"
    ],
      resources: [
        busTimesTable.tableArn,
        busTypesTable.tableArn
    ]
    });

    // Policy - Get build version
    const ssmReadBuildVersion = new iam.PolicyStatement({
      actions: [
        "ssm:GetParameter"
    ],
      resources: [
        "*"
    ]
    });


    // Lambda Function - Bus types
    const busTypesFunction = new lambda.Function(this, 'BusTypesFunction', {
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/bus-types')),
      handler: 'main.handler',
      layers: [simpleJsonLayer, requestsLayer],
      runtime: lambda.Runtime.PYTHON_3_9,
      timeout: cdk.Duration.seconds(30),
      architecture: lambda.Architecture.ARM_64,
      environment: {
        BUS_TYPES_TABLE : busTypesTable.tableName
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
    });

    busTypesFunction.role?.attachInlinePolicy(
      new iam.Policy(this, 'busTypesFunctionInlinePolicy', {
        statements: [dynamoDbPutItemBusType],
      }),
    );

    // Lambda Function - Bus times
    const busTimesFunction = new lambda.Function(this, 'BusTimesFunction', {
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/bus-times')),
      handler: 'main.handler',
      layers: [simpleJsonLayer, requestsLayer],
      runtime: lambda.Runtime.PYTHON_3_9,
      timeout: cdk.Duration.seconds(30),
      architecture: lambda.Architecture.ARM_64,
      environment: {
        BUS_TIMES_TABLE : busTimesTable.tableName
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
    });

    busTimesFunction.role?.attachInlinePolicy(
      new iam.Policy(this, 'busTimesFunctionInlinePolicy', {
        statements: [dynamoDbPutItemBusTimes],
      }),
    );

    // Lambda Function - Web Interface
    const busWebInterfaceFunction = new lambda.Function(this, 'BusWebInterfaceFunction', {
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/web-interface')),
      handler: 'main.handler',
      layers: [simpleJsonLayer, requestsLayer, jinja2Layer],
      runtime: lambda.Runtime.PYTHON_3_9,
      timeout: cdk.Duration.seconds(3),
      architecture: lambda.Architecture.ARM_64,
      environment: {
        BUS_TIMES_TABLE : busTimesTable.tableName,
        BUS_TYPES_TABLE : busTypesTable.tableName
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
    });

    busWebInterfaceFunction.role?.attachInlinePolicy(
      new iam.Policy(this, 'busWebInterfaceFunctionInlinePolicy', {
        statements: [dynamoDbReadItemBusTables, ssmReadBuildVersion],
      }),
    );

    // Function URL right to SSM Parameter in friendly for Cloudfront manner
    const busWebInterfaceFunctionUrl = busWebInterfaceFunction.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE,
    });

    const functionHostUrl = cdk.Fn.select(2, cdk.Fn.split('/', busWebInterfaceFunctionUrl.url));

    const functionHostUrlParam = new ssm.StringParameter(this, 'BusWebInterfaceFunctionUrlParam', {
      parameterName: '/lothianbus/functionurlhost',
      stringValue: functionHostUrl
    });


    // Set build number
    let buildDate: Date = new Date()
    let buildNumber: string = 
      "1.0." +
      buildDate.getFullYear().toString() +
      ('0' + (buildDate.getMonth()+1)).slice(-2) +
      ('0' + (buildDate.getDate())).slice(-2) +
      ('0' + (buildDate.getHours())).slice(-2) +
      ('0' + (buildDate.getMinutes())).slice(-2)


    const buildVersionParam = new ssm.StringParameter(this, 'BuildVersionParam', {
      parameterName: '/lothianbus/buildnumber',
      stringValue: buildNumber
    });

    // CLOUDWATCH Events
    // Run every 1 days
    new events.Rule(this, 'Every1DaysRule', {
      schedule: events.Schedule.rate(cdk.Duration.days(1)),
      targets: [
        new LambdaFunction(busTypesFunction)
      ]
    }); 

    // Run every 1 minutes
    new events.Rule(this, 'Every1MinutesRule', {
      schedule: events.Schedule.rate(cdk.Duration.minutes(1)),
      targets: [
        new LambdaFunction(busTimesFunction)
      ]
    }); 
  }
}

export class LothianBusStackUsEast1 extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ACM
    const arn : string = process.env.CERTIFICATE_ARN!;
    const busAcmCertificate = acm.Certificate.fromCertificateArn(this, 'busAcmCertificate', arn);

    // SSM Lookup
    const originUrl = ssmcross.StringParameter.fromStringParameterName(this, "OriginUrl", 
      "eu-west-1", 
      "/lothianbus/functionurlhost");


    // Cloudfront
    const busCloudfrontDistro = new cloudfront.Distribution(this, 'busCFDistribution', {
      defaultBehavior: { 
        origin: new origins.HttpOrigin(originUrl.stringValue),
        cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
      },
      domainNames: ['bus.rstu.xyz'],
      certificate: busAcmCertificate,
      comment: 'bus.rstu.xyz'
    });
  }
}

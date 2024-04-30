import pytest
import os
from moto import mock_aws
import boto3
from verticalscaling.tags import *

@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture()
def aws(aws_credentials):
    with mock_aws():
        yield boto3.client("cloudwatch", region_name="us-east-1")

@pytest.fixture()
def createAlarmScaleDown(aws):
    boto3.client('cloudwatch').put_metric_alarm(
      AlarmName = 'testlessthan',
      AlarmDescription = 'testlessthan',
      ActionsEnabled = True,
      OKActions = [ 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' ],
      AlarmActions = [ 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' ],
      InsufficientDataActions = [ 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' ],
      MetricName = 'CPUUtilization',
      Namespace = 'AWS/RDS',
      Statistic = 'Maximum',
      Dimensions = [ { 'Name': 'DBInstanceIdentifier', 'Value': 'testscaling' } ],
      Period = 300,
      EvaluationPeriods = 1,
      DatapointsToAlarm = 1,
      Threshold = 20.0,
      ComparisonOperator = 'LessThanOrEqualToThreshold',
      Tags = [ { 'Key': 'rds_scaling_action', 'Value': 'down'}]
    )

@pytest.fixture()
def createRdsDBInstance(aws):
    boto3.client('rds').create_db_instance(
      DBInstanceIdentifier = 'testscaling',
      DBInstanceClass = 'db.t2.micro',
      Engine = 'mysql',
      MasterUsername = 'XXXX',
      MasterUserPassword = 'XXXXXXXX',
      AllocatedStorage = 20,
      Tags = [ 
            { 'Key': 'rds_scaling_low_instanceclass', 'Value': 'db.t2.micro'},
            { 'Key': 'rds_scaling_high_instanceclass', 'Value': 'db.m5.large'}
        ]
    )
    
@pytest.fixture()
def createRdsDBInstanceNoTags(aws):
    boto3.client('rds').create_db_instance(
      DBInstanceIdentifier = 'testscaling',
      DBInstanceClass = 'db.t2.micro',
      Engine = 'mysql',
      MasterUsername = 'XXXX',
      MasterUserPassword = 'XXXXXXXX',
      AllocatedStorage = 20,
      Tags = [ 
        ]
    )

@pytest.fixture()
def createGreenRdsDBInstance(aws):
    boto3.client('rds').create_db_instance(
      DBInstanceIdentifier = 'testscaling-123',
      DBInstanceClass = 'db.m5.large',
      Engine = 'mysql',
      MasterUsername = 'XXXX',
      MasterUserPassword = 'XXXXXXXX',
      AllocatedStorage = 20,
      Tags = [ 
            { 'Key': 'rds_scaling_low_instanceclass', 'Value': 'db.t2.micro'},
            { 'Key': 'rds_scaling_high_instanceclass', 'Value': 'db.m5.large'}
        ]
    )


@pytest.fixture()
def scalingTags():
    return [ 
            { 'Key': 'rds_scaling_low_instanceclass', 'Value': 'db.t2.micro'},
            { 'Key': 'rds_scaling_high_instanceclass', 'Value': 'db.m5.large'}
        ]

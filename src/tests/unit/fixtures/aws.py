"""
This file is part of "Aimably Vertical Autoscaling".

"Aimably Vertical Autoscaling" is free software: you can redistribute it and/or modify it under the terms 
of the GNU General Public License as published by the Free Software Foundation, either version 3 of the 
License, or (at your option) any later version.

Aimably Vertical Autoscaling is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License along with Foobar. 
If not, see <https://www.gnu.org/licenses/>.
"""
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

#Clusters
@pytest.fixture()
def createRdsClusterInstanceNoTags(aws):
    boto3.client('rds').create_db_cluster(
      DBClusterIdentifier = 'testclusterscaling',
      DBClusterParameterGroupName = 'default.aurora-mysql5.7',
      Engine = 'aurora-mysql',
      MasterUsername = 'XXXX',
      MasterUserPassword = 'XXXXXXXX',
      Port = 3306,
      DBSubnetGroupName = 'default',
      VpcSecurityGroupIds = [ 'sg-XXXXXXXX' ],
      DBClusterInstanceClass = 'db.t2.micro',
      EngineMode = 'provisioned',
      Tags = []
    )

@pytest.fixture()
def createRdsClusterInstance(aws):
    try:
        r = boto3.client('rds').create_db_cluster(
        DatabaseName = 'testclusterscaling',
        DBClusterIdentifier = 'testclusterscaling',
        DBClusterParameterGroupName = 'default.aurora-mysql5.7',
        Engine = 'aurora-mysql',
        EngineVersion = "8.0",
        MasterUsername = 'XXXX',
        MasterUserPassword = 'XXXXXXXX',
        Port = 3306,
        DBSubnetGroupName = 'default',
        VpcSecurityGroupIds = [ 'sg-XXXXXXXX' ],
        DBClusterInstanceClass = 'db.t2.micro',
        Tags = [
                { 'Key': 'rds_scaling_low_instanceclass', 'Value': 'db.t2.micro'},
                { 'Key': 'rds_scaling_high_instanceclass', 'Value': 'db.m5.large'}
            ]
        )

        boto3.client('rds').create_db_instance(
        DBInstanceIdentifier = 'testclusterscaling-instance',
        DBClusterIdentifier = 'testclusterscaling',
        DBInstanceClass = 'db.t4g.medium',
        Engine = 'aurora-mysql'
        )
    except Exception as e:
        print(e)


@pytest.fixture()
def createRdsClusterInstanceMultipleInstances(aws):
    try:
        r = boto3.client('rds').create_db_cluster(
        DatabaseName = 'testclusterscaling',
        DBClusterIdentifier = 'testclusterscaling',
        DBClusterParameterGroupName = 'default.aurora-mysql5.7',
        Engine = 'aurora-mysql',
        EngineVersion = "8.0",
        MasterUsername = 'XXXX',
        MasterUserPassword = 'XXXXXXXX',
        Port = 3306,
        DBSubnetGroupName = 'default',
        VpcSecurityGroupIds = [ 'sg-XXXXXXXX' ],
        DBClusterInstanceClass = 'db.t2.micro',
        Tags = [
                { 'Key': 'rds_scaling_low_instanceclass', 'Value': 'db.t2.micro'},
                { 'Key': 'rds_scaling_high_instanceclass', 'Value': 'db.m5.large'}
            ]
        )

        boto3.client('rds').create_db_instance(
            DBInstanceIdentifier = 'testclusterscaling-instance',
            DBClusterIdentifier = 'testclusterscaling',
            DBInstanceClass = 'db.t4g.medium',
            Engine = 'aurora-mysql'
        )

        boto3.client('rds').create_db_instance(
            DBInstanceIdentifier = 'testclusterscaling-instance2',
            DBClusterIdentifier = 'testclusterscaling',
            DBInstanceClass = 'db.t4g.medium',
            Engine = 'aurora-mysql'
        )
    except Exception as e:
        print(e)

@pytest.fixture()
def createRdsClusterInstanceMultipleInstancesAtEnd(aws):
    try:
        r = boto3.client('rds').create_db_cluster(
        DatabaseName = 'testclusterscaling',
        DBClusterIdentifier = 'testclusterscaling',
        DBClusterParameterGroupName = 'default.aurora-mysql5.7',
        Engine = 'aurora-mysql',
        EngineVersion = "8.0",
        MasterUsername = 'XXXX',
        MasterUserPassword = 'XXXXXXXX',
        Port = 3306,
        DBSubnetGroupName = 'default',
        VpcSecurityGroupIds = [ 'sg-XXXXXXXX' ],
        DBClusterInstanceClass = 'db.t2.micro',
        Tags = [
                { 'Key': 'rds_scaling_low_instanceclass', 'Value': 'db.t2.micro'},
                { 'Key': 'rds_scaling_high_instanceclass', 'Value': 'db.m5.large'}
            ]
        )

        boto3.client('rds').create_db_instance(
            DBInstanceIdentifier = 'testclusterscaling-instance',
            DBClusterIdentifier = 'testclusterscaling',
            DBInstanceClass = 'db.t4g.large',
            Engine = 'aurora-mysql',
            Tags = [
                { 'Key': 'rds_aurora_scaling', 'Value': 'original_writer'},
                { 'Key': 'rds_aurora_scaling_target', 'Value': 'dbt4g.large'}
            ]
        )

        boto3.client('rds').create_db_instance(
            DBInstanceIdentifier = 'testclusterscaling-instance2',
            DBClusterIdentifier = 'testclusterscaling',
            DBInstanceClass = 'db.t4g.medium',
            Engine = 'aurora-mysql',
            Tags = [
                { 'Key': 'rds_aurora_scaling', 'Value': 'original_writer'},
                { 'Key': 'rds_aurora_scaling_target', 'Value': 'dbt4g.large'}
            ]
        )
    except Exception as e:
        print(e)


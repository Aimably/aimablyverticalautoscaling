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
from moto import mock_aws
import boto3

@pytest.fixture()
def eventBridgeRdsInstanceEvent():
  return {'version': '0', 'id': '0b1286f9-0f58-d397-55d1-d6d7e8e9517b', 'detail-type': 'RDS DB Instance Event', 'source': 'aws.rds', 'account': '123456789012', 'time': '2024-04-23T17:12:32Z', 'region': 'us-east-1', 'resources': ['arn:aws:rds:us-east-1:123456789012:db:testscaling'], 'detail': {'EventCategories': ['empty'], 'SourceType': 'DB_INSTANCE', 'SourceArn': 'arn:aws:rds:us-east-1:123456789012:db:testscaling', 'Date': '2024-04-23T17:12:32.740Z', 'Message': 'Performance Insights has been disabled', 'SourceIdentifier': 'testscaling'}}

@pytest.fixture()
def cloudwatchAlarm():
  return {
    'source': 'aws.cloudwatch', 
    'alarmArn': 'arn:aws:cloudwatch:us-east-1:123456789012:alarm:testlessthan', 
    'accountId': '123456789012', 
    'time': '2024-04-23T20:59:58.290+0000', 
    'region': 'us-east-1', 
    'alarmData': 
    {
      'alarmName': 'testlessthan', 
      'state': {'value': 'OK', 'reason': 'testsing', 'timestamp': '2024-04-23T20:59:58.290+0000'}, 
      'previousState': 
      {
        'value': 'ALARM', 
        'reason': 'Threshold Crossed: 1 out of the last 1 datapoints [3.4666088898518357 (23/04/24 20:44:00)] was less than or equal to the threshold (20.0) (minimum 1 datapoint for OK -> ALARM transition).', 
        'reasonData': '{"version":"1.0","queryDate":"2024-04-23T20:50:27.367+0000","startDate":"2024-04-23T20:44:00.000+0000","statistic":"Maximum","period":300,"recentDatapoints":[3.4666088898518357],"threshold":20.0,"evaluatedDatapoints":[{"timestamp":"2024-04-23T20:44:00.000+0000","sampleCount":5.0,"value":3.4666088898518357}]}', 
        'timestamp': '2024-04-23T20:50:27.369+0000'
      }, 
      'configuration': 
      {
        'metrics': 
        [
          {
            'id': 'f4c78617-7578-e68e-e779-a44c8db169a0', 
            'metricStat': 
            {
              'metric': 
              {
                'namespace': 'AWS/RDS', 
                'name': 'CPUUtilization', 
                'dimensions': {'DBInstanceIdentifier': 'testscaling'}
              }, 
              'period': 300, 
              'stat': 'Maximum'
            }, 
            'returnData': True
          }
        ]
      }
    }
  }

@pytest.fixture()
def userScaleUp():
  return {'source': 'custom', 'action': 'scaleup', 'region': 'us-east-1', 'instances': [ 'testscaling' ]}

@pytest.fixture()
def userScaleUpNoInstances():
  return {'source': 'custom', 'action': 'scaleup' }

@pytest.fixture()
def consoleDefaultEvent():
  return {
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
  }
  
@pytest.fixture()
def rdsDeletionEvent():
  return {'version': '0', 'id': 'bf59f6cf-eacc-ee3b-d235-f5d498956d51', 'detail-type': 'RDS DB Instance Event', 'source': 'aws.rds', 'account': '123456789012', 'time': '2024-04-30T00:20:13Z', 'region': 'us-east-1', 'resources': ['arn:aws:rds:us-east-1:123456789012:db:testscaling-old1'], 'detail': {'EventCategories': ['deletion'], 'SourceType': 'DB_INSTANCE', 'SourceArn': 'arn:aws:rds:us-east-1:123456789012:db:testscaling-old1', 'Date': '2024-04-30T00:20:13.042Z', 'Message': 'DB instance deleted', 'SourceIdentifier': 'testscaling-old1', 'EventID': 'RDS-EVENT-0003'}}

@pytest.fixture()
def blueGreenEvent():
  return {'version': '0', 'id': '7887483c-b2c8-de0d-cddc-84a18374c419', 'detail-type': 'RDS Blue Green Deployment Event', 'source': 'aws.rds', 'account': '123456789012', 'time': '2024-04-30T01:23:54Z', 'region': 'us-east-1', 'resources': ['arn:aws:rds:us-east-1:123456789012:deployment:bgd-hdqs3ik6vrwgutsn'], 'detail': {'EventCategories': ['creation'], 'SourceType': 'BLUE_GREEN_DEPLOYMENT', 'SourceArn': 'arn:aws:rds:us-east-1:123456789012:deployment:bgd-hdqs3ik6vrwgutsn', 'Date': '2024-04-30T01:23:54.932Z', 'Message': 'Blue/green deployment tasks completed. You can make more modifications to the green environment databases or switch over the deployment.', 'SourceIdentifier': 'bgd-hdqs3ik6vrwgutsn', 'EventID': 'RDS-EVENT-0244', 'Tags': {'rds_vertical_scaling_bluegreen': 'TRUE'}}}

@pytest.fixture()
def blueGreenEventDeletion():
  return {'version': '0', 'id': 'a4873fc1-f7b5-4e0f-a412-4c0ec1b457d0', 'detail-type': 'RDS Blue Green Deployment Event', 'source': 'aws.rds', 'account': '123456789012', 'time': '2024-04-30T02:01:29Z', 'region': 'us-east-1', 'resources': ['arn:aws:rds:us-east-1:123456789012:deployment:bgd-hdqs3ik6vrwgutsn'], 'detail': {'EventCategories': ['deletion'], 'SourceType': 'BLUE_GREEN_DEPLOYMENT', 'SourceArn': 'arn:aws:rds:us-east-1:123456789012:deployment:bgd-hdqs3ik6vrwgutsn', 'Date': '2024-04-30T02:01:29.568Z', 'Message': 'Blue/green deployment deleted.', 'SourceIdentifier': 'bgd-hdqs3ik6vrwgutsn', 'EventID': 'RDS-EVENT-0246'}}

# DB Cluster Events
@pytest.fixture()
def auroraClusterStoppedEvent():
  return {'version': '0', 'id': 'ca5edcb8-d149-ef91-b075-f0e9a6740d7f', 'detail-type': 'RDS DB Cluster Event', 'source': 'aws.rds', 'account': '123456789012', 'time': '2024-04-30T21:51:22Z', 'region': 'us-east-1', 'resources': ['arn:aws:rds:us-east-1:339712808883:cluster:auroratestscaling'], 'detail': {'EventCategories': ['notification'], 'SourceType': 'CLUSTER', 'SourceArn': 'arn:aws:rds:us-east-1:339712808883:cluster:auroratestscaling', 'Date': '2024-04-30T21:51:22.358Z', 'Message': 'DB cluster stopped', 'SourceIdentifier': 'auroratestscaling', 'EventID': 'RDS-EVENT-0150'}}

@pytest.fixture()
def userClusterScaleUp():
  return {'source': 'custom', 'action': 'scaleup', 'region': 'us-east-1', 'clusters': [ 'testclusterscaling' ]}

@pytest.fixture()
def clusterFailoverCompletedEvent():
  return {'version': '0', 'id': '2c5c9739-02be-610b-ab16-33a388360c78', 'detail-type': 'RDS DB Cluster Event', 'source': 'aws.rds', 'account': '339712808883', 'time': '2024-05-06T23:08:24Z', 'region': 'us-east-1', 'resources': ['arn:aws:rds:us-east-1:339712808883:cluster:auroratestscaling'], 'detail': {'EventCategories': ['failover'], 'SourceType': 'CLUSTER', 'SourceArn': 'arn:aws:rds:us-east-1:339712808883:cluster:auroratestscaling', 'Date': '2024-05-06T23:08:24.252Z', 'Message': 'Completed failover to DB instance: auroratestscaling-liqeq', 'SourceIdentifier': 'auroratestscaling', 'EventID': 'RDS-EVENT-0071', 'Tags': {'rds_scaling_low_instanceclass': 'db.t3.medium', 'rds_scaling_high_instanceclass': 'db.t3.large'}}}

@pytest.fixture()
def clusterStartedFailoverEvent():
  return {'version': '0', 'id': '82bf3a7b-43d7-95e6-db0a-0b97af305ac2', 'detail-type': 'RDS DB Cluster Event', 'source': 'aws.rds', 'account': '339712808883', 'time': '2024-05-06T23:07:45Z', 'region': 'us-east-1', 'resources': ['arn:aws:rds:us-east-1:339712808883:cluster:auroratestscaling'], 'detail': {'EventCategories': ['failover'], 'SourceType': 'CLUSTER', 'SourceArn': 'arn:aws:rds:us-east-1:339712808883:cluster:auroratestscaling', 'Date': '2024-05-06T23:07:45.884Z', 'Message': 'Started same AZ failover to DB instance: auroratestscaling-liqeq', 'SourceIdentifier': 'auroratestscaling', 'EventID': 'RDS-EVENT-0072', 'Tags': {'rds_scaling_low_instanceclass': 'db.t3.medium', 'rds_scaling_high_instanceclass': 'db.t3.large'}}}

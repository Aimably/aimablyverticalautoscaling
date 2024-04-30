import unittest
import datetime
import tzlocal
import boto3
from moto import mock_aws
from tests.unit.fixtures.aws import *
from tests.unit.fixtures.events import *
from verticalscaling.bluegreenscaling import *
import pytest

default_account = "123456789012"

@mock_aws
def test_start_blue_green_with_no_instances():
    ScalingOperation(ScalingAction.ScaleUp).Scale(["testscaling"])

@mock_aws
def test_start_blue_green_with_one_instance(createRdsDBInstance):
    ScalingOperation(ScalingAction.ScaleUp).Scale(["testscaling"])

@mock_aws
def test_tags_upper(scalingTags):
    instanceClass = ScalingOperation(ScalingAction.ScaleUp)._getScalingInstanceClassFromTags(scalingTags)
    assert instanceClass == "db.m5.large"

@mock_aws
def test_tags_down(scalingTags):
    instanceClass = ScalingOperation(ScalingAction.ScaleDown)._getScalingInstanceClassFromTags(scalingTags)
    assert instanceClass == "db.t2.micro"

@mock_aws
def test_no_change_same_instance_class(createRdsDBInstance):
    actions = ScalingOperation(ScalingAction.ScaleDown).Scale(["testscaling"])
    assert len(actions) == 1
    assert actions[0] == ScalingStatus.NoOp
    # Dammit BlueGreen hasn't been implemented.
    # response = boto3.client('rds').describe_blue_green_deployments()
    # assert len(response["BlueGreenDeployments"]) == 0

@mock_aws
def test_no_change_same_instance_class(createRdsDBInstanceNoTags):
    actions = ScalingOperation(ScalingAction.ScaleUp).Scale(["testscaling"])
    assert len(actions) == 1
    assert actions[0] == ScalingStatus.NoOp


class BlueGreenBrigde_No_Deployments:
    def __init__(self):
        pass

    def describe_blue_green_deployments(self, **kwargs):
        return { "BlueGreenDeployments": []}

    def create_blue_green_deployment(self, **kwargs):
        return {
            'BlueGreenDeployment': {
                'BlueGreenDeploymentIdentifier': 'testscaling-verticalscaling',
                'BlueGreenDeploymentName': 'testscaling-verticalscaling',
                'Source': f'aws:arn:rds:{default_account}:db:testscaling',
                'Target': f'aws:arn:rds:{default_account}:db:testscaling-dewfed',
                'Status': 'PROVISIONING',
            }
        }

    def switchover_blue_green_deployment(self, **kwargs):
        return {}

    def delete_blue_green_deployment(self, **kwargs):
        return {}


@mock_aws
def test_should_scale_up(createRdsDBInstance):
    actions = ScalingOperation(ScalingAction.ScaleUp, BlueGreenBrigde_No_Deployments()).Scale(["testscaling"])
    assert len(actions) == 1
    assert actions[0] == ScalingStatus.Started
    # Dammit BlueGreen hasn't been implemented.
    # response = boto3.client('rds').describe_blue_green_deployments()
    # assert len(response["BlueGreenDeployments"]) == 1

class BlueGreenBrigde_Deployments_Provisioning:
    def __init__(self):
        pass

    def describe_blue_green_deployments(self, **kwargs):
        return { 
            "BlueGreenDeployments": 
            [ 
                { 
                    'BlueGreenDeploymentIdentifier': 'testscaling-verticalscaling',
                    'BlueGreenDeploymentName': 'testscaling-verticalscaling',
                    'Source': f'aws:arn:rds:{default_account}:db:testscaling',
                    'Target': f'aws:arn:rds:{default_account}:db:testscaling-dewfed',
                    'Status': BlueGreenStatus.PROVISIONING
                }
            ]}

@mock_aws
def test_should_scale_up_inprogress(createRdsDBInstance):
    action = ScalingOperation(ScalingAction.ScaleUp, BlueGreenBrigde_Deployments_Provisioning()).Scale(["testscaling"])
    assert action == ScalingStatus.InProgress

class BlueGreenBrigde_Deployments_Available:
    def __init__(self):
        pass

    def describe_blue_green_deployments(self, **kwargs):
        return { 
            "BlueGreenDeployments": 
            [ 
                { 
                    'BlueGreenDeploymentIdentifier': 'testscaling-verticalscaling',
                    'BlueGreenDeploymentName': 'testscaling-verticalscaling',
                    'Source': f'arn:aws:rds:us-east-1:{default_account}:db:testscaling',
                    'Target': f'arn:aws:rds:us-east-1:{default_account}:db:testscaling-123',
                    'Status': BlueGreenStatus.AVAILABLE
                }
            ]}

    def switchover_blue_green_deployment(self, **kwargs):
        return {}

    def delete_blue_green_deployment(self, **kwargs):
        return {}

@mock_aws
def test_should_scale_up_available(createRdsDBInstance, createGreenRdsDBInstance):
    actions = ScalingOperation(ScalingAction.ScaleUp, BlueGreenBrigde_Deployments_Available()).Scale(["testscaling"])
    assert len(actions) == 1
    assert actions[0] == ScalingStatus.InProgress


class BlueGreenBrigde_Deployments_Inprogress:
    def __init__(self):
        pass

    def describe_blue_green_deployments(self, **kwargs):
        return { 
            "BlueGreenDeployments": 
            [ 
                { 
                    'BlueGreenDeploymentIdentifier': 'testscaling-verticalscaling',
                    'BlueGreenDeploymentName': 'testscaling-verticalscaling',
                    'Source': f'arn:aws:rds:us-east-1:{default_account}:db:testscaling',
                    'Target': f'arn:aws:rds:us-east-1:{default_account}:db:testscaling-123',
                    'Status': BlueGreenStatus.SWITCHOVER_IN_PROGRESS
                }
            ]}

    def switchover_blue_green_deployment(self, **kwargs):
        return {}

    def delete_blue_green_deployment(self, **kwargs):
        return {}

@mock_aws
def test_should_scale_up_inprogress(createRdsDBInstance, createGreenRdsDBInstance):
    actions = ScalingOperation(ScalingAction.ScaleUp, BlueGreenBrigde_Deployments_Inprogress()).Scale(["testscaling"])
    assert len(actions) == 1
    assert actions[0] == ScalingStatus.InProgress

class BlueGreenBrigde_Deployments_Cleanup:
    def __init__(self):
        pass

    def describe_blue_green_deployments(self, **kwargs):
        return { 
            "BlueGreenDeployments": 
            [ 
                { 
                    'BlueGreenDeploymentIdentifier': 'testscaling-verticalscaling',
                    'BlueGreenDeploymentName': 'testscaling-verticalscaling',
                    'Source': f'arn:aws:rds:us-east-1:{default_account}:db:testscaling',
                    'Target': f'arn:aws:rds:us-east-1:{default_account}:db:testscaling-123',
                    'Status': BlueGreenStatus.SWITCHOVER_COMPLETED
                }
            ]}

    def switchover_blue_green_deployment(self, **kwargs):
        return {}

    def delete_blue_green_deployment(self, **kwargs):
        return {}

@mock_aws
def test_should_scale_up_cleanup(createRdsDBInstance, createGreenRdsDBInstance):
    actions = ScalingOperation(ScalingAction.ScaleUp, BlueGreenBrigde_Deployments_Cleanup()).Scale(["testscaling"])
    assert len(actions) == 1
    assert actions[0] == ScalingStatus.Completed
    instances = boto3.client("rds").describe_db_instances()
    assert len(instances['DBInstances']) == 1

@mock_aws
def test_should_test_args(createRdsDBInstance, createGreenRdsDBInstance):
    actions = ScalingOperation(ScalingAction.ScaleUp).Scale(["testscaling"])
    assert len(actions) == 1
    assert actions[0] == ScalingStatus.NoOp

class BlueGreenBrigde_Deployments_RealResponses:
    def __init__(self):
        pass

    def describe_blue_green_deployments(self, **kwargs):
        #return {}
        return {
            'BlueGreenDeployments': 
                [
                    {
                        'BlueGreenDeploymentIdentifier': 'bgd-2pwkjlqr026ji9gs', 
                        'BlueGreenDeploymentName': 'testscaling-bovuq', 
                        'Source': f'arn:aws:rds:us-east-1:{default_account}:db:testscaling-old1', 
                        'Target': f'arn:aws:rds:us-east-1:{default_account}:db:testscaling', 
                        'SwitchoverDetails': [{'SourceMember': f'arn:aws:rds:us-east-1:{default_account}:db:testscaling-old1', 'TargetMember': f'arn:aws:rds:us-east-1:{default_account}:db:testscaling', 'Status': 'SWITCHOVER_COMPLETED'}], 'Tasks': [{'Name': 'CREATING_READ_REPLICA_OF_SOURCE', 'Status': 'COMPLETED'}, {'Name': 'READ_REPLICA_SCALE_COMPUTE', 'Status': 'COMPLETED'}, {'Name': 'CONFIGURE_BACKUPS', 'Status': 'COMPLETED'}], 
                        'Status': 'SWITCHOVER_COMPLETED', 
                        #'CreateTime': datetime.datetime(2024, 4, 29, 21, 46, 51, 130000, tzinfo=tzlocal()), 
                        'TagList': [{'Key': 'rds_vertical_scaling_bluegreen', 'Value': 'TRUE'}]
                    }
                ],
            'ResponseMetadata': {'RequestId': '60b5741f-a32e-4795-ae77-edfaccf470de', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': '60b5741f-a32e-4795-ae77-edfaccf470de', 'strict-transport-security': 'max-age=31536000', 'content-type': 'text/xml', 'content-length': '1332', 'date': 'Mon, 29 Apr 2024 22:38:15 GMT'}, 'RetryAttempts': 0}
        }

    def switchover_blue_green_deployment(self, **kwargs):
        return {}

    def delete_blue_green_deployment(self, **kwargs):
        return {}

@mock_aws
def test_should_update_bluegreen(createRdsDBInstance, createGreenRdsDBInstance):
    actions = ScalingOperation(ScalingAction.ScaleUp, BlueGreenBrigde_Deployments_RealResponses()).Scale(["testscaling"])
    assert len(actions) == 1


if __name__ == '__main__':
    unittest.main()
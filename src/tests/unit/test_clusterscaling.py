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
import unittest
import datetime
import tzlocal
import boto3
from moto import mock_aws
from tests.unit.fixtures.aws import *
from tests.unit.fixtures.events import *
from verticalscaling.scaling import *
import pytest

default_account = "123456789012"

@mock_aws
def test_start_cluster_readreplica():
    actions = ScalingOperation(ScalingAction.ScaleUp).ScaleClusters(["testclusterscaling"])
    assert len(actions) == 1
    assert actions[0] == "none"

@mock_aws
def test_start_cluster_readreplica_one_instance_No_Tags(createRdsClusterInstanceNoTags):
    actions = ScalingOperation(ScalingAction.ScaleUp).ScaleClusters(["testclusterscaling"])
    assert len(actions) == 1
    assert actions[0] == "none"

@mock_aws
def test_start_cluster_readreplica_one_instance(createRdsClusterInstance):
    actions = ScalingOperation(ScalingAction.ScaleUp).ScaleClusters(["testclusterscaling"])
    assert len(actions) == 1
    assert actions[0] == ScalingStatus.InProgress

def test_aurora_scaling_tag_false():
    assert ScalingOperation(ScalingAction.ScaleUp)._isAuroraReadOnlyInstance([{ 'Key': 'rds_scaling_low_instanceclass', 'Value': 'db.t2.micro'}]) == False
    assert ScalingOperation(ScalingAction.ScaleUp)._isAuroraReadOnlyInstance([{ 'Key': ScalingTag.AuroraScalingTag, 'Value': AuroraTagValue.Original_Writer}]) == False
    
def test_aurora_scaling_tag_true():
    assert ScalingOperation(ScalingAction.ScaleUp)._isAuroraReadOnlyInstance([{ 'Key': ScalingTag.AuroraScalingTag, 'Value': AuroraTagValue.Read_Replica}]) == True
    
@mock_aws
def test_start_cluster_readreplica_one_instance(createRdsClusterInstanceMultipleInstances):
    actions = ScalingOperation(ScalingAction.ScaleUp).ScaleClusters(["testclusterscaling"])
    assert len(actions) == 1
    assert actions[0] == ScalingStatus.InProgress

@mock_aws
def test_scale_cluster_from_instance_event(createRdsClusterInstanceMultipleInstances):
    actions = ScalingOperation(ScalingAction.ScaleUp).ScaleInstances(["testclusterscaling-instance"])
    assert len(actions) == 1
    assert actions[0] == ScalingStatus.NoOp

class FailoverBridge:
    def failover_db_cluster(self, **kwargs):
        return {}

@mock_aws
def test_scale_cluster_remove_tags_from_instances(createRdsClusterInstanceMultipleInstancesAtEnd):
    actions = ScalingOperation(ScalingAction.ScaleUp, FailoverBridge()).ScaleInstances(["testclusterscaling-instance"])
    assert len(actions) == 1
    assert actions[0] == ScalingStatus.InProgress

@mock_aws
def test_scale_cluster_remove_tags_from_instances_reader(createRdsClusterInstanceMultipleInstancesAtEnd):
    actions = ScalingOperation(ScalingAction.ScaleUp, FailoverBridge()).ScaleInstances(["testclusterscaling-instance2"])
    assert len(actions) == 1
    assert actions[0] == ScalingStatus.InProgress

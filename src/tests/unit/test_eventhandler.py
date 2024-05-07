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
from moto import mock_aws
from verticalscaling.event_handler import EventHandler
from tests.unit.fixtures.aws import *
from tests.unit.fixtures.events import *
from verticalscaling.consts import *

@mock_aws
def test_event_handler_alarm(cloudwatchAlarm, createAlarmScaleDown):
    event = EventHandler(cloudwatchAlarm)
    assert event.region == 'us-east-1'
    assert event.isAlarm() == True
    assert event.isEventBridge() == False
    instances = event.getDBInstances()
    assert len(instances)> 0
    assert instances[0] == 'testscaling'
    assert event.getAction() == ScalingAction.ScaleDown
    assert event.isValid()

def test_event_handler_eventbridge(eventBridgeRdsInstanceEvent):
    event = EventHandler(eventBridgeRdsInstanceEvent)
    assert event.region == 'us-east-1'
    assert event.isAlarm() == False
    assert event.isEventBridge() == True
    instances = event.getDBInstances()
    assert len(instances)> 0
    assert instances[0] == 'testscaling'
    assert event.getAction() == 'none'
    assert event.isValid()

def test_event_handler_custom(userScaleUp):
    event = EventHandler(userScaleUp)
    assert event.region == 'us-east-1'
    assert event.isAlarm() == False
    assert event.isEventBridge() == False
    instances = event.getDBInstances()
    assert len(instances)> 0
    assert instances[0] == 'testscaling'
    assert event.getAction() == 'scaleup'
    assert event.isValid()

def test_event_handler_custom_without_instances(userScaleUpNoInstances):
    event = EventHandler(userScaleUpNoInstances)
    assert event.isValid() == False

def test_default_console(consoleDefaultEvent):
    event = EventHandler(consoleDefaultEvent)
    assert not event.isValid()

def test_deletion_event(rdsDeletionEvent):
    event = EventHandler(rdsDeletionEvent)
    assert event.isValid() == True
    assert event.isCluster() == False

def test_bluegreen_event(blueGreenEvent):
    event = EventHandler(blueGreenEvent)
    assert event.isValid() == True
    assert event.isAlarm() == False
    assert event.isEventBridge() == True
    assert event.isBlueGreen() == True

def test_bluegreen_event_deletion(blueGreenEventDeletion):
    event = EventHandler(blueGreenEventDeletion)
    assert event.isValid() == False
    assert event.isAlarm() == False
    assert event.isEventBridge() == True
    assert event.isBlueGreen() == True

#Cluster Tests
def test_aurora_cluster_event_stopped(auroraClusterStoppedEvent):
    event = EventHandler(auroraClusterStoppedEvent)
    assert event.isValid() == True
    assert event.isCluster() == True

def test_aurora_cluster_user_event(userClusterScaleUp):
    event = EventHandler(userClusterScaleUp)
    assert event.isValid() == True
    assert event.isCluster() == True
    clusters = event.getClusters()
    assert len(clusters)> 0
    assert clusters[0] == 'testclusterscaling'
    assert event.getAction() == 'scaleup'

def test_aurora_cluster_failover_started_event(clusterStartedFailoverEvent):
    event = EventHandler(clusterStartedFailoverEvent)
    assert event.isValid() == True
    assert event.isCluster() == True
    assert event.getAction() == ScalingAction.Failover

def test_aurora_cluster_failover_finished_event(clusterFailoverCompletedEvent):
    event = EventHandler(clusterFailoverCompletedEvent)
    assert event.isValid() == True
    assert event.isCluster() == True
    assert event.getAction() == ScalingAction.Failover

if __name__ == '__main__':
  unittest.main()
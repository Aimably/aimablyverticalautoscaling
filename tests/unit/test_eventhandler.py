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

def test_bluegreen_event(blueGreenEvent):
    event = EventHandler(blueGreenEvent)
    assert event.isValid() == True
    assert event.isAlarm() == False
    assert event.isEventBridge() == False
    assert event.isBlueGreen() == True

def test_bluegreen_event_deletion(blueGreenEventDeletion):
    event = EventHandler(blueGreenEventDeletion)
    assert event.isValid() == False
    assert event.isAlarm() == False
    assert event.isEventBridge() == False
    assert event.isBlueGreen() == True

if __name__ == '__main__':
  unittest.main()
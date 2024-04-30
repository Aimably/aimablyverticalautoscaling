import unittest
import boto3
from moto import mock_aws
from tests.unit.fixtures.aws import *
from tests.unit.fixtures.events import *
import lambda_function
import verticalscaling.bluegreenscaling

@mock_aws
def test_lambda_handler_alarm(cloudwatchAlarm):
  ret = lambda_function.lambda_handler(cloudwatchAlarm, "")

@mock_aws
def test_lambda_handler_rdsinstance(eventBridgeRdsInstanceEvent):
  ret = lambda_function.lambda_handler(eventBridgeRdsInstanceEvent, "")

@mock_aws
def test_lambda_handler_user(userScaleUp):
  ret = lambda_function.lambda_handler(userScaleUp, "")

@mock_aws
def test_lambda_handler_default(consoleDefaultEvent):
  ret = lambda_function.lambda_handler(consoleDefaultEvent, "")

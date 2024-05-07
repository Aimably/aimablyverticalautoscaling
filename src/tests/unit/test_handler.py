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
import boto3
from moto import mock_aws
from tests.unit.fixtures.aws import *
from tests.unit.fixtures.events import *
import lambda_function
import verticalscaling.scaling

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

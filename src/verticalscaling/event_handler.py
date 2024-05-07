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
import boto3
from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent
from aws_lambda_powertools.utilities.data_classes import cloud_watch_alarm_event
from verticalscaling.tags import *
from verticalscaling.consts import *
from verticalscaling.log import *

class EventHandler:
    def __init__(self, event):
        try:
            self.valid = False
            self.action = ScalingAction.NoOp

            if event['source']:
                if event['source'] == EventSource.CloudWatch:
                    log_info(f"Received CloudWatch event: {event}")
                    self._cloudwatch_alarm_event(event)
                    
                if event['source'] == EventSource.RDS:
                    log_info(f"Received RDSInstance event: {event}")
                    self._rdsevent(event)
                
                if event['source'] == EventSource.Custom:
                    log_info(f"Received Custom event: {event}")
                    self._customevent(event)

        except KeyError:
            log_error(f"Received an unknown event: {event}")
            self.valid = False
            self.action = ScalingAction.NoOp

        except AttributeError:
            log_error(f"Received an unknown event: {event}")
            self.valid = False
            self.action = ScalingAction.NoOp

        except Exception as e:
            self.valid = False
            self.action = ScalingAction.NoOp
            log_exception(e)        

    def _customevent(self, event):
        self.type = 'custom'

        try:
            self.action = event['action']
            try:
                self.instances = event['instances']
                self.subtype = 'instance'
            except KeyError:
                self.instances = []

            try:
                self.clusters = event['clusters']
                self.subtype = 'cluster'
            except KeyError:
                self.clusters = []

            self.region = event['region']
            self.valid = True

        except KeyError:
            log_debug(f"action, instances or region not specified in event: {event}")
            self.instances = []

        except AttributeError:
            log_debug(f"No instances specified in event: {event}")
            self.instances = []

    def _rdsevent(self, event):
        self.event = EventBridgeEvent(event)
        self.valid = True
        self.subtype = "instance"
        self.type = 'eventbridge'
        
        if "Blue Green" in self.event.detail_type:
            self.subtype = 'bluegreen'
            # Check for our tag.
            try:
                self.valid = self.event.detail["Tags"][ScalingTag.BlueGreenTag] == "TRUE"
                    
            except (StopIteration, AttributeError, KeyError):
                self.valid = False
        
        elif "DB Cluster" in self.event.detail_type:
            self.subtype = 'cluster'
            if 'failover' in self.event.detail['Message']:
                self.action = ScalingAction.Failover
        
        self.region = self.event.region
        self.action = ScalingAction.NoOp
        self.instances = []
        self.instancearns = []
        self.clusters = []

        message = self.event.detail["Message"]

        if 'failover' in message:
            self.action = ScalingAction.Failover
        
        if "deleted" not in message:
            for resource in self.event.resources:
                if self.subtype == 'cluster':
                    self.clusters.append(resource)
                else:
                    self.instancearns.append(resource)
                    self.instances.append(resource.split(':')[-1])

    def _cloudwatch_alarm_event(self, event):
        self.event = cloud_watch_alarm_event.CloudWatchAlarmEvent(event)
        self.type = 'alarm'
        self.region = self.event.region
        self.alarm_name = self.event.alarm_data.alarm_name
        self.valid = True

        self.instances = []
        for metric in self.event.alarm_data.configuration.metrics:
            self.instances.append(metric.metric_stat.metric['dimensions']['DBInstanceIdentifier'])
                        
        try:
            client = boto3.client('cloudwatch')
            response = client.list_tags_for_resource(ResourceARN=self.event.alarm_arn)
            self._processTags(response['Tags'])
        except Exception as e:
            self.action = ScalingAction.NoOp   
    
    def _processTags(self, tags):
        for tag in tags:
            if tag['Key'] == ScalingTag.AlertActionTag:
                value = tag["Value"]
                if value == "down":
                    self.action = ScalingAction.ScaleDown
                elif value == "up":
                    self.action = ScalingAction.ScaleUp
                else:
                    self.action = ScalingAction.NoOp
    
    def isValid(self):
        return self.valid
    
    def isAlarm(self):
        return self.type == 'alarm'

    def isEventBridge(self):
        return self.type == 'eventbridge'

    def isBlueGreen(self):
        return self.type == 'eventbridge' and self.subtype == 'bluegreen'

    def isCluster(self):
        return (self.type in ['eventbridge', 'custom']) and self.subtype == 'cluster'
    
    def getDBInstances(self):
        return self.instances

    def getClusters(self):
        return self.clusters

    def getAction(self):
        return self.action

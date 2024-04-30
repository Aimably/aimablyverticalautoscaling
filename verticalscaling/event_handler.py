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
            self.instances = event['instances']
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
        
        if "Blue Green" in self.event.detail_type:
            self.type = 'bluegreen'
            # Check for our tag.
            try:
                self.valid = self.event.detail["Tags"][ScalingTag.BlueGreenTag] == "TRUE"
                    
            except (StopIteration, AttributeError, KeyError):
                self.valid = False
            
        else:
            self.type = 'eventbridge'

        self.region = self.event.region
        self.action = ScalingAction.NoOp
        self.instances = []

        message = self.event.detail["Message"]
        
        if "deleted" not in message:
            for resource in self.event.resources:
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
        return self.type == 'bluegreen'
    
    def getDBInstances(self):
        return self.instances

    def getAction(self):
        return self.action

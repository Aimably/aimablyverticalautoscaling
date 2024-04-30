import json
import logging
import boto3
from botocore.exceptions import ClientError
from verticalscaling.event_handler import *
from verticalscaling.bluegreenscaling import * 
from verticalscaling.log import *

def lambda_handler(event, context):
    try:
        log_debug(f'Event: {event}')
        event_handler = EventHandler(event)

        if event_handler.isValid():
            operation = ScalingOperation(event_handler.getAction())

            if event_handler.isBlueGreen():
                # If the BlueGreen deployment is ready, deploy it!
                operation.Deploy(event_handler.getDBInstances())
            else:
                # Perform a scaling operation if needed, and move the progress of the BlueGreen deployment
                # if one is in motion.
                operation.Scale(event_handler.getDBInstances())
        else:
            log_debug(f'Invalid event: {event}')
           
    except ClientError as e:
        log_error(e)
        return {
            'statusCode': 500,
            'body': json.dumps(event)
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }

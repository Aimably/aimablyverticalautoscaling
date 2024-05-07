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
from botocore.exceptions import ClientError
from verticalscaling.event_handler import *
from verticalscaling.scaling import * 
from verticalscaling.log import *

def lambda_handler(event, context):
    try:
        log_info(f'Event: {event}')
        event_handler = EventHandler(event)

        if event_handler.isValid():
            operation = ScalingOperation(event_handler.getAction())

            if event_handler.isBlueGreen():
                # If the BlueGreen deployment is ready, deploy it!
                operation.Deploy(event_handler.getDBInstances())

            elif event_handler.isCluster():
                # Use the read relplica scaling operation to scale the clusters.
                operation.ScaleClusters(event_handler.getClusters())

            else:
                # Perform a scaling operation if needed, and move the progress of the BlueGreen deployment
                # if one is in motion.
                operation.ScaleInstances(event_handler.getDBInstances())
        else:
            log_debug(f'Invalid event: {event}')
           
    except ClientError as e:
        log_error(e)
        raise
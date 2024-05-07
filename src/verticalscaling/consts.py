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
class EventSource(object):
    __slots__ = ()
    CloudWatch = "aws.cloudwatch"
    RDS = "aws.rds"
    Custom = "custom"

class ScalingAction(object):
    __slots__ = ()
    ScaleUp = "scaleup"
    ScaleDown = "scaledown"
    NoOp = "none"
    Failover = "failover"

class ScalingStatus(object):
    __slots__ = ()
    NoOp = "none"
    InProgress = "inprogress"
    Completed = "completed"
    Started = "started"

class BlueGreenStatus(object):
    __slots__ = ()
    PROVISIONING = "PROVISIONING"
    AVAILABLE = "AVAILABLE"
    SWITCHOVER_IN_PROGRESS = "SWITCHOVER_IN_PROGRESS"
    INVALID_CONFIGURATION = "INVALID_CONFIGURATION"
    SWITCHOVER_FAILED = "SWITCHOVER_FAILED"
    DELETING = "DELETING"
    SWITCHOVER_COMPLETED = "SWITCHOVER_COMPLETED"

   
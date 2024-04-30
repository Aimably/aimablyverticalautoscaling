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

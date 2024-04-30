import logging
import boto3
from verticalscaling.tags import *
from verticalscaling.consts import *
from verticalscaling.log import *
from verticalscaling.random import *

class BlueGreenBrigde:
    def __init__(self):
        self.client = boto3.client('rds')

    def describe_blue_green_deployments(self, **kwargs):
        return self.client.describe_blue_green_deployments(**kwargs)

    def create_blue_green_deployment(self, **kwargs):
        return self.client.create_blue_green_deployment(**kwargs)

    def switchover_blue_green_deployment(self, **kwargs):
        return self.client.switchover_blue_green_deployment(**kwargs)

    def delete_blue_green_deployment(self, **kwargs):
        return self.client.delete_blue_green_deployment(**kwargs)

class ScalingOperation:
    def __init__(self, action, bluegreenbridge = BlueGreenBrigde()):
        self.action = action
        self.client = boto3.client('rds')
        self.bluegreenbridge = bluegreenbridge

    def Scale(self, instances):
        results = []
        try:
            if len(instances) == 0:
                log_info("No instances to scale")
                return []
            
            for instance in instances:
                try:
                    results.append(self._scaleInstance(instance))
                except Exception as e:
                    log_exception(e)

        except Exception as e:
            log_exception(e)
        
        return results
        
    def Deploy(self, instances):
        results = []
        try:
            if len(instances) == 0:
                log_info("No instances to deploy")
                return []
            
            for instance in instances:
                try:
                    results.append(self._deployBlueGreenInstance(instance))
                except Exception as e:
                    log_exception(e)

        except Exception as e:
            log_exception(e)
        
        return results
        
    def _scaleInstance(self, instance):
        result = ScalingStatus.NoOp
        try:
            log_debug(f'Checking instance {instance}')

            # Is the instance running.
            dbinstances = self.client.describe_db_instances(DBInstanceIdentifier=instance)
            
            if (len(dbinstances['DBInstances']) > 0):
                dbinstance = dbinstances['DBInstances'][0]
                instanceClass = dbinstance['DBInstanceClass']

                log_info(f'The instance \'{instance}\' is \'{dbinstance['DBInstanceStatus']}\'')

                if dbinstance['DBInstanceStatus'] == 'available':
                    try:
                        if self.action != ScalingAction.NoOp:
                            instanceClass = self._getScalingInstanceClassFromTags(dbinstance["TagList"])
                            
                            if (dbinstance['DBInstanceClass'] == instanceClass):
                                log_info(f'Instance {instance} already in {instanceClass} state')
                                self.action = ScalingAction.NoOp
                            else:
                                log_info(f'Scaling {instance} to {instanceClass}')
                            
                    except (StopIteration,KeyError):
                        log_error(f'Instance {instance} has no scaling tag. Please add tags {ScalingTag.LowerInstanceClass} and {ScalingTag.UpperInstanceClass} to specify the instance classes to scale to.')

                    # Check for bluegreen deployment, there might be an old Blue Green still around.
                    result = self._checkBlueGreenDeployment(instance, dbinstance, instanceClass)
                      
                elif dbinstance['DBInstanceStatus'] == 'modifying':
                    result = self._checkBlueGreenDeployment(instance, dbinstance, instanceClass)
                      
                elif dbinstance['DBInstanceStatus'] == 'switching-over':
                    result = ScalingStatus.InProgress

                elif dbinstance['DBInstanceStatus'] == 'configuring-enhanced-monitoring':
                    result = ScalingStatus.InProgress
                    
                elif dbinstance['DBInstanceStatus'] == 'deleting':
                    result = ScalingStatus.InProgress
                     
                else:
                    log_info(f'Instance {instance} not running')
                    
            else:
                log_error(f'Instance {instance} not found')
                return

        except Exception as e:
            log_info(f'Error scaling instance {instance}')
            log_exception(e)
        
        return result

    def _checkBlueGreenDeployment(self, instance, dbinstance, instanceClass):
        result = ScalingStatus.NoOp

        # Check for bluegreen deployment, there might be an old Blue Green still around.
        response = self.bluegreenbridge.describe_blue_green_deployments()

        if len(response['BlueGreenDeployments']) > 0:
            try:
                deployment = next(deployment for deployment in response['BlueGreenDeployments'] if deployment['Target'].split(':')[-1] == dbinstance["DBInstanceIdentifier"] or deployment['Source'].split(':')[-1] == dbinstance["DBInstanceIdentifier"])

                log_info(f'BlueGreen deployment found for {instance} with a status of {deployment['Status']}')

                # If the deployment is available then check the dbinstance.                                  
                if deployment['Status'] == BlueGreenStatus.AVAILABLE:
                    newdatabase = deployment['Target'].split(':')[-1]
                    newdbinstance = self.client.describe_db_instances(DBInstanceIdentifier=newdatabase)

                    if len(newdbinstance['DBInstances']) > 0:
                        # We need to add the old tags to the new database.
                        tags = list(filter(lambda x: x['Key'].startswith("rds_"), dbinstance["TagList"]))
                        
                        self.client.add_tags_to_resource(
                            ResourceName=deployment['Target'],
                            Tags=tags
                            )
                        
                        if newdbinstance['DBInstances'][0]['DBInstanceStatus'] == 'available':
                            self._switchOverDeployment(deployment)

                    result = ScalingStatus.InProgress

                elif deployment['Status'] == BlueGreenStatus.SWITCHOVER_IN_PROGRESS:
                    log_info(f'Switchover in progress for {instance}')
                    result = ScalingStatus.InProgress

                elif deployment['Status'] == BlueGreenStatus.SWITCHOVER_COMPLETED:
                    self._cleanupDeployment(instance, deployment)
                    result = ScalingStatus.Completed

            except (StopIteration, AttributeError):
                log_error(f'BlueGreen deployment not found for {instance}')
                            
        else:
            if self.action != ScalingAction.NoOp:
                #Initiate a new BlueGreenDeployment with the instanceClass
                createresponse = self.bluegreenbridge.create_blue_green_deployment(
                                    BlueGreenDeploymentName=dbinstance["DBInstanceIdentifier"] + "-" + randomString(),
                                    Source=dbinstance["DBInstanceArn"],
                                    TargetDBInstanceClass=instanceClass,
                                    UpgradeTargetStorageConfig=False,
                                    Tags=[{ 'Key': ScalingTag.BlueGreenTag, 'Value': 'TRUE' }]
                                    )
                result = ScalingStatus.Started
                
        return result

    def _deployBlueGreenInstance(self, instance):
        result = ScalingStatus.NoOp

        log_info(f'Deploying BlueGreen instance {instance}')

        response = self.bluegreenbridge.describe_blue_green_deployments(
            BlueGreenDeploymentIdentifier=instance
        )

        if len(response['BlueGreenDeployments']) > 0:
            try:
                deployment = response['BlueGreenDeployments'][0]
                status = deployment['Status']

                if status == BlueGreenStatus.AVAILABLE:
                    log_info(f'Switching BlueGreen instance {instance}')
                    self._switchOverDeployment(deployment)
                    result = ScalingStatus.InProgress

                elif status == BlueGreenStatus.SWITCHOVER_IN_PROGRESS:
                    result = ScalingStatus.InProgress

                elif status == BlueGreenStatus.SWITCHOVER_COMPLETED:
                    self._cleanupDeployment(instance, deployment)
                    result = ScalingStatus.InProgress

            except (StopIteration, AttributeError):
                log_error(f'BlueGreen deployment not found {instance}')
        
        return result

    def _switchOverDeployment(self, deployment):
        self.bluegreenbridge.switchover_blue_green_deployment(
                        BlueGreenDeploymentIdentifier=deployment['BlueGreenDeploymentIdentifier'],
                        SwitchoverTimeout=300
                        )

    def _cleanupDeployment(self, instance, deployment):
        log_info(f'Switchover completed for {instance}')
        olddatabase = deployment['Source'].split(':')[-1]
        self.bluegreenbridge.delete_blue_green_deployment(
                        BlueGreenDeploymentIdentifier=deployment['BlueGreenDeploymentIdentifier'],
                        DeleteTarget=False
                        )
        self.client.delete_db_instance(
                        DBInstanceIdentifier=olddatabase,
                        SkipFinalSnapshot=True,
                        DeleteAutomatedBackups=False
                        )
    
    def _getScalingInstanceClassFromTags(self, tags):
        if self.action == ScalingAction.ScaleUp:
            tag = next(item for item in tags if item['Key'] == ScalingTag.UpperInstanceClass)
            return tag["Value"]
        elif self.action == ScalingAction.ScaleDown:
            tag = next(item for item in tags if item['Key'] == ScalingTag.LowerInstanceClass)
            return tag["Value"]

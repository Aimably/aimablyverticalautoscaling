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
import datetime
from botocore.exceptions import *
from verticalscaling.tags import *
from verticalscaling.consts import *
from verticalscaling.log import *
from verticalscaling.random import *
from verticalscaling.rds_bridge import *
from verticalscaling.exceptions import *

use_monitoring_as_trigger_to_scale = True

class ScalingOperation:
    def __init__(self, action, rdsbridge = RDSBridge()):
        self.action = action
        self.client = boto3.client('rds')
        self.rdsbridge = rdsbridge

    def ScaleClusters(self, clusters):
        results = []
        try:
            if len(clusters) == 0:
                log_info("No clusters to scale")
                return []

            for cluster in clusters:
                try:
                    if self.action == ScalingAction.Failover:
                        results.append(self._checkCluster(cluster))
                    else:
                        results.append(self._scaleCluster(cluster))

                except Exception as e:
                    log_exception(e)

        except Exception as e:
            log_exception(e)

        return results

    def ScaleInstances(self, instances):
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

                if self._isAuroraReadOnlyInstance(dbinstance['TagList']):
                    log_info(f'Instance {instance} is read only replica.')
                    result = self._scale_rds_instance_for_cluster(instance, dbinstance)
                elif 'DBClusterIdentifier' in dbinstance and len(dbinstance['DBClusterIdentifier']) > 0:
                    log_info(f'Instance {instance} is part of a cluster.')
                    result = self._scale_rds_instance_for_cluster(instance, dbinstance)
                else:
                    result = self._scale_rds_instance(instance, dbinstance)
                    
            else:
                log_error(f'Instance {instance} not found')
                return

        except Exception as e:
            log_info(f'Error scaling instance {instance}')
            log_exception(e)
        
        return result

    def _scale_rds_instance(self, instance, dbinstance):
        result = ScalingStatus.NoOp
        instanceClass = "none"
        
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

        return result

    def _checkBlueGreenDeployment(self, instance, dbinstance, instanceClass):
        result = ScalingStatus.NoOp

        # Check for bluegreen deployment, there might be an old Blue Green still around.
        response = self.rdsbridge.describe_blue_green_deployments()

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
                createresponse = self.rdsbridge.create_blue_green_deployment(
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

        response = self.rdsbridge.describe_blue_green_deployments(
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
        self.rdsbridge.switchover_blue_green_deployment(
                        BlueGreenDeploymentIdentifier=deployment['BlueGreenDeploymentIdentifier'],
                        SwitchoverTimeout=300
                        )

    def _cleanupDeployment(self, instance, deployment):
        log_info(f'Switchover completed for {instance}')
        olddatabase = deployment['Source'].split(':')[-1]
        self.rdsbridge.delete_blue_green_deployment(
                        BlueGreenDeploymentIdentifier=deployment['BlueGreenDeploymentIdentifier'],
                        DeleteTarget=False
                        )
        self.client.delete_db_instance(
                        DBInstanceIdentifier=olddatabase,
                        SkipFinalSnapshot=True,
                        DeleteAutomatedBackups=False
                        )
    
    def _getScalingInstanceClassFromTags(self, tags):
        try:
            if self.action == ScalingAction.ScaleUp:
                tag = next(item for item in tags if item['Key'] == ScalingTag.UpperInstanceClass)
                return tag["Value"]
            elif self.action == ScalingAction.ScaleDown:
                tag = next(item for item in tags if item['Key'] == ScalingTag.LowerInstanceClass)
                return tag["Value"]
            elif self.action == ScalingAction.NoOp:
                return ScalingAction.NoOp
            else:
                log_info(f'Invalid scaling action specified, please use \'{ScalingAction.ScaleUp}\' or \'{ScalingAction.ScaleDown}\'.')
                raise InvalidScalingAction()
        except (StopIteration) as e:
            raise MissingTagsOnDatabase()

    def _checkCluster(self, cluster):
        result = ScalingStatus.NoOp

        try:
            log_info(f'Checking cluster {cluster}')
            
            response = self.client.describe_db_clusters(DBClusterIdentifier=cluster)
            if (len(response['DBClusters']) > 0):
                dbcluster = response['DBClusters'][0]
                status = dbcluster['Status']
                if status == 'available':
                    try:                    
                        if len(dbcluster['DBClusterMembers']) > 0:
                            writer = next(d for d in dbcluster['DBClusterMembers'] if d['IsClusterWriter'] == True)
                            dbinstances = self.client.describe_db_instances(DBInstanceIdentifier=writer['DBInstanceIdentifier'])
                            
                            if (len(dbinstances['DBInstances']) > 0):
                                dbwriterinstance = dbinstances['DBInstances'][0]
                                if self._isClusterAlreadyScaling(dbwriterinstance) == False:
                                    if dbwriterinstance['DBInstanceStatus'] == 'available':
                                        if self._hasInstanceFallenOver(dbwriterinstance):
                                            # We are at the last stage of the scaling.  We just need to remove the tags.
                                            self.client.remove_tags_from_resource(
                                                ResourceName=dbwriterinstance['DBInstanceArn'],
                                                TagKeys=[ScalingTag.AuroraScalingTag, ScalingTag.AuroraScalingTargetTag]
                                            )
                                            result = ScalingStatus.Completed

                                    else:
                                        log_info(f'Instance {writer["DBInstanceIdentifier"]} not in an available state. Currently in \'{dbwriterinstance['DBInstanceStatus']}\'')
                                        result = ScalingStatus.NoOp

                                else:
                                    log_info(f'Instance {writer["DBInstanceIdentifier"]} is already scaling.')
                                    result = ScalingStatus.NoOp
                            
                            result = ScalingStatus.InProgress
                        else:
                            log_info(f'Cluster {cluster} has multiple instances, unable to scale it.')
                            result = ScalingStatus.NoOp

                    except (MissingTagsOnDatabase):
                        log_info(f'Tags missing from {cluster}, no action will be performed.')
                        result = ScalingStatus.NoOp
                
                else:
                    log_info(f'Cluster {cluster} is in state {status}.')

        except (InvalidScalingAction):
            result = ScalingStatus.NoOp
            
        except (ClientError) as e:
            if e.response['Error']['Code'] == 'DBClusterNotFoundFault':
                log_info(f'Cluster {cluster} not found')
            else:
                log_exception(e)
                
        except (Exception) as e:
            log_exception(e)

        return result

    # Scale The Aurora cluster using a read replica promotion.
    def _scaleCluster(self, cluster):
        result = ScalingStatus.NoOp
        
        try:
            log_info(f'Scaling cluster {cluster}')
            
            # Check to see if there is a read replica.
            response = self.client.describe_db_clusters(DBClusterIdentifier=cluster)
            if (len(response['DBClusters']) > 0):
                dbcluster = response['DBClusters'][0]
                status = dbcluster['Status']
                if status == 'available':
                    try:                    
                        instanceClass = self._getScalingInstanceClassFromTags(dbcluster["TagList"])

                        if len(dbcluster['DBClusterMembers']) > 0:
                            writer = next(d for d in dbcluster['DBClusterMembers'] if d['IsClusterWriter'] == True)
                            dbinstances = self.client.describe_db_instances(DBInstanceIdentifier=writer['DBInstanceIdentifier'])
                            
                            if (len(dbinstances['DBInstances']) > 0):
                                dbwriterinstance = dbinstances['DBInstances'][0]
                                if self._isClusterAlreadyScaling(dbwriterinstance) == False:
                                    if dbwriterinstance['DBInstanceStatus'] == 'available':
                                        if self._hasInstanceFallenOver(dbwriterinstance):
                                            # We are at the last stage of the scaling.  We just need to remove the tags.
                                            self.client.remove_tags_from_resource(
                                                ResourceName=dbwriterinstance['DBInstanceArn'],
                                                TagKeys=[ScalingTag.AuroraScalingTag, ScalingTag.AuroraScalingTargetTag]
                                            )
                                            result = ScalingStatus.Completed

                                        else:
                                            if dbwriterinstance['DBInstanceClass'] != instanceClass:
                                                log_info(f'Scaling {cluster} from writer {writer["DBInstanceIdentifier"]} with class {instanceClass}')
                                                
                                                self.client.add_tags_to_resource(
                                                    ResourceName=dbwriterinstance['DBInstanceArn'],
                                                    Tags=[{ 'Key': ScalingTag.AuroraScalingTag, 'Value': AuroraTagValue.Original_Writer },
                                                        { 'Key': ScalingTag.AuroraScalingTargetTag, 'Value': instanceClass }]
                                                    )

                                                replicaIdentifier = dbcluster['DBClusterIdentifier'] + "-" + randomString()
                                                log_info(f'Creating read replica of {replicaIdentifier} on {dbcluster['DBClusterIdentifier']}')

                                                self.client.create_db_instance(
                                                    DBClusterIdentifier=dbcluster['DBClusterIdentifier'],
                                                    DBInstanceIdentifier=replicaIdentifier,
                                                    DBInstanceClass=instanceClass,
                                                    AvailabilityZone=dbwriterinstance['AvailabilityZone'],
                                                    Engine=dbcluster['Engine'],
                                                    MonitoringInterval=0,
                                                    Tags=[
                                                        { 'Key': ScalingTag.AuroraScalingTag, 'Value': AuroraTagValue.Read_Replica },
                                                        { 'Key': ScalingTag.AuroraScalingTargetTag, 'Value': instanceClass }
                                                    ]
                                                )

                                                result = ScalingStatus.Started
                                            
                                            else:
                                                log_info(f'Instance {writer["DBInstanceIdentifier"]} already in the correct class.')
                                                result = ScalingStatus.NoOp

                                    else:
                                        log_info(f'Instance {writer["DBInstanceIdentifier"]} not in an available state. Currently in \'{dbwriterinstance['DBInstanceStatus']}\'')
                                        result = ScalingStatus.NoOp

                                else:
                                    log_info(f'Instance {writer["DBInstanceIdentifier"]} is already scaling.')
                                    result = ScalingStatus.NoOp
                            
                            result = ScalingStatus.InProgress
                        else:
                            log_info(f'Cluster {cluster} has multiple instances, unable to scale it.')
                            result = ScalingStatus.NoOp

                    except (MissingTagsOnDatabase):
                        log_info(f'Tags missing from {cluster}, no action will be performed.')
                        result = ScalingStatus.NoOp
                
                elif status == 'stopped':
                    log_info(f'Cluster {cluster} is stopped, unable to scale it.')

                elif status == 'starting':
                    log_info(f'Cluster {cluster} is starting, please wait for it to start.')
                    
                elif status == 'failing-over':
                    log_info(f'Cluster {cluster} is failing over.')

                else:
                    log_info(f'Cluster {cluster} is in state {status}.  No scaling can be performed at this time.')

        except (InvalidScalingAction):
            result = ScalingStatus.NoOp
            
        except (ClientError) as e:
            if e.response['Error']['Code'] == 'DBClusterNotFoundFault':
                log_info(f'Cluster {cluster} not found')
            else:
                log_exception(e)
                
        except (Exception) as e:
            log_exception(e)

        return result

    def _isAuroraReadOnlyInstance(self, tags):
        result = False
        try:
            tag = next(item for item in tags if item['Key'] == ScalingTag.AuroraScalingTag)
            result = tag['Value'] == AuroraTagValue.Read_Replica
        
        except (StopIteration, KeyError) as e:
            result = False

        return result
    
    def _scale_rds_aurora_instance(self, instance, dbinstance):
        log_info(f'Instance {instance} in state {dbinstance['DBInstanceStatus']}')

        if dbinstance['DBInstanceStatus'] == 'available':
            result = ScalingStatus.NoOp
                     
        elif dbinstance['DBInstanceStatus'] == 'modifying':
            result = ScalingStatus.InProgress
                     
        elif dbinstance['DBInstanceStatus'] == 'switching-over':
            result = ScalingStatus.InProgress

        elif dbinstance['DBInstanceStatus'] == 'configuring-enhanced-monitoring':
            result = ScalingStatus.InProgress
                    
        elif dbinstance['DBInstanceStatus'] == 'deleting':
            result = ScalingStatus.InProgress

        else:
            log_info(f'Instance {instance} not running')

        return result

    def _scale_rds_instance_for_cluster(self, instance, dbinstance):
        result = ScalingStatus.NoOp

        if dbinstance['DBInstanceStatus'] == 'available':
            if self._isClusterAlreadyScaling(dbinstance):
                result = self._promote_read_replica(dbinstance)
            elif self._hasInstanceFallenOver(dbinstance):
                log_info(f'Instance {instance} has fallen over, dealing with it')
                targetInstanceClass = self._getTargetInstanceClass(dbinstance)
                if dbinstance['DBInstanceClass'] != targetInstanceClass:
                    self.client.delete_db_instance(
                        DBInstanceIdentifier=instance
                    )
                else:
                    self.client.remove_tags_from_resource(
                        ResourceName=dbinstance['DBInstanceArn'],
                        TagKeys=[ScalingTag.AuroraScalingTag, ScalingTag.AuroraScalingTargetTag]
                    )
                result = ScalingStatus.Completed
            else:
                result = ScalingStatus.NoOp
                                     
        elif dbinstance['DBInstanceStatus'] == 'modifying':
            result = ScalingStatus.InProgress
                     
        elif dbinstance['DBInstanceStatus'] == 'switching-over':
            result = ScalingStatus.InProgress

        elif dbinstance['DBInstanceStatus'] == 'configuring-enhanced-monitoring':
            if use_monitoring_as_trigger_to_scale:
                # Unfortuntely it seems we don't get a callback when the instance is available.  So we'll need to wait this state to change.
                # This seems to have been fixed. 5/6/2024.  Added a flag to turn it back on if it becomes an issue.
                log_info(f'Waiting for instance {instance} to be available')
                waiter = self.client.get_waiter('db_instance_available')
                
                try:
                    r = waiter.wait(
                        DBInstanceIdentifier=instance,
                        WaiterConfig={
                            'Delay': 5,
                            'MaxAttempts': 200
                        }
                    )

                    log_info(f'Promoting read replica of instance {instance} to be writer')
                    result = self._promote_read_replica(dbinstance)
                except (WaiterError) as e:
                    log_exception(e)
            else:
                log_info(f'Instance {instance} is still setting up')
                    
        elif dbinstance['DBInstanceStatus'] == 'deleting':
            result = ScalingStatus.InProgress

        else:
            log_info(f'Instance {instance} not running')

        return result

    def _getClusterStatus(self, cluster):
        result = None
        try:
            response = self.client.describe_db_clusters(DBClusterIdentifier=cluster)
            if (len(response['DBClusters']) > 0):
                dbcluster = response['DBClusters'][0]
                result = dbcluster['Status']

        except (ClientError) as e:
            if e.response['Error']['Code'] == 'DBClusterNotFoundFault':
                log_info(f'Cluster {cluster} not found')
            else:
                log_exception(e)

        return result

    # Failover the writer to the read replica.  But only do it if the Cluster is in an available state.
    def _promote_read_replica(self, dbinstance):
        result = ScalingStatus.NoOp
        try:
            self._setupInstanceForFailover(dbinstance)
            cluster = dbinstance["DBClusterIdentifier"]
            status = self._getClusterStatus(cluster)
            if status == 'available':
                self.rdsbridge.failover_db_cluster(
                    DBClusterIdentifier=dbinstance["DBClusterIdentifier"],
                    TargetDBInstanceIdentifier=dbinstance["DBInstanceIdentifier"]
                )
            elif status == 'failing-over':
                log_info(f'Cluster {cluster} is already failing over.')
            else:
                log_info(f'Cluster {cluster} is not available. Status {status}')
                    
            result = ScalingStatus.InProgress
            
        except (ClientError) as e:
            if e.response['Error']['Code'] == 'InvalidDBInstanceStateFault':
                log_info(f'Instance {dbinstance["DBInstanceIdentifier"]} not in an available state. Currently in \'{dbinstance["DBInstanceStatus"]}\'')
            else:
                log_exception(e)
            result = ScalingStatus.NoOp

        return result

    def _isClusterAlreadyScaling(self, dbinstance):
        result = False
        
        try:
            tag = next(item for item in dbinstance['TagList'] if item['Key'] == ScalingTag.AuroraScalingTag)
            result = tag['Value'] == AuroraTagValue.Original_Writer or tag['Value'] == AuroraTagValue.Read_Replica

        except (StopIteration, KeyError) as e:
            result = False
            
        return result
    
    def _setupInstanceForFailover(self, dbinstance):
        # Change the reader and writer to Failing over.
        response = self.client.describe_db_clusters(DBClusterIdentifier=dbinstance["DBClusterIdentifier"])
        if (len(response['DBClusters']) > 0):
            dbcluster = response['DBClusters'][0]
            writer = next(d for d in dbcluster['DBClusterMembers'] if d['IsClusterWriter'] == True)
            dbinstances = self.client.describe_db_instances(DBInstanceIdentifier=writer['DBInstanceIdentifier'])
            if len(dbinstances['DBInstances']) > 0:
                dbwriterinstance = dbinstances['DBInstances'][0]
                self.client.add_tags_to_resource(
                    ResourceName=dbwriterinstance['DBInstanceArn'],
                    Tags=[{ 'Key': ScalingTag.AuroraScalingTag, 'Value': AuroraTagValue.FailingOver }]
                )
            else:
                log_info(f'Instance {writer["DBInstanceIdentifier"]} not found')
        else:
            log_info(f'Cluster {dbinstance["DBClusterIdentifier"]} not found')

        self.client.add_tags_to_resource(
            ResourceName=dbinstance['DBInstanceArn'],
            Tags=[{ 'Key': ScalingTag.AuroraScalingTag, 'Value': AuroraTagValue.FailingOver }]
        )
    
    def _hasInstanceFallenOver(self, dbinstance):
        result = False
        
        try:
            tag = next(item for item in dbinstance['TagList'] if item['Key'] == ScalingTag.AuroraScalingTag)
            result = tag['Value'] == AuroraTagValue.FailingOver

        except (StopIteration, KeyError) as e:
            result = False
            
        return result
    
    def _getTargetInstanceClass(self, dbinstance):
        result = dbinstance['DBInstanceClass']
        
        try:
            tag = next(item for item in dbinstance['TagList'] if item['Key'] == ScalingTag.AuroraScalingTargetTag)
            result = tag['Value']

        except (StopIteration, KeyError) as e:
            pass
            
        return result
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
from verticalscaling.log import *

"""
_summary_ : RDSBridge class
_description_ : The Moto RDS mock client hasn't implemented all of the RDS functionality.  We need
to abstract the RDS calls so we don't get NotImplementedExceptions.  This class is the bridge to the 
real RDS client.

Returns:
    _type_: _description_
"""
class RDSBridge:
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
    
    def failover_db_cluster(self, **kwargs):
        return self.client.failover_db_cluster(**kwargs)

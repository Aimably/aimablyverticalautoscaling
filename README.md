# Aimably Vertical Autoscaling

Aimably RDS Vertical Autoscaling is a script-based tool that can automatically increase or decrease the capacity and performance capabilities of RDS instances in response to external factors, such as user demand.

Aimably RDS Vertical Autoscaling includes an AWS Lambda Function that uses AWS Blue/Green Deployment to facilitate vertical autoscaling of RDS instances. The function is triggered based on EventBridge events, which can be triggered by CloudWatch alarms configured to track your chosen performance metrics. 

For example, you configure a CloudWatch alarm to alert when the CPU of the RDS instance is below 10% for a specific time period, this can be configured to trigger the Aimably RDS Vertical Autoscaling function to scale down to a lower and less expensive instance class. Conversely, you can configure a CloudWatch alarm to alert if the database CPU is at 90% for a specific period of time, which can trigger the Aimably RDS Vertical Autoscaling function to scale up to a higher and more expensive instance class. This enables you to have the correct instance class based on performance, thereby avoiding expensive overprovisioned databases.

## Best Practices
Utilization Pattern Review: Because RDS was not built for vertical autoscaling by default, it is important to become familiar with the utilization patterns of each of your databases to select the best parameters for the Aimably RDS Vertical Autoscaling function.
This data is readily available in the Monitoring tab of a database in the RDS console.  You can use the standard CloudWatch monitoring or the newer Enhanced Monitoring that is available. You may adjust the reporting time between 1 hour and 15 months to use this data to understand the periods where peak performance is required. 


## Metric Selection: 
Every database experiences performance constraints unique to its workload. Select the metrics that become most constrained in order to achieve the best results. 
Commonly used metrics for an RDS database are CPU Utilization, Database Connections, Freeable Memory, or Read/Write Latency. You can read more in-depth on the various metrics that can be used for an alarm in this support article, AWS CloudWatch/RDS Recommended Alarms.
Threshold Selection: RDS Blue/Green Deployments take an average of 30 minutes or more to complete, which can cause performance issues if thresholds are selected that require immediate results. Select alert thresholds that predict the need for capacity rather than require immediate capacity. 
In the event of highly predictable traffic patterns, you may also choose to configure events in EventBridge to follow a set schedule instead of using CloudWatch alarms. You can read more in-depth on EventBridge scheduling in this support article, Creating an EventBridge Rule That Runs on a Schedule.
Sizing Selection: The Aimably RDS Vertical Autoscaling function requires that you select two specific instance classes, one to service the lower demand and one to service the higher demand. Make sure to review historical capacity demands and select the instance classes that best represent your needs in both scenarios, ensuring the higher class is not triggered too frequently due to demand on the lower class and that the lower class is not excessively overprovisioned so as to keep costs high.
Users may choose to adjust the function to support more than two instance classes.

## Prerequisites
- You need administrator access to your AWS organization
- Your database must make use of Self Managed credential management instead of AWS Secrets Manager
- Aimably RDS Instance Vertical Autoscaling is compatible with Amazon RDS for MySQL, Amazon RDS for PostgreSQL, and Amazon RDS for MariaDB. It is not compatible with Amazon RDS Aurora.

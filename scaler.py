#!/usr/bin/python
from boto.regioninfo import RegionInfo
from boto.ec2.autoscale import LaunchConfiguration
from boto.ec2.autoscale import AutoScalingGroup
from boto.ec2.elb import HealthCheck
from boto.ec2.autoscale import ScalingPolicy
from boto.ec2.cloudwatch import MetricAlarm
import requests
import time

aws_access_key_id=""
aws_secret_access_key=""
def DEBUG(str):
    if 1:
        print str
#-----------------------------------Creating a security group------------------------#
def create_security_group(conn):
	DEBUG("STEP 1:Creating Security group..")
	flag =0
	security_groups = conn.get_all_security_groups()
	for security_group in security_groups:    
	    if security_group.name == "security1":
	         flag =1
	         break
	if flag!=1:
	        # Create security group
	        myscgroup = conn.create_security_group('security1', 'Project 2.2')
	        myscgroup.authorize('tcp', 80, 80, '0.0.0.0/0')
	        myscgroup.authorize('tcp', 22, 22, '0.0.0.0/0')


#----------------------------------Create ELB( Elastic Load Balancer)------------------#
def create_elb():
	DEBUG("STEP 2:Creating Load Balancer..")
	try:
	conn = ELBConnection()	
	requiredzone = ['us-east-1a']
	requiredport = [(80, 80, 'http')]
	lb = conn.create_load_balancer('MyELB', requiredzone, requiredport)
	hc = HealthCheck(
	        interval=20,
	        healthy_threshold=3,
	        unhealthy_threshold=5,
	        target='HTTP:80/heartbeat'
	        )
	lb.configure_health_check(hc)
	DEBUG(Load balancer(DNS) +"= "+lb.dns_name)
	except:
		DEBUG("STEP 2:Exception Occured")
	return lb.dns_name

def create_lc_as_su_sd_alarm():
#------------------------------------------Create LC( Launch Configuration)------------------------------------------#
	DEBUG("STEP 3:Creating Launch Configuration..")

	try:
		lc = LaunchConfiguration(name='P22LaunchConfig', image_id='ami-7c0a4614',
		                             key_name='project',
		                             instance_type='m3.medium',
		                             instance_monitoring=True,
		                             security_groups=['security1'])
		conn = AutoScaleConnection()
		conn.create_launch_configuration(lc)
		DEBUG("STEP 3Launch Config created" +"= " +lc.name)
	except:
		DEBUG("STEP 3:Exception Occured")
	
	#------------------------------------------Auto Scaling Creation----------------------------------------------------#
	DEBUG("STEP 4:Creating Auto Scaling Group..")
	try:
		project_tag = Tag(key='Project',value = '2.2',propagate_at_launch=True,resource_id="P22ASG")
		dc_tag = Tag(key='Name',value = 'Data Center',propagate_at_launch=True,resource_id="P22ASG")	
		ag = AutoScalingGroup(group_name='P22ASG', load_balancers=['MyELB'], launch_config='P22LaunchConfig', 
			                          availability_zones=requiredzone, min_size=1, desired_capacity=2, max_size=2)
		create_or_update_tags(project_tag)
		create_or_update_tags(dc_tag)
		conn.create_auto_scaling_group(ag)
		DEBUG("STEP 4:P22ASG Name ="+ag.name)
	except:		
		DEBUG("STEP 4:Exception Occured")
	#-----------------------------------------Scale Policy---------------------------------------------------------------#
	DEBUG("STEP 5:Creating Scale Out/In Policy..")
	try:
	scale_up_policy = ScalingPolicy(
	        name='scale_up', adjustment_type='ChangeInCapacity',
	        as_name='P22ASG', scaling_adjustment=1, cooldown=180)
	scale_down_policy = ScalingPolicy(
	        name='scale_down', adjustment_type='ChangeInCapacity',
	        as_name='P22ASG', scaling_adjustment=-1, cooldown=180)
	conn.create_scaling_policy(scale_up_policy)
	conn.create_scaling_policy(scale_down_policy)
	scale_up_policy = autoscale.get_all_policies(
	            as_group='P22ASG', policy_names=['scale_up'])[0]
	scale_down_policy = autoscale.get_all_policies(
	            as_group='P22ASG', policy_names=['scale_down'])[0]
	except:		
		DEBUG("STEP 5:Exception Occured")
	#------------------------------------------Alarm-----------------------------------------------------------------------#
	DEBUG("STEP 6:Creating Alarm..")
	try:
	cloudwatch = boto.ec2.cloudwatch.connect_to_region('us-east-1')
	alarm_dimensions = {"AutoScalingGroupName": 'P22ASG'}
	scale_up_alarm = MetricAlarm(
	            name='scale_up_on_cpu', namespace='AWS/EC2',
	            metric='CPUUtilization', statistic='Average',
	            comparison='>', threshold='70',
	            period='60', evaluation_periods=2,
	            alarm_actions=[scale_up_policy.policy_arn],
	            dimensions=alarm_dimensions)
	cloudwatch.create_alarm(scale_up_alarm)
	scale_down_alarm = MetricAlarm(
	            name='scale_down_on_cpu', namespace='AWS/EC2',
	            metric='CPUUtilization', statistic='Average',
	            comparison='<', threshold='40',
	            period='60', evaluation_periods=2,
	            alarm_actions=[scale_down_policy.policy_arn],
	            dimensions=alarm_dimensions)
	cloudwatch.create_alarm(scale_down_alarm)
	except:		
		DEBUG("STEP 6:Exception Occured")
   

######################################################################################################
#------------------------------------------Main code-------------------------------------------------#
######################################################################################################       
To be written
	


	
 

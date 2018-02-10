#!/usr/bin/env python

import rospy
from geometry_msgs.msg import PoseStamped
from mavros_msgs.srv import CommandBool
from mavros_msgs.srv import SetMode
from mavros_msgs.msg import State

current_state = State()

def state_cb(updated_state):
	current_state = updated_state
	pass

def main():

	rospy.init_node('offb_node_python', anonymous = True)
	# Subscribe to relavant channels
	state_sub = rospy.Subscriber('mavros/state', State, state_cb, queue_size=10)
	local_pos_pub = rospy.Publisher('mavros/setpoint_position/local', PoseStamped, queue_size=10)

	# Connect to arming client
	rospy.wait_for_service('mavros/cmd/arming')
	try:
		arming_client = rospy.ServiceProxy('mavros/cmd/arming', CommandBool)
	except rospy.ServiceException, e:
		rospy.logerr("Service call failed: %s", e)

	# Connect to setmode client
	rospy.wait_for_service('mavros/setmode');
	try:
		set_mode_client = rospy.ServiceProxy('mavros/setmode', SetMode)
	except rospy.ServiceException, e:
		rospy.logerr("Service call failed: %s", e)

	rate = rospy.Rate(20.0)

	# Wait for connected state
	while not rospy.is_shutdown() and not current_state.connected:
		print current_state.connected
		rate.sleep()

	pose = PoseStamped()
	pose.pose.position.x = 0
	pose.pose.position.y = 0
	pose.pose.position.z = 2

	# Send some sample values before starting
	for x in range(0,100):
		if rospy.is_shutdown():
			break
		
		local_pos_pub.publish(pose);
		rate.sleep()

	offb_set_mode = SetMode();
	offb_set_mode.request.custom_mode = "GUIDED"

	arm_cmd = CommandBool()
	arm_cmd.request.value = True

	last_request = rospy.get_rostime()

	# Start main loop here
	while not rospy.is_shutdown():
		if current_state != "GUIDED" and (rospy.get_rostime() - last_request > rospy.Time(5)):
			if set_mode_client.call(offb_set_mode) and offb_set_mode.respose.mode_sent:
				rospy.loginfo("Offboard enabled")
			last_request = rospy.get_rostime()

		else:
			if not current_state.armed and (rospy.get_rostime() - last_request > rospy.Time(5)):
				if arming_client.call(arm_cmd) and arm_cmd.response.armed:
					rospy.loginfo("Vehicle armed")
				last_request = rospy.get_rostime()

		local_pose_pub.publish(pose)
		rate.sleep()

	return 0

if __name__ == '__main__':	
	try:
		main()
	except rospy.ROSInterruptException:
		pass
	

#!/usr/bin/env python
"""Generic PID implimentation."""
import rospy
from geometry_msgs.msg import Twist
from std_msgs.msg import Empty
from std_msgs.msg import Float64
from drone_application.msg import pid_error
from ardrone_autonomy.msg import Navdata
from visualization_msgs.msg import Marker
import numpy as np
import time

pubx = rospy.Publisher('plot_x', Float64, queue_size=5)
puby = rospy.Publisher('plot_y', Float64, queue_size=5)
pubz = rospy.Publisher('plot_z', Float64, queue_size=5)
pub_yaw = rospy.Publisher('plot_yaw', Float64, queue_size=5)

error_pub = rospy.Publisher('pid_error', pid_error, queue_size=5)


def pid(data, set_array, state):
    """Run one step of PID.

    convention in which to send data:
    data[0] = x-axis (+ve is front)
    data[1] = y-axis (-ve is left)
    data[2] = z-axis (+ve is up)
    data[3] = yaw (+ve is counter-clockwise

    convention in which to send data for aruco_mapping:
    data[0] = x-axis (positive values always and front is less is front)
    data[1] = y-axis (-ve is left)
    data[2] = z-axis (+ve is up)
    data[3] = yaw (+ve is counter-clockwise

    Args:
        data (numpy.array): current pose of the drone
        set_array (numpy.array): pose to attain
        state (dict): storing all the values to be used in every call to pid

    Returns:
        geometry_msgs.msg.Twist: twist to be published to cmd_vel for drone
        dict: storing all the values to be used in every call to pid
    """
    current_time = time.time()
    dt = current_time - state['last_time']

    error = set_array - np.array([data[0], data[1], data[2], data[3]])
    error = np.around(error, decimals=2)

    # publish errors for plotting.
    pubx.publish(error[0])
    puby.publish(error[1])
    pubz.publish(error[2])
    pub_yaw.publish(error[3])

    error_pub.publish(error)

    state['integral'] += error * dt
    state['derivative'] = (error - state['lastError']) / dt

    f = state['p'] * error + state['i'] * \
        state['integral'] + state['d'] * state['derivative']

    state['lastError'] = error
    state['last_time'] = current_time

    twist = Twist()
    f = np.clip(f, -0.5, 0.5)

    # converting from world frame to drone frame
    twist.linear.x = (f[0] * np.cos(error[3])) - (f[1] * np.sin(error[3]))
    twist.linear.y = (f[1] * np.cos(error[3])) + (f[0] * np.sin(error[3]))
    twist.linear.z = f[2]
    twist.angular.z = f[3]
    return twist, state

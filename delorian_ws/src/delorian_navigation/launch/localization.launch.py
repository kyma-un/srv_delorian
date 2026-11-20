# EKF (robot_localization): ruedas (vx) + IMU (vyaw) -> /odometry/filtered y TF odom -> base_footprint.
#   ros2 launch delorian_navigation localization.launch.py
# Requiere la simulación con odom_tf:=false, para que la TF del DiffDrive no compita con esta.
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    ekf_file = os.path.join(get_package_share_directory('delorian_navigation'),
                            'config', 'ekf.yaml')
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),

        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[ekf_file, {'use_sim_time': use_sim_time}],
        ),
    ])

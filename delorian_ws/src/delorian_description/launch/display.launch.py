# Visualiza el Delorian en RViz (sin Gazebo) para validar mallas, frames y ruedas.
#   ros2 launch delorian_description display.launch.py
#   ros2 launch delorian_description display.launch.py gui:=false
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg = get_package_share_directory('delorian_description')
    xacro_file = os.path.join(pkg, 'urdf', 'delorian.urdf.xacro')
    rviz_file = os.path.join(pkg, 'rviz', 'display.rviz')

    gui = LaunchConfiguration('gui')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file, ' sim:=false']), value_type=str)

    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true',
                              description='Sliders para mover las ruedas a mano'),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
        ),
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            condition=IfCondition(gui),
        ),
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            condition=UnlessCondition(gui),
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_file],
        ),
    ])

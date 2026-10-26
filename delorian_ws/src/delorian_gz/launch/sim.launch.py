# Lanza el Delorian en Gazebo (gz sim) con el puente a ROS 2.
#   ros2 launch delorian_gz sim.launch.py
#   ros2 launch delorian_gz sim.launch.py world:=empty.sdf rviz:=false
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument,
                            IncludeLaunchDescription, SetEnvironmentVariable)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    desc_pkg = get_package_share_directory('delorian_description')
    gz_pkg = get_package_share_directory('delorian_gz')
    ros_gz_sim_pkg = get_package_share_directory('ros_gz_sim')

    xacro_file = os.path.join(desc_pkg, 'urdf', 'delorian.urdf.xacro')
    rviz_file = os.path.join(desc_pkg, 'rviz', 'display.rviz')
    bridge_file = os.path.join(gz_pkg, 'config', 'bridge.yaml')

    world = LaunchConfiguration('world')
    rviz = LaunchConfiguration('rviz')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file, ' sim:=true']), value_type=str)

    return LaunchDescription([
        DeclareLaunchArgument('world', default_value=os.path.join(gz_pkg,'worlds','delorian.sdf'),
                              description='Mundo de gz sim (archivo .sdf)'),
        DeclareLaunchArgument('rviz', default_value='true',
                              description='Abrir RViz junto a Gazebo'),

        # Para que gz resuelva package://delorian_description/meshes/...
        AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH', os.path.dirname(desc_pkg)),

        # gz-transport se anuncia por la primera interfaz que no sea lo, y si le toca
        # el wifi los procesos de gz no se ven entre si: la ventana sale en negro y
        # `create` se queda pidiendo mundos. Forzar loopback, que todo corre local.
        SetEnvironmentVariable('GZ_IP', '127.0.0.1'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(ros_gz_sim_pkg, 'launch', 'gz_sim.launch.py')),
            launch_arguments={'gz_args': ['-r ', world]}.items(),
        ),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description,
                         'use_sim_time': True}],
        ),

        Node(
            package='ros_gz_sim',
            executable='create',
            arguments=['-topic', 'robot_description', '-name', 'delorian', '-z', '0.05'],
        ),

        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{'config_file': bridge_file, 'use_sim_time': True}],
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_file],
            parameters=[{'use_sim_time': True}],
            condition=IfCondition(rviz),
        ),
    ])

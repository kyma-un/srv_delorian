# Nav2 sobre el mapa de rtabmap: navegar mientras se mapea.
#   Terminal 1: ros2 launch delorian_gz sim.launch.py odom_tf:=false rviz:=false
#   Terminal 2: ros2 launch delorian_navigation mapping.launch.py
#   Terminal 3: ros2 launch delorian_navigation navigation.launch.py
# En RViz: botón "2D Goal Pose", clic y arrastrar sobre el mapa para dar el objetivo.
# Sin amcl ni map_server: el mapa (/rtabmap/map) y la TF map -> odom los da rtabmap.
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    nav_pkg = get_package_share_directory('delorian_navigation')
    nav2_pkg = get_package_share_directory('nav2_bringup')
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('params_file',
                              default_value=os.path.join(nav_pkg, 'config', 'nav2_params.yaml')),
        DeclareLaunchArgument('rviz', default_value='true',
                              description='RViz con la vista de Nav2 (mapa, costmaps, ruta)'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(nav2_pkg, 'launch', 'navigation_launch.py')),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'params_file': LaunchConfiguration('params_file'),
                'autostart': 'true',
            }.items(),
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', os.path.join(nav2_pkg, 'rviz', 'nav2_default_view.rviz')],
            parameters=[{'use_sim_time': use_sim_time}],
            # La vista de Nav2 espera el mapa en /map
            remappings=[('/map', '/rtabmap/map')],
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])

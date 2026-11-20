# Mapeo con rtabmap: EKF (odom -> base_footprint) + rtabmap SLAM (map -> odom, mapa 2D).
#   Terminal 1: ros2 launch delorian_gz sim.launch.py odom_tf:=false
#   Terminal 2: ros2 launch delorian_navigation mapping.launch.py
#   Terminal 3: ros2 run teleop_twist_keyboard teleop_twist_keyboard
# Mapa 2D en /rtabmap/map (OccupancyGrid); base de datos en ~/.ros/rtabmap.db
# (se borra al arrancar; nuevo:=false para continuar un mapa anterior).
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    nav_pkg = get_package_share_directory('delorian_navigation')
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('nuevo', default_value='true',
                              description='true = borrar ~/.ros/rtabmap.db y empezar un mapa nuevo'),
        DeclareLaunchArgument('rtabmap_viz', default_value='false',
                              description='Abrir la interfaz de rtabmap'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(nav_pkg, 'launch', 'localization.launch.py')),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
        ),

        Node(
            package='rtabmap_slam',
            executable='rtabmap',
            namespace='rtabmap',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'frame_id': 'base_footprint',
                'map_frame_id': 'map',
                # Sin tópico de odometría: la toma de la TF odom -> base_footprint (EKF)
                'odom_frame_id': 'odom',
                'subscribe_rgb': True,
                'subscribe_depth': True,
                'approx_sync': True,
                'approx_sync_max_interval': 0.05,
                'wait_for_transform': 0.2,
                # Robot terrestre: grafo en x, y, yaw
                'Reg/Force3DoF': 'true',
                # Nodo nuevo cada 10 cm o ~6°
                'RGBD/LinearUpdate': '0.1',
                'RGBD/AngularUpdate': '0.1',
                # Mapa 2D a partir de la profundidad de la OAK-D
                'Grid/Sensor': '1',
                # Profundidad lejana = más ruido = falsos obstáculos
                'Grid/RangeMax': '3.0',
                # Suelo/obstáculo solo por altura: < 5 cm suelo, 5 cm..1.5 m obstáculo.
                # Las normales (por defecto) con el ruido de la profundidad marcan suelo
                # como obstáculo. Asume suelo plano; con terreno irregular, revisar.
                'Grid/NormalsSegmentation': 'false',
                'Grid/MaxGroundHeight': '0.05',
                'Grid/MaxObstacleHeight': '1.5',
                'Grid/RayTracing': 'true',
                'Grid/3D': 'false',
            }],
            remappings=[
                ('rgb/image', '/oak/rgb/image_raw'),
                ('depth/image', '/oak/depth/image_raw'),
                ('rgb/camera_info', '/oak/rgb/camera_info'),
            ],
            arguments=[PythonExpression(["'-d' if '", LaunchConfiguration('nuevo'), "' == 'true' else ''"])],
        ),

        Node(
            package='rtabmap_viz',
            executable='rtabmap_viz',
            namespace='rtabmap',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'frame_id': 'base_footprint',
                'odom_frame_id': 'odom',
                'subscribe_rgb': True,
                'subscribe_depth': True,
                'approx_sync': True,
            }],
            remappings=[
                ('rgb/image', '/oak/rgb/image_raw'),
                ('depth/image', '/oak/depth/image_raw'),
                ('rgb/camera_info', '/oak/rgb/camera_info'),
            ],
            condition=IfCondition(LaunchConfiguration('rtabmap_viz')),
        ),
    ])

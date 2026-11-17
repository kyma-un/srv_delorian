# Abre solo RViz para mirar un robot que ya está corriendo (la simulación o el real),
# en esta máquina o en otra de la red. No lanza robot_state_publisher ni nada más.
#   ros2 launch delorian_description rviz.launch.py               # robot y TF, liviano
#   ros2 launch delorian_description rviz.launch.py camara:=true  # + imagen y nube de puntos
#   ros2 launch delorian_description rviz.launch.py use_sim_time:=false  # robot real
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    rviz_dir = os.path.join(get_package_share_directory('delorian_description'), 'rviz')

    camara = LaunchConfiguration('camara')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # liviano.rviz = display.rviz sin Image ni PointCloud2: la imagen y la nube no pasan
    # bien por la red (ver docs/remoto.md)
    rviz_file = PythonExpression([
        "'", os.path.join(rviz_dir, 'display.rviz'), "' if '", camara, "' == 'true' else '",
        os.path.join(rviz_dir, 'liviano.rviz'), "'"])

    return LaunchDescription([
        DeclareLaunchArgument('camara', default_value='false',
                              description='true = mostrar también imagen y nube de puntos'),
        DeclareLaunchArgument('use_sim_time', default_value='true',
                              description='Reloj de la simulación (false con el robot real)'),

        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_file],
            parameters=[{'use_sim_time': use_sim_time}],
        ),
    ])

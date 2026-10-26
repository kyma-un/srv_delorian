from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false', description='Use simulation (Gazebo) clock if true'),

        Node(
            package='rtabmap_odom',
            executable='rgbd_odometry',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'frame_id': 'base_footprint',
                'odom_frame_id': 'odom',
                # El DiffDrive (y luego robot_localization) ya publica odom -> base_footprint
                'publish_tf': False,
                'approx_sync': True,
                'approx_sync_max_interval': 0.01,
                # Robot terrestre: solo x, y, yaw
                'Reg/Force3DoF': 'true',
            }],
            remappings=[
                ('rgb/image', '/oak/rgb/image_raw'),
                ('depth/image', '/oak/depth/image_raw'),
                ('rgb/camera_info', '/oak/rgb/camera_info'),
                ('odom', '/odom'),
            ],
        ),
    ])
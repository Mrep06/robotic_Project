import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction 
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node

def generate_launch_description():

    package_name='articubot_one' 

    # 1. Robot State Publisher
    rsp = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory(package_name),'launch','rsp.launch.py'
                )]), launch_arguments={'use_sim_time': 'true'}.items()
    )

    # 2. Gazebo (เพิ่ม launch_arguments บังคับใช้ use_sim_time ให้ตรงกับโหนดอื่นๆ)
    gazebo = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')]),
                launch_arguments={'use_sim_time': 'true'}.items() 
             )

    # 3. Spawn Entity
    spawn_entity = Node(package='gazebo_ros', executable='spawn_entity.py',
                        arguments=['-topic', 'robot_description',
                                   '-entity', 'robot779_1',
                                   '-x', '-5.142680',
                                   '-y', '-5.211670',
                                   '-z', '0.1',
                                   '-Y', '1.57'],
                        output='screen')

    # 4. Joint State Broadcaster (รอ 3 วินาทีหลังเริ่ม)
    delayed_joint_state_broadcaster_spawner = TimerAction(
        period=3.0,
        actions=[
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=["joint_state_broadcaster"],
            )
        ]
    )

    # 5. Arm Controller (รอ 5 วินาทีเพื่อให้ชัวร์ว่า Broadcaster มาแล้ว)
    delayed_arm_controller_spawner = TimerAction(
        period=5.0,
        actions=[
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=["arm_controller"],
            )
        ]
    )

    return LaunchDescription([
        rsp,
        gazebo,
        spawn_entity,
        delayed_joint_state_broadcaster_spawner,
        delayed_arm_controller_spawner,
    ])
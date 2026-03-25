from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="vision_perception",
            executable="event_action_bridge",
            name="event_action_bridge",
            output="screen",
        ),
    ])

"""Launch mock_event_publisher for frontend development."""
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="vision_perception",
            executable="mock_event_publisher",
            name="mock_event_publisher",
            output="screen",
        ),
    ])

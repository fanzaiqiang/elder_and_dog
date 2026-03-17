"""Minimal launch file for face_perception package.

Usage:
  ros2 launch face_perception face_perception.launch.py
  ros2 launch face_perception face_perception.launch.py headless:=false
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory("face_perception")
    default_config = os.path.join(pkg_dir, "config", "face_perception.yaml")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "config_file",
                default_value=default_config,
                description="Path to face_perception config YAML",
            ),
            Node(
                package="face_perception",
                executable="face_identity_node",
                name="face_identity_node",
                parameters=[LaunchConfiguration("config_file")],
                output="screen",
            ),
        ]
    )

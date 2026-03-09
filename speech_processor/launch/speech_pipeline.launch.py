from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare



def generate_launch_description() -> LaunchDescription:
    params_file = LaunchConfiguration("params_file")
    enable_vad = LaunchConfiguration("enable_vad")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "params_file",
                default_value=PathJoinSubstitution(
                    [FindPackageShare("speech_processor"), "config", "speech_processor.yaml"]
                ),
                description="Path to speech processor parameter file",
            ),
            DeclareLaunchArgument(
                "enable_vad",
                default_value="true",
                description="Launch vad_node together with stt_intent_node",
            ),
            Node(
                package="speech_processor",
                executable="vad_node",
                name="vad_node",
                output="screen",
                parameters=[params_file],
                condition=IfCondition(enable_vad),
            ),
            Node(
                package="speech_processor",
                executable="stt_intent_node",
                name="stt_intent_node",
                output="screen",
                parameters=[params_file],
            ),
        ]
    )

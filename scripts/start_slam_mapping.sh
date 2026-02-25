#!/usr/bin/env zsh

set -euo pipefail

if [ -z "${ZSH_VERSION:-}" ]; then
  exec /usr/bin/env zsh "$0" "$@"
fi

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
WORKSPACE_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)

export ROBOT_IP="${ROBOT_IP:-192.168.123.161}"
export CONN_TYPE="${CONN_TYPE:-webrtc}"
export GO2_LIDAR_DECODER="${GO2_LIDAR_DECODER:-wasm}"
export LIDAR_POINT_STRIDE="${LIDAR_POINT_STRIDE:-8}"

if ! ping -c 1 "$ROBOT_IP" > /dev/null 2>&1; then
  echo "FAIL: cannot reach $ROBOT_IP"
  echo "Please verify cable/NIC and ROBOT_IP"
  exit 1
fi

if [ ! -f /opt/ros/humble/setup.zsh ]; then
  echo "FAIL: missing /opt/ros/humble/setup.zsh"
  exit 1
fi

if [ ! -f "$WORKSPACE_ROOT/install/setup.zsh" ]; then
  echo "FAIL: missing $WORKSPACE_ROOT/install/setup.zsh"
  echo "Build workspace first: colcon build"
  exit 1
fi

echo "Running prelaunch cleanup..."
zsh "$WORKSPACE_ROOT/scripts/go2_ros_preflight.sh" prelaunch

set +u
source /opt/ros/humble/setup.zsh
source "$WORKSPACE_ROOT/install/setup.zsh"
set -u

if ! command -v ros2 > /dev/null 2>&1; then
  echo "FAIL: ros2 command unavailable after sourcing environment"
  exit 1
fi

echo "Launching Gate B (SLAM-only): slam:=true nav2:=false"
ros2 launch go2_robot_sdk robot.launch.py \
  slam:=true \
  nav2:=false \
  rviz2:=false \
  foxglove:=false \
  joystick:=false \
  teleop:=false \
  enable_video:=false \
  decode_lidar:=true \
  publish_raw_image:=false \
  publish_compressed_image:=false \
  lidar_processing:=false \
  minimal_state_topics:=true \
  lidar_point_stride:=$LIDAR_POINT_STRIDE \
  enable_tts:=false

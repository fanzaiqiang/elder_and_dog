#!/usr/bin/env zsh

set -e

if [ -z "$ZSH_VERSION" ]; then
  exec /usr/bin/env zsh "$0" "$@"
fi

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
WORKSPACE_ROOT="$SCRIPT_DIR"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

MODE="${1:-minimal}"
if [ "$MODE" != "minimal" ] && [ "$MODE" != "full" ]; then
  echo -e "${RED}Unsupported mode: $MODE${NC}"
  echo "Usage: zsh start_go2_wired_webrtc.sh [minimal|full]"
  exit 1
fi

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}   Go2 wired WebRTC mode startup       ${NC}"
echo -e "${BLUE}=======================================${NC}"

export ROBOT_IP="${ROBOT_IP:-192.168.123.161}"
export CONN_TYPE="webrtc"
export GO2_LIDAR_DECODER="${GO2_LIDAR_DECODER:-wasm}"

FOXGLOVE="${FOXGLOVE:-false}"
TELEOP="${TELEOP:-false}"
RVIZ2="${RVIZ2:-false}"
ENABLE_VIDEO="${ENABLE_VIDEO:-false}"
DECODE_LIDAR="${DECODE_LIDAR:-true}"
LIDAR_PROCESSING="${LIDAR_PROCESSING:-false}"
PUBLISH_RAW_VOXEL="${PUBLISH_RAW_VOXEL:-false}"
MINIMAL_STATE_TOPICS="${MINIMAL_STATE_TOPICS:-false}"
LIDAR_POINT_STRIDE="${LIDAR_POINT_STRIDE:-1}"

SLAM="false"
NAV2="false"
if [ "$MODE" = "full" ]; then
  SLAM="true"
  NAV2="true"
fi

echo -e "${YELLOW}1. Checking network connectivity...${NC}"
if ping -c 1 "$ROBOT_IP" > /dev/null 2>&1; then
  echo -e "${GREEN}OK: robot reachable (IP: $ROBOT_IP)${NC}"
else
  echo -e "${RED}FAIL: cannot reach $ROBOT_IP${NC}"
  echo "Please verify cable and host NIC IP in 192.168.123.x"
  exit 1
fi

echo -e "${YELLOW}2. Loading ROS2 environment...${NC}"
source /opt/ros/humble/setup.zsh
source "$WORKSPACE_ROOT/install/setup.zsh"

if [ "$TELEOP" = "true" ]; then
  if ! ros2 pkg prefix twist_mux > /dev/null 2>&1; then
    echo -e "${YELLOW}WARN: twist_mux not installed, disabling teleop${NC}"
    TELEOP="false"
  fi
fi

echo -e "${YELLOW}3. Launching go2_robot_sdk...${NC}"
echo "Mode: $MODE"
echo "Settings:"
echo "  - ROBOT_IP: $ROBOT_IP"
echo "  - CONN_TYPE: $CONN_TYPE"
echo "  - GO2_LIDAR_DECODER: $GO2_LIDAR_DECODER"
echo "  - RViz2: $RVIZ2"
echo "  - SLAM: $SLAM"
echo "  - Nav2: $NAV2"
echo "  - Foxglove: $FOXGLOVE"
echo "  - Teleop: $TELEOP"
echo "  - Enable video: $ENABLE_VIDEO"
echo "  - Decode lidar: $DECODE_LIDAR"
echo "  - Lidar processing: $LIDAR_PROCESSING"
echo "  - Publish raw voxel: $PUBLISH_RAW_VOXEL"
echo "  - Minimal state topics: $MINIMAL_STATE_TOPICS"
echo "  - Lidar point stride: $LIDAR_POINT_STRIDE"
echo "  - Enable TTS: false"

ros2 launch go2_robot_sdk robot.launch.py \
  rviz2:=$RVIZ2 \
  slam:=$SLAM \
  nav2:=$NAV2 \
  enable_video:=$ENABLE_VIDEO \
  decode_lidar:=$DECODE_LIDAR \
  publish_raw_voxel:=$PUBLISH_RAW_VOXEL \
  publish_raw_image:=false \
  publish_compressed_image:=false \
  lidar_processing:=$LIDAR_PROCESSING \
  minimal_state_topics:=$MINIMAL_STATE_TOPICS \
  lidar_point_stride:=$LIDAR_POINT_STRIDE \
  enable_tts:=false \
  foxglove:=$FOXGLOVE \
  joystick:=false \
  teleop:=$TELEOP

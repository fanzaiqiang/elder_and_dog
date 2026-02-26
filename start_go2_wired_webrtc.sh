#!/usr/bin/env zsh

set -euo pipefail

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

MODE="${1:-gatec}"
if [ "$MODE" != "minimal" ] && [ "$MODE" != "full" ] && [ "$MODE" != "gatec" ]; then
  echo -e "${RED}Unsupported mode: $MODE${NC}"
  echo "Usage: zsh start_go2_wired_webrtc.sh [gatec|minimal|full]"
  exit 1
fi

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}   Go2 wired WebRTC mode startup       ${NC}"
echo -e "${BLUE}=======================================${NC}"

export ROBOT_IP="${ROBOT_IP:-192.168.123.161}"
export CONN_TYPE="webrtc"
export GO2_LIDAR_DECODER="${GO2_LIDAR_DECODER:-wasm}"

FOXGLOVE="${FOXGLOVE:-}"
TELEOP="${TELEOP:-false}"
RVIZ2="${RVIZ2:-false}"
ENABLE_VIDEO="${ENABLE_VIDEO:-false}"
DECODE_LIDAR="${DECODE_LIDAR:-true}"
LIDAR_PROCESSING="${LIDAR_PROCESSING:-false}"
PUBLISH_RAW_VOXEL="${PUBLISH_RAW_VOXEL:-false}"
MINIMAL_STATE_TOPICS="${MINIMAL_STATE_TOPICS:-true}"
LIDAR_POINT_STRIDE="${LIDAR_POINT_STRIDE:-8}"
PUBLISH_RAW_IMAGE="${PUBLISH_RAW_IMAGE:-false}"
PUBLISH_COMPRESSED_IMAGE="${PUBLISH_COMPRESSED_IMAGE:-}"
AUTOSTART="${AUTOSTART:-true}"
MAP_YAML="${MAP_YAML:-/home/jetson/elder_and_dog/src/go2_robot_sdk/maps/phase1.yaml}"
RUN_PREFLIGHT="${RUN_PREFLIGHT:-true}"

resolve_map_yaml() {
  local requested="$1"
  if [ -f "$requested" ]; then
    printf "%s\n" "$requested"
    return 0
  fi

  local candidates=(
    "/home/jetson/elder_and_dog/src/go2_robot_sdk/maps/phase1.yaml"
    "/home/jetson/elder_and_dog/src/go2_robot_sdk/maps/phase1_test.yaml"
    "/home/jetson/go2_map.yaml"
  )

  for candidate in "${candidates[@]}"; do
    if [ -f "$candidate" ]; then
      printf "%s\n" "$candidate"
      return 0
    fi
  done

  return 1
}

SLAM="false"
NAV2="true"
if [ "$MODE" = "minimal" ]; then
  NAV2="false"
  if [ -z "${FOXGLOVE}" ]; then FOXGLOVE="false"; fi
  if [ -z "${PUBLISH_COMPRESSED_IMAGE}" ]; then PUBLISH_COMPRESSED_IMAGE="false"; fi
elif [ "$MODE" = "full" ]; then
  SLAM="true"
  NAV2="true"
fi

if [ -z "${FOXGLOVE}" ]; then
  FOXGLOVE="true"
fi
if [ -z "${PUBLISH_COMPRESSED_IMAGE}" ]; then
  PUBLISH_COMPRESSED_IMAGE="true"
fi

if [ "$ENABLE_VIDEO" = "false" ] && { [ "$PUBLISH_RAW_IMAGE" = "true" ] || [ "$PUBLISH_COMPRESSED_IMAGE" = "true" ]; }; then
  ENABLE_VIDEO="true"
fi

if [ "$NAV2" = "true" ]; then
  if ! MAP_YAML=$(resolve_map_yaml "$MAP_YAML"); then
    echo -e "${RED}FAIL: map yaml not found${NC}"
    exit 1
  fi
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
set +u
source /opt/ros/humble/setup.zsh
source "$WORKSPACE_ROOT/install/setup.zsh"
set -u

if ! command -v ros2 > /dev/null 2>&1; then
  echo -e "${RED}FAIL: ros2 command unavailable after sourcing environment${NC}"
  exit 1
fi

if [ "$RUN_PREFLIGHT" = "true" ] && [ -f "$WORKSPACE_ROOT/scripts/go2_ros_preflight.sh" ]; then
  echo -e "${YELLOW}2.5 Running prelaunch cleanup...${NC}"
  zsh "$WORKSPACE_ROOT/scripts/go2_ros_preflight.sh" prelaunch
fi

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
echo "  - Publish raw image: $PUBLISH_RAW_IMAGE"
echo "  - Publish compressed image: $PUBLISH_COMPRESSED_IMAGE"
echo "  - Decode lidar: $DECODE_LIDAR"
echo "  - Lidar processing: $LIDAR_PROCESSING"
echo "  - Publish raw voxel: $PUBLISH_RAW_VOXEL"
echo "  - Minimal state topics: $MINIMAL_STATE_TOPICS"
echo "  - Lidar point stride: $LIDAR_POINT_STRIDE"
echo "  - Autostart: $AUTOSTART"
echo "  - Map YAML: $MAP_YAML"
echo "  - Enable TTS: false"

ros2 launch go2_robot_sdk robot.launch.py \
  rviz2:=$RVIZ2 \
  slam:=$SLAM \
  nav2:=$NAV2 \
  autostart:=$AUTOSTART \
  map:=$MAP_YAML \
  enable_video:=$ENABLE_VIDEO \
  decode_lidar:=$DECODE_LIDAR \
  publish_raw_voxel:=$PUBLISH_RAW_VOXEL \
  publish_raw_image:=$PUBLISH_RAW_IMAGE \
  publish_compressed_image:=$PUBLISH_COMPRESSED_IMAGE \
  lidar_processing:=$LIDAR_PROCESSING \
  minimal_state_topics:=$MINIMAL_STATE_TOPICS \
  lidar_point_stride:=$LIDAR_POINT_STRIDE \
  enable_tts:=false \
  foxglove:=$FOXGLOVE \
  joystick:=false \
  teleop:=$TELEOP

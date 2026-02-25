#!/usr/bin/env zsh

set -euo pipefail

if [ -z "${ZSH_VERSION:-}" ]; then
  exec /usr/bin/env zsh "$0" "$@"
fi

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
WORKSPACE_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)

if [ $# -eq 0 ]; then
  echo "Usage: zsh scripts/ros2w.sh <ros2 args...>"
  echo "Example: zsh scripts/ros2w.sh topic hz /scan"
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

set +u
source /opt/ros/humble/setup.zsh
source "$WORKSPACE_ROOT/install/setup.zsh"
set -u

exec ros2 "$@"

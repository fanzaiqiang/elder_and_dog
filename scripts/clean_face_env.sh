#!/usr/bin/env bash
# clean_face_env.sh — 清理人臉辨識相關殘留 process
# 用法:
#   bash scripts/clean_face_env.sh            # 只清 face node
#   bash scripts/clean_face_env.sh --all      # 清 face + camera + foxglove + tmux
set -euo pipefail

echo "=== Cleaning face perception environment ==="

# Kill face identity processes
pkill -f "face_identity_node" 2>/dev/null && echo "  killed face_identity_node" || true
pkill -f "face_identity_infer_cv" 2>/dev/null && echo "  killed face_identity_infer_cv" || true

if [[ "${1:-}" == "--all" ]]; then
    # Kill realsense camera
    pkill -f "realsense2_camera_node" 2>/dev/null && echo "  killed realsense2_camera_node" || true
    pkill -f "rs_launch.py" 2>/dev/null && echo "  killed rs_launch.py" || true

    # Kill foxglove bridge
    pkill -x foxglove_bridge 2>/dev/null && echo "  killed foxglove_bridge" || true
fi

# Kill tmux session if exists
tmux kill-session -t face_identity 2>/dev/null && echo "  killed tmux session 'face_identity'" || true

echo "=== Done ==="

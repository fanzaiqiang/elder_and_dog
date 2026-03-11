#!/usr/bin/env bash

set -euo pipefail

SESSION_NAME="${1:-speech-stable-debug}"
WORKDIR="/home/jetson/elder_and_dog"
LOG_ROOT="$WORKDIR/log/speech_debug"
TARGET_DIR="${2:-}"

if [ -z "$TARGET_DIR" ]; then
  TARGET_DIR="$(ls -1dt "$LOG_ROOT"/* 2>/dev/null | head -n 1 || true)"
fi

if [ -z "$TARGET_DIR" ] || [ ! -d "$TARGET_DIR" ]; then
  echo "[ERROR] target log dir not found"
  exit 1
fi

cd "$WORKDIR"
set +u
source /opt/ros/humble/setup.bash
source install/setup.bash
set -u

date -Iseconds >"$TARGET_DIR/snapshot_time.txt"
tmux ls >"$TARGET_DIR/tmux_sessions.txt" 2>&1 || true
tmux list-windows -t "$SESSION_NAME" >"$TARGET_DIR/tmux_windows.txt" 2>&1 || true
tmux list-panes -t "$SESSION_NAME" -F '#{pane_index} #{pane_id} #{pane_start_command} #{pane_current_command}' >"$TARGET_DIR/tmux_panes.txt" 2>&1 || true
ros2 node list >"$TARGET_DIR/ros2_node_list.txt" 2>&1 || true
ros2 topic list >"$TARGET_DIR/ros2_topic_list.txt" 2>&1 || true
ros2 topic info /event/speech_activity -v >"$TARGET_DIR/topic_info_event_speech_activity.txt" 2>&1 || true
ros2 topic info /audio/speech_segment -v >"$TARGET_DIR/topic_info_audio_speech_segment.txt" 2>&1 || true
ros2 topic info /asr_result -v >"$TARGET_DIR/topic_info_asr_result.txt" 2>&1 || true
ros2 topic info /event/speech_intent_recognized -v >"$TARGET_DIR/topic_info_intent_event.txt" 2>&1 || true
ros2 topic info /tts -v >"$TARGET_DIR/topic_info_tts.txt" 2>&1 || true
ros2 topic info /webrtc_req -v >"$TARGET_DIR/topic_info_webrtc_req.txt" 2>&1 || true
ps -eo pid,ppid,pcpu,pmem,cmd --sort=-pcpu >"$TARGET_DIR/ps_cpu_sorted.txt"
pactl get-default-source >"$TARGET_DIR/pulse_default_source.txt" 2>&1 || true
pactl list short sources >"$TARGET_DIR/pulse_sources.txt" 2>&1 || true
arecord -l >"$TARGET_DIR/arecord_l.txt" 2>&1 || true

for pane_id in $(tmux list-panes -t "$SESSION_NAME" -F '#{pane_id}' 2>/dev/null); do
  pane_name="${pane_id#%}"
  tmux capture-pane -pt "$pane_id" -S -300 >"$TARGET_DIR/pane_${pane_name}_tail.txt" 2>&1 || true
done

echo "[OK] snapshot written to $TARGET_DIR"

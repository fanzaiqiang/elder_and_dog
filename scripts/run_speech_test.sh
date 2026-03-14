#!/usr/bin/env bash
# Orchestrate 30-round speech validation test.
# Usage: scripts/run_speech_test.sh [--yaml path] [--skip-build] [--skip-driver]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKDIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CT2_LIB_PATH="$HOME/.local/ctranslate2-cuda/lib"
YAML_FILE="${WORKDIR}/test_scripts/speech_30round.yaml"
SKIP_BUILD=0
SKIP_DRIVER=0

# Parse args (while+shift, not for loop)
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-build) SKIP_BUILD=1; shift ;;
    --skip-driver) SKIP_DRIVER=1; shift ;;
    --yaml=*) YAML_FILE="${1#*=}"; shift ;;
    --yaml) YAML_FILE="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [ ! -f "$YAML_FILE" ]; then
  echo "[ERROR] YAML file not found: $YAML_FILE"
  exit 1
fi

echo "=== Speech 30-Round Validation ==="
echo "YAML: $YAML_FILE"

# Step 1: Clean environment
echo "[1/7] Cleaning environment..."
bash "$SCRIPT_DIR/clean_speech_env.sh" || { echo "[ERROR] Clean failed"; exit 1; }

# Step 2: Build (optional)
if [ "$SKIP_BUILD" = "0" ]; then
  echo "[2/7] Building..."
  cd "$WORKDIR"
  zsh -lc "source /opt/ros/humble/setup.zsh && colcon build --packages-select speech_processor go2_robot_sdk"
else
  echo "[2/7] Build skipped"
fi

cd "$WORKDIR"

# Step 3: Launch main nodes in tmux
echo "[3/7] Starting main nodes..."
SESSION_NAME="speech-test"
ROBOT_IP="${ROBOT_IP:-192.168.123.161}"
CONN_TYPE="${CONN_TYPE:-webrtc}"

if [ "$SKIP_DRIVER" = "0" ]; then
  tmux new-session -d -s "$SESSION_NAME" \
    "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && \
     export ROBOT_IP=$ROBOT_IP CONN_TYPE=$CONN_TYPE && \
     ros2 launch go2_robot_sdk robot.launch.py enable_tts:=false nav2:=false slam:=false rviz2:=false foxglove:=false'"
else
  echo "  [skip-driver] go2_driver_node skipped — assuming already running"
  tmux new-session -d -s "$SESSION_NAME" "echo 'Driver skipped — this pane is a placeholder'; sleep 999999"
fi

tmux split-window -h -t "$SESSION_NAME" \
  "zsh -lc 'setopt nonomatch; cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && \
   export LD_LIBRARY_PATH=$CT2_LIB_PATH:\${LD_LIBRARY_PATH:-} && \
   ros2 run speech_processor stt_intent_node --ros-args \
   -p provider_order:=\"[\\\"whisper_local\\\"]\" \
   -p whisper_local.model_name:=small \
   -p whisper_local.device:=cuda \
   -p whisper_local.compute_type:=float16 \
   -p input_device:=0 \
   -p sample_rate:=16000 \
   -p capture_sample_rate:=44100'"

tmux split-window -v -t "$SESSION_NAME" \
  "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && \
   ros2 run speech_processor intent_tts_bridge_node'"

PIPER_MODEL="/home/jetson/models/piper/zh_CN-huayan-medium.onnx"
PIPER_CONFIG="/home/jetson/models/piper/zh_CN-huayan-medium.onnx.json"
tmux split-window -v -t "$SESSION_NAME" \
  "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && \
   export PATH=\"\$HOME/.local/bin:\$PATH\" && \
   ros2 run speech_processor tts_node --ros-args \
   -p provider:=piper \
   -p piper_model_path:=$PIPER_MODEL \
   -p piper_config_path:=$PIPER_CONFIG'"

# Health check helper + ROS2 env for orchestrator shell
wait_for_topic() {
  local TOPIC="$1"
  local TIMEOUT="$2"
  local ELAPSED=0
  while [ "$ELAPSED" -lt "$TIMEOUT" ]; do
    if ros2 topic info "$TOPIC" 2>/dev/null | grep -q "Publisher count: [1-9]"; then
      return 0
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
  done
  return 1
}

source /opt/ros/humble/setup.bash
source "$WORKDIR/install/setup.bash"

# Health checks for speech nodes (observer not started yet)
echo "[4/7] Health checks..."

HEALTH_CHECKS="/tts:15 /event/speech_intent_recognized:45"
if [ "$SKIP_DRIVER" = "0" ]; then
  HEALTH_CHECKS="/webrtc_req:15 $HEALTH_CHECKS"
fi

for CHECK in $HEALTH_CHECKS; do
  TOPIC="${CHECK%:*}"
  TIMEOUT="${CHECK#*:}"
  echo "  Waiting for $TOPIC (${TIMEOUT}s)..."
  if ! wait_for_topic "$TOPIC" "$TIMEOUT"; then
    echo "[ERROR] $TOPIC not ready after ${TIMEOUT}s"
    tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
    exit 1
  fi
  echo "  OK $TOPIC ready"
done

# Step 5: Warmup round BEFORE observer starts (so warmup is not recorded)
echo ""
echo "=== WARMUP (不計分) ==="
echo "請說任意一句話做暖機（observer 尚未啟動，此輪不會進入統計）..."
read -rp "（完成後按 Enter）"
echo ""

# Step 4b: Launch observer AFTER warmup (clean start, no warmup pollution)
echo "[4b/7] Starting observer..."
tmux split-window -v -t "$SESSION_NAME" \
  "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && \
   ros2 run speech_processor speech_test_observer --ros-args \
   -p output_dir:=$WORKDIR/test_results'"

# Wait for observer to be ready
echo "  Waiting for observer..."
if ! wait_for_topic "/speech_test_observer/round_meta_ack" 15; then
  echo "[ERROR] Observer not ready"
  tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
  exit 1
fi
echo "  OK observer ready"

# Parse YAML into tab-separated lines (one python3 call for all rounds)
echo "[5/7] Running test rounds..."

ROUND_DATA=$(python3 -c "
import yaml, json, sys
with open('$YAML_FILE') as f:
    d = yaml.safe_load(f)
fixed = d.get('fixed_rounds', [])
free = d.get('free_rounds', [])
total = len(fixed) + len(free)
for r in fixed:
    print('\t'.join([str(r['round_id']), 'fixed', r['expected_intent'],
          r.get('utterance',''), r.get('notes',''), str(total)]))
for r in free:
    print('\t'.join([str(r['round_id']), 'free', '', '',
          r.get('notes',''), str(total)]))
")

# Read rounds using here-string (not pipe) to keep stdin for operator interaction
while IFS=$'\t' read -r ROUND_ID MODE EXPECTED UTTERANCE NOTES TOTAL; do
  echo ""
  if [ "$MODE" = "fixed" ]; then
    echo "[Round $ROUND_ID/$TOTAL] [FIXED] 請說：「$UTTERANCE」"
    echo "  expected_intent: $EXPECTED"
  else
    echo "[Round $ROUND_ID/$TOTAL] [FREE] 自由講"
    if [ -n "$NOTES" ]; then
      echo "  提示：$NOTES"
    fi
    read -rp "  expected_intent?（可留空）：" EXPECTED </dev/tty
  fi

  # Send round meta and wait for ack
  META_JSON="{\"round_id\":$ROUND_ID,\"mode\":\"$MODE\",\"expected_intent\":\"$EXPECTED\",\"utterance_text\":\"$UTTERANCE\"}"

  # Start listening for ack before publishing (avoid race)
  timeout 5 ros2 topic echo --once /speech_test_observer/round_meta_ack std_msgs/msg/String 2>/dev/null &
  ACK_PID=$!
  sleep 0.2
  ros2 topic pub --once /speech_test_observer/round_meta_req std_msgs/msg/String "{data: '$META_JSON'}" >/dev/null 2>&1
  wait $ACK_PID 2>/dev/null || echo "  [WARN] meta ack timeout"

  read -rp "  （準備好後按 Enter，輸入 q 結束）" INPUT </dev/tty
  if [ "$INPUT" = "q" ]; then
    echo "[INFO] 測試提前結束"
    break
  fi

  # Wait for observer to collect round data, then show result
  sleep 3

  # Read latest observer log for this round's result (best-effort)
  RESULT=$(timeout 2 ros2 topic echo --once /state/interaction/speech std_msgs/msg/String 2>/dev/null || true)
  echo "  [Round $ROUND_ID] 已記錄（詳見最終報告）"

done <<< "$ROUND_DATA"

# Step 6: Wait for last round to finish, then generate report
echo ""
echo "[6/7] Waiting for last round to finish..."
sleep 8  # drain: let TTS + webrtc playback complete for the final round
echo "Generating report..."

# Start listening for ack BEFORE publishing (avoid race condition)
timeout 10 ros2 topic echo --once /speech_test_observer/generate_report_ack std_msgs/msg/String 2>/dev/null &
REPORT_ACK_PID=$!
sleep 0.2
ros2 topic pub --once /speech_test_observer/generate_report_req std_msgs/msg/String "{data: '{}'}" >/dev/null 2>&1
wait $REPORT_ACK_PID 2>/dev/null && echo "[OK] Report generated" || echo "[WARN] Report ack timeout"

# Step 7: Display summary
echo ""
echo "[7/7] Done!"
echo "Results in: $WORKDIR/test_results/"
ls -la "$WORKDIR/test_results/" 2>/dev/null || echo "(no results yet)"

# Show summary JSON if available
LATEST_SUMMARY=$(ls -t "$WORKDIR/test_results/"*_summary.json 2>/dev/null | head -1)
if [ -n "$LATEST_SUMMARY" ]; then
  echo ""
  echo "=== Summary ==="
  python3 -c "
import json, sys
with open('$LATEST_SUMMARY') as f:
    s = json.load(f)
print(f'Grade: {s[\"grade\"]}')
print(f'Completed: {s[\"completed\"]}/{s[\"total_rounds\"]}')
fr = s.get('fixed_rounds', {})
print(f'Fixed accuracy: {fr.get(\"hit\",0)}/{fr.get(\"total\",0)} = {fr.get(\"accuracy\",0):.1%}')
lat = s.get('latency', {})
print(f'E2E median: {lat.get(\"e2e_median_ms\",0):.0f}ms, max: {lat.get(\"e2e_max_ms\",0):.0f}ms')
print(f'Play OK rate: {lat.get(\"play_ok_rate\",0):.1%}')
for k, v in s.get('pass_criteria', {}).items():
    mark = 'PASS' if v['pass'] else 'FAIL'
    print(f'  {k}: {v[\"actual\"]} (threshold: {v[\"threshold\"]}) [{mark}]')
"
fi

echo ""
echo "=== Test Complete ==="

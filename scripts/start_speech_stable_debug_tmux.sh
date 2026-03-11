#!/usr/bin/env bash

set -euo pipefail

SESSION_NAME="speech-stable-debug"
WORKDIR="/home/jetson/elder_and_dog"
TMUX_COLS="240"
TMUX_ROWS="72"

ROBOT_IP="${ROBOT_IP:-192.168.123.161}"
CONN_TYPE="${CONN_TYPE:-webrtc}"

INPUT_DEVICE="${INPUT_DEVICE:-}"
ALSA_DEVICE="${ALSA_DEVICE:-}"
CHANNELS="${CHANNELS:-}"
SAMPLE_RATE="16000"
CAPTURE_SAMPLE_RATE="44100"
FRAME_SAMPLES="512"
VAD_THRESHOLD="${VAD_THRESHOLD:-0.28}"
MIN_SILENCE_MS="${MIN_SILENCE_MS:-450}"
SPEECH_PAD_MS="${SPEECH_PAD_MS:-120}"

ASR_MODEL_NAME="${ASR_MODEL_NAME:-tiny}"
ASR_LANGUAGE="${ASR_LANGUAGE:-zh}"
INTENT_MIN_CONFIDENCE="${INTENT_MIN_CONFIDENCE:-0.55}"

TTS_PROVIDER="piper"
PIPER_MODEL_PATH="/home/jetson/models/piper/zh_CN-huayan-medium.onnx"
PIPER_CONFIG_PATH="/home/jetson/models/piper/zh_CN-huayan-medium.onnx.json"
PIPER_SPEAKER_ID="0"
PIPER_LENGTH_SCALE="1.20"
PIPER_NOISE_SCALE="0.45"
PIPER_NOISE_W="0.55"
ROBOT_CHUNK_INTERVAL_SEC="0.04"
ROBOT_PLAYBACK_TAIL_SEC="0.2"
ROBOT_VOLUME="${ROBOT_VOLUME:-100}"

NOW="$(date +%Y%m%d-%H%M%S)"
LOG_DIR="$WORKDIR/log/speech_debug/$NOW"

if ! command -v tmux >/dev/null 2>&1; then
  echo "[ERROR] tmux not found."
  exit 1
fi

if [ ! -d "$WORKDIR" ]; then
  echo "[ERROR] Workdir not found: $WORKDIR"
  exit 1
fi

if [ ! -f "$PIPER_MODEL_PATH" ] || [ ! -f "$PIPER_CONFIG_PATH" ]; then
  echo "[ERROR] Piper model/config missing under /home/jetson/models/piper"
  exit 1
fi

cd "$WORKDIR"
mkdir -p "$LOG_DIR"

pkill -9 -f go2_driver_node 2>/dev/null || true
pkill -9 -f go2_pointcloud_to_laserscan 2>/dev/null || true
pkill -9 -f go2_robot_state_publisher 2>/dev/null || true
pkill -9 -f go2_teleop_node 2>/dev/null || true
pkill -9 -f twist_mux 2>/dev/null || true
pkill -9 -f joy_node 2>/dev/null || true
pkill -9 -f stt_intent_node 2>/dev/null || true
pkill -9 -f vad_node 2>/dev/null || true
pkill -9 -f asr_node 2>/dev/null || true
pkill -9 -f intent_node 2>/dev/null || true
pkill -9 -f intent_tts_bridge_node 2>/dev/null || true
pkill -9 -f tts_node 2>/dev/null || true
pkill -9 -f "ros2 launch go2_robot_sdk" 2>/dev/null || true
pkill -9 -f "ros2 run speech_processor" 2>/dev/null || true
pkill -9 -f "ros2 topic echo" 2>/dev/null || true
tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true

sleep 1

if [ -z "$INPUT_DEVICE" ]; then
  INPUT_DEVICE="$(python3 - <<'PY'
import sounddevice as sd
idx = -1
for i, d in enumerate(sd.query_devices()):
    name = str(d.get("name", ""))
    if d.get("max_input_channels", 0) > 0 and "SoloCast" in name:
        idx = i
        break
print(idx)
PY
)"
fi

if [ -z "$INPUT_DEVICE" ]; then
  INPUT_DEVICE="-1"
fi

if [ -z "$CHANNELS" ]; then
  if [ "$INPUT_DEVICE" = "0" ]; then
    CHANNELS="2"
  else
  CHANNELS="$(INPUT_DEVICE="$INPUT_DEVICE" python3 - <<'PY'
import sounddevice as sd
import os

device = int(os.environ.get("INPUT_DEVICE", "-1"))
if device >= 0:
    info = sd.query_devices(device)
else:
    info = sd.query_devices(kind='input')

name = str(info.get('name', ''))
max_ch = int(info.get('max_input_channels', 1) or 1)
if 'SoloCast' in name:
    print(2)
elif max_ch >= 2:
    print(2)
else:
    print(1)
PY
  )"
  fi
fi

SOLOCAST_SOURCE="$(pactl list short sources 2>/dev/null | grep -m1 'SoloCast' | awk '{print $2}' || true)"
if [ -n "$SOLOCAST_SOURCE" ]; then
  pactl set-default-source "$SOLOCAST_SOURCE" 2>/dev/null || true
fi

VAD_ALSA_ARG=""
if [ -n "$ALSA_DEVICE" ]; then
  VAD_ALSA_ARG="-p alsa_device:=$ALSA_DEVICE"
fi

tmux new-session -d -x "$TMUX_COLS" -y "$TMUX_ROWS" -s "$SESSION_NAME" \
  "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && export ROBOT_IP=$ROBOT_IP CONN_TYPE=$CONN_TYPE && ros2 launch go2_robot_sdk robot.launch.py enable_tts:=false rviz2:=false nav2:=false slam:=false foxglove:=false joystick:=false teleop:=false decode_lidar:=false enable_lidar:=false minimal_state_topics:=true'"

GO2_PANE="$(tmux list-panes -t "$SESSION_NAME":0 -F '#{pane_id}')"
VAD_PANE="$(tmux split-window -h -P -F '#{pane_id}' -t "$GO2_PANE" "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && ros2 run speech_processor vad_node --ros-args -p input_device:=$INPUT_DEVICE $VAD_ALSA_ARG -p channels:=$CHANNELS -p sample_rate:=$SAMPLE_RATE -p capture_sample_rate:=$CAPTURE_SAMPLE_RATE -p frame_samples:=$FRAME_SAMPLES -p vad_threshold:=$VAD_THRESHOLD -p min_silence_ms:=$MIN_SILENCE_MS -p speech_pad_ms:=$SPEECH_PAD_MS'")"
ASR_PANE="$(tmux split-window -v -P -F '#{pane_id}' -t "$VAD_PANE" "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && ros2 run speech_processor asr_node --ros-args -p model_name:=$ASR_MODEL_NAME -p language:=$ASR_LANGUAGE'")"
INTENT_PANE="$(tmux split-window -v -P -F '#{pane_id}' -t "$ASR_PANE" "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && ros2 run speech_processor intent_node --ros-args -p min_confidence:=$INTENT_MIN_CONFIDENCE'")"
BRIDGE_PANE="$(tmux split-window -v -P -F '#{pane_id}' -t "$INTENT_PANE" "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && ros2 run speech_processor intent_tts_bridge_node'")"
TTS_PANE="$(tmux split-window -v -P -F '#{pane_id}' -t "$GO2_PANE" "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && export PATH=\"$HOME/.local/bin:\$PATH\" && ros2 run speech_processor tts_node --ros-args -p provider:=$TTS_PROVIDER -p piper_model_path:=$PIPER_MODEL_PATH -p piper_config_path:=$PIPER_CONFIG_PATH -p piper_speaker_id:=$PIPER_SPEAKER_ID -p piper_length_scale:=$PIPER_LENGTH_SCALE -p piper_noise_scale:=$PIPER_NOISE_SCALE -p piper_noise_w:=$PIPER_NOISE_W -p robot_chunk_interval_sec:=$ROBOT_CHUNK_INTERVAL_SEC -p robot_playback_tail_sec:=$ROBOT_PLAYBACK_TAIL_SEC -p robot_volume:=$ROBOT_VOLUME'")"

tmux select-layout -t "$SESSION_NAME" tiled
tmux set-option -t "$SESSION_NAME" mouse on >/dev/null
tmux set-option -t "$SESSION_NAME" remain-on-exit on >/dev/null

tmux pipe-pane -o -t "$GO2_PANE" "cat >> '$LOG_DIR/00_go2_driver.log'"
tmux pipe-pane -o -t "$VAD_PANE" "cat >> '$LOG_DIR/01_vad.log'"
tmux pipe-pane -o -t "$ASR_PANE" "cat >> '$LOG_DIR/02_asr.log'"
tmux pipe-pane -o -t "$INTENT_PANE" "cat >> '$LOG_DIR/03_intent.log'"
tmux pipe-pane -o -t "$BRIDGE_PANE" "cat >> '$LOG_DIR/04_intent_bridge.log'"
tmux pipe-pane -o -t "$TTS_PANE" "cat >> '$LOG_DIR/05_tts.log'"

cat >"$LOG_DIR/README.txt" <<EOF
session: $SESSION_NAME
started_at: $NOW
workdir: $WORKDIR
robot_ip: $ROBOT_IP
conn_type: $CONN_TYPE
input_device: $INPUT_DEVICE
channels: $CHANNELS
alsa_device: ${ALSA_DEVICE:-<default>}
sample_rate: $SAMPLE_RATE
capture_sample_rate: $CAPTURE_SAMPLE_RATE
vad_threshold: $VAD_THRESHOLD
min_silence_ms: $MIN_SILENCE_MS
speech_pad_ms: $SPEECH_PAD_MS
asr_model: $ASR_MODEL_NAME
asr_language: $ASR_LANGUAGE
intent_min_confidence: $INTENT_MIN_CONFIDENCE
robot_volume: $ROBOT_VOLUME
EOF

echo "[OK] Started $SESSION_NAME"
echo "[OK] Logs: $LOG_DIR"
echo "[INFO] Fake playback probe: ros2 topic pub --once /tts std_msgs/msg/String \"{data: 你好，穩定性測試}\""
echo "[INFO] Attach: tmux attach -t $SESSION_NAME"

if [ -t 1 ]; then
  tmux attach -t "$SESSION_NAME"
fi

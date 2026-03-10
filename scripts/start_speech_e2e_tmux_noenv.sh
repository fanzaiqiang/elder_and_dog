#!/usr/bin/env bash

set -euo pipefail

SESSION_NAME="speech-e2e-noenv"
WORKDIR="/home/jetson/elder_and_dog"
TMUX_COLS="240"
TMUX_ROWS="72"

ROBOT_IP="192.168.123.161"
CONN_TYPE="webrtc"

INPUT_DEVICE="-1"
ALSA_DEVICE=""
CHANNELS="1"
SAMPLE_RATE="16000"
CAPTURE_SAMPLE_RATE="16000"
FRAME_SAMPLES="512"
VAD_THRESHOLD="0.20"
MIN_SILENCE_MS="700"
SPEECH_PAD_MS="180"

ASR_MODEL_NAME="tiny"
ASR_LANGUAGE="zh"
INTENT_MIN_CONFIDENCE="0.55"

TTS_PROVIDER="piper"
TTS_VOICE_NAME="XrExE9yKIg1WjnnlVkGX"
PIPER_MODEL_PATH="/home/jetson/models/piper/zh_CN-huayan-medium.onnx"
PIPER_CONFIG_PATH="/home/jetson/models/piper/zh_CN-huayan-medium.onnx.json"
PIPER_SPEAKER_ID="0"
PIPER_LENGTH_SCALE="1.20"
PIPER_NOISE_SCALE="0.45"
PIPER_NOISE_W="0.55"
PIPER_USE_CUDA="false"
ROBOT_CHUNK_INTERVAL_SEC="0.06"
ROBOT_PLAYBACK_TAIL_SEC="0.5"

if ! command -v tmux >/dev/null 2>&1; then
  echo "[ERROR] tmux not found. Please install tmux first."
  exit 1
fi

if [ ! -d "$WORKDIR" ]; then
  echo "[ERROR] Workdir not found: $WORKDIR"
  exit 1
fi

if [ ! -f "$PIPER_MODEL_PATH" ]; then
  echo "[ERROR] Piper model not found: $PIPER_MODEL_PATH"
  exit 1
fi

if [ ! -f "$PIPER_CONFIG_PATH" ]; then
  echo "[ERROR] Piper config not found: $PIPER_CONFIG_PATH"
  exit 1
fi

VAD_ALSA_ARG=""
if [ -n "$ALSA_DEVICE" ]; then
  VAD_ALSA_ARG="-p alsa_device:=$ALSA_DEVICE"
fi

cd "$WORKDIR"

zsh -lc "cd $WORKDIR && source /opt/ros/humble/setup.zsh && colcon build --packages-select go2_robot_sdk speech_processor && source install/setup.zsh"

tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true

tmux new-session -d -x "$TMUX_COLS" -y "$TMUX_ROWS" -s "$SESSION_NAME" "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && export ROBOT_IP=$ROBOT_IP && export CONN_TYPE=$CONN_TYPE && ros2 launch go2_robot_sdk robot.launch.py enable_tts:=false nav2:=false slam:=false rviz2:=false foxglove:=false'"

GO2_PANE="$(tmux list-panes -t "$SESSION_NAME":0 -F '#{pane_id}')"
VAD_PANE="$(tmux split-window -h -P -F '#{pane_id}' -t "$GO2_PANE" "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && ros2 run speech_processor vad_node --ros-args -p input_device:=$INPUT_DEVICE $VAD_ALSA_ARG -p channels:=$CHANNELS -p sample_rate:=$SAMPLE_RATE -p capture_sample_rate:=$CAPTURE_SAMPLE_RATE -p frame_samples:=$FRAME_SAMPLES -p vad_threshold:=$VAD_THRESHOLD -p min_silence_ms:=$MIN_SILENCE_MS -p speech_pad_ms:=$SPEECH_PAD_MS'")"
ASR_PANE="$(tmux split-window -v -P -F '#{pane_id}' -t "$VAD_PANE" "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && ros2 run speech_processor asr_node --ros-args -p model_name:=$ASR_MODEL_NAME -p language:=$ASR_LANGUAGE'")"
INTENT_PANE="$(tmux split-window -v -P -F '#{pane_id}' -t "$ASR_PANE" "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && ros2 run speech_processor intent_node --ros-args -p min_confidence:=$INTENT_MIN_CONFIDENCE'")"
BRIDGE_PANE="$(tmux split-window -v -P -F '#{pane_id}' -t "$INTENT_PANE" "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && ros2 run speech_processor intent_tts_bridge_node'")"
 TTS_PANE="$(tmux split-window -v -P -F '#{pane_id}' -t "$BRIDGE_PANE" "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && export PATH=\"$HOME/.local/bin:\$PATH\" && ros2 run speech_processor tts_node --ros-args -p provider:=$TTS_PROVIDER -p voice_name:=$TTS_VOICE_NAME -p piper_model_path:=$PIPER_MODEL_PATH -p piper_config_path:=$PIPER_CONFIG_PATH -p piper_speaker_id:=$PIPER_SPEAKER_ID -p piper_length_scale:=$PIPER_LENGTH_SCALE -p piper_noise_scale:=$PIPER_NOISE_SCALE -p piper_noise_w:=$PIPER_NOISE_W -p piper_use_cuda:=$PIPER_USE_CUDA -p robot_chunk_interval_sec:=$ROBOT_CHUNK_INTERVAL_SEC -p robot_playback_tail_sec:=$ROBOT_PLAYBACK_TAIL_SEC'")"

EVENT_PANE="$(tmux split-window -h -P -F '#{pane_id}' -t "$ASR_PANE" "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && while true; do ros2 topic echo /event/speech_intent_recognized; sleep 1; done'")"
TTS_TOPIC_PANE="$(tmux split-window -v -P -F '#{pane_id}' -t "$EVENT_PANE" "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && while true; do ros2 topic echo /tts; sleep 1; done'")"
tmux split-window -v -t "$TTS_TOPIC_PANE" "zsh -lc 'cd $WORKDIR && source /opt/ros/humble/setup.zsh && source install/setup.zsh && while true; do ros2 topic echo /webrtc_req; sleep 1; done'"

tmux select-layout -t "$SESSION_NAME" tiled
tmux set-option -t "$SESSION_NAME" mouse on >/dev/null
tmux set-option -t "$SESSION_NAME" remain-on-exit on >/dev/null

echo "[OK] tmux session '$SESSION_NAME' started (NO .env.local)."
echo "[INFO] Provider is fixed to: $TTS_PROVIDER"
echo "[INFO] attach with: tmux attach -t $SESSION_NAME"

tmux attach -t "$SESSION_NAME"

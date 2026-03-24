# 語音模組 Reference

## 定位

ASR（語音轉文字）+ Intent 分類 + LLM 對話 + TTS（文字轉語音）+ Go2 播放。
E2E 流程：使用者說話 → Whisper → Intent → LLM → TTS → USB 喇叭播放（或 Megaphone fallback）。

## 權威文件

- **語音模組設計**：`docs/語音功能/README.md`
- **LLM 整合規格**：`docs/superpowers/specs/2026-03-16-llm-integration-mini-spec.md`
- **ROS2 介面契約**：`docs/architecture/interaction_contract.md` (語音相關 topics)

## 核心程式

| 檔案 | 用途 |
|------|------|
| `speech_processor/speech_processor/stt_intent_node.py` | ASR + Energy VAD + Intent 分類 |
| `speech_processor/speech_processor/intent_classifier.py` | Intent 分類器（純 Python，從 stt_intent_node 抽出） |
| `speech_processor/speech_processor/llm_bridge_node.py` | Cloud LLM 呼叫 + RuleBrain fallback + greet dedup |
| `speech_processor/speech_processor/llm_contract.py` | LLM JSON 契約（純 Python，從 llm_bridge_node 抽出） |
| `speech_processor/speech_processor/tts_node.py` | TTS 合成 + USB 喇叭 local 播放 / Megaphone DataChannel 播放 |
| `speech_processor/speech_processor/intent_tts_bridge_node.py` | 舊版模板回覆（保留作 fallback） |
| `speech_processor/config/speech_processor.yaml` | 語音模組參數 |

## 關鍵 Topics

- `/event/speech_intent_recognized` — Intent 事件 JSON（觸發式）
- `/state/interaction/speech` — 語音管線狀態（5 Hz）
- `/tts` — TTS 輸入文字（std_msgs/String）
- `/webrtc_req` — Go2 WebRTC 命令

## 啟動方式

```bash
# 一鍵 LLM E2E（推薦，預設走 USB 外接設備）
bash scripts/start_llm_e2e_tmux.sh

# 切回 HyperX + Megaphone 模式
LOCAL_PLAYBACK=false INPUT_DEVICE=0 CHANNELS=2 CAPTURE_SAMPLE_RATE=44100 \
  bash scripts/start_llm_e2e_tmux.sh

# Smoke test
bash scripts/smoke_test_e2e.sh 5

# 單句 TTS 測試
ros2 topic pub --once /tts std_msgs/msg/String '{data: "測試播放"}'
```

## 外接音訊設備（2026-03-24 驗證通過）

- **麥克風**：UACDemoV1.0（`hw:2,0`，mono，48kHz）— sounddevice index 24
- **喇叭**：CD002-AUDIO（`hw:3,0`，stereo，48kHz）— 音量需 `amixer -c 3 set PCM 147`
- Piper 原生 22050Hz 直出，清晰度相比 Megaphone 16kHz 大幅改善
- `LD_LIBRARY_PATH` 必須含 `/home/jetson/.local/ctranslate2-cuda/lib`（啟動腳本已處理）
- Whisper 必須用 `device=cuda, compute_type=float16`（Jetson CPU 不支援 int8）

## 已知陷阱

- **VAD 斷句 2-10s** 是最大延遲瓶頸，不是 LLM
- **Whisper int8 on Jetson CPU 不可用**：必須用 `cuda` + `float16`，否則 silent fail
- **USB 喇叭 card number 可能漂移**：拔插後 `aplay -l` 確認
- **Megaphone cooldown**：4002 EXIT 後 sleep 0.5s（Megaphone 模式）
- **ASR warmup**：daemon thread 預熱 Whisper CUDA ~12s
- **Whisper 幻覺**：靜音/噪音段可能被誤解為假文字

## 測試

- `speech_processor/test/test_intent_classifier.py` — Intent 分類器單元測試
- `speech_processor/test/test_llm_contract.py` — LLM 契約單元測試
- `speech_processor/test/test_speech_test_observer.py` — Observer 單元測試
- `scripts/run_speech_test.sh` — 30 輪驗收測試
- `test_scripts/speech_30round.yaml` — 30 輪測試定義

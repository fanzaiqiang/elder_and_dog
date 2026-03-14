# 語音互動系統

> Unitree Go2 Pro + Jetson Orin Nano 8GB + 5×RTX 8000

## 目標效果

- 人說話機器聽得懂，機器回話自然流暢
- **連續對話**（記得上下文）+ **上下文理解**（記得人名、地點、偏好）
- 可以執行任務導向的互動（不只是閒聊）

---

## 今天先從這裡開始（MVP 起手）

先不要一次做完整 ASR+LLM+TTS。依照目前 repo 真實狀態，先把「TTS 鏈路可用」打通，因為 `speech_processor` 現在穩定存在的是 `tts_node`。

### 目前程式現況（已存在）

- 語音文件主檔：`docs/語音功能/README.md`
- TTS node：`speech_processor/speech_processor/tts_node.py`
- 套件 entrypoint：`speech_processor/setup.py`
- Go2 launch 內可開關 TTS：`go2_robot_sdk/launch/robot.launch.py`（`enable_tts`）

### Phase 1（今天必做）: 先驗證 TTS 端到端

1. 在 Jetson build 指定套件

```bash
ssh jetson-nano "cd /home/jetson/elder_and_dog && source /opt/ros/humble/setup.bash && colcon build --packages-select speech_processor go2_robot_sdk"
```

2. 啟動 Go2（先關掉不需要的模組，只開 TTS）

```bash
ssh jetson-nano "cd /home/jetson/elder_and_dog && unset COLCON_CURRENT_PREFIX && source /opt/ros/humble/setup.bash && source install/setup.bash && export ROBOT_IP=<GO2_IP> && export CONN_TYPE=webrtc && export ELEVENLABS_API_KEY=<YOUR_KEY> && ros2 launch go2_robot_sdk robot.launch.py enable_tts:=true nav2:=false slam:=false rviz2:=false foxglove:=false"
```

3. 另一個終端送測試句

```bash
ssh jetson-nano "cd /home/jetson/elder_and_dog && source /opt/ros/humble/setup.bash && source install/setup.bash && ros2 topic pub --once /tts std_msgs/msg/String '{data: \"哈囉，語音模組測試成功\"}'"
```

4. 驗收（至少滿足兩項）

- `tts_node` log 出現 `TTS completed successfully`
- Go2 有實際播音
- `/webrtc_req` 有音訊分塊封包送出

### Phase 2（明天接）: 補齊 STT/Intent 最小閉環

目前 source tree 沒有 `speech_processor/speech_processor/stt_intent_node.py`，但 `speech_processor/setup.py` 已宣告 entrypoint `stt_intent_node`。下一步先補這個檔案，做最小版本：

- 訂閱音訊或文字輸入
- 輸出固定 intent topic（先做 3-5 個指令）
- 接到 intent 後轉發 `/tts` 做回覆

這樣可先形成「聽到（簡化）-> 理解（規則）-> 說話」的可展示閉環。

---

## 邊緣端 (Jetson 8GB) - 前端處理

### VAD (語音活動檢測)

| 方案 | 特點 | 延遲 |
|------|------|------|
| **WebRTC VAD** | 經典低負載 | sub-ms |
| **Silero VAD** | 輕量、快速、單 CPU 執行緒 | sub-ms |

**建議**：Silero VAD 適合常駐

### 喚醒詞 (Wake Word)

| 方案 | 特點 | 中文支援 |
|------|------|----------|
| **openWakeWord** | 預訓練模型、可訓練新詞 | 可訓練 |
| **Mycroft Precise** | 需收集樣本訓練 | 需自行訓練 |
| **Porcupine** | 純邊緣、資源占用極低 | 支援多喚醒詞 |

**現實**：中文喚醒詞開源資源較少，通常需自行訓練/調參

### 輕量 ASR (離線降級用)

**Whisper 模型選擇**：

| 模型 | 參數量 | VRAM | 延遲 | 適用 |
|------|--------|------|------|------|
| **tiny** | ~39M | ~1GB | 80-120ms | 喚醒詞、簡單指令 |
| **base** | ~74M | ~1GB | - | 日常對話 |
| **small** | ~244M | ~2GB | 300-500ms | 一般對話 |
| **medium** | ~769M | ~5GB | 1.2-2s | 複雜場景 |

**Jetson 8GB 建議**：tiny/base/small 較合理，medium 需看視覺負載

**加速方案**：
- **faster-whisper** (CTranslate2)：更高吞吐/更低延遲

---

## 邊緣 LLM 選項與限制

### 實測可行模型清單

| 模型 | 量化格式 | 記憶體占用 | 首 token 延遲 | 吞吐量 | 中文能力 | 推薦場景 |
|:---|:---|:---|:---|:---|:---|:---|
| **Qwen2.5-1.5B** | **INT4 (GGUF)** | **~1.2 GB** | **0.8-1.2 s** | **8-12 token/s** | **優秀** | **日常對話、家庭互動（推薦首選）** |
| Qwen2.5-0.5B | INT4 (GGUF) | ~0.6 GB | 0.3-0.5 s | 15-20 token/s | 良好 | 極簡指令、喚醒回應 |
| Qwen2.5-3B | INT4 (GGUF) | ~2.1 GB | 1.5-2.5 s | 5-8 token/s | 優秀 | 複雜推理、長回應 |
| Phi-3-mini-3.8B | INT4 (GGUF) | ~2.5 GB | 1.2-2.0 s | 6-10 token/s | 良好 | 推理任務、多語言 |
| TinyLlama-1.1B | INT8 (GGUF) | ~0.8 GB | 0.5-0.8 s | 15-20 token/s | 基礎 | 英文為主、快速反應 |

**實測環境**：Jetson Orin Nano 8GB，JetPack 5.1+，llama.cpp 推理引擎

### 推理框架比較

| 框架 | 適用模型格式 | Jetson 支援 | 易用性 | 效能 | 社群活躍度 |
|:---|:---|:---|:---|:---|:---|
| **llama.cpp** | **GGUF** | **優秀（CUDA/Metal）** | **中等** | **最佳** | **極高** |
| **Ollama** | 多種（自動轉換） | 良好 | **極佳** | 良好 | 高 |
| TensorRT-LLM | TensorRT engine | 官方支援 | 複雜 | 最佳（特定模型）| 中等 |
| ONNX Runtime | ONNX | 良好 | 中等 | 中等 | 高 |

**綜合建議**：
- 開發階段：使用 **Ollama** 快速驗證
- 生產部署：遷移至 **llama.cpp** 獲得更精細控制
- 追求極致效能：評估 **TensorRT-LLM**（需模型支援）

### 量化策略影響

| 量化格式 | 相對速度 | 相對記憶體 | 準確度損失 | 適用情境 |
|:---|:---|:---|:---|:---|
| FP16 (基準) | 1.0× | 1.0× | 0% | 開發調試 |
| INT8 | 1.5-2.0× | 0.5× | 2-5% | 平衡效能與品質 |
| **INT4 (GPTQ/AWQ)** | **2.5-4.0×** | **0.25×** | **5-15%** | **極致邊緣部署（推薦）** |

**llama.cpp 推薦格式**：Q4_K_M（K-quant，品質與速度平衡）

---

## 雲端端 (5×RTX 8000) - 核心推理

### 中文 ASR

| 方案 | 特點 | 延遲 (10秒語音) | 中文 WER | 推薦度 |
|:---|:---|:---|:---|:---|
| Whisper-tiny | 品質一般 | 1.5-2.5 s | 18-25% | ⭐⭐ |
| Whisper-base | 品質中等 | 3-5 s | 12-18% | ⭐⭐ |
| Faster-Whisper-small | 加速版 | 2-3 s | 10-15% | ⭐⭐⭐⭐ |
| **Qwen3-ASR-1.7B** | **中文專門優化** | **0.8-1.5 s** | **8-12%** | **⭐⭐⭐⭐⭐（推薦首選）** |
| NVIDIA Riva (ASR) | 企業級 | <1 s | 10-15% | 需授權 |

**推薦**：以中文互動為主的應用，**Qwen3-ASR 是首選方案**

### NLU/對話 LLM

**部署引擎**：
- **vLLM**：高吞吐、PagedAttention、支援量化 (GPTQ/AWQ)

**模型選擇**：

| 類型 | 延遲 | 品質 | 建議 |
|------|------|------|------|
| **70B 量化** | 較高 | 推理強 | 長對話一致性佳 |
| **34B 全精度** | 中等 | 細節好 | 需跨卡並行 |
| **較小模型** | 低 | 夠用 | 配合工具調用 |

**5×RTX 8000 分工建議**：

| 節點 | GPU 配置 | 部署模型 | 功能 |
|:---|:---|:---|:---|
| 節點 1-2 | 各 1×RTX 8000 | **Qwen2.5-72B-INT4** | 高品質對話 LLM |
| 節點 3 | 1×RTX 8000 | Qwen2.5-32B-INT8 + Qwen3-ASR-1.7B | 對話 + ASR 混合 |
| 節點 4-5 | 各 1×RTX 8000 | Qwen3-TTS-1.7B + 備援 LLM | TTS 服務 + 容錯 |

### TTS (文字轉語音)

| TTS 方案 | 模型大小 | 優化後延遲 (Jetson) | 記憶體占用 | MOS 音質 | 中文自然度 | 核心優勢 |
|:---|:---|:---|:---|:---|:---|:---|
| **Piper** | 50-200 MB | 0.2-0.5 s | ~300 MB | 3.0-3.5 | 可接受 | 極輕量、易部署 |
| **MeloTTS** | 300-800 MB | 0.4-0.8 s (TensorRT) | 0.8-1.2 GB | 3.8-4.2 | 良好 | 中文優化、語調自然 |
| **Qwen3-TTS-1.7B (INT4)** | ~3.2 GB | **1.3-1.7 s** | **2.1-3.2 GB** | **4.2-4.5** | **優秀** | **情感豐富、VoiceDesign** |
| **F5-TTS (TensorRT-LLM)** | ~2.5-3.5 GB | **0.04-0.08 s** | **2.5-3.5 GB** | **4.0-4.3** | 良好 | **延遲極低、流匹配架構** |
| XTTS-v2 | >1.5 GB | >3 s (推估) | >4 GB | 4.3-4.6 | 優秀 | 語音克隆（不適合邊緣）|

**選型建議**：
- 功能提示音：**Piper**（延遲最低）
- 日常對話：**MeloTTS**（中文自然度佳）
- 情感互動：**Qwen3-TTS**（支援 Voice Design）
- 極低延遲：**F5-TTS**（TensorRT-LLM 優化後）

---

## 多卡並行與故障切換

### 服務化部署

| 工具 | 用途 |
|------|------|
| **Triton Inference Server** | 通用模型伺服器、多框架後端、動態批次 |
| **vLLM** | LLM 專用引擎 |
| **Ray Serve** | Python 原生、多模型組合推理 |

### 避免顯存碎片化

**問題**：各自起 Python process → 權重重複載入 → 顯存切碎

**解法**：
- Triton 集中管理多模型
- vLLM 專用引擎
- Ray Serve 資源排程

### 故障切換

**Kubernetes + NVIDIA device plugin**：
- Deployment/Replica 形式
- 健康狀態檢查
- 自動重啟/換節點

---

## 對話深度與記憶

### 記憶層級

| 層級 | 範圍 | 技術 |
|------|------|------|
| **工作記憶** | 當前對話 | LLM context window |
| **短期記憶** | 今日對話 | 滑動窗口 + 摘要 |
| **長期記憶** | 歷史偏好 | 向量資料庫 (ChromaDB/Milvus) |
| **程式記憶** | 技能策略 | LoRA/微調 |

### 實體記憶

- 記得「人名、地點、物品位置」
- 向量資料庫儲存對話嵌入
- 語義檢索相關歷史

---

## 雲端優先 + 離線備援架構

### 三層架構

| 層級 | 功能 | 觸發條件 |
|------|------|----------|
| **第一層** | VAD + Wake Word + 固定指令 | 永遠可用 |
| **第二層** | Whisper tiny/base + 規則 NLU | 網路不穩 |
| **第三層** | 雲端 ASR/LLM/TTS | 網路恢復 |

### 網路偵測與自動切換

**多層次偵測機制**：

| 層級 | 檢測內容 | 頻率 | 失敗閾值 |
|:---|:---|:---|:---|
| 第一層：連線層 | ping 預設閘道器 | 5 秒 | 連續 3 次 |
| 第二層：DNS 層 | 解析公共 DNS | 10 秒 | 連續 2 次 |
| 第三層：服務層 | HTTP 健康檢查雲端 API | 30 秒 | 連續 2 次 |

**切換策略**：進入 OFFLINE 後，需**持續 30 秒穩定連線**才回切 ONLINE，防止震盪。

### 開源語音助手框架

| 專案 | 特點 |
|------|------|
| **Rhasspy** | Fully offline 語音助手 |
| **Open Voice OS** | Plugin 架構、可換 STT/TTS/Wake Word |
| **Home Assistant Voice** | 支援雲端與本地多種後端、可配置降級策略 |

**推薦參考**：Open Voice OS 的容器化架構與 K3s 編排方式

---

## 語音互動 UX

### 關鍵延遲預算

| 階段 | 目標延遲 |
|------|----------|
| 語音喚醒 | <200ms |
| ASR | 200-500ms |
| LLM 規劃 | 500-1500ms |
| TTS | 200-500ms |
| **總計** | **<2s** |

### 打斷處理

- 人說話時機器人正在說
- 如何優雅切換？
- 常見：VAD 檢測到新語音 → 暫停 TTS → 切換聆聽模式

---

## 30 輪驗收工具（2026-03-14 新增）

Phase 1-4 各自通過後，需要端到端可重複驗證。以下工具用於 30 輪統計測試。

### 檔案索引

| 檔案 | 用途 |
|------|------|
| `speech_processor/speech_processor/speech_test_observer.py` | Observer node：訂閱 topic、聚合 RoundRecord、輸出 CSV/JSON |
| `speech_processor/test/test_speech_test_observer.py` | 單元測試（20 tests） |
| `test_scripts/speech_30round.yaml` | 測試定義（15 固定句 + 15 自由句） |
| `scripts/clean_speech_env.sh` | 環境清理（kill tmux sessions + speech nodes） |
| `scripts/run_speech_test.sh` | 一鍵 orchestration（clean → build → launch → observe → report） |

### 快速使用

```bash
# 完整流程（含 build + driver 啟動）
bash scripts/run_speech_test.sh

# 跳過 build，假設 driver 已在跑
bash scripts/run_speech_test.sh --skip-driver --skip-build

# 指定不同 YAML
bash scripts/run_speech_test.sh --yaml=test_scripts/custom.yaml
```

### 輸出

- `test_results/speech_test_YYYYMMDD_HHMMSS.csv` — 逐輪原始紀錄
- `test_results/speech_test_YYYYMMDD_HHMMSS_summary.json` — 摘要統計 + PASS/MARGINAL/FAIL 評分

### 通過門檻（來源：jetson-MVP 測試手冊 §14.1）

| 指標 | 門檻 |
|------|------|
| Fixed round 命中率 | ≥ 80% |
| E2E 中位數延遲 | ≤ 3500ms |
| E2E 最差延遲 | ≤ 6000ms |
| Go2 播放成功率 | ≥ 80% |

> 詳細設計見 `docs/superpowers/specs/2026-03-14-speech-30round-validation-design.md`

---

## 參考資源

- [Whisper](https://github.com/openai/whisper)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [WeNet](https://github.com/wenet-e2e/wenet)
- [FunASR](https://github.com/alibaba-damo-academy/FunASR)
- [vLLM](https://github.com/vllm-project/vllm)
- [MeloTTS](https://github.com/myshell-ai/MeloTTS)
- [StyleTTS2](https://github.com/yl4579/StyleTTS2)
- [Bark](https://github.com/suno-ai/bark)
- [openWakeWord](https://github.com/dscripka/openWakeWord)
- [Silero VAD](https://github.com/snakers4/silero-vad)
- [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR)
- [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)
- [F5-TTS](https://github.com/SWivid/F5-TTS)

# OpenClaw + Jetson Orin Nano 架構可行性評估

## 結論摘要

✅ **可行性：高，但有條件**

這個架構**可行且創新**，但必須遵循「快系統本地處理 + OpenClaw 高階決策」的分層原則。8GB 記憶體足夠運行 OpenClaw + ROS2 + 本地導航，但複雜 AI 模型必須 offload 到 GPU Server。

---

## 建議架構（可行性版本）

```
┌─────────────────────────────────────────────────────────────────────┐
│                        使用者互動層                                  │
│     WhatsApp / Telegram / Slack / Discord / WebChat / TUI           │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│              Jetson Orin Nano SUPER 8GB (本地大腦)                   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  OpenClaw Gateway (控制中樞)                                  │    │
│  │  ├── system.run tool → 執行 ROS2 指令                        │    │
│  │  ├── sessions_* tools → 多 agent 協作                       │    │
│  │  ├── Memory → 使用者偏好/歷史紀錄                             │    │
│  │  └── ElevenLabs TTS → 語音回饋                              │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Sensor Gateway (感測器中介層) - 必須自建                     │    │
│  │  ├── 訂閱 ROS2 topics (/point_cloud2, /camera/depth)         │    │
│  │  ├── 資料降採樣 (點雲→障礙物列表, 深度→距離統計)              │    │
│  │  └── 提供 API: snapshot (拉) + stream (推)                  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  ROS2 Humble (機器人堆疊)                                     │    │
│  │  ├── ros-mcp-server → MCP 協定轉 ROS2                        │    │
│  │  ├── go2_robot_sdk → Go2 驅動                                │    │
│  │  ├── Nav2 + SLAM → 本地避障導航 (<200ms)                     │    │
│  │  ├── coco_detector → 本地 80 類物件偵測                      │    │
│  │  └── Safety Layer → 緊急停止/限速                           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  感測器層                                                     │    │
│  │  ├── RealSense D435 (深度 + RGB)                             │    │
│  │  ├── LiDAR (/point_cloud2)                                   │    │
│  │  └── Go2 內建相機                                            │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────┬───────────────────────────────┘
                                       │ CycloneDDS (<1ms)
                                       ↓
                            ┌─────────────────────┐
                            │   Go2 機器狗 (MCU)   │
                            │   45+ 動作 / 感測器  │
                            └─────────────────────┘
                                       ↑
┌──────────────────────────────────────┴───────────────────────────────┐
│                     GPU Server (RTX 6000) - 慢系統                    │
│  (當 Jetson 8GB 不足時，透過 HTTP API 呼叫)                           │
│  ├── Qwen2.5-72B → 複雜語意理解                                      │
│  ├── LLaVA-34B → 高階視覺理解 (需要時)                               │
│  ├── Whisper Large V3 → 精準語音轉文字                               │
│  └── SAM2 → 精確物件追蹤 (需要時)                                    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 關鍵發現

### 1. OpenClaw 終端機操作能力 ✅

- **system.run / bash tool**：可以執行任意終端機指令
- **適用於**：`ros2 topic pub /cmd_vel ...`、`ros2 service call /stop_movement ...`
- **限制**：不適合執行長時間 blocking 的 roslaunch（需要用 daemon 模式）

**使用範例**：
```json
{
  "tool": "system.run",
  "params": {
    "command": "ros2 topic pub /cmd_vel geometry_msgs/Twist '{linear: {x: 0.1}, angular: {z: 0.0}}' --once",
    "timeout": 5000
  }
}
```

### 2. 感測器資料整合架構 ✅

**Oracle 專家建議**：不要直接把原始感測器資料灌進 OpenClaw！

**正確做法**：
```
ROS2 原始感測器
    ↓
Perception Bridge (降採樣/特徵提取)
    ↓
Sensor Gateway (ring buffer + API)
    ↓
OpenClaw 自定義 node (snapshot/stream)
    ↓
Agent 決策
```

**傳輸資料類型**：
| 資料類型 | 原始大小 | 處理後 | 頻率 |
|---------|---------|--------|------|
| LiDAR 點雲 | ~10MB/s | 障礙物列表 (JSON, ~1KB) | 10Hz |
| 深度影像 | ~5MB/s | 距離統計 (JSON, ~500B) | 10Hz |
| RGB 影像 | ~10MB/s | JPEG keyframe | 1-2Hz |

### 3. 資源需求評估 ✅

**Jetson Orin Nano SUPER 8GB 分配**：

| 組件 | 預估記憶體 | 備註 |
|------|-----------|------|
| Jetson OS + 系統 | ~1.5GB | 作業系統 overhead |
| OpenClaw Gateway | ~500MB-1GB | Node.js runtime |
| ROS2 Humble core | ~500MB | 基本節點 |
| Nav2 + SLAM | ~1-1.5GB | 導航堆疊 |
| RealSense ROS2 | ~300-500MB | 深度 + RGB |
| coco_detector | ~300-500MB | MobileNet 模型 |
| Sensor Gateway | ~200-300MB | 中介層服務 |
| **預留緩衝** | ~2GB | GPU 共享記憶體 |
| **總計** | **~6.5-7.5GB** | ✅ **在 8GB 範圍內** |

**結論**：8GB **夠用**，但需要優化：
- 使用 Docker 資源限制
- 關閉不必要的 ROS2 節點
- 調整 Nav2 參數降低記憶體使用

### 4. 快系統 <200ms 的實現 ✅

**關鍵原則**：快反應**不能**經過 OpenClaw/LLM！

**分層架構**：
| 層級 | 延遲 | 責任 | 實現位置 |
|------|------|------|----------|
| **Layer 0** | <50ms | 緊急停止/碰撞避免 | ROS2 Safety Node (本地) |
| **Layer 1** | <200ms | 避障導航/路徑規劃 | Nav2 (本地) |
| **Layer 2** | 500ms-2s | 任務策略/目標選擇 | OpenClaw Agent |
| **Layer 3** | 2-5s | 複雜語意/VLM | GPU Server |

**運作流程**：
1. OpenClaw 發出高階指令：「去客廳找沙發」
2. Nav2 本地規劃路徑並執行（<200ms 反應）
3. Safety Node 持續監測 LiDAR，遇障礙立即反應（<50ms）
4. OpenClaw 監控進度，必要時調整策略

---

## 快系統 vs 慢系統分工

### 快系統 (Jetson 8GB) - 必須本地

| 功能 | 技術 | 延遲 |
|------|------|------|
| 避障導航 | Nav2 + SLAM | <200ms |
| 緊急停止 | Safety Layer | <50ms |
| 物件偵測 | coco_detector | <150ms |
| 深度估計 | RealSense D435 | <30ms |
| 簡單指令理解 | 小型 LLM (3-4B, 量化) | <500ms |
| TTS 播放 | ElevenLabs (快系統緩存) | <200ms |

### 慢系統 (GPU Server RTX 6000) - 遠端呼叫

| 功能 | 技術 | 延遲 | 觸發條件 |
|------|------|------|----------|
| 複雜語意理解 | Qwen2.5-72B | 2-5s | 模糊/多義指令 |
| 視覺場景理解 | LLaVA-34B | 3-5s | 需要視覺描述 |
| 精準語音轉文字 | Whisper Large V3 | 1-2s | 音訊輸入時 |
| 物件追蹤 | SAM2 | ~22ms | 需要精確追蹤時 |
| 人體姿態 | RTMPose | ~2ms | 互動動作時 |

**Offload 機制**：
```python
# OpenClaw Agent 決策邏輯
if task_complexity == "high":
    # 呼叫 GPU Server
    result = http_post("http://gpu-server:8000/vlm", {
        "image": keyframe_jpeg,
        "prompt": "描述這個場景中有什麼物品"
    })
else:
    # 本地處理
    result = local_llm(process(prompt))
```

---

## 風險評估

### ⚠️ 高風險：OpenClaw 安全漏洞

**問題**：
- 1,800+ 暴露實例洩漏 API 金鑰和聊天歷史
- 預設配置可能允許未授權存取

**緩解措施**：
1. **網路隔離**：只允許區網存取（192.168.x.x）
2. **Tailscale**：使用 tailnet-only 模式，不暴露公開 IP
3. **密碼驗證**：強制設置 `gateway.auth.mode: "password"`
4. **DM 配對**：啟用 `dmPolicy="pairing"`，只允許白名單使用者
5. **Firewall**：關閉所有不需要的 ports

### ⚠️ 中風險：記憶體壓力

**問題**：8GB 同時跑多個服務可能 OOM

**緩解措施**：
1. **Docker 限制**：為每個容器設置記憶體上限
2. **交換空間**：啟用 zram 或外部 swap
3. **監控**：設置 Prometheus/Grafana 監控記憶體使用
4. **優雅降級**：記憶體不足時關閉非關鍵功能

### ⚠️ 中風險：延遲控制

**問題**：感測器 → OpenClaw → 決策的延遲可能超過 200ms

**緩解措施**：
1. **本地 Safety Layer**：緊急情況不經過 OpenClaw
2. **資料降採樣**：只傳精簡表徵，不傳原始點雲
3. **快取策略**：常用資料預先載入記憶體

---

## 實作路線圖

### Phase 1：基礎驗證（1-2 週）

1. **Jetson 環境建置**
   - 安裝 JetPack + CUDA + ROS2 Humble
   - 測試 OpenClaw Gateway 運行
   - 驗證記憶體使用

2. **ROS2 整合測試**
   - 部署 ros-mcp-server
   - 測試 system.run 執行 ROS2 指令
   - 驗證 Go2 基本控制

3. **感測器驗證**
   - RealSense D435 安裝與測試
   - LiDAR 資料品質確認
   - coco_detector 本地推論測試

### Phase 2：中介層開發（2-3 週）

1. **Sensor Gateway 開發**
   - ROS2 Bridge 節點（資料降採樣）
   - Gateway API 服務（snapshot/stream）
   - WebSocket/HTTP 介面

2. **OpenClaw Node 擴展**
   - 自定義 sensors node
   - 實作 `get_latest()` 和 `subscribe()`
   - 整合測試

3. **資料流優化**
   - 延遲測量與優化
   - 背壓處理
   - 錯誤恢復

### Phase 3：快/慢系統整合（2 週）

1. **GPU Server 介面**
   - HTTP API 封裝（Qwen/LLaVA/Whisper）
   - 自動分流邏輯（簡單任務本地，複雜任務遠端）
   - 容錯機制（遠端失敗時降級本地處理）

2. **Agent 協作**
   - 多 agent 分工設計
   - Memory 整合（使用者偏好）
   - TTS 整合（ElevenLabs）

### Phase 4：測試與部署（1-2 週）

1. **整合測試**
   - 端到端場景測試（尋物、導航、避障）
   - 壓力測試（長時間運行）
   - 安全測試（未授權存取防護）

2. **部署優化**
   - Docker Compose 配置
   - 開機自動啟動
   - 監控告警

---

## 成本效益分析

### 硬體成本

| 項目 | 價格 | 備註 |
|------|------|------|
| Jetson Orin Nano SUPER 8GB | $249 | 本地大腦 |
| RealSense D435 | ~$200 | 深度攝影機 |
| 網路線/配件 | ~$50 | 連接配件 |
| **總計** | **~$500** | |

### 與當前架構比較

| 項目 | 當前 (Mac VM + GPU Server) | 新架構 (Jetson + OpenClaw) |
|------|---------------------------|---------------------------|
| **使用者介面** | 需要自建 Web UI | ✅ 免費獲得 WhatsApp/Telegram/Slack/Web |
| **記憶系統** | 需要自建 | ✅ OpenClaw 內建 |
| **TTS** | ElevenLabs 整合 | ✅ OpenClaw 內建 |
| **語音輸入** | 需要自建 | ✅ OpenClaw 支援語音 wake |
| **移動性** | 僅限實驗室 | ✅ 可移動部署（有線/無線） |
| **成本** | Mac VM 資源成本 | ✅ 一次性 $500 |
| **複雜度** | 中等 | ⚠️ 較高（需整合多組件） |
| **風險** | 低 | ⚠️ 中（OpenClaw 新專案） |

---

## 最終建議

### ✅ 建議採用此架構，條件如下：

1. **必須自建 Sensor Gateway**：這是關鍵中介層，不能跳過
2. **必須分層處理**：快反應留在 Jetson，OpenClaw 只做高階決策
3. **必須安全隔離**：使用 Tailscale + 密碼，避免暴露公開網路
4. **必須監控資源**：8GB 容易滿，需要監控和優雅降級

### 🎯 預期成果

- **即時互動**：透過 WhatsApp/Telegram 直接與機器狗對話
- **智能導航**：自然語言指令 → 自主導航避障
- **個人化記憶**：機器狗記得使用者偏好和常用物品位置
- **語音互動**：語音喚醒 + TTS 回饋
- **雲地協作**：簡單任務本地，複雜理解上雲

---

## 研究任務完成狀態

- [✅] OpenClaw 終端機操作能力分析 (bg_d973dc03)
- [✅] Jetson + OpenClaw + ROS2 資源評估 (bg_9cb5530c)
- [✅] OpenClaw 感測器資料整合架構 (bg_b9fa9d83)
- [✅] 快/慢系統分工策略設計
- [✅] 安全風險評估


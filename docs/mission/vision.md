# PawAI 專案願景 (Pi-Mono + Skills 架構版)

**版本：** v5.0 (Nano Super)  
**日期：** 2026-02-11  
**狀態：** 🚧 重構進行中

---

## 🎯 專案使命

**打造「PawAI」—— 一隻真正聰明、安全、有技能的機器狗。**

我們正在將傳統的 ROS2 機器人控制，升級為 **AI Agent 驅動的 Skills 架構**。透過 [Pi-Mono](https://github.com/badlogic/pi-mono) 框架，讓 Go2 機器狗具備：

- 🧠 **智慧決策**：LLM Agent 理解自然語言，規劃行動序列
- 🛡️ **安全優先**：所有動作經過 Safety Gate，禁止危險指令
- 🎯 **技能導向**：模組化 Skills，可組合、可測試、可擴展
- 🖥️ **雙介面支援**：本地 TUI 監控 + Web 遠端控制

---

## 🏗️ 架構演進

### 過去：MCP 通用工具模式

```
User → Claude Desktop → ros-mcp-server → ROS2 → Go2
         ↓
    43個通用工具 (call_service, publish_topic, ...)
    
問題：
- 功能過於通用，缺乏 Go2 專屬抽象
- 安全邊界不夠硬（LLM 可能直接發 cmd_vel）
- 無法支援複雜的多步驟任務
```

### 現在：Skills-First 架構

```
┌─────────────────────────────────────────────────────────┐
│                   PawAI Agent (Pi-Mono)                  │
│                   (開發機 / Jetson)                      │
├─────────────────────────────────────────────────────────┤
│  Pi-Agent-Core (Agent Runtime)                          │
│       ↓ Skill Calling                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ perception  │  │   motion    │  │   navigation    │ │
│  │  skills     │  │   skills    │  │     skills      │ │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘ │
│         └─────────────────┴──────────────────┘          │
│                    Safety Gate (強制限制)               │
│                    - MAX_LINEAR: 0.3 m/s               │
│                    - MAX_ANGULAR: 0.5 rad/s            │
│                    - MAX_DURATION: 10.0 s              │
│                    - 自動 emergency-stop               │
│                          ↓                              │
│              ROS2 Bridge (roslibjs/WebSocket)          │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────┐
│              ROS2 Humble (Jetson Orin Nano SUPER 8GB)   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ go2_driver  │  │   skills/   │  │  sensor_gateway │ │
│  │   _node     │  │   *_service │  │                 │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 核心設計原則

### 1. Safety-First 設計

| 限制項目 | 數值 | 說明 |
|---------|------|------|
| **最大線速度** | 0.3 m/s | 老人安全行走速度 |
| **最大角速度** | 0.5 rad/s | 避免快速旋轉暈眩 |
| **最大持續時間** | 10.0 s | 強制定時停止 |
| **緊急停止** | 任意時刻 | 任何失敗自動觸發 |

**關鍵規則**：
- ❌ **禁止** Agent 直接發送 `/cmd_vel`
- ✅ **強制** 所有移動經過 `safe-move` Skill
- ✅ **強制** 失敗時自動呼叫 `emergency-stop`

### 2. Skills Contract

每個 Skill 都有明確的：
- **Use when**：什麼時候使用
- **Do NOT use for**：什麼時候不該用
- **執行步驟**：4-7 步的標準流程
- **失敗回退**：必含 stop 的錯誤處理
- **驗收測試**：可驗證的測試句

### 3. 分層架構

```
Layer 4: Agent (Pi-Agent-Core)
         - LLM 決策、規劃、對話
         
Layer 3: Skills Runtime
         - Skill Router、狀態管理
         
Layer 2: Skills
         - perception/ motion/ navigation/ action/ system
         
Layer 1: Safety Gate
         - 硬限制、clamp、emergency stop
         
Layer 0: ROS2
         - topics、services、actions
```

---

## 🛠️ Skills 藍圖

### Phase 1: MVP Skills (進行中)

| Skill | 類別 | 說明 | 狀態 |
|-------|------|------|------|
| `safe-move` | motion | 安全移動（速度/時間限制） | 🚧 開發中 |
| `emergency-stop` | motion | 緊急停止 | 🚧 開發中 |
| `find-object` | perception | 尋找物體（視覺辨識） | 🚧 開發中 |
| `perform-action` | action | 執行動作（站立、蹲下） | 🚧 開發中 |
| `system-status` | system | 系統健康檢查 | 🚧 開發中 |

### Phase 2: 導航 Skills

| Skill | 說明 |
|-------|------|
| `navigate-to` | Nav2 導航到指定點 |
| `nav-status` | 查詢導航狀態 |
| `cancel-nav` | 取消導航 |

### Phase 3: 進階 Skills

| Skill | 說明 |
|-------|------|
| `avoid-obstacles` | 自動避障 |
| `explore-map` | 地圖探索 |
| `emotional-interaction` | 情感互動 |
| `voice-chat` | 語音對話 |

---

## 💻 技術棧

### 核心框架

| 組件 | 技術 | 用途 |
|------|------|------|
| **Agent Runtime** | pi-agent-core | Skills 調度、狀態管理 |
| **LLM API** | pi-ai | 統一多供應商 LLM 介面 |
| **本地 UI** | pi-tui | 終端監控介面 |
| **Web UI** | pi-web-ui | 遠端控制面板 |
| **ROS2 橋接** | roslibjs | WebSocket 連接 ROS2 |

### 硬體平台

| 設備 | 規格 | 用途 |
|------|------|------|
| **Jetson Orin Nano SUPER** | 8GB RAM / 1024 CUDA | 邊緣運算中樞 |
| **Go2 Pro** | Unitree 四足機器人 | 運動平台 |

### LLM 支援

- OpenAI GPT-4 Turbo
- Anthropic Claude 3.5 Sonnet
- Google Gemini Pro
- 本地 vLLM (via pi-pods)

---

## 📈 與原願景的差異

| 項目 | 原願景 (2025/12) | 新願景 (2026/02) | 原因 |
|------|------------------|------------------|------|
| **控制架構** | MCP 通用工具 | **Skills-First Agent** | 安全、專屬、可控 |
| **技術棧** | Python/ros-mcp-server | **TypeScript/Pi-Mono** | 現代 Agent 框架 |
| **安全層** | Prompt 提示 | **硬限制 Safety Gate** | 防止 LLM 幻覺 |
| **介面** | 僅 CLI | **TUI + Web UI** | 更好的使用者體驗 |
| **抽象層級** | 低階 ROS2 操作 | **高階 Skills 組合** | 更易開發維護 |

---

## 🎬 使用場景

### 場景 1：尋物

```
User: 「幫我找眼鏡」
Agent: 收到！我來幫您找眼鏡。
      → find-object (glasses)
      ← 發現眼鏡在沙發上
      → navigate-to (sofa)
      ← 導航完成
Agent: 找到眼鏡了！在沙發上。
```

### 場景 2：安全移動

```
User: 「向前走 5 秒」
Agent: 規劃：以 0.2 m/s 前進 5 秒（已限制在最大 10 秒內）。確認執行嗎？
User: 確認
Agent: → safe-move (linear=0.2, duration=5)
      ← 完成！實際移動 4.8 秒
```

### 場景 3：緊急狀況

```
[執行中突然遇到障礙]
Agent: ⚠️ 偵測到障礙物！
      → emergency-stop
      ← 已緊急停止
Agent: 已緊急停止，請確認安全後再繼續。
```

---

## ✅ 成功指標

| 指標 | 目標值 | 說明 |
|------|--------|------|
| **Skill 覆蓋率** | 80%+ | 常用流程不需直接使用 MCP tools |
| **安全限制生效** | 100% | 所有移動經過 safety gate |
| **緊急停止延遲** | < 500ms | 任意時刻可中斷 |
| **UI 可用性** | TUI + Web | 雙介面正常運作 |
| **LLM 整合** | 3+ 供應商 | OpenAI/Anthropic/Google |

---

## 📚 參考文件

- [Pi-Mono GitHub](https://github.com/badlogic/pi-mono)
- [Pi.dev](https://pi.dev)
- [Ros2_Skills.md](../refactor/Ros2_Skills.md) - Skills 詳細設計
- [refactor_plan.md](../refactor/refactor_plan.md) - 重構執行計畫
- [pi_agent.md](../refactor/pi_agent.md) - Pi-Mono 整合方案

---

**版本紀錄：**

| 版本 | 日期 | 變更 |
|------|------|------|
| v1.0 | 2025/11 | 初版願景 (雲端 MCP) |
| v2.0 | 2025/12 | 加入 MCP 架構 |
| v3.0 | 2026/01 | 轉向 Jetson 邊緣運算 |
| v4.0 | 2026/02 | Skills-First 架構 (本文件) |
| v5.0 | 2026/02 | Pi-Mono + Nano Super (本文件) |

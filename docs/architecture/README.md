# PawAI 系統架構文件

**專案**：老人與狗 (Elder and Dog) - Go2 機器狗智慧陪伴系統  
**版本**：v1.0  
**定案日期**：2026-03-08  
**狀態**：介面凍結（3/9 後不再變更外部契約）

---

## 文件導航

| 文件 | 用途 | 適合讀者 |
|------|------|----------|
| **[README.md](./README.md)** (本文件) | 架構總覽與導航 | 全員 |
| **[clean_architecture.md](./clean_architecture.md)** | Clean Architecture 分層原則與實作 | 開發者 |
| **[face_perception.md](./face_perception.md)** | 人臉辨識模組詳細架構 | Face Owner |
| **[interaction_contract.md](./interaction_contract.md)** | ROS2 介面契約（Topic/Action/參數） | 全員 |
| **[data_flow.md](./data_flow.md)** | 資料流與互動流程 | 開發者、整合者 |

---

## 1. 架構總覽

### 1.1 三層架構

PawAI 系統採用 **三層架構** 設計：

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Interaction Executive v1（中控層）                  │
│  ├─ 事件聚合器 (Event Aggregator)                           │
│  ├─ 狀態機 (State Machine)                                  │
│  ├─ 技能分派器 (Skill Dispatcher)                           │
│  ├─ 安全仲裁器 (Safety Guard)                               │
│  └─ 控制權管理 (Control Arbitration)                        │
└─────────────────────────────────────────────────────────────┘
                              ↑↓ ROS2 Topics / Actions
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Perception / Interaction Module Layer              │
│  ├─ face_perception (人臉辨識)                              │
│  ├─ speech_processor (語音處理)                            │
│  └─ gesture_module (手勢辨識 - P1)                          │
└─────────────────────────────────────────────────────────────┘
                              ↑↓ ROS2 Topics
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Device / Runtime Layer                             │
│  ├─ go2_robot_sdk (Go2 驅動)                                │
│  ├─ realsense2_camera (D435 相機)                          │
│  └─ ROS2 Humble (rclpy/rclcpp)                              │
└─────────────────────────────────────────────────────────────┘
```

**設計原則**：
1. **單一控制權**：所有動作唯一出口在 Layer 3
2. **事件驅動**：Layer 2 發布事件，Layer 3 訂閱後決策
3. **介面凍結**：3/9 後 topic/schema/action 不再變更

---

## 2. 核心模組

### 2.1 已落地模組

| 模組 | 路徑 | Layer | 狀態 | 負責人 |
|------|------|-------|------|--------|
| **go2_robot_sdk** | `go2_robot_sdk/` | Layer 1 | ✅ 穩定 | System Architect |
| **face_perception** | `face_perception/` | Layer 2 | ✅ MVP 完成 | 楊 |
| **go2_interfaces** | `go2_interfaces/` | 共用介面 | ✅ 穩定 | System Architect |

### 2.2 開發中模組

| 模組 | 路徑 | Layer | 狀態 | 負責人 |
|------|------|-------|------|--------|
| **speech_processor** | `speech_processor/` | Layer 2 | 🔄 開發中 | 鄔 |
| **interaction_executive** | `interaction_executive/` | Layer 3 | 🔄 設計中 | System Architect |

---

## 3. Clean Architecture 實作

所有 Layer 2 模組採用 **Clean Architecture** 分層：

```
face_perception/face_perception/
├── domain/                    # 無 ROS2 依賴
│   ├── entities/              # FaceDetection, FaceTrack
│   └── interfaces/            # IFaceDetector, IFaceTracker...
│
├── application/               # 使用案例層
│   └── services/              # FacePerceptionService
│
├── infrastructure/            # 外部依賴適配
│   ├── detector/              # YuNetDetector
│   ├── tracker/               # IOUTracker
│   ├── recognizer/            # SFaceRecognizer (可選)
│   └── ros2/                  # ROS2FacePublisher
│
└── presentation/              # ROS2 Node 入口
    ├── face_perception_node.py
    └── face_interaction_node.py
```

**詳見**：[clean_architecture.md](./clean_architecture.md)

---

## 4. 關鍵介面

### 4.1 Topic 介面

| Topic | 類型 | 說明 | 發布者 | 訂閱者 |
|-------|------|------|--------|--------|
| `/state/perception/face` | String(JSON) | 人臉狀態 (10 Hz) | face_perception | Executive |
| `/event/face_detected` | String(JSON) | 人臉偵測事件 | face_perception | Executive |
| `/webrtc_req` | WebRtcReq | Skill 執行請求 | face_interaction | go2_driver |

### 4.2 技能命令

| Skill | api_id | 說明 | 安全等級 |
|-------|--------|------|----------|
| `Hello` | 1016 | 揮手打招呼 | 🟢 安全 |
| `Sit` | 1009 | 坐下 | 🟢 安全 |
| `BalanceStand` | 1002 | 平衡站立 | 🟢 安全 |

**詳見**：[interaction_contract.md](./interaction_contract.md)

---

## 5. 資料流

### 5.1 人臉偵測 → 揮手 流程

```
[RealSense D435]
    ↓ RGB + Depth (640×480 @ 30Hz)
[face_perception_node]
    ↓ YuNetDetector.detect()
    ↓ IOUTracker.update() + 深度估計
    ↓ ROS2FacePublisher
    ↓ /state/perception/face (JSON, 10Hz)
    ↓ /event/face_detected (JSON, on trigger)
[face_interaction_node]
    ↓ 檢查 cooldown (5s)
    ↓ WebRtcReq → /webrtc_req
[go2_driver_node]
    ↓ WebRTC → Go2 Pro
[Go2 Robot]
    ↓ 執行 Hello (1016) 🐕👋
```

**詳見**：[data_flow.md](./data_flow.md)

---

## 6. 專案結構

```
elder_and_dog/
├── docs/
│   └── architecture/          # 本目錄
│       ├── README.md          # 本文件
│       ├── clean_architecture.md
│       ├── face_perception.md
│       ├── interaction_contract.md
│       └── data_flow.md
│
├── go2_robot_sdk/             # Layer 1: Go2 驅動
│   └── go2_robot_sdk/
│       ├── domain/            # Clean Architecture
│       ├── application/
│       ├── infrastructure/
│       └── presentation/
│
├── face_perception/           # Layer 2: 人臉辨識
│   └── face_perception/
│       ├── domain/            # 實體、介面
│       ├── application/       # 服務
│       ├── infrastructure/    # 實作
│       └── presentation/      # ROS2 節點
│
├── go2_interfaces/            # ROS2 共用介面
│   ├── msg/
│   ├── srv/
│   └── action/
│
└── speech_processor/          # Layer 2: 語音 (開發中)
```

---

## 7. 相關文件

- **[mission/README.md](../mission/README.md)** - 專案使命與願景
- **[人臉辨識/README.md](../人臉辨識/README.md)** - 人臉模組詳細設計
- **[setup/README.md](../setup/README.md)** - 環境建置指南

---

*維護者：System Architect*  
*最後更新：2026-03-08*

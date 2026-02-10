# PawAI 專案重構計畫 (Nano Super v5.0)

**日期**: 2026-02-10  
**目標**: 升級至 Nano Super 架構，整合 OpenClaw，重構 Skills 化架構  
**範圍**: 全專案結構重組、套件遷移、功能升級

---

## 1) 專案現況總覽

### 1.1 專案結構問題

目前專案存在以下結構性問題：

| 問題 | 嚴重程度 | 影響 |
|-----|---------|------|
| ROS2 套件散佈根目錄 | 🔴 高 | 違反 colcon 慣例 |
| Git 倉庫髒亂 (二進制檔案) | 🔴 高 | 21.4MB 無用數據 |
| lidar_processor Python/C++ 冗餘 | 🔴 高 | 維護困難 |
| coco_detector 過時 | 🟡 中 | 需升級 YOLO-World |
| MCP 工具過於通用 | 🟡 中 | 需 Skills 化 |

### 1.2 套件分布現況

**根目錄散落套件** (需遷移至 `src/`):
- `go2_robot_sdk/` - 主驅動套件
- `go2_interfaces/` - 自定義訊息
- `lidar_processor/` - Python LiDAR 處理 (標記刪除)
- `lidar_processor_cpp/` - C++ LiDAR 處理
- `coco_detector/` - COCO 偵測器 (標記替換)
- `speech_processor/` - TTS 語音

**已在正確位置**:
- `src/search_logic/` - Nav2 測試套件

**獨立 Python 套件** (不移動):
- `ros-mcp-server/` - MCP 伺服器

---

## 2) 各套件詳細分析

### 2.1 go2_robot_sdk (主驅動套件)

**位置**: `/go2_robot_sdk/` → 遷移至 `/src/go2_robot_sdk/`

**Clean Architecture 分層**:
```
go2_robot_sdk/go2_robot_sdk/
├── domain/                 # ✅ 無 ROS2 依賴
│   ├── entities/           # RobotConfig, RobotData
│   ├── interfaces/         # IRobotController, IRobotDataPublisher
│   ├── constants/          # RTC_TOPIC, ROBOT_CMD
│   └── math/               # Quaternion, Vector3
├── application/            # ✅ 無 ROS2 依賴
│   ├── services/           # RobotDataService, RobotControlService
│   └── utils/              # command_generator
├── infrastructure/         # ⚠️ ROS2 依賴
│   ├── webrtc/             # WebRTCAdapter, Go2Connection
│   ├── ros2/               # ROS2Publisher
│   └── sensors/            # LidarDecoder, CameraConfig
└── presentation/           # ⚠️ ROS2 節點
    └── go2_driver_node.py
```

**現有服務**:
| 服務 | 檔案 | 功能 |
|-----|------|------|
| go2_driver_node | `main.py` + `go2_driver_node.py` | 主驅動節點 |
| snapshot_service | `snapshot_service.py` | `/capture_snapshot` 相機截圖 |
| move_service | `move_service.py` | `/move_for_duration` 安全移動 |

**安全限制** (move_service):
- MAX_LINEAR = 0.3 m/s
- MAX_ANGULAR = 0.5 rad/s
- MAX_DURATION = 10.0 s
- 緊急停止: `/stop_movement`

**待補服務**:
- [ ] move_service 未在 robot.launch.py 中啟動
- [ ] Nav2 Action Service (`/navigate_to_pose_simple`)
- [ ] Sensor Gateway 節點

---

### 2.2 go2_interfaces (介面定義)

**位置**: `/go2_interfaces/` → 遷移至 `/src/go2_interfaces/`

**現有訊息 (34 個)**:

| 類別 | 訊息 | 用途 |
|-----|------|------|
| **機器人狀態** | Go2State | 運動狀態 (位置、速度、障礙物距離) |
| **感測器** | IMU, LidarState | IMU 數據、LiDAR 狀態 |
| **控制** | WebRtcReq | WebRTC 指令 (api_id, topic, parameter) |
| **底層** | LowState, LowCmd | 馬達、電池、腳力 |
| **特殊** | VoxelMapCompressed | 壓縮體素地圖 |

**現有服務**:
- `MoveForDuration.srv` - 安全移動請求/回應

**需新增訊息**:
```msg
# msg/ObstacleList.msg
std_msgs/Header header
Obstacle[] obstacles
float32 processing_time_ms
string algorithm_version

# msg/Obstacle.msg
int32 id
float64[3] center
float64[3] size
int32 point_count
float32 confidence
```

---

### 2.3 lidar_processor (Python) - 標記刪除

**狀態**: ⚠️ **確認 C++ 版本功能後刪除**

**檔案**:
- `lidar_to_pointcloud_node.py` - 點雲聚合與儲存
- `pointcloud_aggregator_node.py` - 點雲過濾

**Python 版本獨特功能** (需確認 C++ 有無):

| 功能 | Python 實現 | C++ 狀態 |
|-----|------------|---------|
| Open3D 地圖儲存 | ✅ | ❓ |
| 統計離群值移除 | ✅ (自實現) | ✅ (PCL) |
| Range 過濾 (0.1-20m) | ✅ | ❓ |
| Height 過濾 (-2-3m) | ✅ | ❓ |
| 動態降取樣 | ✅ | ❓ |

**Topics**:
- 訂閱: `/point_cloud2`
- 發布: `/pointcloud/aggregated`, `/pointcloud/filtered`, `/pointcloud/downsampled`

**驗證清單** (刪除前必做):
- [ ] C++ 版本有統計離群值移除
- [ ] C++ 版本有 Range + Height 過濾
- [ ] C++ 版本有動態降取樣
- [ ] C++ 版本可儲存地圖

---

### 2.4 lidar_processor_cpp (保留)

**位置**: `/lidar_processor_cpp/` → 遷移至 `/src/lidar_processor_cpp/`

**實現**:
- 基於 PCL (Point Cloud Library)
- C++17 標準
- 節點:
  - `lidar_to_pointcloud_node`
  - `pointcloud_aggregator_node`

**優勢**:
- Jetson 效能更好
- PCL 優化算法
- 記憶體效率更高

---

### 2.5 speech_processor (保留)

**位置**: `/speech_processor/` → 遷移至 `/src/speech_processor/`

**功能**:
- TTS (Text-to-Speech) 使用 ElevenLabs API
- 音訊快取 (MD5 hash)
- 機器狗播放 (WebRTC 分塊傳輸)

**參數**:
- provider: elevenlabs
- voice_name: XrExE9yKIg1WjnnlVkGX
- local_playback: false
- use_cache: true

**依賴**:
```python
install_requires=[
    'requests',
    'pydub',
]
```

**已知問題**:
⚠️ `setup.py` 引用了不存在的節點:
```python
'speech_synthesizer = speech_processor.speech_synthesizer_node:main',  # ❌
'audio_manager = speech_processor.audio_manager_node:main',          # ❌
```

---

### 2.6 coco_detector - 標記替換

**狀態**: 🔴 **開發 yolo_detector 完全替換**

**當前實現**:
- 模型: FasterRCNN_MobileNet_V3_Large_320_FPN
- 權重: COCO_V1 (80 類別)
- 輸入: `/camera/image_raw`
- 輸出: `/detected_objects` (Detection2DArray)
- 參數: device, detection_threshold (0.9), publish_annotated_image

**限制**:
- 僅 80 COCO 類別
- 無法零樣本偵測
- 速度較慢

**遷移目標 (YOLO-World)**:
- 模型: YOLO-Worldv2-S/M
- 零樣本偵測: 任意文字描述類別
- TensorRT 加速 (Jetson)
- 保持 Detection2DArray 輸出相容

**新介面**:
```python
# yolo_detector 參數
confidence_threshold: 0.5
nms_threshold: 0.45
classes: ["bottle", "glasses", "phone"]
model_size: "s"
```

---

## 3) 重構執行計畫

### Phase 1: 基礎重組 (Week 1-2)

#### 3.1 Git 清理
```bash
# 1. 更新 .gitignore
cat >> .gitignore << 'EOF'
# Binary data files
*.ply
*.pt
*.pth
*.onnx
*.engine
*.bin
*.bag
*.db
*.ckpt
*.safetensors

# IDE
.vscode/
.idea/
EOF

# 2. 從歷史移除大檔案 (使用 git-filter-repo)
git filter-repo --strip-blobs-bigger-than 1M
```

#### 3.2 套件遷移至 src/
```bash
# 創建臨時目錄
mkdir -p /tmp/ros_pkgs

# 移動套件
mv go2_robot_sdk go2_interfaces lidar_processor_cpp \
   speech_processor coco_detector /tmp/ros_pkgs/

# 移回 src/
mv /tmp/ros_pkgs/* src/

# 刪除 Python lidar_processor (確認 C++ 版本後)
rm -rf lidar_processor
```

#### 3.3 go2_interfaces 擴展
新增訊息定義:
- `msg/ObstacleList.msg`
- `msg/Obstacle.msg`
- `msg/NavigateToPoseSimple.srv` (Nav2 Action 封裝)

---

### Phase 2: Sensor Gateway 開發 (Week 3-4)

**目標**: 實作 Fast Path (<200ms) 障礙物偵測

**新套件**: `sensor_gateway/`

```
sensor_gateway/
├── sensor_gateway/
│   ├── sensor_gateway_node.py
│   ├── ground_removal.py      # RANSAC
│   ├── clustering.py          # Euclidean Clustering
│   └── __init__.py
├── launch/
│   └── sensor_gateway.launch.py
├── package.xml
└── setup.py
```

**資料流**:
```
/point_cloud2 (10MB/s)
    ↓
[sensor_gateway]
    ├── RANSAC Ground Removal
    ├── Euclidean Clustering (PCL)
    └── JSON Serialization
    ↓
/obstacles_json (~1KB)
    {
      "obstacles": [
        {"id": 0, "center": [x,y,z], "size": [w,h,d], ...}
      ],
      "timestamp": 1234567890.0
    }
```

---

### Phase 3: YOLO-World 整合 (Week 5-6)

**新套件**: `yolo_detector/`

```python
# yolo_detector_node.py (骨架)
from ultralytics import YOLO

class YoloDetectorNode(Node):
    def __init__(self):
        self.model = YOLO("yolov8s-worldv2.pt")
        self.model.set_classes(self.classes)
        
    def detect(self, image):
        results = self.model(image)
        return self.to_detection2d_array(results)
```

**相容性要求**:
- 輸入: `/camera/image_raw` (Image)
- 輸出: `/detected_objects` (Detection2DArray)
- 參數: confidence_threshold, nms_threshold, classes

---

### Phase 4: Skills 化重構 (Week 7-8)

參考 `docs/refactor/Ros2_Skills.md`，建立 Skills 架構:

```
skills/
├── perception/
│   └── find_object/           # 取代 find_object MCP tool
├── motion/
│   ├── safe_move/             # 包裝 /move_for_duration
│   └── emergency_stop/        # 包裝 /stop_movement
├── navigation/
│   ├── navigate_to/           # Nav2 Action 封裝
│   ├── nav_status/
│   └── cancel_nav/
├── action/
│   ├── perform_action/        # go2_perform_action
│   └── list_actions/
└── system/
    ├── check_gpu/             # GPU server 健康檢查
    ├── status/                # 系統狀態
    └── connect/               # 機器人連線
```

**安全原則**:
1. 禁止 Agent 直接發 `/cmd_vel`
2. 所有移動必經 safety gate
3. 任何失敗先執行 `emergency-stop`
4. 真機執行需明確執行意圖

---

## 4) 相依關係與順序

```
go2_interfaces (必須最先)
    ├── go2_robot_sdk
    ├── lidar_processor_cpp
    ├── speech_processor
    └── coco_detector/yolo_detector

go2_robot_sdk
    ├── launch 引用 lidar_processor_cpp
    ├── launch 引用 speech_processor
    └── 需要 sensor_gateway (新增)
```

**執行順序**:
1. go2_interfaces (新增 ObstacleList.msg)
2. lidar_processor_cpp (驗證功能)
3. speech_processor (修復 setup.py)
4. go2_robot_sdk (新增 Sensor Gateway, Nav2 Service)
5. yolo_detector (替換 coco_detector)
6. skills/ (Skills 化架構)

---

## 5) 風險與對策

| 風險 | 說明 | 對策 |
|-----|------|------|
| 結構重組破壞建構 | 移動套件後 colcon build 失敗 | 分步遷移，每次驗證 |
| lidar_processor_cpp 功能不足 | 缺少 Python 版本的過濾功能 | 先驗證，必要時移植 |
| YOLO-World TensorRT 轉換失敗 | Jetson 上無法加速 | 保留 CPU fallback |
| Skills 化過度複雜 | 架構變更太大 | 保留 MCP fallback，漸進遷移 |
| Git 歷史重寫 | filter-repo 影響協作 | 團隊同步，備份分支 |

---

## 6) 完成定義 (Definition of Done)

### Phase 1 Done:
- [ ] 所有套件遷移至 src/
- [ ] .gitignore 更新，大檔案從歷史移除
- [ ] go2_interfaces 新增 ObstacleList.msg
- [ ] colcon build 成功

### Phase 2 Done:
- [ ] sensor_gateway 節點可運行
- [ ] /obstacles_json 輸出正常
- [ ] 處理延遲 < 200ms

### Phase 3 Done:
- [ ] yolo_detector 可偵測自定義類別
- [ ] Detection2DArray 輸出相容 coco_detector
- [ ] TensorRT 加速 (可選)

### Phase 4 Done:
- [ ] 核心 5 個 skills 可獨立執行
- [ ] Demo 主流程不依賴 MCP low-level tools
- [ ] 安全限制可測試驗證

---

## 7) 參考文件

- `docs/refactor/Ros2_Skills.md` - Skills 化詳細計畫
- `go2_robot_sdk/AGENTS.md` - 驅動套件知識庫
- `go2_interfaces/AGENTS.md` - 介面定義知識庫
- `docs/01-guides/slam_nav/Jetson 8GB 快系統實作指南.md` - Jetson 優化

---

**文件版本**: v1.0  
**最後更新**: 2026-02-10  
**負責人**: Sisyphus Agent

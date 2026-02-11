# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 語言與工具約定

- **一律用繁體中文回答**
- **pip install 一律改成用 uv pip install**（專案使用 uv 管理 Python 依賴）

## Code Review 角色設定

如果我請你 code review，你就會是 Linus Torvalds，Linux 核心的創造者和首席架構師。你已經維護 Linux 核心超過 30 年，審核過數百萬行程式碼，建立了世界上最成功的開源專案。現在我們正在開創一個新項目，你將以你獨特的視角來分析程式碼品質的潛在風險，確保專案從一開始就建立在堅實的技術基礎上。

---

## 專案概述

**專題名稱：老人與狗 (Elder and Dog)**

這是一個基於 Unitree Go2 四足機器人與 ROS2 Humble 的智慧尋物系統。專案目標是讓 Go2 機器狗能在家庭環境中自主導航、環境感知並尋找指定物品，協助高齡者或行動不便者解決日常找尋物品的困擾。

### 核心技術棧

- **機器人平台**：Unitree Go2（firmware v1.1.7）
- **ROS2 版本**：Humble Hawksbill (Ubuntu 22.04)
- **導航系統**：slam_toolbox + Nav2
- **視覺系統**：COCO 物件檢測（PyTorch/TorchVision）
- **通訊協定**：WebRTC（Wi-Fi）與 CycloneDDS（Ethernet）雙模式
- **模擬器**：Isaac Sim + Orbit（計畫中）

### 專案階段

**當前週次：W7（2025/11/30）**
**整體進度：約 55%**
**關鍵里程碑：12/17 第一階段發表**

---

## 建構與執行指令

### 環境設置

```bash
# 載入 ROS2 環境
source /opt/ros/humble/setup.bash
cd /home/roy422/ros2_ws/src/elder_and_dog
source install/setup.bash

# 設定環境變數
export ROBOT_IP="192.168.12.1"           # 單機器人
export CONN_TYPE="webrtc"                # 或 "cyclonedds"
export MAP_NAME="3d_map"
export MAP_SAVE="true"
export ELEVENLABS_API_KEY="..."          # 語音合成 API（選用）
```

### 建構指令

```bash
# 在工作空間根目錄 (/home/roy422/ros2_ws/src/elder_and_dog)
colcon build                                           # 建構所有套件
colcon build --packages-select go2_robot_sdk          # 建構特定套件
colcon build --packages-select lidar_processor_cpp    # 建構 C++ LiDAR 處理器
colcon build --cmake-force-configure                  # 強制重新配置 CMake

# 安裝 ROS2 依賴
rosdep install --from-paths src --ignore-src -r -y

# 安裝 Python 依賴（使用 uv）
uv pip install -r requirements.txt
```

### 執行系統

```bash
# 主系統啟動（完整版）
ros2 launch go2_robot_sdk robot.launch.py rviz2:=true slam:=true nav2:=true foxglove:=true

# 僅啟動特定組件
ros2 launch go2_robot_sdk robot.launch.py slam:=false nav2:=false

# 物件檢測節點
ros2 run coco_detector coco_detector_node
ros2 run coco_detector coco_detector_node --ros-args -p device:=cuda -p detection_threshold:=0.7

# 使用 Phase 1 自動化測試腳本（推薦）
zsh phase1_test.sh env        # 環境檢查
zsh phase1_test.sh t1         # Terminal 1: 啟動驅動
zsh phase1_test.sh t2         # Terminal 2: 監控感測器頻率
zsh phase1_test.sh t3         # Terminal 3: 啟動 SLAM + Nav2
zsh phase1_test.sh t4         # Terminal 4: 手動控制或輸入 'auto' 自動巡房
zsh phase1_test.sh save_map   # 儲存地圖
zsh phase1_test.sh nav_test   # 測試導航功能
```

### 調試與監控

```bash
# 查看主題
ros2 topic list
ros2 topic echo /joint_states
ros2 topic hz /point_cloud2       # 量測發布頻率

# 節點資訊
ros2 node list
ros2 node info /go2_driver_node

# TF 樹視覺化
ros2 run tf2_tools view_frames

# 圖像工具
ros2 topic echo /detected_objects
ros2 run image_tools showimage --ros-args -r /image:=/annotated_image
```

---

## 架構與設計模式

### Clean Architecture 三層分離

專案採用 Clean Architecture 設計，核心套件 `go2_robot_sdk` 清楚分離職責：

```
go2_robot_sdk/go2_robot_sdk/
├── application/        # ROS2 節點實作與命令處理器
│   ├── services/       # 應用層服務（座標轉換等）
│   └── utils/          # 應用層工具
├── domain/             # 核心業務邏輯與實體
│   ├── entities/       # 領域實體（機器人狀態、感測器資料）
│   ├── interfaces/     # 領域介面（port）
│   ├── constants/      # 領域常數
│   └── math/           # 數學計算
├── infrastructure/     # 外部通訊與硬體介面層
│   ├── webrtc/         # WebRTC 連線與加密
│   ├── sensors/        # 感測器解碼（LiDAR、Camera）
│   └── ros2/           # ROS2 發布器
└── presentation/       # ROS2 訊息格式與節點入口
```

**設計原則：**
- **依賴反轉**：application 和 infrastructure 層依賴 domain 介面，而非實作
- **單一職責**：每層只處理自己的關注點
- **可測試性**：domain 層純邏輯，無 ROS2 依賴，易於單元測試

### 主要啟動流程

**入口點：** `robot.launch.py` → 雙類設計模式

1. **Go2LaunchConfig**：解析環境變數，決定配置（單/多機器人、連線類型、URDF 選擇）
2. **Go2NodeFactory**：根據配置動態建立所有 ROS2 節點與 launch includes

**啟動順序：**
```
1. go2_driver_node (主驅動)
2. robot_state_publisher (發布 URDF 與 TF)
3. pointcloud_to_laserscan (LiDAR → 2D scan 轉換)
4. lidar_to_pointcloud + pointcloud_aggregator (點雲處理)
5. slam_toolbox (SLAM 建圖)
6. nav2_bringup (導航堆疊)
7. tts_node (語音合成，選用)
8. joystick/teleop nodes (手動控制)
9. rviz2/foxglove_bridge (視覺化)
```

### 多機器人支援

透過單一 launch 檔案處理 1-N 台機器人：

```bash
# 單機器人模式
export ROBOT_IP="192.168.12.1"

# 多機器人模式
export ROBOT_IP="192.168.12.1,192.168.12.2,192.168.12.3"
```

**實作機制：**
- 自動偵測 IP 數量，決定 `single` 或 `multi` 模式
- 多機模式使用 namespace remapping（`robot0/`, `robot1/` 等）
- 動態載入不同 URDF（`go2.urdf` vs `multi_go2.urdf`）

---

## 套件說明

### 1. go2_robot_sdk (Python - 主驅動)

**節點：** `go2_driver_node`

**職責：**
- WebRTC/CycloneDDS 連線管理
- 感測器資料解碼與發布（joint states, IMU, LiDAR, camera）
- 接收 `/cmd_vel` 控制指令並下達至 Go2

**已知限制：**
- Joint state 更新頻率固定 1 Hz（firmware v1.1.7 限制）
- LiDAR 原始頻率 ~7 Hz（Clean Architecture 重構後提升）

### 2. go2_interfaces (C++ - 自訂訊息)

包含 Go2 專用的 ROS2 訊息定義（`.msg`, `.srv`, `.action`）。

### 3. lidar_processor (Python) / lidar_processor_cpp (C++)

**節點：**
- `lidar_to_pointcloud`：聚合原始 LiDAR 資料為 PointCloud2
- `pointcloud_aggregator`：濾波、降採樣、高度過濾

**參數：**
```yaml
max_range: 20.0
min_range: 0.1
height_filter_min: -2.0
height_filter_max: 3.0
downsample_rate: 5
publish_rate: 10.0
```

**C++ 版本：** 使用 PCL (Point Cloud Library)，效能更高，介面與 Python 版本相同。

### 4. coco_detector (Python - 物件檢測)

**節點：** `coco_detector_node`

**模型：** TorchVision FasterRCNN_MobileNet（COCO 資料集）

**訂閱：** `/camera/image_raw`
**發布：** `/detected_objects` (Detection2DArray), `/annotated_image` (Image)

**參數：**
```yaml
device: 'cpu'                  # 或 'cuda'
detection_threshold: 0.9       # 信心閾值
publish_annotated_image: true
```

**已知問題：**
- 當前進度約 30%（W6），節點框架已完成，待整合座標轉換
- 目標：12/03 完成雛形

### 5. speech_processor (Python - 語音合成)

**節點：** `tts_node`

**支援：** ElevenLabs API

**配置：** 需設定 `ELEVENLABS_API_KEY` 環境變數

### 6. search_logic (Python - 尋物狀態機，開發中)

**位置：** `src/search_logic/`

**規劃節點：** `search_fsm_node`

**狀態機：**
- IDLE → PATROL → DETECTED → APPROACH → ARRIVED

**目標：** W9 完成端到端測試（12/09）

---

## 座標系統與資料流

### 關鍵座標轉換流程（W7-W8 開發重點）

**問題：** VLM 輸出 2D 像素座標 `[u, v]`，需轉換為 Nav2 可用的 3D 世界座標

**解決方案：**

1. **取得深度**（三種方案）
   - Plan A（主要）：LiDAR 投影法（讀取 `/point_cloud2`，投影至圖像平面）
   - Plan B：深度相機（若 Go2 配備深度攝影機）
   - Plan C：地面假設法（假設物體在地面 Z=0，最簡方案）

2. **反投影至相機座標系**
   ```python
   # 使用相機內參矩陣 K
   X_cam = (u - cx) * Z / fx
   Y_cam = (v - cy) * Z / fy
   Z_cam = Z
   ```

3. **TF 轉換至世界座標**
   ```python
   # camera_link → base_link → map
   tf_buffer.lookup_transform('map', 'camera_link', time)
   world_pose = tf_buffer.transform(camera_pose, 'map')
   ```

4. **發布導航目標**
   ```python
   goal = PoseStamped()
   goal.header.frame_id = 'map'
   goal.pose.position.x = X_world
   goal.pose.position.y = Y_world
   publisher.publish(goal)
   ```

### ROS2 主題架構

**感測器輸出：**
```
/joint_states         (sensor_msgs/JointState, 1 Hz)
/imu                  (sensor_msgs/Imu, 50 Hz)
/point_cloud2         (sensor_msgs/PointCloud2, 7 Hz)
/camera/image_raw     (sensor_msgs/Image, 10 Hz)
```

**處理層：**
```
/scan                 (sensor_msgs/LaserScan, ~5 Hz)     ← pointcloud_to_laserscan
/detected_objects     (vision_msgs/Detection2DArray)      ← coco_detector (開發中)
/tf, /tf_static       (TF Tree)                           ← robot_state_publisher
```

**導航層：**
```
/map                  (nav_msgs/OccupancyGrid, ~1 Hz)    ← slam_toolbox
/goal_pose            (geometry_msgs/PoseStamped)         ← 座標轉換節點 (開發中)
/cmd_vel              (geometry_msgs/Twist)               ← Nav2 → go2_driver
```

---

## 配置檔案位置

所有配置檔位於 `go2_robot_sdk/config/`：

- **joystick.yaml**：手把按鍵映射
- **twist_mux.yaml**：速度指令多工與優先權
- **mapper_params_online_async.yaml**：SLAM Toolbox 參數
- **nav2_params.yaml**：Nav2 規劃器與控制器參數
- **cyclonedds.xml**：CycloneDDS 網路配置（Mac VM 需調整 `MaxAutoParticipantIndex`）
- **\*.rviz**：RViz2 視覺化配置（single/multi/cyclonedx）

---

## 開發環境架構

### 雙機開發拓樸（當前配置）

```
Mac 主機 (運算中樞)
├── Wi-Fi 介面: 192.168.12.117 ← 連接 Go2 (192.168.12.1)
├── 有線介面: 192.168.1.177   ← 連接 Windows
└── Ubuntu 22.04 VM
    ├── enp0s2: 192.168.12.222 (共享 Go2 網路)
    └── enp0s1: 192.168.64.2   (橋接 Mac)

Windows 主機 (指揮艙)
├── 有線網路: 192.168.1.146
├── VS Code SSH Remote → Mac VM (Port 2222)
└── Foxglove Studio WebSocket → VM (Port 8765)

Go2 機器狗
└── Wi-Fi AP: 192.168.12.1
```

### 網路配置重點

**Mac VM 網卡啟動：**
```bash
sudo ip addr flush dev enp0s2
sudo ip addr add 192.168.12.222/24 dev enp0s2
sudo ip link set enp0s2 up
sudo ip route add 192.168.12.0/24 dev enp0s2
```

**CycloneDDS 配置：**
- Windows：`C:\dev\cyclonedds.xml`，強制指定網卡 IP
- Mac VM：`~/ros2_ws/src/elder_and_dog/go2_robot_sdk/config/cyclonedds.xml`
  - **關鍵參數：** `MaxAutoParticipantIndex: 120`（避免節點數超限崩潰）

**防火牆：**
- Windows：開放 UDP 7400-7500（ROS2 DDS）
- Mac/VM：預設允許（若使用防火牆需手動開放）

---

## 測試與驗收

### Phase 1 測試流程（已完成）

**使用腳本：** `phase1_test.sh`

**驗收項目：**
1. ✅ 環境雙通（網際網路 + Go2 連線）
2. ✅ 感測器頻率達標（/scan > 5 Hz）
3. ✅ SLAM 建圖成功
4. ✅ 地圖儲存（.yaml + .pgm）
5. ✅ Nav2 單點導航
6. ✅ 自動巡房建圖（`auto` 指令）
7. ✅ 無紅字錯誤

**測試報告位置：**
- `docs/archive/2026-02-11-restructure/testing/slam-phase1_test_results_ROY.md`

### Phase 2 測試（計畫中）

**目標：** 大空間 SLAM 穩定性與多機器人驗證

---

## 當前開發狀態與風險

### 已完成（✅）

- ROS2 環境建置（Mac VM + Windows）
- Go2 驅動與感測器整合（WebRTC + CycloneDDS）
- SLAM + Nav2 導航堆疊
- Phase 1 自動化測試腳本
- Foxglove 視覺化工具連線
- 雙機協同開發環境

### 進行中（🔄）

- **COCO VLM 整合（W6，30%）**：研究 TorchVision 架構，尚未實作 `/detected_objects` 節點
- **座標轉換開發（W7-W8，0%）**：核心技術，連結視覺與導航的唯一橋樑

### 待開發（⏳）

- **尋物 FSM（W9）**：巡邏→掃描→鎖定→導航狀態機
- **Isaac Sim 部署（20%）**：go2_omniverse 方案確認，待部署至遠端 GPU

### 關鍵風險

| 風險 | 等級 | 緩解措施 | 應對方案 |
|------|------|---------|---------|
| 座標轉換誤差過大 | 🔴 高 | W7/W8 主攻模擬器校正；增加校正點位 | Plan B：Demo 時導航到大致區域，Web 介面標示 VLM 圖像座標 |
| VLM 節點開發滯後 | 🟡 中 | W6 加速至 50% 進度 | Plan B：使用預錄 VLM 結果與實機導航結合 |
| 實機過熱/故障 | 🟡 中 | 模擬器為主要開發環境；設定運行時間限制 | Plan B/C：實機僅展示移動與 SLAM；核心功能在模擬器或影片展示 |

---

## 重要文件索引

### 快速開始
- `README.md`：專題目標與完整架構
- `docs/01-guides/quickstart_w6_w9.md`：W6-W9 每日任務清單
- `docs/01-guides/slam_nav/README.md`：SLAM/Nav2 測試總覽
- `docs/01-guides/slam_nav/Windows-ROS2-快速開始.md`：Windows 環境設置

### 設計文件
- `docs/archive/2026-02-11-restructure/overview/專題目標.md`：願景、時程、風險管理、技術架構圖集（5 張 Mermaid 圖）
- `docs/archive/2026-02-11-restructure/overview/開發計畫.md`：現況 vs 目標符合度評估
- `docs/02-design/integration_plan.md`：W6-W9 技術整合藍圖
- `docs/01-guides/坐標轉換/座標組間介面約定.md`：座標轉換介面規範

### 測試與日誌
- `docs/archive/2026-02-11-restructure/testing/slam-phase1_test_results_ROY.md`：Phase 1 測試結果
- `docs/04-notes/dev_notes/2025-11-30-dev.md`：最新開發日誌
- `docs/04-notes/CHANGELOG.md`：文件與程式異動紀錄

### 團隊進度
- `docs/archive/2026-02-11-restructure/overview/團隊進度追蹤/團隊進度.md`
- `docs/archive/2026-02-11-restructure/overview/團隊進度追蹤/Roy第一階段計畫.md`

---

## 常見開發情境

### 新增 ROS2 節點

1. 在對應套件目錄建立節點檔案（例如 `src/search_logic/search_logic/my_node.py`）
2. 更新 `setup.py` 的 `entry_points`：
   ```python
   'console_scripts': [
       'my_node = search_logic.my_node:main',
   ],
   ```
3. 重新建構：`colcon build --packages-select search_logic`
4. Source：`source install/setup.bash`
5. 執行：`ros2 run search_logic my_node`

### 修改 Launch 檔案

- 主 launch 檔案：`go2_robot_sdk/launch/robot.launch.py`
- 修改後無需重新建構，直接重啟 launch 即可

### 調整 SLAM/Nav2 參數

- SLAM：編輯 `go2_robot_sdk/config/mapper_params_online_async.yaml`
- Nav2：編輯 `go2_robot_sdk/config/nav2_params.yaml`
- 修改後重啟 launch 檔案

### 切換連線模式（WebRTC ↔ CycloneDDS）

```bash
# WebRTC 模式（Wi-Fi）
export CONN_TYPE="webrtc"
export ROBOT_IP="192.168.12.1"

# CycloneDDS 模式（Ethernet）
export CONN_TYPE="cyclonedds"
export ROBOT_IP="192.168.123.161"  # Go2 Ethernet IP
export CYCLONEDDS_URI="file:///path/to/cyclonedds.xml"
```

### 儲存與載入地圖

```bash
# 儲存（SLAM 期間）
ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map

# 載入（Nav2 導航前）
ros2 run nav2_map_server map_server --ros-args -p yaml_filename:=~/maps/my_map.yaml

# 使用 phase1_test.sh 自動儲存
zsh phase1_test.sh save_map
```

### 除錯 TF 問題

```bash
# 檢查 TF 樹
ros2 run tf2_tools view_frames
# 會產生 frames.pdf，檢查是否有斷裂

# 實時監控 TF
ros2 run tf2_ros tf2_echo map base_link

# 檢查特定轉換
ros2 run tf2_ros tf2_echo camera_link base_link
```

---

## 技術債與改進方向

### 已知限制

1. **Joint state 低頻率（1 Hz）**：受 firmware v1.1.7 限制，影響 URDF 同步延遲
2. **LiDAR 頻率（7 Hz）**：已透過 Clean Architecture 重構提升，原本 ~2 Hz
3. **WebRTC 連線穩定性**：偶爾需要重啟 Go2 或調整網卡配置
4. **CycloneDDS 節點數限制**：需手動調整 `MaxAutoParticipantIndex`

### 未來改進建議

- 整合 ROS2 Control 框架（目前直接透過 WebRTC SDK 控制）
- 新增單元測試（domain 層優先）
- Docker Compose 自動化部署（已有 `docker/` 目錄，待完善）
- CI/CD 整合（GitHub Actions）

---

## 參考資源

### ROS2 套件依賴

- `slam_toolbox`：Grid-based SLAM
- `nav2_bringup`：Navigation2 框架
- `foxglove_bridge`：Web 視覺化
- `twist_mux`：速度指令多工
- `pointcloud_to_laserscan`：3D 點雲轉 2D scan

### 外部函式庫

- `aiortc==1.9.0`：WebRTC 通訊
- `torch + torchvision`：物件檢測
- `open3d`：點雲處理
- `opencv-python`：影像處理
- `paho-mqtt`：MQTT 通訊（若使用）

### Unitree Go2 SDK

- 官方文件：https://support.unitree.com/
- firmware 版本：v1.1.7（專案開發時版本）

---

**最後更新：2025/11/30**
**維護者：FJU Go2 專題組**

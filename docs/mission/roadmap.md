# PawAI 開發路線圖 (Pi-Mono + Skills 架構)

**版本：** v5.0 (Nano Super)  
**日期：** 2026-02-11  
**狀態：** 🚧 依據 refactor_plan.md 執行

---

## 🗺️ 路線圖總覽

```
Phase 1 (Week 1-2)    Phase 2 (Week 3-4)    Phase 3 (Week 5-6)    Phase 4 (Week 7-8)
│                      │                      │                      │
├─ Skills MVP          ├─ Sensor Gateway      ├─ 套件遷移至 src/      ├─ Git 歷史清理
├─ 安全層強化           ├─ YOLO-World          ├─ colcon 結構重組      ├─ 二進制檔案移除
└─ 前置條件驗證         └─ 訊息定義            └─ launch 檔更新        └─ 備份驗證

技術棧: Pi-Mono (TypeScript) + ROS2 Humble + Jetson Orin Nano SUPER 8GB
```

---

## 📋 前置條件檢查清單

執行本路線圖前，必須完成以下驗證：

| # | 驗證項目 | 目前狀態 | 風險 | 驗證方法 |
|---|---------|---------|------|---------|
| **#1** | **lidar_processor Python 可刪除性** | ❌ robot.launch.py 仍在引用 | 🔴 高 | 驗證 C++ 版功能 → 更新 launch → 才可刪除 |
| **#2** | **Obstacle.msg / ObstacleList.msg** | ❌ 尚未建立 | 🟡 中 | 在 go2_interfaces 新增 → colcon build |
| **#3** | **Git 歷史重寫安全性** | ⚠️ 需鏡像備份 | 🔴 高 | `git clone --mirror` → 驗證後執行 |
| **#4** | **Nav2 Action via rosbridge** | ⚠️ 未實測 | 🟡 中 | 實測 send_action_goal 端到端 |

**⚠️ 重要**：各 Phase 開始前必須確認對應前置條件已完成。

---

## Phase 1: Skills MVP + 安全層強化 (Week 1-2)

**目標：** 建立 Skills 架構，強化安全邊界，不改變既有結構

**為何先做**：最低風險、最高價值、可獨立測試

### Week 1: Skills 基礎建設

| 任務 | 負責 | 驗收標準 |
|------|------|----------|
| 建立 `skills/` 目錄結構 | Roy | 目錄存在，獨立於 ROS2 套件 |
| 設計 Skill Contract | Roy | 完成 schema 定義 (I/O, Use when, Do NOT use for) |
| 實作 `safe-move` Skill | Roy | 速度/時間限制生效，超限會 clamp |
| 實作 `emergency-stop` Skill | Roy | 任意時刻可中斷，自動觸發 |

**Skills 目錄結構：**
```
skills/                     # 新建，不影響既有套件
├── motion/
│   ├── safe-move/         # 包裝 /move_for_duration
│   └── emergency-stop/    # 包裝 /stop_movement
├── perception/
│   └── find-object/       # 整合 /capture_snapshot + VLM
├── action/
│   └── perform-action/    # go2_perform_action 封裝
└── system/
    └── status/            # 系統健康檢查
```

### Week 2: 安全層驗證 + Pi-Mono 起步

| 任務 | 負責 | 驗收標準 |
|------|------|----------|
| 驗證 Safety Gate | Roy | 測試超限會被限制，異常會 stop |
| 建立 Pi-Mono 專案骨架 | Roy | `go2-pi-agent/` 可編譯 |
| 實作 ROS2 WebSocket Bridge | Roy | 可連接 rosbridge_server |
| Skills 不依賴 MCP 驗證 | Roy | 核心流程不走 MCP low-level tools |

**安全限制驗證：**
```bash
# 測試 safe-move 限制
ros2 service call /move_for_duration go2_interfaces/srv/MoveForDuration \
  "{linear_x: 0.5, duration: 15.0}"
# 預期：速度截斷至 0.3，時間截斷至 10.0
```

### Phase 1 完成定義 (Definition of Done)

- [ ] `skills/` 目錄建立，獨立於 ROS2 套件
- [ ] `safe_move` Skill 實作完成，速度/時間限制生效
- [ ] `emergency_stop` Skill 實作完成，可中斷任意操作
- [ ] 安全限制可測試驗證（超限會 clamp，異常會 stop）
- [ ] Skills 不依賴 MCP low-level tools
- [ ] Pi-Mono 專案骨架可編譯

---

## Phase 2: Sensor Gateway + YOLO-World (Week 3-4)

**目標：** 新增感知功能，不依賴結構變更

**前置條件**：#2 (Obstacle.msg) 必須在此 Phase 開始前完成

### Week 3: 訊息定義 + Sensor Gateway

| 任務 | 負責 | 驗收標準 |
|------|------|----------|
| 新增 `Obstacle.msg` | Roy | msg 定義完成，colcon build 成功 |
| 新增 `ObstacleList.msg` | Roy | 其他套件可正常引用 |
| 開發 `sensor_gateway` 套件 | Roy | 節點可運行 |
| 實作 RANSAC Ground Removal | Roy | 地面點雲移除正常 |

**新增訊息：**
```msg
# msg/Obstacle.msg
int32 id
float64[3] center
float64[3] size
int32 point_count
float32 confidence

# msg/ObstacleList.msg
std_msgs/Header header
Obstacle[] obstacles
float32 processing_time_ms
string algorithm_version
```

**Sensor Gateway 資料流：**
```
/point_cloud2 (10MB/s)
    ↓
[sensor_gateway]
    ├── RANSAC Ground Removal
    ├── Euclidean Clustering (PCL)
    └── JSON Serialization
    ↓
/obstacles_json (~1KB)
```

### Week 4: YOLO-World + 整合測試

| 任務 | 負責 | 驗收標準 |
|------|------|----------|
| 開發 `yolo_detector` 套件 | Roy | 可偵測自定義類別 |
| TensorRT 加速優化 | Roy | Jetson 上實時執行 |
| 保持 Detection2DArray 相容 | Roy | 可替換 coco_detector |
| 感知鏈整合測試 | Roy | snapshot → YOLO → 結果輸出 |

**YOLO-World 參數：**
```python
confidence_threshold: 0.5
nms_threshold: 0.45
classes: ["bottle", "glasses", "phone", "wallet"]
model_size: "s"  # s/m/l
```

### Phase 2 完成定義

- [ ] 前置條件 #2 完成: Obstacle.msg / ObstacleList.msg 建立
- [ ] `sensor_gateway` 節點可運行
- [ ] `/obstacles_json` 輸出正常，處理延遲 < 200ms
- [ ] `yolo_detector` 可偵測自定義類別
- [ ] Detection2DArray 輸出相容 coco_detector

---

## Phase 3: 套件遷移至 src/ (Week 5-6)

**目標：** 重組專案結構，符合 colcon 慣例

**前置條件**：#1 (lidar_processor_cpp 驗證) 必須完成

### Week 5: 逐步遷移 (低風險套件)

| 任務 | 負責 | 驗收標準 |
|------|------|----------|
| 建立 `src/` 目錄 | Roy | 目錄存在 |
| 遷移 `go2_interfaces` | Roy | colcon build 成功 |
| 遷移 `go2_robot_sdk` | Roy | colcon build 成功 |
| 遷移 `lidar_processor_cpp` | Roy | colcon build 成功 |
| 功能測試 | Roy | 與遷移前一致 |

**遷移步驟：**
```bash
# 1. 備份
 git commit -m "backup: before package migration"

# 2. 逐步遷移 (一次一個，測試後再下一個)
mkdir -p src/
mv go2_interfaces src/
cd src/ && colcon build --packages-select go2_interfaces && cd ..
# 測試通過...

mv go2_robot_sdk src/
cd src/ && colcon build --packages-select go2_robot_sdk && cd ..
# 測試通過...
```

### Week 6: 更新 launch + 清理 Python 版

| 任務 | 負責 | 驗收標準 |
|------|------|----------|
| 更新 `robot.launch.py` | Roy | 改用 C++ 版 lidar_processor |
| 遷移 `speech_processor` | Roy | colcon build 成功 |
| 遷移 `coco_detector` (或 yolo_detector) | Roy | colcon build 成功 |
| 驗證 lidar_processor_cpp 完整 | Roy | 所有功能正常 |
| **刪除 Python 版 lidar_processor** | Roy | 確認不再引用後刪除 |

**⚠️ 重要**：lidar_processor Python 版必須等到前置條件 #1 完全驗證後才可刪除。

### Phase 3 完成定義

- [ ] 前置條件 #1 完成: lidar_processor_cpp 驗證通過
- [ ] 所有套件遷移至 src/ (go2_interfaces, go2_robot_sdk, ...)
- [ ] colcon build 全部成功
- [ ] robot.launch.py 已改用 C++ 版 lidar_processor
- [ ] 功能測試與遷移前一致

---

## Phase 4: Git 歷史清理 (Week 7-8)

**目標：** 減少 repo 體積，清理二進制檔案

**前置條件**：#3 (完整鏡像備份) 必須完成

### Week 7: 備份 + 低風險清理

| 任務 | 負責 | 驗收標準 |
|------|------|----------|
| 完整鏡像備份 | Roy | `git clone --mirror` 完成 |
| 驗證備份可還原 | Roy | 測試還原成功 |
| 低風險清理 (方案 A) | Roy | 從 tracking 移除 |
| 更新 .gitignore | Roy | 防止再次追蹤 |

**低風險清理 (不重寫歷史)：**
```bash
# 方案 A: 只清理工作目錄，不重寫歷史
git rm --cached *.ply *.pt *.pth *.onnx
echo "*.ply" >> .gitignore
echo "*.pt" >> .gitignore
echo "*.pth" >> .gitignore
git commit -m "chore: remove binary files from tracking"
```

### Week 8: 高風險清理 (謹慎)

| 任務 | 負責 | 驗收標準 |
|------|------|----------|
| BFG Repo-Cleaner 測試 | Roy | 測試 repo 驗證通過 |
| 執行歷史重寫 (如必要) | Roy | repo 體積減少 |
| 驗證 Submodule 完整 | Roy | 功能正常 |
| 通知團隊重新 clone | Roy | 所有成員已同步 |

**高風險操作 (僅在備份無誤後執行)：**
```bash
# 方案 B: BFG Repo-Cleaner (比 filter-repo 安全)
java -jar bfg.jar --delete-files *.ply
java -jar bfg.jar --delete-files *.pt
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

**⚠️ 風險提醒**：
- Submodule 可能會被破壞，需重新初始化
- 所有協作者需要重新 clone
- CI/CD 可能需要更新

### Phase 4 完成定義

- [ ] 前置條件 #3 完成: 完整鏡像備份已驗證
- [ ] 二進制檔案從 tracking 移除 (或歷史重寫完成)
- [ ] .gitignore 更新防止再次追蹤
- [ ] Submodule 功能正常 (如有破壞已修復)
- [ ] 團隊成員已同步

---

## 🔄 Phase 相依關係

```
前置條件 #2 (Obstacle.msg)
    ↓ (必須完成)
Phase 2 (Sensor Gateway)
    ↓ (建議完成)
Phase 1 (Skills MVP) ←──→ 可獨立並行
    ↓
前置條件 #1 (lidar_processor_cpp)
    ↓ (必須完成)
Phase 3 (套件遷移)
    ↓
前置條件 #3 (備份)
    ↓ (必須完成)
Phase 4 (Git 清理)
```

---

## 📊 完成度追蹤

| Phase | 進度 | 狀態 |
|-------|------|------|
| Phase 0 (前置條件) | 0/4 | 🔴 待完成 |
| Phase 1 (Skills MVP) | 0% | ⏳ 未開始 |
| Phase 2 (Sensor Gateway) | 0% | ⏳ 未開始 |
| Phase 3 (套件遷移) | 0% | ⏳ 未開始 |
| Phase 4 (Git 清理) | 0% | ⏳ 未開始 |

---

## ⚠️ 風險與對策

| 風險 | 說明 | 對策 | 相關前置條件 |
|-----|------|------|-------------|
| lidar_processor 誤刪 | robot.launch.py 仍在引用 Python 版 | 驗證 C++ 版後更新 launch | #1 |
| 訊息不存在 | plan 誤植 Obstacle.msg 為既有 | 明確標記為需新建 | #2 |
| Git 歷史破壞 | filter-repo 破壞 submodule | 先鏡像備份，測試後執行 | #3 |
| Nav2 action 不穩 | rosbridge 端到端未實測 | 實測所有 action 流程 | #4 |
| 結構重組失敗 | 套件遷移後 build 失敗 | 分步遷移，每次驗證 | Phase 3 |
| YOLO-World 失敗 | TensorRT 轉換失敗 | 保留 CPU fallback | Phase 2 |

---

## 📚 參考文件

- [refactor_plan.md](../refactor/refactor_plan.md) - 詳細重構計畫
- [Ros2_Skills.md](../refactor/Ros2_Skills.md) - Skills 化設計
- [pi_agent.md](../refactor/pi_agent.md) - Pi-Mono 整合方案

---

**版本紀錄：**

| 版本 | 日期 | 變更 |
|------|------|------|
| v1.0 | 2026/02/11 | 初版，依據 refactor_plan.md |

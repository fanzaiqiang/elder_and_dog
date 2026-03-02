# Go2 導航避障系統 — 完整計畫

> 專案：老人與狗 (Elder and Dog)  
> 平台：Unitree Go2 + Jetson Orin Nano 8GB + 3D LiDAR  
> 軟體主線：ROS2 Humble + Nav2 + AMCL + DWB

**更新日期：** 2026-03-02  
**當前階段：** Phase A — 安全與穩定止血（Week 1-2）  
**核心策略：** 先安全、再穩定、最後流暢

---

## 快速導讀（30 秒）

- **問題本質**：不是「控制器不夠先進」，而是「感測太稀疏 + 安全包絡太小」
- **當前瓶頸**：`LIDAR_POINT_STRIDE=8` 丟棄 87.5% 點雲，近場幾乎失明
- **解法方向**：先修感測 → 再調安全參數 → 最後優化體感
- **研究結論**：5 個開源專案皆「借概念不搬整套」，保留 Nav2 主線
- **下一步**：完成 stride A/B 測試，選定生產 stride 值

**詳細落地計畫**：[落地計畫_v2.md](./落地計畫_v2.md)  
**每週執行細節**：[weekly_plan.md](./weekly_plan.md)  
**開源專案決策**：[開源專案/](./開源專案/)

---

## 1. 安全第一

- **急停機制與操作模式**：系統分為 `mapping`、`navigation`、`guard` 三種模式；任何模式皆可觸發急停，`guard` 模式優先權最高，可中斷導航控制輸出。
- **安全不變量**：`footprint`、`footprint_padding`、`inflation_radius` 與停車規則屬於不可任意跳過的硬條件；未滿足時不得進入下一輪測試。
- **無 TF → 無運動 gate**：若 `map -> odom -> base_link` 或感測關聯 TF 缺失、過期、跳時，直接封鎖 `/cmd_vel` 輸出，禁止「盲動」。
- **碰撞防護層級**：
  1. 規劃層（Planner）避免穿越障礙區
  2. 控制層（Controller）抑制高風險軌跡
  3. 監督層（Safety Supervisor / Guard）最終裁決停車與降級
- **建議安全工具**：Nav2 官方 `nav2_collision_monitor`（獨立於 costmap 的緊急停車/減速區域過濾 `/cmd_vel`），或 `diff_drive_controller` 的 `reference_timeout: 0.5`（無速度指令 500ms 即停）。

## 2. 系統總覽

### 2.1 架構圖（text-based）

```text
3D LiDAR/Robot State
        |
        v
  Perception Pipeline -----> TF Tree (map/odom/base_link/front_camera)
        |                                 |
        v                                 v
 Local/Global Costmap <-------------- AMCL Localization
        |                                 |
        v                                 v
 SmacPlannerHybrid -----------------> DWB Controller
        |                                 |
        +------------- Nav2 --------------+
                      |
                      v
            Safety Supervisor Layer
        (TF gate / collision rules / mode guard)
                      |
                      v
                   /cmd_vel
```

### 2.2 TF 座標系

- `base_link`：機器狗本體控制基準。
- `odom`：短期連續運動座標。
- `map`：全域定位座標。
- `front_camera`：Go2 預設相機框架（非 `camera_link`）。

### 2.3 關鍵 Topics 與 ownership

| Topic | 主要擁有者 | 角色 |
|---|---|---|
| `/point_cloud2` | LiDAR 驅動/轉換節點 | 原始點雲輸入 |
| `/scan` | `pointcloud_to_laserscan` 管線 | Nav2 近場障礙感知 |
| `/amcl_pose` | AMCL | 定位估計輸出 |
| `/local_costmap/costmap_raw` | Nav2 local costmap | 近場避障代價圖 |
| `/navigate_to_pose/_action/status` | Nav2 action server | 任務狀態追蹤 |
| `/cmd_vel` | Controller + 安全監督層 | 最終速度命令 |

### 2.4 硬體平台

- 計算平台：Jetson Orin Nano 8GB
- 機器人：Unitree Go2
- 感測器：3D LiDAR

## 3. 現況基線

- 目前主線：`Nav2 + AMCL + DWB`
- 下表為當前參數基線（主線操作與評估以此為起點）

| 類別 | 基線值 |
|---|---|
| Controller | DWB, 20Hz, `max_vel_x=0.22`, `max_vel_theta=0.30` |
| Footprint | `[[0.3, 0.15], [0.3, -0.15], [-0.3, -0.15], [-0.3, 0.15]]` |
| `footprint_padding` | `0.05` |
| Local costmap | `6x6m`, `0.05m resolution`, `update 8Hz` |
| Inflation | `inflation_radius=0.35`, `cost_scaling_factor=2.0` |
| Obstacle layer | `obstacle_max_range=3.0`, `raytrace_max_range=3.5` |
| Planner | `SmacPlannerHybrid (Reeds-Shepp)`, `min_turning_radius=0.30` |
| AMCL | `OmniMotionModel`, `max_particles=2000`, `max_beams=60` |
| Progress checker | `movement_time_allowance=20.0`, `required_movement_radius=0.03` |
| DWB Critics | `BaseObstacle(0.40)`, `PathAlign(16.0)`, `GoalAlign(10.0)`, `PathDist(24.0)`, `GoalDist(16.0)`, `RotateToGoal(0.25)` |
| LiDAR stride | `LIDAR_POINT_STRIDE default: 8` |

## 4. 已診斷問題與根因分析

### 4.1 風險排序（Top 5）

1. `LIDAR_POINT_STRIDE=8`（丟棄 87.5% 點雲）— 🔴 致命
2. `inflation_radius=0.35`（Go2 體長 0.6m，僅 5cm 緩衝）— 🟠 高危
3. `movement_time_allowance=20s`（卡住判定過慢）— 🟡 中危
4. `BaseObstacle.scale=0.40`（避障權重不足）— 🟡 中危
5. `obstacle_max_range=3.0`（偵測距離偏短）— 🟢 低危

### 4.2 Oracle 補充發現（系統性根因）

- **TF/時間完整性**：sensor timestamps 與 DDS QoS 若不一致，容易產生 TF extrapolation、延遲與控制誤判。
- **四足特有動態問題**：足部滑移與 `odom` 跳動會放大 AMCL 不確定性，導致局部路徑追蹤抖動。
- **近場盲區對齊問題**：感知可視範圍必須與 `footprint + inflation + collision monitor` 保護範圍一致，否則會出現「看見但來不及停」或「能停但感測不到」的落差。

## 5. 開源專案研究與採納決策

| 專案 | 定位 | 立即採納 | 條件採納 | 暫不採納 |
|---|---|---|---|---|
| Odin-Nav-Stack | ROS1 導航棧 | 安全外圈、可觀測性、有界恢復 | Heading 對齊、障礙記憶衰減 | 全棧移植、NeuPAN |
| OM1 | AI Runtime | 安全監督層、模式治理、失敗分類 | 語義導航、Zenoh 互通 | 全棧替換、LLM 控制閉環 |
| NavDP | Sim-to-Real 研究 | 服務化接口、MPC 旁路、深度管線參考 | Shadow mode 策略對比 | 端到端主線替換 |
| LoGoPlanner | 研究基準 | 深度前處理、A/B 評估模式、MPC shadow | Guarded-assist 建議器 | 直接接管主導航 |
| visualnav-transformer | GNM/ViNT/NoMaD | 資料前處理、Shadow 評測 | 視覺子目標建議器 | 直接接管 `cmd_vel` |

採納決策詳見：

- `docs/導航避障/開源專案/Odin_採納決策.md`
- `docs/導航避障/開源專案/OM1_採納決策.md`
- `docs/導航避障/開源專案/NavDP_採納決策.md`
- `docs/導航避障/開源專案/LoGoPlanner_採納決策.md`
- `docs/導航避障/開源專案/visualnav-transformer_採納決策.md`
- `docs/導航避障/開源專案/NavDP_採納轉移路線圖.md`

## 6. 三階段落地路線

### Phase A：安全與穩定止血（Week 1-2）

- **A1 感測密度**：執行 stride A/B（`8 -> 2 -> 1`），以 `/scan` 穩定率、有效回波、CPU 使用率共同決策。
- **A2 安全包絡**：同步調整 `inflation/footprint/recovery`，先達成 0 碰撞再談速度體感。
- **A3 可觀測性**：建立 incident packet 與 debug cockpit，讓每次失敗可被分類與追溯。

### Phase B：控制體感優化（Week 3-4）

- **B1 DWB Critics 調優**：依單變數 A/B 原則，降低 stop-go、猶豫、過度旋轉。
- **B2 MPPI 選擇性評估**：僅在 DWB 已通過 Gate 且 Jetson 資源有 headroom 時進行。
- **MPPI Jetson 注意事項**：官方建議 `batch_size` 降至 ~1000（8GB 記憶體限制），`iteration_count` 保持 1，監控 thermal throttling。

### Phase C：架構升級評估（Week 5+）

- **C1 Cartographer（條件性）**：僅當主瓶頸確認為定位一致性時導入。
- **C2 D435 融合（條件性）**：作為近場補強，不替代 LiDAR 安全主線。
- **C3 AI 模型評估（研究化）**：採 shadow/sandbox 策略，不直接接管實機閉環。

## 7. Gate 定義（進階硬條件）

- **G1 安全**：0 碰撞（至少 200 次短距或 10 小時）。
- **G2 可靠**：成功率 `>= 95%`，`ABORT <= 5%`。
- **G3 感測**：`/scan` 穩定 `>= 8Hz`，無持續 TF 問題。
- **G4 資源**：無 CPU 飽和，記憶體穩定。

## 8. 啟動與操作指南

### 8.1 環境變數

- `GO2_LIDAR_DECODER`
- `LIDAR_POINT_STRIDE`
- `MAP_YAML`
- `FOXGLOVE`
- `ENABLE_VIDEO`
- `PUBLISH_COMPRESSED_IMAGE`

### 8.2 每日操作流程

流程：`preflight -> launch -> set_initial_pose -> postlaunch -> test -> shutdown`  
（完整週期與判讀規則請見 `docs/導航避障/weekly_plan.md`）

```bash
# 1) preflight
zsh scripts/go2_ros_preflight.sh prelaunch

# 2) launch
GO2_LIDAR_DECODER=wasm LIDAR_POINT_STRIDE=<chosen_stride> \
  MAP_YAML=/home/jetson/go2_map.yaml \
  zsh scripts/start_nav2_localization.sh

# 3) set_initial_pose
sleep 25
zsh scripts/set_initial_pose.sh 0.0 0.0 0.0

# 4) postlaunch
zsh scripts/go2_ros_preflight.sh postlaunch

# 5) test（示例）
zsh scripts/check_gate_c_rates.sh 5 10
python3 scripts/nav2_goal_autotest.py --distance 0.5 --timeout 45

# 6) shutdown
zsh scripts/go2_ros_preflight.sh prelaunch
```

### 8.3 Debug Cockpit

建議 tmux pane 佈局（對齊 Week 2 診斷流程）：

- Pane 1：`/cmd_vel`
- Pane 2：`/navigate_to_pose/_action/status`
- Pane 3：速率總覽（`check_gate_c_rates.sh`）
- Pane 4：`/local_costmap/costmap_raw` 速率

## 9. 測試方法論

- **固定座標 A↔B 循環**：使用固定絕對目標，不用 `--distance` 相對目標作為最終驗收依據。
- **單變數 A/B 原則**：每輪只改一個關鍵變數，避免多因子混疊。
- **必填紀錄欄位**：成功/失敗、原因分類、參數版本（含日期與 commit）。
- **失敗分類標準**：感測稀疏 / costmap / controller / TF時間。

## 10. 關鍵文件索引

| 路徑 | 說明 |
|---|---|
| `go2_robot_sdk/config/nav2_params.yaml` | Nav2 完整參數 |
| `go2_robot_sdk/launch/robot.launch.py` | 主要啟動檔 |
| `scripts/start_nav2_localization.sh` | Nav2 定位啟動 |
| `scripts/go2_ros_preflight.sh` | 前後置檢查 |
| `scripts/check_gate_c_rates.sh` | 速率檢查 |
| `scripts/nav2_goal_autotest.py` | 自動化目標測試 |
| `scripts/set_initial_pose.sh` | 初始座標設定 |
| `go2_robot_sdk/urdf/go2.urdf` | Go2 機器人模型 |
| `docs/導航避障/落地計畫_v2.md` | 詳細落地計畫 |
| `docs/導航避障/weekly_plan.md` | 每週執行計畫 |
| `docs/導航避障/開源專案/*.md` | 各專案採納決策 |

## 11. 不做事項

1. 不在同一輪改多組關鍵參數。
2. 不在安全 gate 未過前追求高速。
3. 不把研究型模型直接接管主控制。
4. 不用 benchmark 結果直接推論實機安全。
5. 不在控制閉環中引入非確定性推理。

## 12. 結論

一句話：「先讓機器狗『看得見』，再讓它『跑得順』；基礎不打穩，前沿模型只是空中樓閣。」

---

## 附錄 A：術語對照表

| 英文 | 中文 | 說明 |
|------|------|------|
| stride | 點雲步進 | LiDAR 點取樣間隔（每 N 個點取 1 個）|
| inflation | 膨脹 | costmap 障礙物膨脹半徑 |
| footprint | 足跡 | 機器人佔地面積多邊形 |
| DWB | Dynamic Window B | Nav2 預設局部規劃器 |
| MPPI | Model Predictive Path Integral | Nav2 進階局部規劃器（GPU 友好）|
| AMCL | Adaptive Monte Carlo Localization | 粒子濾波定位 |
| ABORT | 任務中止 | Nav2 action 回報 status=6 |
| costmap | 代價地圖 | 障礙物與通行性的格狀表示 |
| shadow mode | 影子模式 | 旁路觀測，不控制機器人 |
| guarded assist | 守衛輔助 | 受安全層裁決的建議式控制 |

## 附錄 B：給未來 AI Agent 的備註

本文件是導航避障子系統的**單一真相源 (Single Source of Truth)**。若需繼續工作：

1. 先確認當前所處 Phase 與 Gate 狀態（見第 6、7 節）
2. 查看 `weekly_plan.md` 確認本週具體任務
3. 所有歷史採納決策記錄於 `開源專案/` 目錄
4. 參數基線見第 3 節，任何修改需 A/B 驗證後才可寫入預設值
5. **關鍵環境變數**：`GO2_LIDAR_DECODER=wasm`、`LIDAR_POINT_STRIDE`、`MAP_YAML`
6. **已知陷阱**：`--distance` 相對目標會造成漂移，改用固定絕對座標 A↔B

---

*文件版本：v1.0 | 維護：FJU PawAI 專題組*

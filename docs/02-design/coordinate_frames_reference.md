# Go2 機器狗座標系統參考

**文件目的：** 記錄 Go2 機器狗的 TF 座標系名稱，避免開發時混淆
**最後更新：** 2025/12/02
**資料來源：** `frames_2025-12-02_12.55.43.pdf`

---

## 📐 核心導航座標系

### 1. SLAM 與導航鏈路

```
map → odom → base_link
```

| 座標系名稱 | 說明 | 發布者 | 頻率 | 備註 |
|-----------|------|--------|------|------|
| `map` | SLAM 全域地圖座標系 | slam_toolbox | - | 固定參考系 |
| `odom` | 里程計座標系 | go2_driver_node | 38.25 Hz | 相對於起始點的累積位移 |
| `base_link` | 機器人本體中心座標系 | go2_driver_node | 38.25 Hz | 機器人幾何中心 |
| `base_footprint` | 機器人地面投影座標系 | robot_state_publisher | 靜態 | 用於地面接觸點計算 |

**轉換關係：**
- `map → odom`：由 SLAM 估計（修正累積誤差）
- `odom → base_link`：由驅動器提供（IMU + 編碼器融合）

---

## 📷 感測器座標系

### 2. 相機座標系

```
base_link → Head_upper → front_camera
```

| 座標系名稱 | 說明 | 父座標系 | 類型 | 重要性 |
|-----------|------|----------|------|--------|
| `front_camera` | 前置相機座標系 | Head_upper | 靜態轉換 | 🔴 **座標轉換開發必須使用此名稱** |

**⚠️ 重要提醒：**
- ❌ **不是** `camera_link`（標準 ROS2 命名）
- ✅ **必須使用** `front_camera`

**座標轉換程式碼範例：**
```python
# 正確做法
camera_frame = "front_camera"
transform = tf_buffer.lookup_transform("map", "front_camera", time)

# 錯誤做法（會找不到座標系）
# camera_frame = "camera_link"  # ❌ 錯誤！
```

---

### 3. LiDAR 座標系

```
base_link → radar
```

| 座標系名稱 | 說明 | 父座標系 | 類型 | 重要性 |
|-----------|------|----------|------|--------|
| `radar` | LiDAR 雷達座標系 | base_link | 靜態轉換 | 🔴 **LiDAR 投影法必須使用此名稱** |

**⚠️ 重要提醒：**
- ❌ **不是** `lidar_link` 或 `laser_link`（標準命名）
- ✅ **必須使用** `radar`

**座標轉換程式碼範例：**
```python
# 正確做法
lidar_frame = "radar"
transform = tf_buffer.lookup_transform("front_camera", "radar", time)

# 錯誤做法（會找不到座標系）
# lidar_frame = "lidar_link"  # ❌ 錯誤！
```

---

### 4. IMU 座標系

```
base_link → imu
```

| 座標系名稱 | 說明 | 父座標系 | 類型 | 用途 |
|-----------|------|----------|------|------|
| `imu` | 慣性測量單元座標系 | base_link | 靜態轉換 | 姿態估計、SLAM 輔助 |

---

### 5. 頭部座標系

```
base_link → Head_upper → Head_lower
```

| 座標系名稱 | 說明 | 父座標系 | 類型 |
|-----------|------|----------|------|
| `Head_upper` | 頭部上半部 | base_link | 靜態轉換 |
| `Head_lower` | 頭部下半部 | Head_upper | 靜態轉換 |

---

## 🦾 機器人關節座標系

### 6. 四條腿關節鏈

Go2 機器狗有 4 條腿，每條腿有相同的關節結構：

```
base_link → {leg}_hip → {leg}_thigh → {leg}_calf → {leg}_foot
                                    └→ {leg}_calflower → {leg}_calflower1
```

**腿部命名規則：**
- `FL` = Front Left（前左）
- `FR` = Front Right（前右）
- `RL` = Rear Left（後左）
- `RR` = Rear Right（後右）

**完整關節列表：**

| 腿 | 關節鏈 | 更新頻率 |
|----|--------|----------|
| **前左（FL）** | base_link → FL_hip → FL_thigh → FL_calf → FL_foot | 11.8 Hz |
| **前右（FR）** | base_link → FR_hip → FR_thigh → FR_calf → FR_foot | 11.8 Hz |
| **後左（RL）** | base_link → RL_hip → RL_thigh → RL_calf → RL_foot | 11.8 Hz |
| **後右（RR）** | base_link → RR_hip → RR_thigh → RR_calf → RR_foot | 11.8 Hz |

**關節說明：**
- `hip`：髖關節（連接軀幹）
- `thigh`：大腿
- `calf`：小腿
- `foot`：腳掌
- `calflower`：小腿下部（精細結構）

---

## 🔧 座標轉換開發重點提醒

### W7-W8 座標轉換開發必讀

當你開始開發座標轉換節點時，**請務必注意以下命名差異**：

#### ❌ 常見錯誤（標準 ROS2 命名）

```python
# 這些名稱在 Go2 上不存在！
camera_frame = "camera_link"      # ❌ 錯誤
lidar_frame = "lidar_link"        # ❌ 錯誤
laser_frame = "laser_link"        # ❌ 錯誤
```

#### ✅ 正確做法（Go2 實際命名）

```python
# 使用 Go2 實際的座標系名稱
camera_frame = "front_camera"     # ✅ 正確
lidar_frame = "radar"             # ✅ 正確
base_frame = "base_link"          # ✅ 正確
map_frame = "map"                 # ✅ 正確
```

---

## 📊 座標系頻率統計

| 座標系轉換 | 頻率 | 發布者 | 備註 |
|-----------|------|--------|------|
| map → odom | 6.13 Hz | slam_toolbox | SLAM 更新頻率 |
| odom → base_link | 38.25 Hz | go2_driver_node | 高頻位姿更新 |
| base_link → 關節 | 11.8 Hz | robot_state_publisher | Joint State 更新頻率 |
| base_link → 感測器 | 10000 Hz | robot_state_publisher | 靜態轉換（不變） |

**說明：**
- **10000 Hz** 表示靜態轉換（Static Transform），不會隨時間變化
- **動態轉換**（SLAM、里程計、關節）會根據機器人運動實時更新

---

## 🎯 快速查找表

**我需要哪個座標系？**

| 需求 | 正確座標系名稱 | 用途 |
|------|---------------|------|
| SLAM 全域地圖 | `map` | 導航目標座標系 |
| 里程計 | `odom` | 短期位置追蹤 |
| 機器人中心 | `base_link` | 機器人本體參考點 |
| 相機 | `front_camera` | VLM 圖像座標轉換 |
| LiDAR | `radar` | 深度估計、點雲處理 |
| IMU | `imu` | 姿態估計 |
| 地面 | `base_footprint` | 地面接觸計算 |

---

## 📚 相關文件

- **TF 樹視覺化：** `frames_2025-12-02_12.55.43.pdf`
- **TF 樹原始資料：** `frames_2025-12-02_12.55.43.gv`
- **座標轉換設計：** `docs/02-design/座標轉換設計.md`（待建立）
- **Phase 1.5 測試報告：** `docs/03-testing/slam-phase1_5_test_results_ROY.md`

---

## 🔍 驗證座標系是否存在

**測試指令：**

```bash
# 列出所有 TF 座標系
ros2 run tf2_ros tf2_echo map base_link

# 查看特定轉換
ros2 run tf2_ros tf2_echo map front_camera
ros2 run tf2_ros tf2_echo base_link radar

# 產生完整 TF 樹圖
ros2 run tf2_tools view_frames
```

**預期結果：**
- ✅ 所有指令應該成功輸出轉換矩陣
- ❌ 如果顯示 "frame does not exist"，請檢查座標系名稱拼寫

---

**文件版本：** v1.0
**最後驗證：** 2025/12/02（Phase 1.5 測試期間）
**下次更新：** 當 URDF 或 TF 樹結構變更時

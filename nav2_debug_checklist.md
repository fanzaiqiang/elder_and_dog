# Nav2 原地打轉問題修復檢查清單

## ✅ 已完成修正

### 1. 參數更新 (Priority 1)
- ✅ `max_vel_theta`: 3.0 → 1.0（降低角速度）
- ✅ `min_vel_x`: 0.0 → 0.1（強制前進）
- ✅ `min_speed_xy`: 0.0 → 0.1（最小線速度）
- ✅ `RotateToGoal.scale`: 32.0 → 10.0（降低旋轉權重）
- ✅ `inflation_radius`: 0.25 → 0.15（縮小膨脹半徑）

### 2. 座標系修正 (Priority 2)
- ✅ `global_costmap.global_frame`: odom → **map**（修正座標系錯配）

### 3. LiDAR 地板過濾 (Priority 3)
- ✅ 新增 `min_obstacle_height: 0.1`（避免掃到地板）

---

## 🧪 測試步驟

### Step 1: 重新載入環境
```bash
cd /home/roy422/ros2_ws/src/elder_and_dog
source install/setup.bash
```

### Step 2: 啟動系統
```bash
# 使用 phase1_test.sh 或手動啟動
ros2 launch go2_robot_sdk robot.launch.py slam:=true nav2:=true rviz2:=true
```

### Step 3: 驗證參數是否生效
```bash
# 檢查角速度上限（應該是 1.0）
ros2 param get /controller_server FollowPath.max_vel_theta

# 檢查最小線速度（應該是 0.1）
ros2 param get /controller_server FollowPath.min_vel_x

# 檢查 global_costmap 座標系（應該是 "map"）
ros2 param get /global_costmap/global_costmap global_frame
```

### Step 4: 發送導航目標
```bash
# 在 RViz2 中使用 "2D Goal Pose" 工具
# 或使用指令：
ros2 topic pub -1 /goal_pose geometry_msgs/msg/PoseStamped "{
  header: {frame_id: 'map'},
  pose: {
    position: {x: 2.0, y: 0.0, z: 0.0},
    orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
  }
}"
```

### Step 5: 監控行為
```bash
# 觀察 /cmd_vel（應該看到 linear.x > 0）
ros2 topic echo /cmd_vel

# 觀察導航狀態
ros2 topic echo /navigate_to_pose/_action/status
```

---

## 🔍 故障排查

### 問題 1: 仍然原地打轉
**檢查：**
```bash
ros2 topic echo /cmd_vel
```
**預期：** `linear.x` 應該在 0.1 ~ 0.5 之間，而非一直是 0

**可能原因：**
- 代價地圖顯示前方有障礙物 → 檢查 `/local_costmap/costmap` 在 RViz2 中是否過度膨脹
- TF 轉換錯誤 → 執行 `ros2 run tf2_ros tf2_echo map base_link`

---

### 問題 2: Recovery Loop（反覆重試）
**檢查：**
```bash
ros2 topic echo /behavior_tree_log
```

**可能原因：**
- 目標點設在障礙物上 → 在 RViz2 中確認目標點是否在自由空間（白色區域）
- 路徑規劃失敗 → 檢查 `/plan`（全域路徑）是否生成

---

### 問題 3: 角速度仍然過高（> 1.0）
**檢查：**
```bash
ros2 param get /controller_server FollowPath.max_vel_theta
```

**如果返回不是 1.0：**
```bash
# 手動設定參數（臨時）
ros2 param set /controller_server FollowPath.max_vel_theta 1.0
```

---

## 📊 關鍵主題監控

| 主題 | 預期頻率 | 檢查內容 |
|------|----------|----------|
| `/scan` | ~5 Hz | LiDAR 資料是否正常 |
| `/map` | ~1 Hz | SLAM 地圖是否更新 |
| `/local_costmap/costmap` | ~1 Hz | 代價地圖是否合理 |
| `/plan` | 當導航時 | 全域路徑是否生成 |
| `/cmd_vel` | ~10 Hz | linear.x 是否 > 0 |
| `/tf` | 持續 | map → odom → base_link 鏈是否完整 |

---

## 🎯 成功標準

1. ✅ 發送導航目標後，機器狗**向前移動**（不只是原地轉）
2. ✅ `/cmd_vel` 的 `linear.x` 在 0.1 ~ 0.5 之間
3. ✅ `angular.z` 不超過 1.0 rad/s
4. ✅ 沒有出現 "Goal canceled" 或 "Recovery Loop"
5. ✅ 能夠到達目標點（xy_goal_tolerance: 0.3 m 以內）

---

## 🔧 進階調校（若基本測試成功）

### 微調 RotateToGoal 行為
如果機器狗還是過度對準目標方向：
```yaml
RotateToGoal.scale: 10.0 → 5.0  # 進一步降低
```

### 調整速度曲線
如果移動太慢或太快：
```yaml
max_vel_x: 0.5 → 0.7  # 提高最大速度
acc_lim_x: 2.5 → 1.5  # 降低加速度，更平滑
```

### 優化路徑規劃器
如果路徑過於保守（繞遠路）：
```yaml
inflation_radius: 0.15 → 0.12  # 進一步縮小
cost_scaling_factor: 3.0 → 2.0  # 降低代價衰減
```

---

## 📝 日誌收集（若需要進一步診斷）

```bash
# 啟動時加上 --log-level debug
ros2 launch go2_robot_sdk robot.launch.py slam:=true nav2:=true --log-level debug

# 儲存 TF 樹
ros2 run tf2_tools view_frames
# 會產生 frames.pdf

# 錄製 ROS2 bag（包含所有主題）
ros2 bag record -a -o nav2_debug_$(date +%Y%m%d_%H%M%S)
```

---

**最後更新：** 2025-12-07
**修復重點：** 參數未生效 + 座標系錯配 + LiDAR 地板過濾

# Phase 1 SLAM + Nav2 綜合測試指南（Windows 開發環境）

**目標讀者：** Windows 主機開發者（透過 SSH 連接 Mac UTM VM）
**測試環境：** Windows 桌機 + Mac UTM (Ubuntu 22.04) + Go2 機器狗
**建立日期：** 2025/11/25
**最後更新：** 2025/11/25

---

## 📋 文件目的

本指南專為 **Windows 遠端開發環境** 設計，提供完整的 Phase 1 SLAM + Nav2 導航測試流程，包括：
- 網路架構說明
- 三種視覺化方案比較
- 完整測試步驟
- 故障排查手冊

---

## 🌐 當前網路架構

```
┌─────────────────────────────────────────────────────────┐
│ Windows 桌機（主要開發機）192.168.1.146                  │
│ ┌─────────────────┐  ┌──────────────┐  ┌─────────────┐ │
│ │ VS Code SSH     │  │ Foxglove     │  │ RViz2       │ │
│ │ Port 2222       │  │ Port 8765    │  │ (可選安裝)   │ │
│ └────────┬────────┘  └──────┬───────┘  └──────┬──────┘ │
└──────────┼────────────────────┼──────────────────┼───────┘
           │                    │                  │
           │ 有線網路            │ WebSocket        │ ROS2 DDS
           ↓                    ↓                  ↓
┌─────────────────────────────────────────────────────────┐
│ Mac 主機 (192.168.1.177)                                 │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ UTM 虛擬機 (Ubuntu 22.04)                            │ │
│ │ - enp0s1: 192.168.64.2 (Shared，連網際網路)          │ │
│ │ - enp0s2: 192.168.12.222 (Bridged，連 Go2)          │ │
│ │                                                       │ │
│ │ ┌─────────────┐  ┌──────────────┐  ┌─────────────┐ │ │
│ │ │ ROS2 Nodes  │  │ foxglove_    │  │ RViz2       │ │ │
│ │ │             │  │ bridge       │  │ (可選)      │ │ │
│ │ └──────┬──────┘  └──────┬───────┘  └──────┬──────┘ │ │
│ └────────┼─────────────────┼──────────────────┼────────┘ │
└──────────┼─────────────────┼──────────────────┼──────────┘
           │                 │                  │
           │ Wi-Fi (WebRTC)  │                  │
           ↓                 ↑                  ↑
┌─────────────────────────────────────────────────────────┐
│ Unitree Go2 機器狗                                       │
│ 192.168.12.1 (Wi-Fi AP)                                 │
│ - LiDAR (7 Hz)                                          │
│ - Camera (10 Hz)                                        │
│ - IMU (50 Hz)                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 三種視覺化方案比較

### 方案 A：Windows 本地 RViz2（✅ 最推薦，零延遲）

```
Windows RViz2 ─(ROS2 DDS)→ Mac VM ROS2 Nodes ─(WebRTC)→ Go2
      ↑
    本地渲染（零延遲）
```

**優點：**
- ⚡ **零渲染延遲**（Windows 本地 GPU 渲染）
- 🎮 **完整互動工具**（2D Pose Estimate、2D Nav Goal）
- 🔧 **開發友善**：VS Code + RViz2 + Foxglove 三合一
- 📊 **可離線使用**（無需 Mac VM 運行即可查看 bag 檔案）

**缺點：**
- 📦 需在 Windows 安裝 ROS2 Humble（約 2GB）
- ⚙️ 需配置 ROS_DOMAIN_ID 與網路環境變數

**安裝步驟：**

#### Step 1: 下載並安裝 ROS2 Humble（Windows）

```powershell
# 1. 前往 ROS2 官方下載頁面
# https://docs.ros.org/en/humble/Installation/Windows-Install-Binary.html

# 2. 下載 ros2-humble-*-windows-release-amd64.zip
# 檔案大小約 700 MB，解壓後約 2 GB

# 3. 解壓到 C:\dev\ros2_humble
# 確保路徑無中文或空格
```

#### Step 2: 安裝相依套件

ROS2 Humble Windows 版本需要以下套件：

```powershell
# 1. 安裝 Visual C++ Redistributables
# 下載並安裝：https://aka.ms/vs/17/release/vc_redist.x64.exe

# 2. 安裝 Chocolatey（Windows 套件管理器）
# 以管理員權限開啟 PowerShell：
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 3. 使用 Chocolatey 安裝必要工具
choco install -y python311 cmake git
```

#### Step 3: 配置環境變數

建立啟動腳本 `C:\dev\setup_ros2.bat`：

```batch
@echo off
REM ROS2 Humble Windows 環境設定腳本

REM 1. 載入 ROS2 環境
call C:\dev\ros2_humble\local_setup.bat

REM 2. 配置網路（連接 Mac VM）
set ROS_DOMAIN_ID=0
set ROS_LOCALHOST_ONLY=0
set RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

REM 3. 配置 ROS2 DDS 發現
REM 允許跨子網路通訊（Windows ↔ Mac VM）
set ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
set CYCLONEDDS_URI=file:///C:/dev/cyclonedds_config.xml

echo ====================================
echo ROS2 Humble 環境已設定完成
echo ====================================
echo ROS_DOMAIN_ID: %ROS_DOMAIN_ID%
echo RMW_IMPLEMENTATION: %RMW_IMPLEMENTATION%
echo ====================================
```

#### Step 4: 配置 CycloneDDS（重要！）

建立 `C:\dev\cyclonedds_config.xml`：

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<CycloneDDS xmlns="https://cdds.io/config" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Domain id="any">
    <General>
      <!-- 允許跨網段通訊 -->
      <NetworkInterfaceAddress>auto</NetworkInterfaceAddress>
      <AllowMulticast>true</AllowMulticast>
      <EnableMulticastLoopback>true</EnableMulticastLoopback>
    </General>
    <Discovery>
      <!-- 延長發現時間，適應跨網段延遲 -->
      <ParticipantIndex>auto</ParticipantIndex>
      <MaxAutoParticipantIndex>100</MaxAutoParticipantIndex>
      <SPDPInterval>1000ms</SPDPInterval>
    </Discovery>
  </Domain>
</CycloneDDS>
```

**為什麼需要這個配置？**
- Windows 與 Mac VM 在不同子網路（192.168.1.x vs 192.168.64.x）
- CycloneDDS 預設僅在同一子網路內發現節點
- 此配置允許跨子網路的 DDS 通訊

#### Step 5: 測試連線

```powershell
# 1. 開啟 PowerShell
# 2. 執行環境設定腳本
C:\dev\setup_ros2.bat

# 3. 確認 Mac VM 的 ROS2 系統正在運行
# （在 Mac VM SSH 中執行）
# ros2 launch go2_robot_sdk robot.launch.py slam:=true nav2:=true

# 4. 在 Windows PowerShell 測試連線
ros2 topic list

# 預期輸出（應看到 Mac VM 的 topics）：
# /camera/camera_info
# /camera/image_raw
# /cmd_vel
# /joint_states
# /map
# /odom
# /scan
# /tf
# /tf_static
```

**如果看不到 topics，進行故障排查：**

```powershell
# 1. 檢查網路連通性
ping 192.168.1.177  # Mac VM IP

# 2. 檢查環境變數
echo %ROS_DOMAIN_ID%          # 應為 0
echo %ROS_LOCALHOST_ONLY%     # 應為 0
echo %RMW_IMPLEMENTATION%     # 應為 rmw_cyclonedds_cpp

# 3. 確認 Mac VM 也使用相同配置
# 在 Mac VM SSH 執行：
echo $ROS_DOMAIN_ID           # 應為 0
echo $RMW_IMPLEMENTATION      # 應為 rmw_cyclonedds_cpp

# 4. 檢查 Windows 防火牆
# Windows 安全性 → 防火牆與網路保護 → 進階設定
# 新增輸入規則：允許 UDP 7400-7500（DDS 埠）
```

#### Step 6: 下載專案 RViz2 配置檔案

```powershell
# 1. 從 Mac VM 複製 RViz2 配置到 Windows
# 方法 A：使用 SCP（推薦）
scp -P 2222 roy422@192.168.1.177:~/ros2_ws/src/elder_and_dog/go2_robot_sdk/config/single_robot_conf.rviz C:\dev\rviz_configs\

# 方法 B：手動下載
# 在 Windows 瀏覽器開啟：
# \\wsl$\Ubuntu-22.04\home\roy422\ros2_ws\src\elder_and_dog\go2_robot_sdk\config\
# 複製 single_robot_conf.rviz 到 C:\dev\rviz_configs\
```

**專案已有的 RViz2 配置檔案：**
```
- single_robot_conf.rviz    （單機器狗配置，最常用）
- multi_robot_conf.rviz     （多機器狗配置）
- cyclonedds_config.rviz    （CycloneDDS 專用配置）
```

這些配置已經包含：
- ✅ SLAM Toolbox Plugin（建圖工具）
- ✅ Nav2 Plugin（導航工具）
- ✅ 地圖、LiDAR、TF 顯示
- ✅ Costmap（障礙物地圖）
- ✅ 路徑規劃可視化

---

### 方案 B：X11 轉發（Mac RViz2 → Windows 顯示）

```
Windows X Server ←(X11 over SSH)← Mac VM RViz2 ←(ROS2)← Go2
      ↑
   網路渲染（延遲 10-50ms）
```

**優點：**
- 🚀 **快速設置**（不需安裝完整 ROS2）
- 💾 **節省 Windows 儲存空間**
- 🔄 **自動同步**（Mac 更新 ROS2 時，Windows 無需重裝）

**缺點：**
- ⏱️ **有渲染延遲**（10-50ms，取決於網路與 3D 複雜度）
- 🖼️ **效能較差**（X11 協議較舊，3D 加速支援有限）
- 🔌 **依賴 SSH 連線**（SSH 斷線則 RViz2 關閉）

**安裝步驟：**

#### Windows 端（安裝 X Server）

**選項 1：VcXsrv（推薦，免費）**
```powershell
# 1. 下載安裝 VcXsrv
# https://sourceforge.net/projects/vcxsrv/

# 2. 啟動 XLaunch
# - Multiple windows
# - Start no client
# - ✅ Disable access control (重要!)
# - 完成後會在系統匣看到 X 圖示

# 3. 允許防火牆
# Windows 安全性 → 防火牆 → 允許 VcXsrv
```

**選項 2：MobaXterm（推薦，整合 SSH 客戶端）**
```
# 1. 下載安裝 MobaXterm Home Edition
# https://mobaxterm.mobatek.net/download.html

# 2. 內建 X Server 會自動啟動
# 3. 使用 MobaXterm SSH 連線即可自動轉發 X11
```

#### Mac VM 端（配置 X11 轉發）

```bash
# 1. 安裝必要套件（若未安裝）
sudo apt install x11-apps

# 2. 編輯 SSH 配置（允許 X11 轉發）
sudo vim /etc/ssh/sshd_config
# 確認以下行未被註解：
# X11Forwarding yes
# X11DisplayOffset 10

# 3. 重啟 SSH 服務
sudo systemctl restart ssh

# 4. 測試 X11 轉發
# 在 Windows SSH 連線時加上 -X 參數：
# ssh -X -p 2222 roy422@192.168.1.177

# 5. 測試顯示（應該在 Windows 看到視窗）
xclock
# 若看到時鐘視窗則成功
```

#### 啟動 RViz2（透過 X11）

```bash
# Windows PowerShell/CMD
ssh -X -p 2222 roy422@192.168.1.177

# 進入 Mac VM 後
source install/setup.bash
ros2 launch go2_robot_sdk robot.launch.py slam:=true nav2:=true rviz2:=true

# RViz2 視窗會出現在 Windows 桌面
```

---

### 方案 C：純 Foxglove（⚠️ 不推薦用於導航控制）

```
Windows Foxglove ←(WebSocket 8765)← Mac VM foxglove_bridge ←(ROS2)← Go2
      ↑
  網路延遲（20-50ms，指令積壓）
```

**優點：**
- 🌐 **跨平台**（無需安裝 ROS2 或 X Server）
- 📊 **整合介面**（3D + 波形圖 + Log）
- 🎬 **事後分析**（內建 .mcap 播放器）
- 👥 **團隊協作**（Layout 雲端同步）

**缺點：**
- 🔴 **不適合即時控制**（延遲導致導航卡頓，如您遇到的問題）
- 🔌 **需額外節點**（foxglove_bridge）
- 🚫 **部分工具不支援**（2D Pose Estimate 需手動配置）

**適用場景：**
- ✅ **數據監控**（週會展示、遠端觀看）
- ✅ **事後分析**（拖拉時間軸檢查頻率波動）
- ❌ **即時控制**（Phase 1 導航測試 - 請用方案 A 或 B）

---

## 🚀 Phase 1 測試完整流程

### 前置準備（擇一安裝）

#### 若選方案 A（Windows RViz2）
```powershell
# Windows PowerShell
C:\dev\ros2_humble\local_setup.bat
set ROS_DOMAIN_ID=0
set ROS_LOCALHOST_ONLY=0
```

#### 若選方案 B（X11 轉發）
```powershell
# Windows 啟動 VcXsrv 或 MobaXterm
# 確認系統匣有 X 圖示

# SSH 連線（加 -X 參數）
ssh -X -p 2222 roy422@192.168.1.177
```

---

### 步驟 1：啟動 ROS2 系統

```bash
# 在 Mac VM 終端（透過 Windows SSH 連線）
cd ~/ros2_ws/src/elder_and_dog
source install/setup.bash

# 方案 A（Windows RViz2）：不啟動 VM 的 RViz2
ros2 launch go2_robot_sdk robot.launch.py slam:=true nav2:=true foxglove:=true

# 方案 B（X11 轉發）：啟動 VM 的 RViz2，顯示在 Windows
ros2 launch go2_robot_sdk robot.launch.py slam:=true nav2:=true rviz2:=true
```

**預期結果：**
```
✅ [go2_driver_node]: Node started
✅ [slam_toolbox]: Localization mode enabled
✅ [nav2_lifecycle_manager]: Activating navigation
✅ [foxglove_bridge]: WebSocket server listening on port 8765
```

---

### 步驟 2：開啟視覺化工具

#### 方案 A：Windows RViz2（使用專案配置）

```powershell
# Windows 新開 PowerShell

# 1. 載入 ROS2 環境（使用我們建立的腳本）
C:\dev\setup_ros2.bat

# 2. 啟動 RViz2 並載入專案配置檔案
ros2 run rviz2 rviz2 -d C:\dev\rviz_configs\single_robot_conf.rviz
```

**預期結果：**
- RViz2 視窗開啟，顯示完整的導航介面
- 左側面板包含：
  - **SlamToolboxPlugin**（建圖控制）
  - **Navigation 2**（導航控制）
- 3D 視圖顯示：
  - ✅ Grid（網格）
  - ✅ Map（地圖，若已載入 phase1.pgm）
  - ✅ LaserScan（綠色 LiDAR 點雲）
  - ✅ RobotModel（機器狗模型）
  - ✅ TF（座標系箭頭）
  - ✅ Global/Local Costmap（障礙物地圖）
  - ✅ Path（全局路徑，綠色）
  - ✅ Local Plan（局部路徑，紅色）

**工具列按鈕（重點）：**
```
頂部工具列從左到右：
- Interact（互動模式）
- Move Camera（移動視角）
- Select（選擇）
- 2D Pose Estimate（設定初始位置）⭐
- 2D Nav Goal（設定導航目標）⭐
- Publish Point（發佈點座標）
```

**如果 RViz2 無法連接到 topics：**

```powershell
# 檢查 topics 是否可見
ros2 topic list

# 若看不到，檢查 Mac VM 的 ROS_DOMAIN_ID
# 在 Mac VM SSH 執行：
echo $ROS_DOMAIN_ID

# 確保與 Windows 一致（都是 0）
# 若不一致，在 Mac VM 重新設定：
export ROS_DOMAIN_ID=0
# 然後重啟 ROS2 系統
```

#### 方案 B：X11 轉發
```bash
# RViz2 視窗已自動出現在 Windows 桌面
# 若未出現，檢查：
echo $DISPLAY  # 應顯示 localhost:10.0
xeyes          # 測試用小程式，應出現眼睛視窗
```

#### 同時開啟 Foxglove（監控用）
```
Windows 開啟 Foxglove Studio
連線：ws://192.168.1.177:8765

設定 → Network → Update Rate: 5 Hz
取消訂閱：/camera/image_raw, /point_cloud2
```

---

### 步驟 3：RViz2 配置

**首次使用需手動配置：**

1. **Fixed Frame**: `map`
2. **新增顯示項目**（左下 "Add" 按鈕）：
   ```
   ✅ Map (Topic: /map)
   ✅ LaserScan (Topic: /scan)
   ✅ RobotModel (從 robot_description 載入)
   ✅ TF (顯示座標系)
   ✅ Path (Topic: /plan) - 全局路徑
   ✅ Path (Topic: /local_plan) - 局部路徑
   ✅ Map (Topic: /global_costmap/costmap) - 全局障礙物
   ✅ Map (Topic: /local_costmap/costmap) - 局部障礙物
   ```

3. **儲存配置**：
   ```
   File → Save Config As → nav2_default.rviz
   ```

---

### 步驟 4：設定初始位置（2D Pose Estimate）

```
RViz2 工具列 → "2D Pose Estimate" 按鈕
1. 在地圖上點擊機器狗的實際位置
2. 拖動滑鼠設定朝向（箭頭方向）
3. 放開滑鼠
```

**如何找到機器狗位置：**
- 觀察 `/scan` 綠色點雲的位置
- 參考 Foxglove 的影像與地圖對照
- 若不確定，選地圖中央空地

**預期反應：**
- 粒子雲（紅色點）從整個地圖收斂到機器狗周圍
- 機器狗模型位置與 `/scan` 點雲對齊
- 等待 2-3 秒，粒子雲集中成一團

---

### 步驟 5：發送導航目標（2D Nav Goal）

```
RViz2 工具列 → "2D Nav Goal" 按鈕
1. 在地圖上點擊目標位置（白色空地）
2. 拖動設定抵達後的朝向
3. 放開滑鼠
```

**選擇目標點原則：**
- ✅ **短距離**（1-2m）- 首次測試避免太遠
- ✅ **大片白色區域** - 安全可達的空地
- ✅ **遠離障礙物** - 避開黑色或灰色區域
- ❌ 避免選在牆角或狹窄通道

**預期反應：**
1. **立即顯示綠色路徑**（`/plan` topic）
2. **機器狗開始移動**
   - 先調整朝向（原地旋轉）
   - 沿路徑前進
   - 局部路徑（紅色）隨障礙物調整
3. **抵達目標後停止**
   - 位置誤差 < 30cm
   - 朝向誤差 < 15°

---

### 步驟 6：記錄測試數據

**開啟新終端（Mac VM）：**
```bash
# 終端 2：監控 /scan 頻率
ros2 topic hz /scan
# 預期：平均 5-7 Hz

# 終端 3：監控 /map 頻率
ros2 topic hz /map
# 預期：平均 0.5-1 Hz

# 終端 4：查看速度指令
ros2 topic echo /cmd_vel
# 導航時應看到 linear.x 和 angular.z 變化
```

**填寫測試數據：**
```
/scan 頻率: _____ Hz
/map 頻率: _____ Hz
導航成功次數: ___ / 5
平均到達誤差: _____ cm
平均導航時間: _____ 秒
```

---

### 步驟 7：錄製測試過程（可選）

```bash
# 錄製所有 topics
ros2 bag record -a -o phase1_nav_test

# 或僅錄製關鍵 topics（節省空間）
ros2 bag record \
  /scan /map /tf /tf_static \
  /cmd_vel /odom /amcl_pose \
  /plan /local_plan \
  /global_costmap/costmap /local_costmap/costmap \
  -o phase1_nav_test
```

**事後分析：**
```
# 在 Foxglove 拖入 .mcap 檔案
# 檢查導航失敗時的：
# - /scan 頻率是否掉落
# - AMCL 粒子雲是否發散
# - /plan 路徑是否合理
# - /cmd_vel 是否有異常震盪
```

---

## 🔍 故障排查手冊

### 問題 1：Windows RViz2 看不到 topics

**症狀：**
```bash
ros2 topic list
# 空白或僅顯示 /rosout
```

**原因：** ROS_DOMAIN_ID 不一致或網路隔離

**解決方案：**
```powershell
# Windows 確認環境變數
echo %ROS_DOMAIN_ID%  # 應為 0

# Mac VM 確認
echo $ROS_DOMAIN_ID   # 應為 0

# 若不一致，重新設定：
# Windows:
set ROS_DOMAIN_ID=0

# Mac VM:
export ROS_DOMAIN_ID=0

# 重啟 ROS2 nodes
```

**進階檢查（網路連通性）：**
```powershell
# Windows ping Mac VM
ping 192.168.1.177

# 若失敗，檢查防火牆：
# Windows Defender → 進階設定 → 輸入規則
# 允許 UDP 7400-7500 (DDS 使用)
```

---

### 問題 2：X11 轉發失敗（方案 B）

**症狀：**
```bash
ros2 run rviz2 rviz2
# Error: cannot open display: localhost:10.0
```

**解決方案：**

#### Windows 端檢查
```powershell
# 1. 確認 VcXsrv 是否運行
# 系統匣應有 X 圖示

# 2. 確認防火牆規則
# Windows Defender → 允許應用程式
# ✅ VcXsrv windows xserver (私人/公用網路)

# 3. 重新啟動 VcXsrv
# XLaunch → Disable access control ✅
```

#### Mac VM 端檢查
```bash
# 1. 確認 DISPLAY 環境變數
echo $DISPLAY
# 應顯示：localhost:10.0 或類似

# 若為空，手動設定：
export DISPLAY=localhost:10.0

# 2. 測試 X11
xeyes
# 應在 Windows 看到眼睛視窗

# 3. 若 xeyes 失敗，檢查 SSH 配置
grep X11Forwarding /etc/ssh/sshd_config
# 應顯示：X11Forwarding yes

# 4. 重新 SSH 連線（加 -X）
exit
ssh -X -p 2222 roy422@192.168.1.177
```

---

### 問題 3：導航卡頓或機器狗自己旋轉

**症狀：**
- 發送目標後，機器狗原地旋轉不停
- 移動時走走停停，非常卡頓
- `/cmd_vel` 數值震盪

**原因分析：**

#### 原因 A：AMCL 定位未收斂
```bash
# 檢查粒子雲狀態
ros2 topic echo /particlecloud --once

# 若粒子分散在整個地圖 → 定位失敗
```

**解決方案：**
```
1. 重新設定 "2D Pose Estimate"
2. 選擇更精確的位置
3. 等待 5-10 秒讓粒子雲收斂
4. 觀察粒子是否集中成一團
```

#### 原因 B：目標方向與當前方向差異過大
```
如果目標朝向與當前朝向相差 > 90°
Nav2 會先原地旋轉對準方向
```

**解決方案：**
```
1. 設定目標時，拖動箭頭朝向機器狗當前方向
2. 或增加 yaw_goal_tolerance（容忍度）
   vim go2_robot_sdk/config/nav2_params.yaml
   yaw_goal_tolerance: 0.5  # 約 28°
```

#### 原因 C：網路延遲（若使用 Foxglove 控制）
```
Foxglove 透過 WebSocket 發送指令
延遲 20-50ms → 控制週期 50ms → 指令積壓
```

**解決方案：**
```
改用 RViz2（方案 A 或 B），零延遲
```

---

### 問題 4：地圖不顯示或為空白

**症狀：**
```
RViz2 顯示灰色背景
/map topic 無數據
```

**原因：** 地圖檔案未載入或 SLAM 模式錯誤

**解決方案：**

#### 檢查地圖檔案
```bash
ls -lh src/go2_robot_sdk/maps/
# 應有 phase1.pgm 和 phase1.yaml

# 檢查 launch 參數
ros2 param get /slam_toolbox mode
# 應為 "localization"（定位模式）
# 或 "mapping"（建圖模式）
```

#### 若地圖檔案不存在
```bash
# 使用之前的腳本建圖
zsh phase1_test.sh t3  # 啟動 SLAM
zsh phase1_test.sh t4  # 手動建圖
# 輸入 auto 讓機器狗自動巡房

# 建圖完成後存檔
zsh phase1_test.sh save_map
```

#### RViz2 配置問題
```
1. 檢查 Fixed Frame 是否為 "map"
2. 檢查 Map Display 的 Topic 是否為 "/map"
3. 檢查 Map Display 的 Alpha 是否為 1.0（不透明）
```

---

### 問題 5：/scan 頻率過低（< 3 Hz）

**症狀：**
```bash
ros2 topic hz /scan
# average rate: 2.134
```

**原因：** 頻寬不足（camera/pointcloud 佔用）

**解決方案：**

#### 方法 1：關閉高頻寬 topics（推薦）
```bash
# 編輯 launch 檔案，停用 camera 發佈
vim go2_robot_sdk/launch/robot.launch.py

# 或使用環境變數（若支援）
export ENABLE_CAMERA=false
ros2 launch go2_robot_sdk robot.launch.py ...
```

#### 方法 2：在 Foxglove 取消訂閱
```
Foxglove → Topics
❌ /camera/image_raw
❌ /point_cloud2
❌ /pointcloud/aggregated
```

#### 方法 3：降低 camera 發佈頻率
```python
# 編輯驅動節點
vim go2_robot_sdk/presentation/go2_driver_node.py

# 找到 camera publisher，降低頻率
self.create_timer(0.5, self.publish_camera)  # 從 0.1 改為 0.5（2Hz）
```

---

## 📊 測試驗收標準

### Phase 1 合格條件（至少 6/7 項通過）

| # | 檢查項目 | 目標 | 驗收標準 |
|---|---------|------|---------|
| 1 | Go2 驅動啟動 | 所有感測器正常 | RViz2 顯示 `/scan` 綠點、機器狗模型 |
| 2 | /scan 頻率 | > 5 Hz | `ros2 topic hz /scan` 平均 > 5.0 |
| 3 | /map 發布 | ~1 Hz | 地圖顯示清晰，牆壁線條完整 |
| 4 | TF 樹完整性 | map→odom→base_link | `ros2 run tf2_tools view_frames` 無錯誤 |
| 5 | RViz2 連線 | 顯示正常 | 3D 視圖流暢，無卡頓 |
| 6 | 地圖存檔 | 檔案產出 | phase1.pgm (> 10KB) + phase1.yaml |
| 7 | **Nav2 導航** | **成功率 ≥ 80%** | **5 次導航至少 4 次成功到達** |

---

## 📝 測試報告填寫

完成測試後，填寫 `docs/03-testing/slam-phase1_test_results_ROY.md`：

```markdown
## 測試環境

- 開發平台：Windows 桌機 (192.168.1.146)
- ROS2 環境：Mac UTM (Ubuntu 22.04, 192.168.64.2)
- 視覺化方案：[方案 A / 方案 B / 方案 C]
- 測試日期：2025/11/25

## 測試數據

### /scan 頻率
- 平均：_____ Hz
- 最低：_____ Hz
- 最高：_____ Hz

### /map 頻率
- 平均：_____ Hz

### 導航測試（5 次）
| 次數 | 起點 | 終點 | 距離 | 成功 | 到達誤差 | 時間 | 備註 |
|------|------|------|------|------|---------|------|------|
| 1    | (0,0)| (1,0)| 1m   | ✅   | 15cm    | 8s   |      |
| 2    | (1,0)| (2,1)| 1.4m | ✅   | 22cm    | 12s  |      |
| 3    | ...  | ...  | ...  | ...  | ...     | ...  | ...  |

成功率：___ / 5 = ___%

## 截圖

- [ ] RViz2 完整地圖畫面
- [ ] Nav2 路徑規劃（/plan 綠色路徑）
- [ ] Terminal /scan 頻率輸出
- [ ] Foxglove 四分割監控畫面

## 問題與解決

### 遇到的問題
1. ...
2. ...

### 解決方案
1. ...
2. ...
```

---

## 🎯 下一步：準備週會報告（11/26）

### Foxglove 展示 Layout（四分割）

```
┌─────────────────────┬─────────────────────┐
│ 3D Panel            │ Image Panel         │
│ /map + /scan        │ /camera/image_raw   │
│ + Robot Model       │                     │
├─────────────────────┼─────────────────────┤
│ Plot Panel          │ Plot Panel          │
│ /scan 頻率波形圖     │ /cmd_vel 速度曲線    │
└─────────────────────┴─────────────────────┘
```

### 週會簡報重點

1. **Phase 1 成果**
   - ✅ SLAM 建圖成功（展示 phase1.pgm）
   - ✅ Nav2 導航成功率：___%
   - ✅ 自動化測試腳本（phase1_test.sh）

2. **技術亮點**
   - 🌐 **雙機架構**：Windows 開發 + Mac VM 運算
   - ⚡ **三種視覺化方案**：RViz2 / X11 / Foxglove
   - 🔧 **網路延遲診斷**：找出 Foxglove 控制卡頓原因

3. **下週計畫（W7）**
   - 🎯 開始座標轉換開發（地面假設法）
   - 📚 學習 tf2_ros 與相機內參
   - 🧪 建立 Mock VLM 節點測試

---

## 📚 相關文件

- [Phase 1 執行指南（快速版）](./phase1_execution_guide_v2.md)
- [SLAM/Nav2 速查表](./quick_reference.md)
- [座標轉換介面約定](../坐標轉換/座標組間介面約定.md)
- [測試結果報告模板](../../03-testing/slam-phase1_test_results_ROY.md)

---

## 🔄 更新記錄

| 日期 | 版本 | 變更內容 | 作者 |
|------|------|---------|------|
| 2025/11/25 | v1.0 | 初版，針對 Windows 開發環境設計 | Claude Code |

---

**祝測試順利！有任何問題請隨時回報。** 🚀

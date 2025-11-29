# Windows ROS2 快速開始指南

> **目標**: 在 Windows 上安裝 ROS2 Humble + RViz2，連接到 Mac VM 的 ROS2 系統，完成 Phase 1 Nav2 測試
>
> **預計時間**: 2-3 小時（安裝 1-2 小時 + 測試 1 小時）
>
> **最新更新**: 2025/11/29 - 加入完整除錯流程與版本選擇建議

---

## ⚠️ 重要警告：ROS2 版本選擇

**🚨 已知問題（2025/11/29 確認）：**

最新的 **Patch Release 13 (2025-07-21)** Windows Binary 存在嚴重缺陷：
- 壓縮檔大小只有 **375 MB**（正常應該 1.5-2 GB）
- 解壓後缺少關鍵檔案：`_rclpy_pybind11.pyd`, `ros2.exe`, `python.exe`
- 會導致錯誤：`ModuleNotFoundError: No module named 'rclpy._rclpy_pybind11'`

**✅ 推薦使用經過驗證的穩定版本：**
- **Patch Release 7 (2023-06-14)** - 已經過數千名開發者驗證
- 下載連結：[ros2-humble-20230614-windows-release-amd64.zip](https://github.com/ros2/ros2/releases/download/release-humble-20230614/ros2-humble-20230614-windows-release-amd64.zip)
- 檔案大小：約 **1.8-2.0 GB**（壓縮後 ~620 MB）
- 與 Mac VM 的 Humble (2025-05) 完全兼容

---

## 📌 版本資訊驗證（已確認正確）

本指南使用的版本皆符合 [ROS2 Humble Windows Binary 官方要求](https://docs.ros.org/en/humble/Installation/Windows-Install-Binary.html)：

| 套件 | 版本 | 說明 | 官方來源 |
|------|------|------|---------|
| **ROS2 Humble** | **Patch Release 7 (2023-06-14)** | **推薦穩定版本** | [GitHub Release](https://github.com/ros2/ros2/releases/tag/release-humble-20230614) |
| **Python** | `3.8.3` | ROS2 Humble Binary **僅支援** Python 3.8 | [官方文件](https://docs.ros.org/en/humble/Installation/Windows-Install-Binary.html) |
| **Qt5** | `5.12.12` (MSVC 2017 64-bit) | RViz2 GUI 核心依賴 | [官方文件](https://docs.ros.org/en/humble/Installation/Windows-Install-Binary.html) |
| **OpenSSL** | `1.1.1.2100` (對應 1.1.1t) | 雖已 EOL 但 ROS2 Humble 仍需要 | [Chocolatey](https://community.chocolatey.org/packages/openssl) |
| **setuptools** | `59.6.0` | Python 建置工具 | ROS2 測試版本 |
| **empy** | `3.3.4` | 模板引擎（版本鎖定） | ROS2 需求 |
| **lark** | `1.1.1` | 解析器（版本鎖定） | ROS2 需求 |
| **pyparsing** | `2.4.7` | 解析器（版本鎖定） | ROS2 需求 |

**套件管理器選擇**: 使用 **`uv`** 取代傳統 `pip`（速度快 10-100 倍，與 pip 完全兼容）

---

## 📋 今天準備清單（2025/11/25 晚上）

在開始安裝前，先準備好以下資源，明天可以節省時間：

### ✅ 準備項目

- [ ] **下載 ROS2 Humble Windows 安裝包（使用穩定版本）**
  - **推薦版本**: Patch Release 7 (2023-06-14)
  - **下載連結**: [ros2-humble-20230614-windows-release-amd64.zip](https://github.com/ros2/ros2/releases/download/release-humble-20230614/ros2-humble-20230614-windows-release-amd64.zip)
  - **檔案大小**: 約 620 MB（壓縮）→ 解壓後約 2 GB
  - **下載位置**: `C:\Downloads\`
  - **⚠️ 重要**: 確認檔案大小 > 600 MB（如果只有幾十 MB，檔案不完整）
  - **❌ 不要下載**: Patch Release 13 (有缺檔問題)

- [ ] **下載 Visual C++ Redistributables**
  - 連結: https://aka.ms/vs/17/release/vc_redist.x64.exe
  - ROS2 Windows 版本需要 Visual Studio 2022 C++ 運行庫

- [ ] **下載 Qt 5.12.12 Offline Installer（必要！）**
  - 官網: https://download.qt.io/new_archive/qt/5.12/5.12.12/
  - 檔案: `qt-opensource-windows-x86-5.12.12.exe` (約 3 GB)
  - 下載位置: `C:\Downloads\`
  - **🚨 重要**: 這是 RViz2 GUI 介面的核心依賴，沒有這個 RViz2 無法啟動！
  - **建議**: 今晚就先下載，檔案很大需要時間

- [ ] **確認 Windows 網路環境**
  - Windows IP: `192.168.1.146` (假設，請確認實際 IP)
  - Mac VM IP: `192.168.64.2`
  - 測試連通性: `ping 192.168.64.2`

- [ ] **準備文字編輯器**
  - 記事本 or VS Code (用於建立配置檔案)

- [ ] **建立工作目錄**
  ```powershell
  # 在 Windows PowerShell 執行
  mkdir C:\dev
  mkdir C:\dev\rviz_configs
  ```

---

## 🚀 明天執行步驟（2025/11/26）

### 第一階段：安裝 ROS2 Humble（預計 1-1.5 小時）

#### Step 1: 安裝 Chocolatey 套件管理器（5 分鐘）

**Chocolatey 是什麼？** Windows 的套件管理器，類似 Ubuntu 的 `apt`，可以一鍵安裝多個依賴。

```powershell
# 以系統管理員權限開啟 PowerShell
# (右鍵點擊 PowerShell → 以系統管理員身分執行)

# 執行 Chocolatey 安裝腳本
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

**✅ 檢查點**: 執行 `choco --version` 顯示版本號（如 `1.4.0`）

---

#### Step 2: 一鍵安裝 ROS2 運行時依賴（15-20 分鐘）

**重要說明**：即使使用 Binary Release（預編譯版本），ROS2 仍需要以下運行時依賴：

```powershell
# 繼續使用系統管理員 PowerShell

# 1. 安裝 Visual C++ Redistributables（ROS2 執行檔需要）
choco install -y vcredist2013 vcredist140

# 2. 安裝 Python 3.8（ROS2 Humble Binary 要求精確版本）
#    ⚠️ 重要：ROS2 Humble Windows Binary 只支援 Python 3.8
choco install -y python --version=3.8.3

# 3. 安裝 OpenSSL 1.1.1t（安全連線需要）
#    注意：雖然 OpenSSL 1.1.1 已 EOL，但 ROS2 Humble 仍需要此版本
#    Chocolatey 版本號 1.1.1.2100 對應 OpenSSL 1.1.1t
choco install -y openssl --version=1.1.1.2100

# 4. 設定 OpenSSL 環境變數
setx /m OPENSSL_CONF "C:\Program Files\OpenSSL-Win64\bin\openssl.cfg"
```

**✅ 檢查點**: 執行以下指令確認安裝成功
```powershell
python --version    # 應顯示 Python 3.8.3
openssl version     # 應顯示 OpenSSL 1.1.1...
```

---

#### Step 3: 安裝 ROS2 專用依賴包（10 分鐘）

這些是 ROS2 Humble 特別需要的函式庫（從 GitHub 下載）：

```powershell
# 1. 下載依賴包（手動下載或使用以下指令）
# 前往網址下載：https://github.com/ros2/choco-packages/releases/tag/2022-03-15
# 需要的檔案：
#   - asio.1.12.1.nupkg
#   - bullet.3.17.nupkg
#   - cunit.2.1.3.nupkg
#   - eigen.3.3.4.nupkg
#   - tinyxml-usestl.2.6.2.nupkg
#   - tinyxml2.6.0.0.nupkg

# 2. 假設下載到 C:\Downloads，執行安裝
choco install -y -s C:\Downloads\ asio cunit eigen tinyxml-usestl tinyxml2 bullet
```

**如果覺得手動下載麻煩，可以跳過這步**，先測試 ROS2 能否啟動，如果遇到缺少函式庫錯誤再回來安裝。

**✅ 檢查點**: 沒有錯誤訊息，或顯示 "X packages installed"

---

#### Step 4: 安裝 Python 依賴包（5 分鐘）

ROS2 CLI 指令需要這些 Python 函式庫。我們使用 **`uv`** 套件管理器（比 pip 更快）：

```powershell
# 1. 安裝 uv（超快速 Python 套件管理器）
python -m pip install uv

# 2. 使用 uv 安裝 setuptools
uv pip install --system setuptools==59.6.0

# 3. 使用 uv 安裝 ROS2 必要的 Python 套件
uv pip install --system catkin_pkg cryptography empy==3.3.4 lark==1.1.1 lxml netifaces numpy pyparsing==2.4.7 pyyaml
```

**為什麼用 `uv`？**
- 比 `pip` 快 10-100 倍
- 更好的依賴解析
- 與 pip 完全兼容
- `--system` 參數：安裝到系統 Python（不是虛擬環境）

**✅ 檢查點**: 沒有錯誤訊息，顯示 "Successfully installed..."

---

#### Step 5: 安裝 Qt5（RViz2 必要依賴，15-20 分鐘）

**🚨 重要**：這是 RViz2 GUI 介面的核心依賴，沒有這個 RViz2 會無法啟動！

```powershell
# 1. 下載 Qt 5.12.12 Offline Installer
# 網址: https://download.qt.io/new_archive/qt/5.12/5.12.12/
# 檔案名稱: qt-opensource-windows-x86-5.12.12.exe (約 3 GB)
# 建議: 今晚就先下載，明天直接安裝

# 2. 執行安裝程式
# - 可能需要註冊 Qt 帳號（或選擇 "Skip" 跳過）
# - 安裝路徑建議使用預設: C:\Qt

# 3. 元件選擇（關鍵步驟）
# 在安裝選單中：
#   ✅ 展開 "Qt 5.12.12"
#   ✅ 勾選 "MSVC 2017 64-bit"（必須！）
#   ❌ 其他元件可以不勾選（節省空間）

# 4. 完成安裝後，設定環境變數
setx /m Qt5_DIR "C:\Qt\Qt5.12.12\5.12.12\msvc2017_64"
setx /m QT_QPA_PLATFORM_PLUGIN_PATH "C:\Qt\Qt5.12.12\5.12.12\msvc2017_64\plugins\platforms"
```

**✅ 檢查點**:
- 安裝完成後，確認 `C:\Qt\Qt5.12.12\5.12.12\msvc2017_64\` 目錄存在
- 環境變數 `Qt5_DIR` 和 `QT_QPA_PLATFORM_PLUGIN_PATH` 設定成功

**如果沒有這一步會怎樣？**
- RViz2 啟動時會出現錯誤：`This application failed to start because no Qt platform plugin could be initialized`
- 或者直接閃退，沒有任何介面

---

#### Step 6: 解壓縮 ROS2 Humble（10 分鐘）

```powershell
# 1. 解壓縮下載的 ROS2 壓縮檔到 C:\dev\ros2_humble
# 方法 A: 使用 Windows 檔案總管
#   - 右鍵點擊 ros2-humble-*-windows-release-amd64.zip
#   - 選擇「解壓縮全部」
#   - 目標資料夾: C:\dev\ros2_humble

# 方法 B: 使用 PowerShell (需安裝 7-Zip)
Expand-Archive -Path "C:\Downloads\ros2-humble-*-windows-release-amd64.zip" -DestinationPath "C:\dev\ros2_humble"
```

**✅ 檢查點**: 確認 `C:\dev\ros2_humble\local_setup.bat` 存在

---

#### Step 7: 建立環境設定腳本（5 分鐘）

使用記事本或 VS Code 建立以下檔案：

**檔案路徑**: `C:\dev\setup_ros2.bat`

```batch
@echo off
REM ROS2 Humble 環境設定腳本
REM 用途: 快速設定 ROS2 + CycloneDDS 跨網段通訊

echo [INFO] 載入 ROS2 Humble 環境...
call C:\dev\ros2_humble\local_setup.bat

echo [INFO] 設定 ROS2 環境變數...
set ROS_DOMAIN_ID=0
set ROS_LOCALHOST_ONLY=0
set RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
set ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
set CYCLONEDDS_URI=file:///C:/dev/cyclonedds_config.xml

echo [INFO] ROS2 環境設定完成！
echo.
echo 當前配置:
echo   ROS_DOMAIN_ID=%ROS_DOMAIN_ID%
echo   RMW_IMPLEMENTATION=%RMW_IMPLEMENTATION%
echo   CYCLONEDDS_URI=%CYCLONEDDS_URI%
echo.
echo 測試連線: ros2 topic list
```

**✅ 檢查點**: 檔案儲存成功，副檔名為 `.bat` (不是 `.bat.txt`)

---

#### Step 8: 建立 CycloneDDS 配置檔案（5 分鐘）

**檔案路徑**: `C:\dev\cyclonedds_config.xml`

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<CycloneDDS xmlns="https://cdds.io/config" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="https://cdds.io/config https://raw.githubusercontent.com/eclipse-cyclonedds/cyclonedds/master/etc/cyclonedds.xsd">
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

**✅ 檢查點**: 檔案儲存成功，副檔名為 `.xml` (不是 `.xml.txt`)

---

#### Step 9: 測試 ROS2 安裝（10 分鐘）

```powershell
# 1. 開啟新的 PowerShell 視窗

# 2. 執行環境設定腳本
C:\dev\setup_ros2.bat

# 3. 測試 ROS2 指令
ros2 --version
# 預期輸出: ros2 cli version: 0.25.x

# 4. 測試 topic 指令
ros2 topic list
# 目前應該是空的或只有系統 topics（因為還沒連接 Mac VM）
```

**✅ 檢查點**:
- `ros2 --version` 顯示正確版本
- 沒有任何錯誤訊息（找不到指令、缺少 DLL 等）

---

#### Step 10: 設定 Windows 防火牆（10 分鐘）

ROS2 使用 DDS 協議通訊，需要開放 UDP 埠 7400-7500：

```powershell
# 方法 A: 使用圖形介面（推薦）
# 1. Windows 安全性 → 防火牆與網路保護
# 2. 進階設定
# 3. 輸入規則 → 新增規則
# 4. 規則類型: 連接埠
# 5. 協定: UDP，特定本機連接埠: 7400-7500
# 6. 動作: 允許連線
# 7. 設定檔: 勾選所有（網域、私人、公用）
# 8. 名稱: ROS2 DDS Communication
# 9. 完成

# 方法 B: 使用 PowerShell（需系統管理員權限）
New-NetFirewallRule -DisplayName "ROS2 DDS Inbound" -Direction Inbound -Protocol UDP -LocalPort 7400-7500 -Action Allow
New-NetFirewallRule -DisplayName "ROS2 DDS Outbound" -Direction Outbound -Protocol UDP -RemotePort 7400-7500 -Action Allow
```

**✅ 檢查點**: 防火牆規則成功建立，狀態為「已啟用」

---

#### Step 11: 從 Mac VM 複製 RViz2 配置檔案（10 分鐘）

```powershell
# 方法 A: 使用 SCP（推薦）
# 確保 Windows 已安裝 OpenSSH Client（Windows 10/11 內建）

# 複製單機器狗配置（Phase 1 主要使用）
scp roy422@192.168.64.2:~/ros2_ws/src/elder_and_dog/go2_robot_sdk/config/single_robot_conf.rviz C:\dev\rviz_configs\

# 可選：複製其他配置檔案
scp roy422@192.168.64.2:~/ros2_ws/src/elder_and_dog/go2_robot_sdk/config/multi_robot_conf.rviz C:\dev\rviz_configs\
scp roy422@192.168.64.2:~/ros2_ws/src/elder_and_dog/go2_robot_sdk/config/cyclonedds_config.rviz C:\dev\rviz_configs\
```

**如果 SCP 失敗**（Mac VM SSH 未開放或連線問題）：

```powershell
# 方法 B: 手動下載
# 1. 在 Mac VM 中執行（SSH 連線）
cd ~/ros2_ws/src/elder_and_dog/go2_robot_sdk/config/
cat single_robot_conf.rviz

# 2. 複製輸出內容
# 3. 在 Windows 建立檔案 C:\dev\rviz_configs\single_robot_conf.rviz
# 4. 貼上內容並儲存
```

**✅ 檢查點**: `C:\dev\rviz_configs\single_robot_conf.rviz` 存在且大小約 14 KB

---

### 第二階段：連接 Mac VM ROS2 系統（預計 15-30 分鐘）

#### Step 12: 啟動 Mac VM ROS2 系統

在 Mac VM SSH 終端執行：

```bash
# 1. 確認環境變數（Mac VM 也要使用 CycloneDDS）
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# 2. 啟動機器狗驅動 + SLAM + Nav2
cd ~/ros2_ws/src/elder_and_dog
source install/setup.bash
export ROBOT_IP="192.168.12.1"  # 替換成你的 Go2 IP
export CONN_TYPE="webrtc"       # 或 "cyclonedds"
ros2 launch go2_robot_sdk robot.launch.py slam:=true nav2:=true

# 預期輸出（啟動成功訊息）：
# [INFO] [go2_driver_node]: Go2 driver initialized
# [INFO] [slam_toolbox]: SLAM Toolbox started
# [INFO] [bt_navigator]: Nav2 BT Navigator started
```

**✅ 檢查點**: 終端顯示 Go2 驅動、SLAM Toolbox、Nav2 啟動成功，無錯誤訊息

---

#### Step 13: Windows 連線測試

在 Windows PowerShell 執行：

```powershell
# 1. 載入 ROS2 環境
C:\dev\setup_ros2.bat

# 2. 測試連線 - 列出所有 topics
ros2 topic list

# 預期輸出（應看到 Mac VM 的 topics）：
# /camera/camera_info
# /camera/image_raw
# /cmd_vel
# /joint_states
# /map
# /odom
# /point_cloud2
# /scan
# /tf
# /tf_static
# ... (更多 topics)
```

**✅ 檢查點**:
- 能看到至少 10 個以上的 topics
- 包含 `/scan`, `/map`, `/odom`, `/tf` 等關鍵 topics

---

**如果看不到 topics（故障排查）**:

```powershell
# 1. 檢查網路連通性
ping 192.168.64.2
# 應該有回應，延遲 < 10ms

# 2. 檢查 Windows 環境變數
echo %ROS_DOMAIN_ID%          # 應為 0
echo %ROS_LOCALHOST_ONLY%     # 應為 0
echo %RMW_IMPLEMENTATION%     # 應為 rmw_cyclonedds_cpp

# 3. 確認 Mac VM 也使用相同配置
# 在 Mac VM SSH 執行：
echo $ROS_DOMAIN_ID           # 應為 0
echo $RMW_IMPLEMENTATION      # 應為 rmw_cyclonedds_cpp

# 4. 重啟兩端的 ROS2 系統
# Mac VM: Ctrl+C 停止 launch，重新執行
# Windows: 關閉 PowerShell，重新開啟並執行 setup_ros2.bat
```

---

#### Step 14: 測試 topic 數據

```powershell
# 1. 測試 /scan 頻率（LiDAR 數據）
ros2 topic hz /scan
# 預期: average rate: 5.xxx (> 5 Hz 為正常)

# 2. 測試 /map 頻率（SLAM 地圖）
ros2 topic hz /map
# 預期: average rate: 1.xxx (~1 Hz 為正常)

# 3. 查看 /odom 數據（里程計）
ros2 topic echo /odom --once
# 應顯示位置和速度數據

# Ctrl+C 停止測試
```

**✅ 檢查點**:
- `/scan` 頻率 > 5 Hz
- `/map` 頻率 ~1 Hz
- 數據內容正常（非全零或錯誤值）

---

### 第三階段：啟動 RViz2 並執行 Phase 1 測試（預計 30-45 分鐘）

#### Step 15: 啟動 RViz2

```powershell
# 1. 確保已載入 ROS2 環境
C:\dev\setup_ros2.bat

# 2. 啟動 RViz2 並載入專案配置
rviz2 -d C:\dev\rviz_configs\single_robot_conf.rviz
```

**RViz2 介面說明**：

```
┌─────────────────────────────────────────────────────────────┐
│  RViz2 主視窗                                                │
├─────────────────────────────────────────────────────────────┤
│  左側面板:                                                    │
│    - Displays（顯示元件）                                     │
│      ✅ Grid（網格）                                          │
│      ✅ RobotModel（機器人模型）                              │
│      ✅ PointCloud2（點雲 /point_cloud2）                     │
│      □ LaserScan（雷射掃描 /scan）← 可啟用                   │
│      □ Map（地圖 /map）← 可啟用                              │
│      □ Path（路徑 /transformed_global_plan）← 可啟用         │
│                                                               │
│  底部面板:                                                    │
│    - SLAM Toolbox Plugin（建圖工具）                         │
│    - Navigation 2（導航工具）                                │
│                                                               │
│  工具列:                                                      │
│    - 2D Pose Estimate（設定初始位置）                        │
│    - 2D Goal Pose（設定導航目標）                            │
└─────────────────────────────────────────────────────────────┘
```

**✅ 檢查點**:
- RViz2 成功啟動，無錯誤訊息
- 左側 Displays 面板顯示綠色勾勾（表示成功訂閱 topics）
- 主視圖中能看到機器人模型（四足機器狗）
- 點雲數據正在更新（彩色點雲）

---

#### Step 16: 啟用關鍵顯示元件

在 RViz2 中手動啟用以下元件（勾選左側 Displays 面板）：

```
✅ LaserScan (/scan)           - 2D 雷射掃描顯示
✅ Map (/map)                  - SLAM 建立的地圖
✅ Path (/transformed_global_plan) - Nav2 路徑規劃
```

**調整視角**（可選）：
- 滑鼠中鍵拖曳：平移視角
- 滑鼠右鍵拖曳：旋轉視角
- 滑鼠滾輪：縮放

**✅ 檢查點**:
- 地圖開始顯示（灰色網格，黑色障礙物）
- 雷射掃描數據呈現紅色射線
- 視角調整流暢，無卡頓

---

#### Step 17: 執行 Phase 1 測試（對照測試報告）

現在開始執行 **7 項核心測試**，同時填寫測試報告：

**測試報告路徑**（在 Mac VM 中編輯）:
```
~/ros2_ws/src/elder_and_dog/docs/03-testing/slam-phase1_test_results_ROY.md
```

##### 檢查 1: Go2 驅動啟動成功 ✅

**已完成**（Step 8 已驗證）

記錄到測試報告：
- ✅ 狀態: 成功
- ✅ 啟動時間: 約 X 秒（根據實際情況）
- ✅ 錯誤訊息: 無

---

##### 檢查 2: /scan 頻率測試 ✅

**已完成**（Step 10 已測試）

```powershell
# Windows PowerShell 重新測試
ros2 topic hz /scan
```

記錄到測試報告：
- ✅ 狀態: 通過（> 5 Hz）
- 平均頻率: X.XX Hz
- 最高頻率: X.XX Hz
- 最低頻率: X.XX Hz
- 穩定性: 穩定/輕微波動/波動明顯

---

##### 檢查 3: SLAM 與 /map 發布 ✅

```powershell
# 測試 /map 頻率
ros2 topic hz /map

# 檢查 SLAM Toolbox 狀態（在 RViz2 SLAM Toolbox Plugin 面板）
# 應顯示: "SLAM Toolbox Running"
```

記錄到測試報告：
- ✅ 狀態: 通過
- /map 頻率: X.XX Hz（目標 ~1 Hz）
- SLAM 狀態: 正常/異常
- Nav2 啟動時間: X 秒

---

##### 檢查 4: TF 樹完整性檢查 ✅

```powershell
# 方法 A: 使用 tf2 工具（需安裝 tf2-tools）
ros2 run tf2_tools view_frames
# 會生成 frames.pdf（可能在 Windows 無法直接執行）

# 方法 B: 列出所有 TF frames
ros2 topic echo /tf_static --once
```

**在 RViz2 檢查**:
- 工具列 → Panels → TF（勾選啟用）
- 查看 TF 樹狀結構，確保沒有紅色警告

記錄到測試報告：
- ✅ 狀態: 完整/不完整
- 樹狀完整性: 所有 frames 正常連接
- 斷鏈位置: 無/有（記錄位置）

---

##### 檢查 5: Foxglove 連線與可視化 ⏭️

**可選**（本次測試重點是 RViz2，Foxglove 可稍後測試）

如果要測試 Foxglove：
1. Windows 瀏覽器開啟 Foxglove Studio
2. 連線到 `ws://192.168.64.2:8765`
3. 確認地圖、影像、點雲顯示

記錄到測試報告：
- ✅/⏭️ 狀態: 通過/跳過
- 連線延遲: X ms
- 影像 FPS: X fps
- 地圖顯示品質: 良好/普通/不佳

---

##### 檢查 6: 建圖與地圖存檔 ✅

**操作步驟**:

1. **在 RViz2 觀察建圖過程**：
   - Map 面板應顯示逐漸擴展的地圖
   - 機器人移動時，地圖會自動更新

2. **手動移動機器人**（建立完整地圖）：

   ```powershell
   # 方法 A: 使用 teleop_twist_keyboard（需安裝）
   ros2 run teleop_twist_keyboard teleop_twist_keyboard

   # 方法 B: 直接發布 /cmd_vel（簡單移動）
   # 前進
   ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2, y: 0, z: 0}, angular: {x: 0, y: 0, z: 0}}"

   # 旋轉
   ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0, y: 0, z: 0}, angular: {x: 0, y: 0, z: 0.3}}"

   # 停止
   ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0, y: 0, z: 0}, angular: {x: 0, y: 0, z: 0}}"
   ```

3. **建圖完成後存檔**（在 Mac VM SSH）：

   ```bash
   # 使用 SLAM Toolbox 存檔指令
   ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap "{name: {data: 'phase1_test_map'}}"

   # 地圖會儲存在當前目錄:
   # - phase1_test_map.yaml
   # - phase1_test_map.pgm
   ```

記錄到測試報告：
- ✅ 狀態: 成功/失敗
- 移動距離: 約 X 公尺
- 建圖時間: X 分鐘
- 地圖檔案大小: X KB
- 地圖品質: 良好/普通/不佳（清晰度、障礙物識別）

---

##### 檢查 7: Nav2 自動導航測試 🎯

**這是 Phase 1 的核心測試！**

**操作步驟**:

1. **設定機器人初始位置**（AMCL Localization）：
   - RViz2 工具列 → 點擊 **2D Pose Estimate**
   - 在地圖上點擊機器人實際位置
   - 拖曳箭頭指向機器人朝向
   - 鬆開滑鼠，機器人模型應對齊到地圖

2. **設定導航目標**：
   - RViz2 工具列 → 點擊 **2D Goal Pose**（或 Nav2 Goal）
   - 在地圖上點擊目標位置
   - 拖曳箭頭指向期望的最終朝向
   - 鬆開滑鼠，Nav2 開始規劃路徑

3. **觀察導航過程**：
   - **綠色線**：全局路徑規劃（從起點到終點）
   - **紅色/藍色區域**：Costmap（障礙物代價地圖）
   - **機器人移動**：應沿著規劃路徑前進

4. **測試多個目標點**（至少 3-5 次）：
   - 目標 1: 近距離直線（2 公尺內）
   - 目標 2: 中距離轉彎（3-5 公尺）
   - 目標 3: 遠距離複雜路徑（> 5 公尺）
   - 目標 4-5: 隨機位置

5. **記錄成功率**：
   - 成功: 機器人到達目標點，誤差 < 0.5 公尺
   - 失敗: 路徑規劃失敗、碰撞、卡住、超時

記錄到測試報告：
- ✅ 狀態: 通過/未通過
- 測試次數: X 次
- 成功次數: X 次
- 成功率: XX%（目標 ≥ 80%）
- 平均導航時間: X 秒
- 平均誤差距離: X 公尺

---

#### Step 18: 截圖並填寫測試報告（10 分鐘）

**需要的截圖**（Windows 截圖工具: Win + Shift + S）:

1. **RViz2 主界面** - 顯示完整地圖 + 機器人模型
2. **SLAM 建圖過程** - 地圖逐漸擴展的畫面
3. **Nav2 路徑規劃** - 綠色路徑 + Costmap
4. **PowerShell 輸出** - `ros2 topic hz /scan` 和 `/map` 結果
5. **成功導航** - 機器人到達目標點

**儲存截圖**：
- 位置: `C:\dev\phase1_screenshots\`
- 命名: `01_rviz_main.png`, `02_slam_mapping.png`, ...

**在 Mac VM 中編輯測試報告**：
```bash
cd ~/ros2_ws/src/elder_and_dog
code docs/03-testing/slam-phase1_test_results_ROY.md
# 或使用 vim/nano 編輯
```

填寫所有檢查項目的實測結果、數值、狀態。

---

### 第四階段：測試總結與下一步（10 分鐘）

#### Step 19: 完成測試報告

填寫測試報告的最後幾個章節：

1. **測試總結**：
   - 通過項目: X / 7
   - 整體評估: 優點、待改進項、嚴重問題

2. **問題排查記錄**（如果有問題）：
   - 現象、原因、解決方案、驗證結果

3. **系統資訊記錄**：
   - 硬體環境、軟體環境、網路環境

4. **下一步行動**：
   - 如果 ≥ 6/7 通過: 準備 Phase 2 座標轉換
   - 如果 < 6/7: 排查故障，重新測試

5. **時間記錄**：
   - 測試開始/結束時間
   - 總耗時

---

#### Step 20: 準備 11/26 週會報告（可選，30 分鐘）

根據測試結果，準備簡短的週會報告：

**報告大綱**:
1. **本週完成項目**:
   - ✅ Windows ROS2 環境建立
   - ✅ Phase 1 SLAM + Nav2 測試（X/7 通過）
   - ✅ 解決導航延遲問題（改用 RViz2）

2. **測試結果摘要**:
   - /scan 頻率: X Hz
   - /map 更新: X Hz
   - Nav2 成功率: XX%

3. **遇到的問題與解決**:
   - 問題: Foxglove 延遲導致機器狗旋轉
   - 解決: 改用 Windows 本地 RViz2（延遲 < 5ms）

4. **下週計畫**:
   - Phase 2: 座標轉換（W7-W8）
   - 預覽 tf2_ros 和 URDF 技術

---

## 🎯 快速檢查清單（全部完成後打勾）

### 安裝階段
- [ ] Visual C++ Redistributables 安裝完成
- [ ] ROS2 Humble 解壓縮到 `C:\dev\ros2_humble`
- [ ] `C:\dev\setup_ros2.bat` 建立完成
- [ ] `C:\dev\cyclonedds_config.xml` 建立完成
- [ ] `ros2 --version` 測試成功
- [ ] Windows 防火牆規則建立完成
- [ ] RViz2 配置檔案複製完成

### 連線測試階段
- [ ] Mac VM ROS2 系統啟動成功
- [ ] Windows `ros2 topic list` 能看到 Mac VM topics
- [ ] `/scan` 頻率 > 5 Hz
- [ ] `/map` 頻率 ~1 Hz
- [ ] RViz2 成功啟動並載入配置

### Phase 1 測試階段
- [ ] 檢查 1: Go2 驅動啟動成功 ✅
- [ ] 檢查 2: /scan 頻率測試 ✅
- [ ] 檢查 3: SLAM 與 /map 發布 ✅
- [ ] 檢查 4: TF 樹完整性檢查 ✅
- [ ] 檢查 5: Foxglove 連線與可視化 ✅/⏭️
- [ ] 檢查 6: 建圖與地圖存檔 ✅
- [ ] 檢查 7: Nav2 自動導航測試 ✅（成功率 ≥ 80%）

### 報告階段
- [ ] 截圖完成（5 張以上）
- [ ] 測試報告填寫完成
- [ ] 測試總結與下一步行動記錄
- [ ] 週會報告準備完成（可選）

---

## ⚠️ 常見問題與解決方案

### 問題 1: `ros2 topic list` 看不到 Mac VM 的 topics

**可能原因**:
1. Windows 和 Mac VM 的 `ROS_DOMAIN_ID` 不一致
2. CycloneDDS 配置錯誤
3. Windows 防火牆阻擋 UDP 埠

**解決方案**:
```powershell
# 1. 確認環境變數一致（兩端都要檢查）
# Windows:
echo %ROS_DOMAIN_ID%          # 必須為 0
echo %RMW_IMPLEMENTATION%     # 必須為 rmw_cyclonedds_cpp

# Mac VM:
echo $ROS_DOMAIN_ID           # 必須為 0
echo $RMW_IMPLEMENTATION      # 必須為 rmw_cyclonedds_cpp

# 2. 重啟兩端的 ROS2 系統
# 3. 檢查防火牆規則是否啟用
```

---

### 問題 2: RViz2 啟動後 Displays 顯示紅色叉叉

**可能原因**:
1. Topic 名稱不匹配
2. Mac VM ROS2 系統未啟動
3. 網路連線中斷

**解決方案**:
```powershell
# 1. 確認 topic 是否存在
ros2 topic list | findstr /C:"point_cloud2" /C:"scan" /C:"map"

# 2. 手動修改 RViz2 Display 的 Topic 名稱
# 左側 Displays → 展開元件 → Topic → 下拉選單選擇正確的 topic

# 3. 重新載入配置
# File → Open Config → 選擇 C:\dev\rviz_configs\single_robot_conf.rviz
```

---

### 問題 3: Nav2 路徑規劃失敗

**可能原因**:
1. 未設定初始位置（AMCL 未 localize）
2. 目標點在障礙物上或地圖外
3. Costmap 未正確配置

**解決方案**:
```powershell
# 1. 重新設定初始位置
# RViz2 → 2D Pose Estimate → 點擊機器人實際位置

# 2. 檢查 Costmap 顯示
# Displays → 展開 Navigation 2 → 勾選 Local Costmap 和 Global Costmap

# 3. 選擇空曠區域作為目標點
# 避免選擇黑色障礙物區域或灰色未知區域

# 4. 查看 Nav2 日誌（Mac VM）
# 終端會顯示路徑規劃失敗原因
```

---

### 問題 4: 機器人移動時地圖扭曲或跳動

**可能原因**:
1. TF 樹不穩定
2. IMU 數據異常
3. /odom 頻率過低

**解決方案**:
```powershell
# 1. 檢查 /odom 頻率
ros2 topic hz /odom
# 應 > 10 Hz

# 2. 檢查 TF 延遲
ros2 topic echo /diagnostics --once
# 查看 TF delay 相關訊息

# 3. 重啟 SLAM Toolbox
# Mac VM SSH: Ctrl+C 停止 launch，重新啟動
```

---

### 問題 5: 截圖中文顯示亂碼

**可能原因**:
Windows 截圖工具不支援某些字體

**解決方案**:
- 使用 Snipping Tool (Win + Shift + S)
- 或安裝 Greenshot、ShareX 等第三方截圖工具
- 確保截圖前字體顯示正常

---

## 📚 參考資源

- **ROS2 Humble Windows 官方文件**: https://docs.ros.org/en/humble/Installation/Windows-Install-Binary.html
- **CycloneDDS 配置指南**: https://github.com/eclipse-cyclonedds/cyclonedds#configuration
- **RViz2 使用教學**: https://docs.ros.org/en/humble/Tutorials/Intermediate/RViz/RViz-User-Guide/RViz-User-Guide.html
- **Nav2 官方文件**: https://navigation.ros.org/
- **專題測試報告模板**: `docs/03-testing/slam-phase1_test_results_ROY.md`
- **綜合測試指南**: `docs/01-guides/slam_nav/綜合測試指南-Windows開發環境.md`

---

## 🔧 附錄：完整除錯流程（2025/11/29 實戰經驗）

### 問題診斷流程

如果你遇到 `ModuleNotFoundError: No module named 'rclpy._rclpy_pybind11'` 錯誤，請依序執行以下診斷步驟：

#### Step 1: 檢查下載檔案大小

```powershell
# 檢查下載的 ZIP 檔案
$file = Get-Item "$env:USERPROFILE\Downloads\ros2-humble-*.zip"
$sizeGB = [math]::Round($file.Length / 1GB, 2)
Write-Host "檔案大小: $sizeGB GB"

# 正常大小檢查
if ($sizeGB -lt 0.6) {
    Write-Host "❌ 檔案異常！應該 > 0.6 GB" -ForegroundColor Red
    Write-Host "請重新下載或換版本" -ForegroundColor Yellow
} else {
    Write-Host "✅ 檔案大小正常" -ForegroundColor Green
}
```

**預期結果**:
- Patch Release 7 (2023-06-14): ~620 MB (壓縮) → ~2 GB (解壓)
- Patch Release 13 (2025-07-21): **只有 375 MB（異常，缺檔！）**

---

#### Step 2: 檢查解壓後的關鍵檔案

```powershell
# 檢查關鍵檔案是否存在
$files = @{
    "local_setup.bat" = "C:\dev\ros2_humble\local_setup.bat"
    "python.exe" = "C:\dev\ros2_humble\python.exe"
    "ros2.exe" = "C:\dev\ros2_humble\Scripts\ros2.exe"
    "_rclpy_pybind11.pyd" = "C:\dev\ros2_humble\Lib\site-packages\_rclpy_pybind11.pyd"
}

Write-Host "`n檢查結果：" -ForegroundColor Yellow
foreach ($name in $files.Keys) {
    $exists = Test-Path $files[$name]
    $status = if ($exists) { "✅" } else { "❌" }
    Write-Host "$status $name : $exists"
}
```

**預期結果**:
- 所有檔案都應該存在（✅ True）
- 如果 `_rclpy_pybind11.pyd` 不存在 → **版本有問題，重新下載**

---

#### Step 3: 檢查 Python 路徑

```powershell
# 載入 ROS2 環境後檢查
C:\dev\setup_ros2.bat

# 檢查 Python 版本
python --version
# 應顯示: Python 3.8.3

# 檢查 Python 路徑
where python
# 應指向: C:\dev\ros2_humble\python.exe（ROS2 內建的 Python）

# 檢查 ros2 指令路徑
where ros2
# 應指向: C:\dev\ros2_humble\Scripts\ros2.exe
```

**常見問題**:
- 如果 `python` 指向系統 Python（如 `C:\Python38\python.exe`）→ 環境變數設定錯誤
- 解決：確認 `setup_ros2.bat` 中有 `call C:\dev\ros2_humble\local_setup.bat`

---

#### Step 4: 測試 Python 模組導入

```powershell
# 在已載入 ROS2 環境的 PowerShell 中執行
python -c "import rclpy; print('rclpy OK')"
python -c "import rclpy._rclpy_pybind11; print('_rclpy_pybind11 OK')"
```

**預期結果**:
```
rclpy OK
_rclpy_pybind11 OK
```

**如果失敗**:
```
ModuleNotFoundError: No module named 'rclpy._rclpy_pybind11'
```
→ **確認檔案缺失，需要重新下載正確版本**

---

### 解決方案：重新安裝正確版本

如果診斷確認是版本問題，請完整重新安裝：

```powershell
# 1. 完全清理（系統管理員 PowerShell）
Remove-Item -Recurse -Force C:\dev\ros2_humble
Remove-Item -Force "$env:USERPROFILE\Downloads\ros2-humble-*.zip"

# 2. 下載正確版本（使用瀏覽器或 PowerShell）
# 方法 A: 手動下載
# 前往: https://github.com/ros2/ros2/releases/tag/release-humble-20230614
# 下載: ros2-humble-20230614-windows-release-amd64.zip

# 方法 B: 使用 PowerShell 下載（可能較慢）
$url = "https://github.com/ros2/ros2/releases/download/release-humble-20230614/ros2-humble-20230614-windows-release-amd64.zip"
$output = "$env:USERPROFILE\Downloads\ros2-humble-20230614-windows-release-amd64.zip"
Invoke-WebRequest -Uri $url -OutFile $output

# 3. 驗證檔案大小
$file = Get-Item "$env:USERPROFILE\Downloads\ros2-humble-20230614-windows-release-amd64.zip"
Write-Host "檔案大小: $([math]::Round($file.Length / 1MB, 2)) MB"
# 應該顯示 ~620 MB

# 4. 解壓縮（使用 7-Zip 命令列，最可靠）
& "C:\Program Files\7-Zip\7z.exe" x "$env:USERPROFILE\Downloads\ros2-humble-20230614-windows-release-amd64.zip" -o"C:\dev"

# 5. 重新命名（如果解壓後資料夾名稱過長）
if (Test-Path "C:\dev\ros2-humble-20230614-windows-release-amd64") {
    Rename-Item -Path "C:\dev\ros2-humble-20230614-windows-release-amd64" -NewName "ros2_humble"
}

# 6. 驗證安裝
Test-Path "C:\dev\ros2_humble\_rclpy_pybind11.pyd"
# 應該顯示: True ✅

# 7. 測試 ROS2
cmd /k "C:\dev\setup_ros2.bat"
ros2 --help
# 應該顯示幫助訊息，而不是錯誤
```

---

### 網路問題診斷

如果 `ros2 topic list` 看不到 Mac VM 的 topics：

```powershell
# 1. 測試網路連通性
ping 192.168.1.200
# 應該有回應，延遲 < 10ms

# 2. 檢查環境變數（Windows）
echo %ROS_DOMAIN_ID%
echo %RMW_IMPLEMENTATION%
echo %CYCLONEDDS_URI%

# 預期值：
# ROS_DOMAIN_ID=0
# RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
# CYCLONEDDS_URI=file:///C:/dev/cyclonedds_config.xml

# 3. 檢查環境變數（Mac VM SSH）
echo $ROS_DOMAIN_ID
echo $RMW_IMPLEMENTATION

# 預期值：
# ROS_DOMAIN_ID=0
# RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# 4. 檢查防火牆規則
Get-NetFirewallRule -DisplayName "ROS2 DDS*"
# 應該顯示兩條規則（Inbound, Outbound）且狀態為 Enabled

# 5. 測試 DDS 發現
ros2 daemon stop
ros2 daemon start
ros2 topic list
# 等待 5-10 秒讓 DDS 發現節點
```

---

### UTM 網路配置（Mac VM 端）

如果 Windows 無法 ping 通 Mac VM：

**在 Mac 本機執行：**

```bash
# 1. 停止 VM
# UTM 介面 → 停止虛擬機

# 2. 編輯 VM 網路設定
# UTM → 選擇 VM → 編輯 → 網路
# 網路模式：從 "Shared Network" 改為 "Bridged (Advanced)"
# 橋接介面：選擇實體網卡（通常是 en0 或 Wi-Fi）

# 3. 啟動 VM 並設定靜態 IP
# 在 VM 內執行（SSH 或終端）：
sudo nmcli con mod "Wired connection 1" ipv4.addresses 192.168.1.200/24
sudo nmcli con mod "Wired connection 1" ipv4.gateway 192.168.1.1
sudo nmcli con mod "Wired connection 1" ipv4.dns "8.8.8.8"
sudo nmcli con mod "Wired connection 1" ipv4.method manual
sudo nmcli con up "Wired connection 1"

# 4. 驗證網路
ip addr show
# 應該看到 inet 192.168.1.200/24

# 5. 測試從 VM ping Windows
ping 192.168.1.146
# 應該有回應
```

---

### 今日除錯經驗總結（2025/11/29）

#### 📊 時間線

```
09:00 - 10:30  安裝基礎依賴（Python, OpenSSL, Qt5, 6個 .nupkg）✅
10:30 - 12:00  首次下載 ROS2 Patch 13，發現檔案小異常 ⚠️
12:00 - 13:30  嘗試解壓縮，發現缺 _rclpy_pybind11.pyd ❌
13:30 - 15:00  診斷 Python 路徑、PYTHONPATH、環境變數問題 🔍
15:00 - 16:30  網路搜尋，找到 GitHub Issue #1720 確認官方 Bug 🎯
16:30 - 17:00  規劃明日解決方案（下載 Patch 7）📝
```

#### 🎓 學到的經驗

1. **驗證比安裝更重要**
   - 下載後立即檢查檔案大小
   - 解壓後立即檢查關鍵檔案
   - 不要等到執行時才發現問題

2. **不要盲目相信「最新版本」**
   - 最新版本可能有未發現的 Bug
   - 社群驗證過的穩定版本更可靠
   - Patch Release 7 (2023-06) > Patch Release 13 (2025-07)

3. **系統性除錯流程**
   ```
   檔案大小檢查 → 關鍵檔案檢查 → Python 路徑檢查 → 模組導入測試
   ```
   - 每一層都要驗證
   - 從底層往上層排查
   - 不要跳過任何步驟

4. **善用 GitHub Issues**
   - ROS2 官方 repo 的 Issues 是寶庫
   - 搜尋 `ModuleNotFoundError _rclpy_pybind11 Windows`
   - 找到 Issue #1720 確認官方 Bug

#### 🚀 明日行動計畫（2025/11/30）

**目標**：一次性完成 ROS2 安裝並通過 Phase 1 測試

```
09:00 - 09:30  下載 Patch Release 7 (620 MB)
09:30 - 09:45  使用 7-Zip 解壓縮 + 驗證關鍵檔案
09:45 - 10:00  測試 ros2 --help, ros2 topic list
10:00 - 10:30  Mac VM 啟動 ROS2 + Windows 連線測試
10:30 - 11:00  RViz2 啟動 + 視覺化測試
11:00 - 12:00  Phase 1 Nav2 導航測試（3-5 次）
13:00 - 13:30  截圖 + 填寫測試報告
13:30 - 14:00  整理今日成果 + 更新進度
```

**成功標準**：
- ✅ `ros2 topic list` 能看到 Mac VM 的 topics
- ✅ RViz2 正常顯示地圖、LiDAR、機器人模型
- ✅ Nav2 導航成功率 ≥ 80%（至少 4/5 次成功）
- ✅ /scan 頻率 > 5 Hz, /map 頻率 ~1 Hz

---

## ✅ 完成標準

**Phase 1 測試通過條件**:
- ✅ 7 項檢查中至少 **6 項通過**（≥ 85.7%）
- ✅ Nav2 導航成功率 **≥ 80%**（至少 4/5 次成功）
- ✅ 無嚴重錯誤（系統崩潰、數據丟失等）

**如果達成以上條件**:
- 🎉 Phase 1 完成！
- 📝 更新專題進度（Phase 1 → 100%）
- 🚀 準備進入 Phase 2: 座標轉換（W7-W8）

---

**祝測試順利！有任何問題隨時回報。** 🚀

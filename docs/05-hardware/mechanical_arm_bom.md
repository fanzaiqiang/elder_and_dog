# Go2 硬體擴充研究方向

**更新日期：** 2025/12/24
**狀態：** 研究階段（1/7 僅展示設計概念）

---

## 🎯 目標

讓 Go2 從「找得到」升級為「拿得到」+ 「能互動」

---

## 📋 研究方向

### 1. 機械手臂/夾爪

**關鍵字：** `3D printed robot arm`, `servo gripper`, `Arduino robot arm`

| 方向 | 說明 | 搜尋關鍵字 |
|------|------|-----------|
| 舵機式機械臂 | 傳統多關節設計 | `MeArm`, `robot arm servo` |
| 仿人型機械手 | 五指手掌，可握手/按按鈕 | `InMoov hand`, `OpenBionics` |
| 軟性觸手夾爪 | Tendon-driven 軟體機器人 | `soft robotics gripper`, `tendon gripper` |
| 簡易夾爪 | 只有開合功能 | `simple gripper servo` |

---

### 2. 機械眼睛/表情

**關鍵字：** `animatronic eye`, `LED matrix expression`, `robot eye servo`

| 方向 | 說明 | 搜尋關鍵字 |
|------|------|-----------|
| 舵機眼球 | 機械式轉動 | `animatronic eye servo` |
| LED 矩陣 | 像素表情 | `WS2812B 8x8 face` |
| OLED 螢幕 | 高解析表情 | `Adafruit animated eyes` |

---

### 3. 🆕 多功能尾巴（創新方向）

**關鍵字：** `animatronic tail`, `tentacle robot`, `continuum robot`

| 功能 | 說明 | 搜尋關鍵字 |
|------|------|-----------|
| 🔄 抓取 | 像觸手捲起物品 | `tentacle gripper`, `continuum robot` |
| 💬 情緒 | 搖尾巴=開心 | `animatronic tail emotion` |
| 📡 感測 | 尾端裝相機/LiDAR | `robot tail sensor mount` |

**尾巴開源專案：**

| 專案 | 說明 | 連結 |
|------|------|------|
| **Cudatox Animatronic Tail** | ✅ STL + OpenSCAD 完整 | [Thingiverse](https://www.thingiverse.com/thing:5172189) |
| **Animatronic Tail by Pedrodeoro** | ✅ STL + Arduino | [Thingiverse](https://www.thingiverse.com/thing:3214024) |
| **open-tentacle** | 觸手機器人 Arduino | [GitHub](https://github.com/jasonmhead/open-tentacle) |
| **Continuum-Robot** | SolidWorks + Arduino | [GitHub](https://github.com/VisakanMathy/Continuum-Robot) |
| **ENDO Manipulator** | 學術級連續體機器人 | [GitHub](https://github.com/ORIMIS-UK/ENDO) |

---

## 🏆 GitHub 知名開源專案

### Awesome Lists（精選列表）

| 專案 | 說明 |
|------|------|
| [awesome-robotics](https://github.com/ahundt/awesome-robotics) | 機器人資源總整理 |
| [awesome-open-source-robots](https://github.com/stephane-caron/awesome-open-source-robots) | 開源硬體+軟體 |
| [awesome-robotics-projects](https://github.com/mjyc/awesome-robotics-projects) | 可負擔專案 |
| [awesome-ros](https://github.com/ps-micro/awesome-ros) | ROS/ROS2 資源 |

---

### AI / 操作類

| 專案 | 說明 | 亮點 |
|------|------|------|
| [OpenVLA](https://github.com/openvla/openvla) | 視覺-語言-動作模型 | 通用抓取 |
| [LeRobot](https://github.com/huggingface/lerobot) | HuggingFace 機器人 AI | 模仿學習 |
| [MoveIt2](https://github.com/moveit/moveit2) | ROS2 運動規劃框架 | 業界標準 |

---

### 機械手臂

| 專案 | 說明 | 成本 |
|------|------|------|
| [OpenArm](https://github.com/enactic/openarm) | 7-DOF 人形手臂 | 高 |
| [SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100) | 6-DOF LeRobot 相容 | $100 USD |
| [Thor](https://github.com/AngelLM/Thor) | 6-DOF 3D 列印 | 低 |
| [BCN3D Moveo](https://github.com/BCN3D/BCN3D-Moveo) | 5-DOF 教育用 | 低 |
| [AR4-MK3](https://github.com/Annin-Robotics/AR4-MK3) | 6-DOF 工業級 | 中 |
| [AmazingHand](https://github.com/pollen-robotics/AmazingHand) | 仿人手掌 8 舵機 | 低 |
| [InMoov](https://inmoov.fr) | 全身人形（可只做手） | 中 |
| [OpenBionics](https://github.com/OpenBionics) | 開源義肢 | 低 |

---

### 四足機器人

| 專案 | 說明 |
|------|------|
| [Stanford Doggo](https://github.com/Nate711/StanfordDoggoProject) | 史丹佛開源四足 |
| [Spot Micro](https://gitlab.com/public-open-source/spotmicroai) | 迷你版 Spot |
| [mjbots quad](https://github.com/mjbots/quad) | 高性能四足 |

---

### 模擬器

| 專案 | 說明 |
|------|------|
| [Gazebo](https://gazebosim.org) | ROS 官方模擬器 |
| [Isaac Sim](https://developer.nvidia.com/isaac-sim) | NVIDIA 高保真 |
| [PyBullet](https://github.com/bulletphysics/bullet3) | Python 物理引擎 |
| [Unity Robotics Hub](https://github.com/Unity-Technologies/Unity-Robotics-Hub) | Unity + ROS |

---

### 演算法/學習資源

| 專案 | 說明 |
|------|------|
| [PythonRobotics](https://github.com/AtsushiSakai/PythonRobotics) | 機器人演算法 Python |
| [awesome-robotics-manipulation](https://github.com/BaiShuanghao/Awesome-Robotics-Manipulation) | 操作相關論文 |

---

## 🔍 搜尋平台

- **GitHub** - 開源程式碼
- **Thingiverse** - 3D 列印 STL
- **Instructables** - DIY 教學
- **Hackaday.io** - 硬體專案
- **Yeggi** - 3D 模型搜尋引擎

---

## 📅 時程

| 階段 | 時間 | 目標 |
|------|------|------|
| 1/7 | 設計概念圖 | 簡報展示 |
| 寒假 | 選定方案 + 採購 | 確定規格 |
| 3月前 | 實作 + 整合 | 可動原型 |
| 6月前 | 完善 + 論文 | 完整系統 |

---

## ⚠️ Go2 整合重點

1. **安裝：** 魔鬼氈固定於背部/頭部
2. **重量：** 輕量化，避免影響平衡
3. **電源：** 獨立電池或 Go2 USB
4. **通訊：** USB Serial → ROS2 Bridge

---

## ✏️ 待確認

- [ ] 預算上限
- [ ] 優先做哪個（手臂/眼睛/尾巴）
- [ ] 負責人分配

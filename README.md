# PawAI — 老人與狗

> 以 Unitree Go2 Pro 為載體的 embodied AI 互動平台。
> 核心是「人臉辨識 + 中文語音互動 + AI 大腦決策」。

**硬底線**：2026/4/13 展示

完整專案說明請見 [`docs/mission/README.md`](docs/mission/README.md)。

---

## 文件入口

| 文件 | 說明 |
|------|------|
| [`docs/mission/README.md`](docs/mission/README.md) | 專案方向、功能閉環、分工、Demo 定義 |
| [`docs/architecture/README.md`](docs/architecture/README.md) | 技術契約、資料流、Clean Architecture |
| [`docs/Pawai-studio/README.md`](docs/Pawai-studio/README.md) | Studio / Gateway / Brain / Frontend |
| [`docs/setup/README.md`](docs/setup/README.md) | 環境建置、Jetson 設定、操作手冊 |

---

## Quick Start

```bash
# Jetson 上建構
source /opt/ros/humble/setup.zsh
colcon build
source install/setup.zsh

# 啟動 Go2 驅動（最小模式）
export ROBOT_IP="192.168.123.161"
export CONN_TYPE="webrtc"
ros2 launch go2_robot_sdk robot.launch.py \
  enable_tts:=false nav2:=false slam:=false rviz2:=false foxglove:=false
```

詳細環境建置見 [`docs/setup/README.md`](docs/setup/README.md)。

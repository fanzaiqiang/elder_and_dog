# PawAI 文件中心

**專案**：老人與狗 (Elder and Dog) / PawAI

> 新成員先看 mission，再看 architecture，再看 Pawai-studio。

---

## 主幹文件

| 文件 | 說明 |
|------|------|
| [mission/README.md](./mission/README.md) | **專案真相來源** — 功能閉環、P0/P1/P2、Demo、分工、降級策略 |
| [mission/handoff_316.md](./mission/handoff_316.md) | **3/16 分工交付清單** — 誰做什麼、驗收標準、攻守交換 |
| [architecture/interaction_contract.md](./architecture/interaction_contract.md) | **技術契約** — ROS2 Topic schema、節點參數、QoS |
| [architecture/README.md](./architecture/README.md) | 架構文件導航 |
| [Pawai-studio/README.md](./Pawai-studio/README.md) | **PawAI Studio** — system-architecture / event-schema / ui-orchestration / brain-adapter |

---

## 功能模組

| 模組 | 文件 | 優先級 |
|------|------|:------:|
| 人臉辨識 | [人臉辨識/README.md](./人臉辨識/README.md) | P0 |
| 語音功能 | [語音功能/README.md](./語音功能/README.md)、[jetson-MVP測試.md](./語音功能/jetson-MVP測試.md) | P0 |
| 手勢辨識 | [手勢辨識/README.md](./手勢辨識/README.md) | P1 |
| 辨識物體 | [辨識物體/README.md](./辨識物體/README.md) | P2 |
| 導航避障 | [導航避障/README.MD](./導航避障/README.MD) | P2 |

---

## 環境與部署

| 文件 | 說明 |
|------|------|
| [setup/README.md](./setup/README.md) | 環境建置總覽 |
| [setup/hardware/](./setup/hardware/) | Jetson 設定、GPU 連接 |
| [setup/software/](./setup/software/) | 基礎操作說明 |

---

## 文件治理規則

### 目標目錄結構

```
docs/
├── mission/          # 專案方向、決策、分工
├── architecture/     # 技術契約、資料流、分層原則
├── Pawai-studio/     # Studio / Gateway / Brain / Frontend
├── modules/          # 功能模組文件（規劃中）
├── setup/            # 環境、部署、操作手冊
├── archive/          # 歸檔區（不列入主導航）
└── assets/           # 文件媒體資產
```

### 衝突仲裁

- 專案方向、P0/P1/P2、分工、Demo → 以 `mission/` 為準
- ROS2 介面、schema、QoS、跨模組契約 → 以 `architecture/` 為準
- Studio / Gateway / Brain / Frontend → 以 `Pawai-studio/` 為準
- 模組內部設計 → 以各模組 README 為準
- 安裝、部署、操作步驟 → 以 `setup/` 為準

完整治理規則見 [設計規格](./superpowers/specs/2026-03-13-docs-restructure-design.md)。

---

*維護者：System Architect*

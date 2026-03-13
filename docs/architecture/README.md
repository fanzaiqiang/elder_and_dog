# PawAI 架構文件

本目錄管技術契約、架構原則、資料流。專案方向見 [mission/README.md](../mission/README.md)，Studio 設計見 [Pawai-studio/README.md](../Pawai-studio/README.md)。

---

## 文件清單

| 文件 | 說明 | 狀態 |
|------|------|------|
| [interaction_contract.md](./interaction_contract.md) | ROS2 介面契約 v2.0 — Topic/Action/schema/QoS | **凍結** |
| [clean_architecture.md](./clean_architecture.md) | Clean Architecture 分層原則（Layer 2 模組適用） | 有效 |
| [data_flow.md](./data_flow.md) | 系統資料流圖 | 有效（部分節點名稱待對齊） |
| [face_perception.md](./face_perception.md) | ~~歷史人臉模組設計~~ — 已被 `interaction_contract.md` 與 [人臉辨識/README.md](../人臉辨識/README.md) 取代 | SUPERSEDED |

---

## 閱讀建議

- **整合者**：先看 `interaction_contract.md`，再看 `data_flow.md`
- **新模組開發者**：先看 `clean_architecture.md`，再看 `interaction_contract.md`
- **前端/Studio 開發者**：直接看 [Pawai-studio/](../Pawai-studio/README.md)，此目錄非必讀

---

## 邊界

本目錄只管技術契約與架構原則。專案方向與分工見 `mission/`，Studio 設計見 `Pawai-studio/`，安裝部署見 `setup/`。

---

*維護者：System Architect*
*最後更新：2026-03-13*

# Go2 智慧尋物系統文件索引（依現有檔案重整）

**專案名稱：** 基於 Go2 機器狗的智慧陪伴與尋物系統  
**最後更新：** 2025/11/23  
🎯 **第一階段發表：2025/12/17**

> 本頁僅列出目前實際存在的文件，並標註缺漏的 SOP/設計稿，避免讀者點到不存在的連結。

---

## 🗂️ 目錄地圖（現況）

| 資料夾 | 用途 | 代表文件 |
|--------|------|----------|
| `00-overview/` | 高層目標、計畫、進度 | `專題目標.md`，`開發計畫.md`，`團隊進度追蹤/` |
| `01-guides/` | 操作指南與日常流程 | `quickstart_w6_w9.md`，`基礎動作操作說明.md`，`slam_nav/`，`坐標轉換/` |
| `02-design/` | 技術整合藍圖 | `integration_plan.md` |
| `03-testing/` | 測試結果與驗收 | `slam-phase1_test_results_ROY.md` |
| `04-notes/` | 變更紀錄與開發日誌 | `CHANGELOG.md`，`dev_notes/` |

---

## 00-overview · 專案概覽
- [專題目標.md](./00-overview/專題目標.md) — 願景、時程、風險
- [開發計畫.md](./00-overview/開發計畫.md) — 現況 vs 目標差異與行動項目
- **團隊進度**：`00-overview/團隊進度追蹤/`
  - [Roy第一階段計畫.md](./00-overview/團隊進度追蹤/Roy第一階段計畫.md)
  - [團隊進度.md](./00-overview/團隊進度追蹤/團隊進度.md)
  - b組/c組 第一階段計畫
- **缺件提醒**：尚未有 Goal/現況符合度獨立文件（原索引提到的 Goal.md/claude_plan.md 不存在）。

## 01-guides · 操作手冊
- [quickstart_w6_w9.md](./01-guides/quickstart_w6_w9.md) — 每日任務 Checklist
- [基礎動作操作說明.md](./01-guides/基礎動作操作說明.md) — 基本控制指令
- SLAM / Nav2
  - [README](./01-guides/slam_nav/README.md) — 測試總覽與導覽
  - [slam+nav2小空間測試.md](./01-guides/slam_nav/slam+nav2小空間測試.md) — Phase 1 小空間最新指南
  - [slam+nav2大空間測試.md](./01-guides/slam_nav/slam+nav2大空間測試.md) — Phase 2 大空間評估
- 座標轉換
  - [座標組間介面約定.md](./01-guides/坐標轉換/座標組間介面約定.md)
- **缺件提醒**：尚未提供環境安裝/依賴管理/遠端 GPU/WebRTC 故障排查等 SOP（原 README 提到的 environment_setup_ubuntu.md、remote_gpu_setup.md、dependency_management.md… 目前不存在）。

## 02-design · 架構與模組
- [integration_plan.md](./02-design/integration_plan.md) — W6-W9 技術整合藍圖（Plan A：COCO）
- **缺件提醒**：尚未有 VLM、座標轉換、FSM、Isaac Sim 詳細設計稿（可後續新增 `coco_vlm_development.md`、`coordinate_transformation.md`、`search_fsm_design.md`、`isaac_sim_integration.md` 等）。

## 03-testing · 測試與驗收
- [slam-phase1_test_results_ROY.md](./03-testing/slam-phase1_test_results_ROY.md) — Phase 1 測試結果
- **缺件提醒**：尚未有 testing_plan/testing_and_verification 等測試計畫文件。

## 04-notes · 歷程與手札
- [CHANGELOG.md](./04-notes/CHANGELOG.md) — 文件與程式異動紀錄
- `dev_notes/` — 每日開發日誌（2025-11-18~11-23 等）

---

## 🚀 快速開始（依現有文件）
1. 讀概覽：`00-overview/專題目標.md` → `00-overview/開發計畫.md`
2. 看行動藍圖：`02-design/integration_plan.md`
3. 執行 Phase 1/2：`01-guides/slam_nav/README.md` + 小/大空間測試文件
4. 追進度：`00-overview/團隊進度追蹤/`（Roy/b組/c組）
5. 查測試結果：`03-testing/slam-phase1_test_results_ROY.md`

---

## 🧭 待補文件清單（避免再次出現死鏈）
- 環境/依賴/GPU/WebRTC SOP（安裝、proxy、uv 依賴管理）
- VLM/座標轉換/FSM/Isaac Sim 詳細設計稿
- 測試計畫與驗收標準（testing_plan / testing_and_verification）
- 若新增文件，請同步更新本索引與 `04-notes/CHANGELOG.md`。

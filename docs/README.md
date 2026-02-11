# PawAI 文件中心

**專案：** 老人與狗 (Elder and Dog) - Go2 機器狗智慧陪伴系統  
**版本：** v4.0 (文件重構版)  
**最後更新：** 2026-02-11

---

## 🗺️ 文件導航

| 目錄 | 用途 | 主要內容 |
|------|------|----------|
| **[mission/](./mission/)** | 專案使命 | 願景、路線圖、目標 |
| **[setup/](./setup/)** | 環境建置 | 硬體、軟體、網路配置指南 |
| **[design/](./design/)** | 系統設計 | 架構、API、模組設計 |
| **[testing/](./testing/)** | 測試驗收 | 測試計畫、報告、驗收文件 |
| **[logs/](./logs/)** | 開發日誌 | 依日期組織的開發紀錄 |
| **[assets/](./assets/)** | 靜態資源 | 圖片、圖表、截圖 |
| **[archive/](./archive/)** | 歸檔文件 | 歷史版本與過時文件 |

---

## 🚀 快速開始

### 新手上路
1. 閱讀專案願景：[mission/](./mission/)（待建立新內容）
2. 環境設置：[setup/hardware/](./setup/hardware/)
3. 系統架構：[design/modules/mcp_system_prompt.md](./design/modules/mcp_system_prompt.md)

### 日常開發
1. 查看最新進度：[logs/2026/01/](./logs/2026/01/)
2. 查閱設計文件：[design/](./design/)
3. 執行測試：[testing/](./testing/)

---

## 📁 目錄結構詳解

```
docs/
├── mission/              # 專案使命與願景
│   ├── README.md
│   ├── vision.md         # 專案願景（新版，待撰寫）
│   └── roadmap.md        # 開發路線圖（待撰寫）
│
├── setup/                # 環境建置指南
│   ├── README.md
│   ├── hardware/         # 硬體設置
│   ├── software/         # 軟體安裝
│   ├── network/          # 網路配置
│   └── slam_nav/         # SLAM/導航指南
│
├── design/               # 系統設計文件
│   ├── README.md
│   ├── modules/          # 模組設計
│   └── research/         # 研究與分析
│
├── testing/              # 測試與驗收
│   ├── README.md
│   ├── 專題文件大綱.md
│   └── reports/          # 測試報告
│
├── logs/                 # 開發日誌（依日期組織）
│   ├── README.md
│   ├── 2025/11/          # 2025年11月
│   ├── 2025/12/          # 2025年12月
│   └── 2026/01/          # 2026年1月
│
├── assets/               # 靜態資源
│   ├── diagrams/         # 架構圖、流程圖
│   ├── screenshots/      # 截圖
│   └── photos/           # 照片
│
├── archive/              # 歸檔文件
│   └── 2026-02-11-restructure/
│
└── CHANGELOG.md          # 文件變更紀錄
```

---

## 📜 歷史文件

如需查閱 2026-02-11 之前的文件，請參見：
- [archive/2026-02-11-restructure/](./archive/2026-02-11-restructure/)

---

## 🔄 變更紀錄

參見 [CHANGELOG.md](./CHANGELOG.md) 查看文件結構變更歷史。

---

**維護者：** FJU PawAI 專題組  
**文件狀態：** ✅ 重構完成（Phase 8/8）

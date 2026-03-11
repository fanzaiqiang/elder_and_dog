# 物件辨識模組設計 v1.0

> **適用平台**: NVIDIA Jetson Orin Nano SUPER 8GB + 5× RTX 8000  
> **感測器**: Intel RealSense D435 深度攝影機  
> **目標日期**: 2026-04-13 Demo  
> **設計原則**: 本地即時感知、雲端高精度分析、D435 深度不上傳雲端

---

## 1. 設計原則

### 1.1 快系統 / 慢系統分工

本模組採用「**本地主導即時感知、雲端補強高精度分析**」架構：

| 層級 | 職責 | 延遲要求 |
|------|------|----------|
| **本地 (Jetson)** | 即時固定類別偵測、近場 3D 定位、斷網可用 | < 200ms |
| **雲端 (RTX 8000)** | 高精度分析、開放詞彙、視覺語意理解 | 1-3s 可接受 |

### 1.2 D435 深度攝影機定位

- **本地使用**: RGB 影像做即時偵測 + Depth 做 3D 定位
- **不上傳雲端**: 避免頻寬壓力與延遲問題
- **有效範圍**: 0.3m - 3m（近場感知）

### 1.3 模型選型原則

| 位置 | 選型邏輯 | 理由 |
|------|----------|------|
| **本地** | YOLO26n (輕量) | Edge-First 設計、NMS-free、易部署 |
| **雲端** | YOLO26x/YOLOE/Qwen-VL | 高精度、開放詞彙、視覺語意 |

---

## 2. 本地端設計 (Jetson Orin Nano)

### 2.1 模型規格

| 屬性 | 規格 |
|------|------|
| **模型** | YOLO26n |
| **大小** | ~5 MB |
| **輸入解析度** | 640×640 (建議) 或 320×320 |
| **mAP (COCO)** | 40.1% |
| **架構** | One-stage, NMS-free |

### 2.2 類別清單

#### P0 必測類別（6類）- 3/16 前完成

| 類別 | 用途 | 展示價值 | 風險等級 | 備註 |
|------|------|:--------:|:--------:|------|
| person | 人員互動 | 高 | 低 | COCO 標準類別，特徵明顯 |
| chair | 家具/導航參考 | 高 | 低 | COCO 標準類別，大目標 |
| table | 家具/導航參考 | 高 | 低 | COCO 標準類別，大目標 |
| cup | 小物件尋物 | 高 | 中 | COCO 標準類別，小目標挑戰 |
| bottle | 小物件尋物 | 高 | 中 | COCO 標準類別，小目標挑戰 |
| dog | 寵物互動 | 高 | 中 | COCO 標準類別，動態目標 |

> **風險等級說明**：
> - **低**：大目標、特徵明顯、COCO 預訓練效果穩定
> - **中**：中小目標、可能受遮擋或光影影響
> - **高**：非標準 COCO 類別或需額外 fine-tuning

#### P1 擴充類別（4-8類）- 4/13 前完成

| 類別 | 用途 | 展示價值 | 風險等級 | 備註 |
|------|------|:--------:|:--------:|------|
| sofa | 家具 | 中 | 低 | COCO 標準類別 |
| backpack | 物品 | 中 | 中 | COCO 標準類別 |
| remote | 小物件 | 中 | 高 | 小目標，可能需近距離辨識 |
| book | 物品 | 低 | 高 | 扁平物體，角度影響大 |
| laptop | 電子產品 | 中 | 中 | COCO 標準類別，反光表面 |
| toy | 玩具 | 中 | 高 | **非標準 COCO 類別**，需額外資料 |
| slipper | 鞋類 | 低 | 高 | **非標準 COCO 類別**，場景變異大 |

> **注意**：`toy`、`slipper` 等非標準 COCO 類別若要穩定辨識，可能需額外收集資料與 fine-tuning。

### 2.3 輸入輸出介面

#### 訂閱 Topic

| Topic | Message Type | 說明 |
|-------|--------------|------|
| `/camera/camera/color/image_raw` | sensor_msgs/Image | D435 RGB 影像 |
| `/camera/camera/depth/image_rect_raw` | sensor_msgs/Image | D435 深度圖 |
| `/camera/camera/camera_info` | sensor_msgs/CameraInfo | 相機參數 |

#### 發布 Topic

| Topic | Message Type | 說明 |
|-------|--------------|------|
| `/perception/object/detections` | vision_msgs/Detection2DArray | 2D 偵測結果 |
| `/perception/object/3d_detections` | vision_msgs/Detection3DArray | 3D 偵測結果（含深度）|
| `/perception/object/debug_image` | sensor_msgs/Image | 可視化（可關閉）|
| `/events/object_detected` | std_msgs/String (JSON) | 高層事件（見下方 schema）|

##### 事件 JSON Schema 草案

```json
{
  "event_type": "object_detected",
  "source": "object_detector",
  "timestamp": 1710000000.123,
  "frame_id": "camera_color_optical_frame",
  "payload": {
    "class_name": "cup",
    "class_id": 41,
    "confidence": 0.87,
    "bbox_xyxy": [120, 80, 220, 210],
    "center_3d": [0.62, -0.14, 1.08],
    "depth_valid": true,
    "track_id": 7
  }
}
```

> **v1.0 過渡方案**：使用 `std_msgs/String` 承載 JSON。若事件流開始穩定，後續應升級為自訂 `pawai_msgs/ObjectDetectedEvent`，避免 schema 漂移。

### 2.4 與現有 coco_detector 的關係

**重要**: 此替換應視為「**同介面重構**」而非「直接替換」。

- 保留現有 `coco_detector` package 名稱與 entry point
- 內部推理核心由 FasterRCNN 改為 YOLO26n
- **優先維持既有 ROS topic 與 `Detection2DArray` 對外介面不變**
- **bbox 幾何格式可沿用既有轉換邏輯**（同為 xyxy 格式）
- **類別標籤、confidence 分布與訊息欄位填法仍需回歸測試確認**
- **目標是讓多數下游節點無需修改**；若下游依賴舊版類別 ID 或閾值假設，可能仍需微調

---

## 3. 雲端端設計 (RTX 8000)

### 3.1 候選能力線

雲端端並非不能使用 YOLO26，而是應優先承擔本地不適合做的重型任務。以下為三條候選能力線，**4/13 前至少完成一條即可**。

| 候選線 | 模型 | 用途 | 記憶體需求 | 優先級 |
|--------|------|------|------------|:------:|
| **A 線** | YOLO26x | 高精度固定類別再確認 | ~10 GB | P1 |
| **B 線** | YOLOE-26l-seg | 開放詞彙 / prompt-based 分割 | ~15 GB | P2 |
| **C 線** | Qwen-VL | 視覺問答與語意描述 | ~20-40 GB | P2 |

> **4/13 目標**：至少完成一條雲端補強線，不要求三者同時整合。

### 3.2 任務分配

- **高精度再確認**: 本地低信心時送雲端二次確認
- **開放詞彙查詢**: 「那個紅色的東西是什麼？」
- **場景理解**: 複雜環境分析、數位孿生
- **離線分析**: 長期資料統計、模型訓練

### 3.3 輸入來源

- 低頻 RGB frame（從 Jetson 來）
- Cropped ROI（特定目標區域）
- 結構化 detection events

**注意**: 不收整條 D435 depth stream

---

## 4. D435 深度整合

### 4.1 本地 3D 定位流程

```
D435 RGB → YOLO26n 偵測 → 取得 bbox (2D)
                ↓
D435 Depth → 深度取樣策略 → 取得穩定深度值
                ↓
        計算 3D 座標 (x, y, z)
                ↓
        發布 /perception/object/3d_detections
```

#### 4.1.1 深度取樣策略（重要）

**不直接使用單一中心點深度值**，而是：

1. 於 bbox 中心附近採樣小區域（建議 5×5 或 9×9 像素）
2. 過濾無效值（0, NaN, 離群值）
3. 取中位數作為代表深度
4. 若有效像素不足（如 < 50%），標記 `depth_valid=false`

**失敗處理**：
- `depth_valid=false` 時，僅發布 2D bbox，不發布 3D 座標
- 下游模組應檢查此 flag，避免使用無效深度

### 4.2 深度使用限制

| 距離範圍 | 精度 | 用途 |
|----------|------|------|
| < 0.3m | 無效（盲区）| 機械設計規避 |
| 0.3-1.5m | 高 | 主要互動範圍 |
| 1.5-3m | 中 | 環境感知 |
| > 3m | 低 | 僅供參考 |

### 4.3 不上傳雲端的原因

1. **頻寬**: 848×480 depth @ 30fps ≈ 370 Mbps
2. **延遲**: 網路往返 50-200ms，即時性不足
3. **同步**: RGB-D 時間同步複雜
4. **穩定**: 網路抖動影響感知穩定性

### 4.4 時空對齊要求

#### 相機對齊
- 使用 **aligned depth to color** (`/camera/camera/aligned_depth_to_color/image_raw`)
- 或明確定義 RGB/Depth 對齊流程
- 3D 回推以 `camera_color_optical_frame` 為主 frame

#### 時間同步
- RGB、Depth、CameraInfo 建議使用 **approximate time synchronizer**
- 容忍時間差：< 33ms (1 frame @ 30fps)

#### TF / 外參
- 相機內參由 `/camera/camera_info` 提供
- D435 相對機器人體座標的外參應納入 **TF tree** 管理
- 發布 `camera_color_optical_frame` → `base_link` 的 transform

---

## 5. 實作時程

### 今天（Day 1）

- [ ] 備份 `coco_detector_node.py`
- [ ] 安裝 `pip3 install ultralytics`
- [ ] 下載 `yolo26n.pt`
- [ ] 建立新 branch `feature/yolo26-migration`

### 明天（Day 2）

- [ ] 修改模型載入邏輯（Ultralytics API）
- [ ] 調整推理後處理（轉換 Detection2DArray）
- [ ] 測試輸出格式相容性
- [ ] Jetson 實測 FPS

**✅ Day 2 驗收標準**：
- Jetson 可持續輸出 `/perception/object/detections`
- `/perception/object/debug_image` 能正確畫框
- 連跑 5 分鐘無 node crash

### 3/16 前

- [ ] 整合人臉辨識、語音功能測試
- [ ] 驗證 P0 類別（6類）穩定性
- [ ] 回歸測試（下游節點無痛接收）

**✅ 3/16 驗收標準**：
- P0 類別至少 4/6 類在近距離靜態場景可穩定辨識（confidence > 0.6）
- 延遲達成可接受 demo 水準（< 200ms）
- 與網站顯示串通一條 end-to-end 流程

### 4/13 前

- [ ] 擴充至 P1 類別
- [ ] 雲端 YOLO26x / YOLOE 整合
- [ ] 完整 Demo 場景測試

**✅ 4/13 驗收標準**：
- 完成至少 1 條「偵測 → 事件 → AI/網站展示」完整故事線
- 至少 1 個小物件（cup/bottle）demo 成功
- 雲端補強至少完成 1 條能力線（A/B/C 線擇一）

---

## 6. 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| **類別數差異** (80 vs 91) | 部分類別遺漏 | 確認 demo 物件在 COCO 80 類內 |
| **新相依性** (ultralytics) | 版本衝突 | Jetson 測試環境先行驗證 |
| **輸入解析度變更** (320→640) | 效能影響 | 可配置，必要時降回 320 |
| **實測效能不如預期** | 延遲過高 | 保留 FasterRCNN branch 備援 |
| **下游介面不相容** | 系統異常 | 完整回歸測試 |

---

## 7. 效能預估（待實測驗證）

> ⚠️ **以下為官方理論值，實際數值須以 Jetson + ROS2 pipeline 實測為準**

| 指標 | FasterRCNN (現有) | YOLO26n (目標) |
|------|-------------------|----------------|
| **模型大小** | ~19 MB | ~5 MB |
| **mAP (COCO)** | 22.8% | 40.1% |
| **輸入解析度** | 320×320 | 640×640 |
| **Jetson FPS** | 待測 | 待測（目標 >15）|
| **記憶體** | 待測 | 待測（預估省 30-50%）|

---

## 8. 相關文件

- [人臉辨識模組設計](../人臉辨識/README.md)
- [語音功能設計](../語音功能/jetson-MVP測試.md)
- [Jetson 快系統實作指南](../setup/hardware/Jetson%208GB%20快系統實作指南.md)

---

## 9. 參考資料

- [Ultralytics YOLO26 官方文件](https://docs.ultralytics.com/models/yolo26/)
- [YOLO26 vs FasterRCNN 技術比較](https://docs.ultralytics.com/compare/yolo26-vs-efficientdet/)
- [Jetson YOLO 部署指南](https://docs.ultralytics.com/guides/nvidia-jetson/)

---

## 10. 版本紀錄

| 版本 | 日期 | 修改內容 |
|------|------|----------|
| v1.1 | 2026-03-11 | 修正 3D message type、補充事件 schema、類別風險評估、深度取樣策略、時空對齊要求、驗收標準 |
| v1.0 | 2026-03-11 | 初版，定義本地/雲端分工與 YOLO26n 遷移計畫 |

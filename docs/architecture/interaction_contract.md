# ROS2 介面契約 v1.0

**文件定位**：PawAI 系統 ROS2 Topic/Action/Service 介面規格  
**適用範圍**：Layer 1-3 所有模組  
**版本**：v1.0（凍結）  
**凍結日期**：2026-03-09

---

## 1. 介面凍結規則

### 1.1 不可變更項目（3/9 後凍結）

以下項目已凍結，變更需經 System Architect 核准：

- ✅ Topic 名稱與路徑
- ✅ Message schema（欄位名稱、型別、順序）
- ✅ Action/Service 名稱
- ✅ 常數 enum 值（Skill ID、Event Type 等）

### 1.2 可調整項目（內部實作）

以下項目可在各模組內部調整：

- 🔄 演算法實作細節
- 🔄 閾值與參數預設值
- 🔄 內部資料結構
- 🔄 發布頻率（在不影響外部行為前提下）

---

## 2. Topic 介面

### 2.1 Face Perception Topics

#### `/state/perception/face`

**說明**：人臉追蹤狀態（持續發布）  
**發布頻率**：10 Hz  
**QoS**：Reliable, depth=10

**Message Type**：`std_msgs/String` (JSON)

**Schema**：
```json
{
  "stamp": {
    "type": "float",
    "unit": "seconds (Unix timestamp)",
    "description": "訊息時間戳"
  },
  "count": {
    "type": "int",
    "description": "當前追蹤的人臉數量"
  },
  "tracks": {
    "type": "array",
    "items": {
      "track_id": {
        "type": "int",
        "description": "Session-level 追蹤 ID"
      },
      "bbox": {
        "type": "array[4]",
        "items": "int",
        "description": "邊界框 [x1, y1, x2, y2]"
      },
      "confidence": {
        "type": "float",
        "range": "[0.0, 1.0]",
        "description": "偵測置信度"
      },
      "distance_m": {
        "type": "float | null",
        "unit": "meters",
        "description": "深度距離，無深度時為 null"
      },
      "person_name": {
        "type": "string | undefined",
        "description": "識別姓名（僅在啟用 SFace 時）"
      },
      "person_confidence": {
        "type": "float | undefined",
        "range": "[0.0, 1.0]",
        "description": "識別置信度"
      }
    }
  }
}
```

**範例**：
```json
{
  "stamp": 1709823456.789,
  "count": 2,
  "tracks": [
    {
      "track_id": 1,
      "bbox": [100, 150, 200, 280],
      "confidence": 0.95,
      "distance_m": 1.25,
      "person_name": "張先生",
      "person_confidence": 0.87
    },
    {
      "track_id": 2,
      "bbox": [300, 180, 380, 300],
      "confidence": 0.87,
      "distance_m": 2.1
    }
  ]
}
```

---

#### `/event/face_detected`

**說明**：人臉偵測事件（觸發式發布）  
**發布時機**：
- 新的人臉進入畫面
- 間隔 `event_interval_sec` 秒後再次發布

**Message Type**：`std_msgs/String` (JSON)

**Schema**：
```json
{
  "stamp": {
    "type": "float",
    "unit": "seconds"
  },
  "event_type": {
    "type": "string",
    "enum": ["detected"],
    "description": "事件類型"
  },
  "track": {
    "type": "object",
    "properties": {
      "track_id": "int",
      "bbox": "array[4]",
      "confidence": "float",
      "distance_m": "float | null"
    }
  }
}
```

**範例**：
```json
{
  "stamp": 1709823456.789,
  "event_type": "detected",
  "track": {
    "track_id": 1,
    "bbox": [100, 150, 200, 280],
    "confidence": 0.95,
    "distance_m": 1.25
  }
}
```

---

### 2.2 Control Topics

#### `/webrtc_req`

**說明**：Skill 執行請求（由 face_interaction 發布）  
**Message Type**：`go2_interfaces/WebRtcReq`

**Schema**：
```
int64   id          # Message ID，0 表示自動分配
string  topic       # WebRTC topic，固定 "rt/api/sport/request"
int64   api_id      # Skill command ID
string  parameter   # JSON 參數或 command ID 字串
uint8   priority    # 0=normal, 1=priority
```

**範例**（Hello skill）：
```python
req = WebRtcReq()
req.id = 0
req.topic = "rt/api/sport/request"
req.api_id = 1016        # Hello
req.parameter = "1016"   # Command ID as string
req.priority = 0
```

---

## 3. Skill 命令對照表

### 3.1 P0 安全動作

| Skill 名稱 | api_id | 參數 | 說明 | 安全等級 |
|-----------|--------|------|------|----------|
| `Hello` | 1016 | `"1016"` | 揮手打招呼 | 🟢 安全 |
| `BalanceStand` | 1002 | `"1002"` | 平衡站立 | 🟢 安全 |
| `Sit` | 1009 | `"1009"` | 坐下 | 🟢 安全 |
| `RiseSit` | 1010 | `"1010"` | 起身坐下 | 🟢 安全 |
| `StopMove` | 1003 | `"1003"` | 停止移動 | 🟢 安全 |

### 3.2 P1 展示動作

| Skill 名稱 | api_id | 說明 | 安全等級 |
|-----------|--------|------|----------|
| `Stretch` | 1017 | 伸展 | 🟡 中等 |
| `Content` | 1020 | 開心/滿足 | 🟢 安全 |
| `FingerHeart` | 1036 | 比心 | 🟢 安全 |
| `WiggleHips` | 1033 | 搖屁股 | 🟢 安全 |

### 3.3 🔴 高風險動作（避免使用）

| Skill 名稱 | api_id | 說明 | 風險 |
|-----------|--------|------|------|
| `FrontFlip` | 1030 | 前空翻 | 危險 |
| `FrontJump` | 1031 | 前跳 | 危險 |
| `Handstand` | 1301 | 倒立 | 不穩定 |

**完整命令列表**：參見 `go2_robot_sdk/go2_robot_sdk/domain/constants/robot_commands.py`

---

## 4. 參數規格

### 4.1 FacePerceptionNode 參數

| 參數名 | 型別 | 預設值 | 範圍 | 說明 |
|--------|------|--------|------|------|
| `color_topic` | string | `/camera/camera/color/image_raw` | - | RGB 影像來源 |
| `depth_topic` | string | `/camera/camera/aligned_depth_to_color/image_raw` | - | 深度影像來源 |
| `yunet_model` | string | `/home/jetson/face_models/face_detection_yunet_2023mar.onnx` | - | YuNet 模型路徑 |
| `sface_model` | string | `/home/jetson/face_models/face_recognition_sface_2021dec.onnx` | - | SFace 模型路徑 |
| `face_db_model` | string | `/home/jetson/face_db/model_sface.pkl` | - | 人臉資料庫路徑 |
| `enable_identity` | bool | `false` | - | 啟用身分識別 |
| `identity_threshold` | float | `0.35` | [0.0, 1.0] | SFace 識別閾值 |
| `event_interval_sec` | float | `2.0` | [0.5, 10.0] | 事件最小間隔 |
| `tracker_iou_threshold` | float | `0.3` | [0.1, 0.9] | IOU 匹配閾值 |
| `tracker_max_lost` | int | `10` | [1, 50] | 最大遺失幀數 |

### 4.2 FaceInteractionNode 參數

| 參數名 | 型別 | 預設值 | 範圍 | 說明 |
|--------|------|--------|------|------|
| `face_event_topic` | string | `/event/face_detected` | - | 事件訂閱 topic |
| `webrtc_publish_topic` | string | `/webrtc_req` | - | Skill 發布 topic |
| `webrtc_topic_name` | string | `rt/api/sport/request` | - | WebRTC topic |
| `action_api_id` | int | `1016` | 有效 skill ID | Hello skill ID |
| `action_parameter` | string | `"1016"` | - | Command ID 字串 |
| `interaction_cooldown_sec` | float | `5.0` | [0.0, 60.0] | 互動冷卻時間 |

---

## 5. QoS 規格

### 5.1 State Topics

| Topic | Reliability | Durability | Depth | 說明 |
|-------|-------------|------------|-------|------|
| `/state/perception/face` | Reliable | Volatile | 10 | 需確保接收 |
| `/state/interaction/speech` | Reliable | Volatile | 10 | 需確保接收 |
| `/state/executive/brain` | Reliable | Volatile | 10 | 需確保接收 |

### 5.2 Event Topics

| Topic | Reliability | Durability | Depth | 說明 |
|-------|-------------|------------|-------|------|
| `/event/face_detected` | Reliable | Volatile | 10 | 事件不可遺失 |
| `/event/speech_intent` | Reliable | Volatile | 10 | 事件不可遺失 |

### 5.3 Control Topics

| Topic | Reliability | Durability | Depth | 說明 |
|-------|-------------|------------|-------|------|
| `/webrtc_req` | Reliable | Volatile | 10 | 命令需確保送達 |
| `/cmd_vel` | Reliable | Volatile | 10 | 運動命令 |

---

## 6. 錯誤處理

### 6.1 無效訊息處理

接收方應該：
1. 驗證 JSON schema
2. 無效訊息記錄警告但不中斷流程
3. 繼續處理下一筆訊息

```python
try:
    payload = json.loads(msg.data)
except json.JSONDecodeError:
    self.get_logger().warning("Ignore invalid JSON")
    return

# 驗證必要欄位
if "stamp" not in payload or "track" not in payload:
    self.get_logger().warning("Missing required fields")
    return
```

### 6.2 超時處理

| 情境 | 超時時間 | 行為 |
|------|----------|------|
| Skill 執行 | 10 秒 | 記錄錯誤，不回應 |
| State 更新 | 2 秒 | 標記為 stale |
| Event 處理 | 1 秒 | 丟棄過期事件 |

---

## 7. 版本歷史

| 版本 | 日期 | 變更內容 | 作者 |
|------|------|----------|------|
| v1.0 | 2026-03-09 | 介面凍結 | System Architect |

---

## 8. 相關文件

- [mission/README.md](../mission/README.md) - 專案總覽
- [face_perception.md](./face_perception.md) - 人臉模組架構
- [data_flow.md](./data_flow.md) - 資料流說明

---

*維護者：System Architect*  
*狀態：v1.0 凍結*

# 姿勢辨識模型選型調查

> 最後更新：2026-03-21

## 目標效果
- 辨識 standing / sitting / crouching / fallen 四種姿勢
- 4/13 Demo 目標：成功率 ≥ 70%，fallen 偵測延遲 < 2s
- 與 face（CPU）+ STT（CUDA on-demand）共存

## 候選模型

| # | 模型 | 框架 | 輸出 | Installability | Runtime viability | GPU 路徑 | 實測性能 | 納入原因 | 預期淘汰條件 |
|---|------|------|------|:-:|:-:|:-:|---|---|---|
| 1 | **RTMPose lightweight** | rtmlib + onnxruntime-gpu | 133kp wholebody | verified | verified | cuda | **17.6 FPS** (L1) | 最快 GPU 方案，一次推理含 pose+gesture | — |
| 2 | RTMPose balanced | rtmlib + onnxruntime-gpu | 133kp wholebody | verified | verified | cuda | 9.3 FPS (L1) | 精度較高但 GPU 更重 | FPS 不足時降級為 lightweight |
| 3 | MediaPipe Pose | mediapipe 0.10.18 | 33kp body | verified | verified | cpu_only | **13.5 FPS** (L1) | CPU-only，不佔 GPU | 精度不足 or CPU 競爭嚴重 |

### 排除清單

| 模型 | 排除原因 | 證據等級 |
|------|---------|:-------:|
| MediaPipe Pose (舊版) | 先前記為「ARM64 無 wheel」→ 0.10.18 已修正，移出排除 | local_failed → 已修正 |
| YOLO11n-pose | 待測 P2 | — |
| trt_pose | 老專案停更，JetPack 6 相容性未知 | community_only |

## Benchmark 結果（3/21 Jetson 實測）

### L1 單模型基線
| 模型 | FPS | Latency | GPU | Gate |
|------|:---:|:-------:|:---:|:----:|
| **rtmpose_lightweight** | **17.6** | 57ms | CUDA ~90% | PASS |
| mediapipe_pose | 13.5 | 74ms | CPU 0% | PASS |
| rtmpose_balanced | 9.3 | 107ms | CUDA ~95% | PASS |

### L2 共存
| Target | Companion | FPS | vs L1 | 備註 |
|--------|-----------|:---:|:-----:|------|
| rtmpose_lw | yunet@8Hz (CPU) | 16.5 | -6% | CPU+GPU 分離，最佳 |
| rtmpose_lw | scrfd@8Hz (GPU) | 15.8 | -10% | GPU 輕微競爭 |
| rtmpose_lw | whisper_small (GPU) | 14.1 | -20% | GPU 顯著競爭但仍可用 |
| rtmpose_bal | yunet@8Hz (CPU) | 9.1 | -2% | — |

## 已知環境問題
- onnxruntime CPU 版曾覆蓋 GPU 版 → 每次安裝 Python 套件後需確認 CUDA EP 可用
- numpy 必須 < 2（onnxruntime-gpu 1.23.0）
- mediapipe 0.10.18 現在有 ARM64 wheel（推翻先前「不可安裝」結論）

## 決策（3/21 回填）
| 模型 | Decision Code | Placement | 依據 |
|------|:---:|---|---|
| **RTMPose lightweight** | **JETSON_LOCAL** | jetson（主線） | 17.6 FPS，一次推理出 pose+gesture，共存降幅可控 |
| RTMPose balanced | JETSON_LOCAL | jetson（精度優先時） | 9.3 FPS，GPU 更重但精度更高 |
| MediaPipe Pose | **HYBRID** | jetson（CPU fallback） | 13.5 FPS CPU-only，GPU 滿載時的備援 |

#!/usr/bin/env python3
"""L2 benchmark: pose lightweight with whisper_small companion.
Tests GPU contention between two CUDA models.
"""
import sys
import time
import threading
import logging

sys.path.insert(0, ".")

import numpy as np

from benchmarks.adapters.stt_whisper import STTWhisperAdapter
from benchmarks.adapters.pose_rtmpose import PoseRTMPoseAdapter
from benchmarks.core.runner import BenchmarkRunner

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("bench_l2_pose_whisper")

TEST_IMG = "benchmarks/test_inputs/images/synthetic_640x480.jpg"
COMPANION_META = [{"name": "whisper_small", "rate_hz": "on_demand", "mode": "headless"}]


def run_l2():
    # Load whisper companion (occupies GPU memory, periodic inference)
    whisper = STTWhisperAdapter()
    whisper.load({"model_size": "small", "device": "cuda", "compute_type": "float16"})

    # Synthetic 3-sec audio for whisper
    audio = np.random.randn(3 * 16000).astype(np.float32) * 0.01

    # Warmup whisper
    for _ in range(3):
        whisper.infer(audio)

    # Background whisper thread: inference every 5s (simulates on-demand ASR)
    stop = threading.Event()
    def whisper_loop():
        while not stop.is_set():
            whisper.infer(audio)
            time.sleep(5.0)

    t = threading.Thread(target=whisper_loop, daemon=True)
    t.start()
    logger.info("Whisper companion running (on_demand, ~0.2Hz)")

    # Benchmark pose lightweight with whisper companion
    runner = BenchmarkRunner(results_dir="benchmarks/results/raw")
    config = {
        "name": "rtmpose_lightweight",
        "params": {"mode": "lightweight", "device": "cuda", "backend": "onnxruntime"},
        "benchmark": {"n_warmup": 10, "n_measure": 50,
                       "input_source": "benchmarks/test_inputs/images/"},
        "feasibility_gate": {"min_fps": 2.0, "must_not_crash": True},
    }
    result = runner.run(
        adapter=PoseRTMPoseAdapter(),
        config=config,
        task="pose_estimation",
        level=2,
        mode="headless",
        concurrent_models=COMPANION_META,
        test_input_ref=TEST_IMG,
    )
    fps = result["feasibility"]["fps_mean"]
    gate = result["feasibility"]["gate_pass"]

    stop.set()
    t.join(timeout=10)
    whisper.cleanup()

    print(f"\n{'='*60}")
    print(f"L2: pose_lightweight + whisper_small (both CUDA)")
    print(f"  FPS: {fps:.1f}  gate={'PASS' if gate else 'FAIL'}")
    print(f"  Compare: L1=17.6, L2+YuNet(CPU)=16.5, L2+SCRFD(GPU)=15.8")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_l2()

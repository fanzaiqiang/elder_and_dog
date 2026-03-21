"""MediaPipe Pose benchmark adapter.
CPU-only (TFLite XNNPACK). For Jetson ARM64 feasibility comparison.
"""
import logging
from typing import Any, Optional

import cv2
import numpy as np

from benchmarks.adapters.base import BenchAdapter

logger = logging.getLogger(__name__)


class PoseMediaPipeAdapter(BenchAdapter):
    """Benchmark adapter for MediaPipe Pose."""

    def __init__(self):
        self._pose = None

    def load(self, config: dict) -> None:
        try:
            import mediapipe as mp
        except ImportError:
            raise ImportError("mediapipe not installed. Run: pip3 install mediapipe")

        self._mp = mp
        complexity = config.get("model_complexity", 1)
        min_conf = config.get("min_detection_confidence", 0.5)
        static_mode = config.get("static_image_mode", True)

        self._pose = mp.solutions.pose.Pose(
            static_image_mode=static_mode,
            model_complexity=complexity,
            min_detection_confidence=min_conf,
        )
        logger.info(f"MediaPipe Pose loaded: complexity={complexity}, "
                     f"static={static_mode}, min_conf={min_conf}")

    def prepare_input(self, input_ref: str) -> np.ndarray:
        img = cv2.imread(input_ref)
        if img is None:
            raise FileNotFoundError(f"Cannot read image: {input_ref}")
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    def infer(self, input_data: np.ndarray) -> dict:
        if self._pose is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        result = self._pose.process(input_data)
        has_pose = result.pose_landmarks is not None
        n_landmarks = 33 if has_pose else 0

        return {
            "has_pose": has_pose,
            "n_landmarks": n_landmarks,
        }

    def cleanup(self) -> None:
        if self._pose is not None:
            self._pose.close()
            self._pose = None

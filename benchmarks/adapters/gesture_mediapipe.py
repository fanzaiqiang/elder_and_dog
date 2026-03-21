"""MediaPipe Hands benchmark adapter.
CPU-only (TFLite XNNPACK). For Jetson ARM64 feasibility comparison.
"""
import logging
from typing import Any, Optional

import cv2
import numpy as np

from benchmarks.adapters.base import BenchAdapter

logger = logging.getLogger(__name__)


class GestureMediaPipeAdapter(BenchAdapter):
    """Benchmark adapter for MediaPipe Hands."""

    def __init__(self):
        self._hands = None

    def load(self, config: dict) -> None:
        try:
            import mediapipe as mp
        except ImportError:
            raise ImportError("mediapipe not installed. Run: pip3 install mediapipe")

        self._mp = mp
        max_hands = config.get("max_num_hands", 2)
        min_conf = config.get("min_detection_confidence", 0.5)
        static_mode = config.get("static_image_mode", True)

        self._hands = mp.solutions.hands.Hands(
            static_image_mode=static_mode,
            max_num_hands=max_hands,
            min_detection_confidence=min_conf,
        )
        logger.info(f"MediaPipe Hands loaded: max_hands={max_hands}, "
                     f"static={static_mode}, min_conf={min_conf}")

    def prepare_input(self, input_ref: str) -> np.ndarray:
        img = cv2.imread(input_ref)
        if img is None:
            raise FileNotFoundError(f"Cannot read image: {input_ref}")
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    def infer(self, input_data: np.ndarray) -> dict:
        if self._hands is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        result = self._hands.process(input_data)
        n_hands = len(result.multi_hand_landmarks) if result.multi_hand_landmarks else 0

        return {
            "n_hands": n_hands,
            "has_landmarks": result.multi_hand_landmarks is not None,
        }

    def cleanup(self) -> None:
        if self._hands is not None:
            self._hands.close()
            self._hands = None

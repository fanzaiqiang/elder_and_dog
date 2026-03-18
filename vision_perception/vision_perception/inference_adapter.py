"""Abstract inference adapter interface.

Defines InferenceResult dataclass and InferenceAdapter ABC.
Phase 1: MockInference. Phase 2: RTMPoseInference.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class InferenceResult:
    """Standardized keypoint output from any inference backend."""
    body_kps: np.ndarray           # (17, 2) COCO body
    body_scores: np.ndarray        # (17,)
    left_hand_kps: np.ndarray      # (21, 2) COCO-WholeBody hand
    left_hand_scores: np.ndarray   # (21,)
    right_hand_kps: np.ndarray     # (21, 2)
    right_hand_scores: np.ndarray  # (21,)


class InferenceAdapter(ABC):
    @abstractmethod
    def infer(self, image_bgr: np.ndarray | None) -> InferenceResult:
        """Run inference on an image.

        Args:
            image_bgr: BGR image, or None in use_camera=false mode.
                Mock implementations accept None and return scenario keypoints.
                Real implementations must raise ValueError if image_bgr is None.
        """

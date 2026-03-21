"""Whisper STT benchmark adapter.
Uses faster-whisper (CTranslate2) for benchmarking ASR inference.
Reference: speech_processor/speech_processor/stt_intent_node.py
"""
import logging
import os
import time
from typing import Any, Optional

import numpy as np

from benchmarks.adapters.base import BenchAdapter

logger = logging.getLogger(__name__)


class STTWhisperAdapter(BenchAdapter):
    """Benchmark adapter for Whisper via faster-whisper."""

    def __init__(self):
        self._model = None
        self._model_size = "small"

    def load(self, config: dict) -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ImportError(
                "faster-whisper not installed. "
                "Run: pip3 install faster-whisper"
            )

        self._model_size = config.get("model_size", "small")
        device = config.get("device", "cuda")
        compute_type = config.get("compute_type", "float16")

        logger.info(f"Loading Whisper {self._model_size} "
                     f"(device={device}, compute_type={compute_type})...")
        t0 = time.time()
        self._model = WhisperModel(
            self._model_size,
            device=device,
            compute_type=compute_type,
        )
        elapsed = time.time() - t0
        logger.info(f"Whisper {self._model_size} loaded in {elapsed:.1f}s")

    def prepare_input(self, input_ref: str) -> np.ndarray:
        """Load audio file or generate synthetic 3-second audio."""
        if os.path.isfile(input_ref) and input_ref.endswith((".wav", ".mp3")):
            # Load real audio file
            try:
                import soundfile as sf
                audio, sr = sf.read(input_ref, dtype="float32")
                if sr != 16000:
                    # Resample to 16kHz
                    from scipy.signal import resample
                    audio = resample(audio, int(len(audio) * 16000 / sr))
                return audio
            except ImportError:
                pass

        # Fallback: synthetic 3-second silence + noise (simulates real input length)
        duration_sec = 3.0
        sample_rate = 16000
        audio = np.random.randn(int(duration_sec * sample_rate)).astype(np.float32) * 0.01
        return audio

    def infer(self, input_data: np.ndarray) -> dict:
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        segments, info = self._model.transcribe(
            input_data,
            language="zh",
            beam_size=1,
            vad_filter=False,
        )
        # Consume the generator to force actual inference
        text_parts = []
        for seg in segments:
            text_parts.append(seg.text)

        text = "".join(text_parts)
        duration_sec = len(input_data) / 16000
        return {
            "text": text,
            "language": info.language,
            "duration_sec": round(duration_sec, 2),
            "model_size": self._model_size,
        }

    def cleanup(self) -> None:
        self._model = None

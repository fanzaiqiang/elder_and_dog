"""
Custom AudioStreamTrack for TTS playback via WebRTC audio track.

Accepts WAV bytes, resamples to 48kHz mono, and streams via RTP to Go2.
When no audio is queued, sends silence to keep the RTP stream alive.

This is the replacement for the DataChannel Megaphone API (4001/4003/4002)
which stopped working on Go2 firmware v1.1.7+.
"""

import asyncio
import fractions
import io
import logging
import wave

import av
import numpy as np
from aiortc import MediaStreamTrack
from aiortc.mediastreams import MediaStreamError
from av import AudioFrame

logger = logging.getLogger(__name__)

AUDIO_PTIME = 0.02  # 20ms per frame — aiortc standard


class TtsAudioTrack(MediaStreamTrack):
    """
    Custom audio track: reads PCM from an asyncio.Queue,
    sends silence when queue is empty.

    Compatible with aiortc 1.3.0+ (uses MediaStreamTrack base).

    Usage:
        track = TtsAudioTrack()
        pc.addTrack(track)  # before SDP offer

        # From any thread (e.g. ROS2 callback):
        track.enqueue_audio_threadsafe(wav_bytes, loop)
    """

    kind = "audio"

    def __init__(self, sample_rate: int = 48000):
        super().__init__()
        self._sample_rate = sample_rate
        self._samples_per_frame = int(AUDIO_PTIME * sample_rate)  # 960 @ 48kHz

        # PCM buffer queue: stores numpy int16 arrays
        self._queue: asyncio.Queue = asyncio.Queue()

        # Current playback buffer and offset
        self._current_buffer = None
        self._buffer_offset: int = 0

        # PTS counter
        self._pts: int = 0

        logger.info(
            "TtsAudioTrack initialized: %dHz, %d samples/frame",
            sample_rate, self._samples_per_frame,
        )

    async def enqueue_audio(self, wav_bytes: bytes) -> None:
        """
        Parse WAV bytes, resample to 48kHz mono s16, and enqueue for playback.
        Can be called from any thread via enqueue_audio_threadsafe().
        """
        try:
            container = av.open(io.BytesIO(wav_bytes), format="wav")
            resampler = av.AudioResampler(
                format="s16",
                layout="mono",
                rate=self._sample_rate,
            )

            all_samples = []
            for frame in container.decode(audio=0):
                resampled = resampler.resample(frame)
                for rf in resampled:
                    arr = rf.to_ndarray().flatten().astype(np.int16)
                    all_samples.append(arr)

            # Flush resampler
            resampled = resampler.resample(None)
            for rf in resampled:
                arr = rf.to_ndarray().flatten().astype(np.int16)
                all_samples.append(arr)

            container.close()

            if all_samples:
                pcm = np.concatenate(all_samples)
                await self._queue.put(pcm)
                duration_s = len(pcm) / self._sample_rate
                logger.info(
                    "[TTS TRACK] Enqueued %.1fs audio (%d samples)",
                    duration_s, len(pcm),
                )
            else:
                logger.warning("[TTS TRACK] No audio samples decoded from WAV")

        except Exception as e:
            logger.error("[TTS TRACK] Failed to enqueue audio: %s", e)

    def enqueue_audio_threadsafe(
        self, wav_bytes: bytes, loop: asyncio.AbstractEventLoop
    ) -> None:
        """
        Thread-safe entry point for ROS2 callbacks.
        Schedules enqueue_audio() on the asyncio event loop.
        """
        asyncio.run_coroutine_threadsafe(self.enqueue_audio(wav_bytes), loop)

    async def recv(self) -> AudioFrame:
        """
        Called by aiortc every 20ms to get the next audio frame.
        Returns PCM data if available, silence otherwise.
        """
        if self.readyState != "live":
            raise MediaStreamError

        samples = self._samples_per_frame
        output = np.zeros(samples, dtype=np.int16)
        filled = 0

        while filled < samples:
            if (
                self._current_buffer is None
                or self._buffer_offset >= len(self._current_buffer)
            ):
                try:
                    self._current_buffer = self._queue.get_nowait()
                    self._buffer_offset = 0
                except asyncio.QueueEmpty:
                    break

            remaining = len(self._current_buffer) - self._buffer_offset
            needed = samples - filled
            to_copy = min(remaining, needed)

            output[filled : filled + to_copy] = self._current_buffer[
                self._buffer_offset : self._buffer_offset + to_copy
            ]

            self._buffer_offset += to_copy
            filled += to_copy

        frame = AudioFrame.from_ndarray(
            output.reshape(1, -1), format="s16", layout="mono"
        )
        frame.sample_rate = self._sample_rate
        frame.pts = self._pts
        frame.time_base = fractions.Fraction(1, self._sample_rate)

        self._pts += samples

        return frame

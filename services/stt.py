from __future__ import annotations

import io
import logging
import os
import wave

import numpy as np
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

_model: WhisperModel | None = None


def init_stt() -> None:
    """Load the Whisper model into memory. Call once during app startup."""
    global _model
    if _model is not None:
        return

    model_size = os.getenv("WHISPER_MODEL_SIZE", "tiny")
    device = os.getenv("WHISPER_DEVICE", "cpu")
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

    logger.info(
        "Loading faster-whisper model size=%s device=%s compute_type=%s",
        model_size,
        device,
        compute_type,
    )
    _model = WhisperModel(model_size, device=device, compute_type=compute_type)
    logger.info("STT model ready")


def transcribe(audio_bytes: bytes) -> str:
    """
    Transcribe 16 kHz mono PCM WAV bytes to text.

    Raises RuntimeError if the model was not initialized.
    Raises ValueError if the WAV format is not 16 kHz mono PCM.
    """
    global _model
    if _model is None:
        raise RuntimeError("STT model not loaded; call init_stt() at startup")

    samples = _pcm_bytes_to_float32(audio_bytes)
    segments, _info = _model.transcribe(
        samples,
        task="translate",
        vad_filter=False,
    )
    return "".join(segment.text for segment in segments).strip()


def _pcm_bytes_to_float32(data: bytes) -> np.ndarray:
    samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
    samples /= 32768.0
    return samples

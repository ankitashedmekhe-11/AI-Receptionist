"""
STT service — uses Groq Whisper API for fast cloud transcription.

Groq runs whisper-large-v3-turbo on their hardware in under 1 second.
Free tier: 7,200 minutes of audio per month.
Get a free API key at: https://console.groq.com
"""
from __future__ import annotations

import io
import logging
import os
import wave

logger = logging.getLogger(__name__)

_client = None


def init_stt() -> None:
    """Initialize Groq client. Call once during app startup."""
    global _client
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning(
            "GROQ_API_KEY not set — STT will fail at runtime. "
            "Get a free key at https://console.groq.com"
        )
        return
    from groq import Groq
    _client = Groq(api_key=api_key)
    logger.info("STT ready: Groq Whisper API (whisper-large-v3-turbo)")


def transcribe(audio_bytes: bytes) -> str:
    """
    Transcribe 16 kHz mono PCM bytes to text via Groq Whisper API.

    Raises RuntimeError if client not initialized.
    Returns empty string if audio is too short / silent.
    """
    global _client
    if _client is None:
        raise RuntimeError(
            "STT not initialized. Set GROQ_API_KEY env variable and restart."
        )

    if not audio_bytes or len(audio_bytes) < 3200:
        # Less than 0.1 seconds of audio — skip
        return ""

    # Wrap raw PCM bytes in a WAV container so Groq can decode it
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(1)       # mono
        wf.setsampwidth(2)       # 16-bit PCM
        wf.setframerate(16000)   # 16 kHz
        wf.writeframes(audio_bytes)
    wav_buffer.seek(0)

    transcription = _client.audio.transcriptions.create(
        file=("audio.wav", wav_buffer, "audio/wav"),
        model="whisper-large-v3-turbo",
        language="en",
    )
    return transcription.text.strip()

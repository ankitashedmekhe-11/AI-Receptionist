"""
TTS service — uses Groq PlayAI TTS for reliable, fast, production-grade voice synthesis.

Groq runs PlayAI Dialog models on their LPU hardware.
Same GROQ_API_KEY used for STT (Whisper) — no extra credentials needed.
Docs: https://console.groq.com/docs/text-speech
"""
from __future__ import annotations

import asyncio
import logging
import os

logger = logging.getLogger(__name__)

# PlayAI voices available on Groq.
# "Arista-PlayAI" is a clear, professional female voice — ideal for a receptionist.
# Other options: "Fritz-PlayAI" (male), "Celeste-PlayAI", "Atlas-PlayAI", etc.
DEFAULT_VOICE = "Arista-PlayAI"
DEFAULT_MODEL = "playai-tts"

_client = None


def init_tts() -> None:
    """Initialize Groq client for TTS. Call once during app startup."""
    global _client
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning(
            "GROQ_API_KEY not set — TTS will fail at runtime. "
            "Get a free key at https://console.groq.com"
        )
        return
    from groq import Groq
    _client = Groq(api_key=api_key)
    logger.info("TTS engine: Groq PlayAI (%s / %s)", DEFAULT_MODEL, DEFAULT_VOICE)


def synthesize_text(text: str, voice: str = DEFAULT_VOICE) -> bytes:
    """
    Synthesize text to WAV audio bytes via Groq PlayAI TTS.

    Returns raw WAV bytes ready to stream to the client.
    Raises RuntimeError if client not initialized or synthesis fails.
    """
    global _client
    if _client is None:
        # Lazy init attempt (e.g. during local dev without explicit init call)
        init_tts()
    if _client is None:
        raise RuntimeError(
            "TTS not initialized. Set GROQ_API_KEY env variable and restart."
        )

    if not text or not text.strip():
        raise ValueError("No text provided for speech synthesis.")

    try:
        response = _client.audio.speech.create(
            model=DEFAULT_MODEL,
            voice=voice,
            input=text,
            response_format="wav",
        )
        # The Groq SDK returns a binary response — read all bytes
        audio_bytes = response.read()
        if not audio_bytes:
            raise RuntimeError("Groq TTS returned empty audio.")
        return audio_bytes
    except Exception as exc:
        logger.error("Groq PlayAI TTS failed: %s", exc)
        raise RuntimeError(f"TTS synthesis failed: {exc}") from exc


async def synthesize_text_async(text: str, voice: str = DEFAULT_VOICE) -> bytes:
    """
    Async wrapper for synthesize_text — runs the blocking Groq SDK call
    in a thread pool so it doesn't block the FastAPI event loop.
    """
    return await asyncio.to_thread(synthesize_text, text, voice)

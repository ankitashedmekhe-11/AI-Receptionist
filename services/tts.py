"""
TTS service — uses Deepgram Aura TTS for stable, production-grade voice synthesis.

Deepgram Aura is purpose-built for real-time voice AI. No model decommissioning drama.
Free tier: $200 in credits on signup (https://console.deepgram.com)
Voice: aura-asteria-en — warm, clear, professional female voice.
Docs: https://developers.deepgram.com/docs/tts-rest

Set DEEPGRAM_API_KEY in your environment / Render dashboard.
"""
from __future__ import annotations

import asyncio
import logging
import os

import httpx

logger = logging.getLogger(__name__)

DEEPGRAM_TTS_URL = "https://api.deepgram.com/v1/speak"

# Aura voices (English): aura-asteria-en, aura-luna-en, aura-stella-en,
#                        aura-athena-en, aura-hera-en, aura-orion-en,
#                        aura-arcas-en, aura-perseus-en, aura-angus-en,
#                        aura-orpheus-en, aura-helios-en, aura-zeus-en
DEFAULT_MODEL = "aura-asteria-en"   # Warm, professional female — ideal for receptionist


def _get_api_key() -> str:
    key = os.getenv("DEEPGRAM_API_KEY")
    if not key:
        raise RuntimeError(
            "DEEPGRAM_API_KEY not set. "
            "Sign up free at https://console.deepgram.com and add the key to your environment."
        )
    return key


def init_tts() -> None:
    """Validate that DEEPGRAM_API_KEY is present at startup."""
    key = os.getenv("DEEPGRAM_API_KEY")
    if not key:
        logger.warning(
            "DEEPGRAM_API_KEY not set — TTS will fail at runtime. "
            "Get $200 free at https://console.deepgram.com"
        )
    else:
        logger.info("TTS engine: Deepgram Aura (%s)", DEFAULT_MODEL)


def synthesize_text(text: str, model: str = DEFAULT_MODEL) -> bytes:
    """
    Synthesize text to MP3 audio bytes via Deepgram Aura REST API.

    Returns raw MP3 bytes ready to stream over WebSocket.
    Raises RuntimeError on failure.
    """
    if not text or not text.strip():
        raise ValueError("No text provided for speech synthesis.")

    api_key = _get_api_key()

    try:
        response = httpx.post(
            f"{DEEPGRAM_TTS_URL}?model={model}",
            headers={
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json",
            },
            json={"text": text},
            timeout=30.0,
        )
        response.raise_for_status()
        audio_bytes = response.content
        if not audio_bytes:
            raise RuntimeError("Deepgram TTS returned empty audio.")
        return audio_bytes
    except httpx.HTTPStatusError as exc:
        logger.error("Deepgram TTS HTTP error %s: %s", exc.response.status_code, exc.response.text)
        raise RuntimeError(f"TTS synthesis failed: {exc.response.status_code} {exc.response.text}") from exc
    except Exception as exc:
        logger.error("Deepgram TTS failed: %s", exc)
        raise RuntimeError(f"TTS synthesis failed: {exc}") from exc


async def synthesize_text_async(text: str, model: str = DEFAULT_MODEL) -> bytes:
    """
    Async wrapper — runs blocking Deepgram HTTP call in a thread pool
    so it doesn't block the FastAPI event loop.
    """
    return await asyncio.to_thread(synthesize_text, text, model)

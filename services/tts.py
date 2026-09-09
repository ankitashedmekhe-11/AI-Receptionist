"""
TTS service — uses edge-tts for realistic, humanized voices.
Returns raw MP3 audio bytes.
"""
from __future__ import annotations

import logging
import edge_tts

logger = logging.getLogger(__name__)

# A good humanized female voice
DEFAULT_VOICE = "en-US-AriaNeural"

async def synthesize_text_async(text: str, voice: str = DEFAULT_VOICE) -> bytes:
    if not text:
        raise ValueError("No text provided for speech synthesis.")

    try:
        communicate = edge_tts.Communicate(text, voice)
        audio_data = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
        return bytes(audio_data)
    except Exception as exc:
        logger.error(f"edge-tts failed: {exc}")
        raise RuntimeError(f"TTS synthesis failed: {exc}") from exc

def synthesize_text(text: str, lang: str = "en") -> bytes:
    import asyncio
    return asyncio.run(synthesize_text_async(text))

def init_tts() -> None:
    """Warm-up: log which engine is available."""
    logger.info("TTS engine: edge-tts (online)")

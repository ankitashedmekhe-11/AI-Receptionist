import asyncio
import audioop
import json
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from db.session import SessionLocal
from models.call import Call
from services import nlu
from services import reception
from services import stt
from services import tts
from services import business_profile as bp

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

END_OF_UTTERANCE = "end_of_utterance"


async def _send_json(websocket: WebSocket, payload: dict) -> None:
    await websocket.send_text(json.dumps(payload))


def _persist_call_transcript(
    transcript: str,
    intent: str | None = None,
    resolution: str | None = None,
    customer_id: int | None = None,
) -> int:
    db = SessionLocal()
    try:
        call = Call(
            customer_id=customer_id,
            timestamp=datetime.utcnow(),
            transcript=transcript,
            intent=intent,
            resolution=resolution,
        )
        db.add(call)
        db.commit()
        db.refresh(call)
        return call.id
    finally:
        db.close()


async def _speak(websocket: WebSocket, message: str) -> None:
    """Generate TTS for message and stream it to the client."""
    try:
        tts_bytes = await tts.synthesize_text_async(message)
        await _send_json(websocket, {"type": "tts_start"})
        chunk_size = 8192
        for i in range(0, len(tts_bytes), chunk_size):
            await websocket.send_bytes(tts_bytes[i: i + chunk_size])
        await _send_json(websocket, {"type": "tts_end"})
    except Exception:
        logger.exception("TTS synthesis or streaming failed")
        await _send_json(
            websocket,
            {"type": "tts_error", "message": "TTS synthesis failed — text response only."},
        )


@router.websocket("/ws/audio")
async def audio_ws(websocket: WebSocket) -> None:
    """
    Stream audio as binary WebSocket frames (16 kHz mono PCM chunks).

    Protocol:
    1. On connect: server sends greeting TTS using the configured business name.
    2. Client streams binary audio chunks.
    3. After VAD silence or explicit {"type":"end_of_utterance"}, server:
       - Transcribes via STT
       - Extracts intent/entities via NLU (using business profile services)
       - Executes receptionist action (with service & hours validation)
       - Saves call log
       - Sends transcript / nlu_result / action_result JSON
       - Streams TTS response audio
    """
    await websocket.accept()
    buffer = bytearray()

    # ── Load business profile once per session ─────────────────────────────────
    db = SessionLocal()
    try:
        profile = bp.get_business_profile(db)
    except Exception:
        logger.exception("Failed to load business profile")
        profile = bp.BusinessProfile()
    finally:
        db.close()

    # ── Session conversation state ─────────────────────────────────────────────
    # Persists across utterances so multi-turn booking works:
    # e.g. "book" → "haircut" → "tomorrow" → "3pm" → "John"
    session_state: dict = {"intent": "unknown", "entities": {}}

    # ── VAD settings ───────────────────────────────────────────────────────────
    is_speaking = False
    silence_chunks = 0
    RMS_THRESHOLD = 500
    SILENCE_MAX_CHUNKS = 24  # ~1.5 s at 16 kHz / 2048-byte chunks

    # ── Greeting ───────────────────────────────────────────────────────────────
    biz_name = profile.name if profile.is_configured() else "our service"
    greeting = f"Thank you for calling {biz_name}! How can I help you today?"
    await _send_json(websocket, {"type": "action_result", "success": True, "message": greeting})
    await _speak(websocket, greeting)

    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break

            process_utterance = False

            # ── Accumulate audio ───────────────────────────────────────────────
            if "bytes" in message and message["bytes"] is not None:
                chunk = message["bytes"]
                buffer.extend(chunk)

                try:
                    rms = audioop.rms(chunk, 2)
                    if rms > 1200:  # Increased threshold to ignore background noise
                        if not is_speaking:
                            is_speaking = True
                            # Notify client that speech was detected so they feel it's live
                            asyncio.create_task(_send_json(websocket, {"type": "speech_started"}))
                        silence_chunks = 0
                    elif is_speaking:
                        silence_chunks += 1
                        if silence_chunks >= 12:  # Reduced wait time (~0.75s) for much faster response
                            process_utterance = True
                            is_speaking = False
                            silence_chunks = 0
                except Exception:
                    pass

                if not process_utterance:
                    continue

            # ── Control messages ───────────────────────────────────────────────
            if "text" in message and message["text"] is not None:
                try:
                    control = json.loads(message["text"])
                    if control.get("type") == END_OF_UTTERANCE:
                        process_utterance = True
                except json.JSONDecodeError:
                    pass

            if not process_utterance or not buffer:
                continue

            audio_bytes = bytes(buffer)
            buffer.clear()

            # ── STT ────────────────────────────────────────────────────────────
            try:
                text = await asyncio.to_thread(stt.transcribe, audio_bytes)
            except ValueError as exc:
                await _send_json(websocket, {"type": "error", "message": str(exc)})
                continue
            except Exception:
                logger.exception("STT transcription failed")
                await _send_json(websocket, {"type": "error", "message": "Transcription failed"})
                continue

            if not text or not text.strip():
                continue
                
            # Send the transcript immediately so the UI feels incredibly fast
            await _send_json(websocket, {"type": "transcript", "text": text})

            # ── NLU (with business profile for service matching) ───────────────
            try:
                new_nlu_result = await asyncio.to_thread(nlu.extract, text, profile)
            except Exception:
                logger.exception("NLU extraction failed")
                new_nlu_result = {"intent": "unknown", "entities": {}}

            # Merge new result into session state (preserve across turns)
            if new_nlu_result.get("intent") and new_nlu_result["intent"] != "unknown":
                session_state["intent"] = new_nlu_result["intent"]

            for key, value in new_nlu_result.get("entities", {}).items():
                if value is not None:
                    session_state["entities"][key] = value

            # ── Receptionist action (with business profile for validation) ─────
            try:
                action_result = await asyncio.to_thread(
                    reception.apply_nlu_action,
                    text,
                    session_state,
                    profile,
                )
            except Exception:
                logger.exception("Reception action failed")
                action_result = {
                    "intent": session_state.get("intent", "unknown"),
                    "success": False,
                    "message": "I'm sorry, I had trouble processing that. Could you say that again?",
                    "customer_id": None,
                }

            # ── Persist call log ───────────────────────────────────────────────
            # Only save call records for meaningful intents to keep dashboard clean
            log_intent = session_state.get("intent", "unknown")
            call_id = await asyncio.to_thread(
                _persist_call_transcript,
                text,
                intent=log_intent if log_intent != "unknown" else None,
                resolution=action_result.get("message") if action_result.get("success") else None,
                customer_id=action_result.get("customer_id"),
            )

            # ── Clear session state on successful completion ───────────────────
            if action_result.get("success") and not action_result.get("needs_clarification"):
                session_state = {"intent": "unknown", "entities": {}}

            # ── Send text results to client ────────────────────────────────────
            await _send_json(websocket, {"type": "nlu_result", **session_state})
            await _send_json(websocket, {"type": "action_result", **action_result})

            # ── TTS response ───────────────────────────────────────────────────
            response_message = action_result.get("message") or "I'm sorry, I didn't catch that. Could you repeat?"
            await _speak(websocket, response_message)

    except WebSocketDisconnect:
        pass

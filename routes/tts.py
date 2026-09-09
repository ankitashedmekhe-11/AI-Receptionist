from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from services.tts import synthesize_text

router = APIRouter(prefix="/tts", tags=["tts"])


@router.get("/speak")
def speak(text: str = Query(..., min_length=1), lang: str = Query("en")) -> StreamingResponse:
    try:
        audio_bytes = synthesize_text(text, lang=lang)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return StreamingResponse(
        content=iter([audio_bytes]),
        media_type="audio/mpeg",
    )

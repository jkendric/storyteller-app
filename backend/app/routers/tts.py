from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from app.schemas import TTSRequest, TTSResponse, VoiceInfo
from app.services.tts_service import tts_service

router = APIRouter(prefix="/api/tts", tags=["tts"])


@router.post("/generate", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    """Generate TTS audio for text."""
    try:
        result = await tts_service.generate_audio(
            text=request.text,
            voice=request.voice,
            speed=request.speed or 1.0,
        )
        return TTSResponse(audio_url=result["audio_url"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


@router.get("/voices", response_model=list[VoiceInfo])
async def list_voices():
    """List available TTS voices."""
    voices = await tts_service.list_voices()
    return [
        VoiceInfo(
            id=v.get("id", v.get("voice_id", "")),
            name=v.get("name", ""),
            language=v.get("language"),
            gender=v.get("gender"),
        )
        for v in voices
    ]


@router.get("/health")
async def tts_health():
    """Check TTS service health."""
    is_healthy = await tts_service.health_check()
    return {"status": "healthy" if is_healthy else "unavailable"}

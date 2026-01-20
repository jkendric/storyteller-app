from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.tts import TTSRequest, TTSResponse, TTSStreamRequest, VoiceInfo, TTSHealthResponse
from app.services.tts.unified import unified_tts_service
from app.services.tts.manager import TTSProviderManager

router = APIRouter(prefix="/api/tts", tags=["tts"])


@router.post("/generate", response_model=TTSResponse)
async def generate_tts(
    request: TTSRequest,
    db: Session = Depends(get_db),
):
    """Generate TTS audio for text."""
    try:
        # Get provider if specified, otherwise use default
        provider = None
        voice_clone = None

        if request.provider_id:
            provider = TTSProviderManager.get_provider_by_id(db, request.provider_id)
            if not provider:
                raise HTTPException(status_code=404, detail="TTS provider not found")
        else:
            provider = TTSProviderManager.get_default_provider(db)

        # Get voice clone if specified
        if request.voice_clone_id:
            voice_clone = TTSProviderManager.get_voice_clone(db, request.voice_clone_id)
            if not voice_clone:
                raise HTTPException(status_code=404, detail="Voice clone not found")
            # Verify provider supports voice cloning
            if provider and not provider.supports_voice_cloning:
                raise HTTPException(
                    status_code=400,
                    detail="Selected provider does not support voice cloning"
                )

        result = await unified_tts_service.generate_audio(
            text=request.text,
            voice=request.voice,
            speed=request.speed or 1.0,
            provider=provider,
            voice_clone=voice_clone,
        )

        return TTSResponse(
            audio_url=result["audio_url"],
            provider_id=result.get("provider_id"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


@router.post("/stream")
async def stream_tts(
    request: TTSStreamRequest,
    db: Session = Depends(get_db),
):
    """Stream TTS audio in real-time."""
    try:
        # Get provider if specified, otherwise use default
        provider = None
        voice_clone = None

        if request.provider_id:
            provider = TTSProviderManager.get_provider_by_id(db, request.provider_id)
            if not provider:
                raise HTTPException(status_code=404, detail="TTS provider not found")
        else:
            provider = TTSProviderManager.get_default_provider(db)

        # Check if provider supports streaming
        if provider and not provider.supports_streaming:
            raise HTTPException(
                status_code=400,
                detail="Selected provider does not support streaming"
            )

        # Get voice clone if specified
        if request.voice_clone_id:
            voice_clone = TTSProviderManager.get_voice_clone(db, request.voice_clone_id)
            if not voice_clone:
                raise HTTPException(status_code=404, detail="Voice clone not found")

        async def audio_stream():
            async for chunk in unified_tts_service.generate_stream(
                text=request.text,
                voice=request.voice,
                speed=request.speed or 1.0,
                provider=provider,
                voice_clone=voice_clone,
            ):
                yield chunk

        # Both Kokoro and Chatterbox stream MP3 via OpenAI-compatible endpoints
        # Chatterbox's generate_stream uses /v1/audio/speech with response_format="mp3"
        # This ensures proper frame boundaries for smooth streaming playback
        media_type = "audio/mpeg"

        return StreamingResponse(
            audio_stream(),
            media_type=media_type,
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS streaming failed: {str(e)}")


@router.get("/voices", response_model=list[VoiceInfo])
async def list_voices(
    provider_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """List available TTS voices, optionally filtered by provider."""
    try:
        provider = None
        if provider_id:
            provider = TTSProviderManager.get_provider_by_id(db, provider_id)
            if not provider:
                raise HTTPException(status_code=404, detail="TTS provider not found")

        voices = await unified_tts_service.list_voices(provider)
        return [
            VoiceInfo(
                id=v.get("id", v.get("voice_id", "")),
                name=v.get("name", ""),
                language=v.get("language"),
                gender=v.get("gender"),
                provider_id=v.get("provider_id"),
            )
            for v in voices
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list voices: {str(e)}")


@router.get("/health", response_model=TTSHealthResponse)
async def tts_health(db: Session = Depends(get_db)):
    """Check health of all TTS providers."""
    try:
        providers = await unified_tts_service.health_check_all(db)
        default_provider = TTSProviderManager.get_default_provider(db)

        return TTSHealthResponse(
            providers=providers,
            default_provider_id=default_provider.id if default_provider else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

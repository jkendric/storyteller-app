"""TTS provider settings router."""

import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from mutagen import File as MutagenFile

from app.database import get_db
from app.models.tts_provider import TTSProvider, TTSVoiceClone, TTSProviderType
from app.schemas.tts_provider import (
    TTSProviderCreate,
    TTSProviderUpdate,
    TTSProviderResponse,
    TTSProviderList,
    TTSProviderTestResult,
    TTSProviderVoicesResponse,
    VoiceCloneCreate,
    VoiceCloneResponse,
    VoiceCloneList,
)
from app.services.tts.unified import unified_tts_service
from app.services.tts.manager import TTSProviderManager

router = APIRouter(prefix="/api/settings/tts-providers", tags=["tts-settings"])

# Ensure voice samples directory exists
VOICE_SAMPLES_DIR = Path("./data/voice_samples")
VOICE_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


@router.get("", response_model=TTSProviderList)
def list_tts_providers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all TTS providers with pagination."""
    providers = db.query(TTSProvider).offset(skip).limit(limit).all()
    total = db.query(TTSProvider).count()
    return TTSProviderList(providers=providers, total=total)


@router.post("", response_model=TTSProviderResponse, status_code=status.HTTP_201_CREATED)
def create_tts_provider(
    provider: TTSProviderCreate,
    db: Session = Depends(get_db),
):
    """Create a new TTS provider."""
    # If this is being set as default, clear other defaults
    if provider.is_default:
        db.query(TTSProvider).filter(TTSProvider.is_default == True).update(
            {"is_default": False}
        )

    # Set capabilities based on provider type
    provider_data = provider.model_dump()

    # Auto-detect capabilities based on provider type
    provider_type = provider_data["provider_type"]
    if provider_type == TTSProviderType.KOKORO:
        provider_data["supports_streaming"] = True
        provider_data["supports_voice_cloning"] = False
    elif provider_type == TTSProviderType.PIPER:
        provider_data["supports_streaming"] = False
        provider_data["supports_voice_cloning"] = False
    elif provider_type == TTSProviderType.COQUI_XTTS:
        provider_data["supports_streaming"] = True
        provider_data["supports_voice_cloning"] = True
    elif provider_type == TTSProviderType.CHATTERBOX:
        provider_data["supports_streaming"] = True
        provider_data["supports_voice_cloning"] = True
    elif provider_type == TTSProviderType.OPENAI_COMPATIBLE:
        # Keep user-provided values for OpenAI-compatible
        pass

    db_provider = TTSProvider(**provider_data)
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)

    # Clear provider cache
    unified_tts_service.clear_cache()

    return db_provider


@router.get("/{provider_id}", response_model=TTSProviderResponse)
def get_tts_provider(
    provider_id: int,
    db: Session = Depends(get_db),
):
    """Get a TTS provider by ID."""
    provider = db.query(TTSProvider).filter(TTSProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="TTS provider not found")
    return provider


@router.put("/{provider_id}", response_model=TTSProviderResponse)
def update_tts_provider(
    provider_id: int,
    provider_update: TTSProviderUpdate,
    db: Session = Depends(get_db),
):
    """Update a TTS provider."""
    provider = db.query(TTSProvider).filter(TTSProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="TTS provider not found")

    update_data = provider_update.model_dump(exclude_unset=True)

    # Handle is_default flag - clear others if setting to True
    if update_data.get("is_default") is True:
        db.query(TTSProvider).filter(
            TTSProvider.id != provider_id,
            TTSProvider.is_default == True
        ).update({"is_default": False})

    for field, value in update_data.items():
        setattr(provider, field, value)

    db.commit()
    db.refresh(provider)

    # Clear provider cache for this provider
    unified_tts_service.clear_cache(provider_id)

    return provider


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tts_provider(
    provider_id: int,
    db: Session = Depends(get_db),
):
    """Delete a TTS provider and its voice clones."""
    provider = db.query(TTSProvider).filter(TTSProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="TTS provider not found")

    # Delete associated voice clone audio files
    for voice_clone in provider.voice_clones:
        if voice_clone.reference_audio_path:
            audio_path = Path(voice_clone.reference_audio_path)
            if audio_path.exists():
                audio_path.unlink()

    db.delete(provider)
    db.commit()

    # Clear provider cache
    unified_tts_service.clear_cache(provider_id)


@router.post("/{provider_id}/test", response_model=TTSProviderTestResult)
async def test_tts_provider(
    provider_id: int,
    db: Session = Depends(get_db),
):
    """Test connection to a TTS provider and return available voices."""
    provider = db.query(TTSProvider).filter(TTSProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="TTS provider not found")

    try:
        is_healthy = await unified_tts_service.health_check(provider)
        if is_healthy:
            voices = await unified_tts_service.list_voices(provider)
            voice_names = [v.get("id") or v.get("name", "unknown") for v in voices]
            capabilities = unified_tts_service.get_provider_capabilities(provider)
            return TTSProviderTestResult(
                status="ok",
                message="Connection successful",
                voices=voice_names,
                supports_streaming=capabilities["supports_streaming"],
                supports_voice_cloning=capabilities["supports_voice_cloning"],
            )
        else:
            return TTSProviderTestResult(
                status="error",
                message="TTS provider is not responding"
            )
    except Exception as e:
        return TTSProviderTestResult(
            status="error",
            message=str(e)
        )


@router.get("/{provider_id}/voices", response_model=TTSProviderVoicesResponse)
async def list_tts_provider_voices(
    provider_id: int,
    db: Session = Depends(get_db),
):
    """List available voices from a TTS provider."""
    provider = db.query(TTSProvider).filter(TTSProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="TTS provider not found")

    try:
        voices = await unified_tts_service.list_voices(provider)
        return TTSProviderVoicesResponse(voices=voices)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch voices from TTS provider: {str(e)}"
        )


@router.post("/test-url", response_model=TTSProviderTestResult)
async def test_tts_provider_url(
    base_url: str,
    provider_type: TTSProviderType,
):
    """Test connection to a TTS provider URL without saving it."""
    from app.services.tts.kokoro import KokoroProvider
    from app.services.tts.piper import PiperProvider
    from app.services.tts.coqui_xtts import CoquiXTTSProvider
    from app.services.tts.openai_compat import OpenAICompatProvider
    from app.services.tts.chatterbox import ChatterboxProvider

    # Create temporary provider instance
    provider_classes = {
        TTSProviderType.KOKORO: KokoroProvider,
        TTSProviderType.PIPER: PiperProvider,
        TTSProviderType.COQUI_XTTS: CoquiXTTSProvider,
        TTSProviderType.OPENAI_COMPATIBLE: OpenAICompatProvider,
        TTSProviderType.CHATTERBOX: ChatterboxProvider,
    }

    provider_class = provider_classes.get(provider_type)
    if not provider_class:
        return TTSProviderTestResult(
            status="error",
            message=f"Unknown provider type: {provider_type}"
        )

    temp_provider = provider_class(base_url=base_url)

    try:
        is_healthy = await temp_provider.health_check()
        if is_healthy:
            voices = await temp_provider.list_voices()
            voice_names = [v.get("id") or v.get("name", "unknown") for v in voices]
            return TTSProviderTestResult(
                status="ok",
                message="Connection successful",
                voices=voice_names,
                supports_streaming=temp_provider.supports_streaming,
                supports_voice_cloning=temp_provider.supports_voice_cloning,
            )
        else:
            return TTSProviderTestResult(
                status="error",
                message="TTS provider is not responding"
            )
    except Exception as e:
        return TTSProviderTestResult(
            status="error",
            message=str(e)
        )


# Voice Clone Endpoints
@router.get("/{provider_id}/voice-clones", response_model=VoiceCloneList)
def list_voice_clones(
    provider_id: int,
    db: Session = Depends(get_db),
):
    """List voice clones for a TTS provider."""
    provider = db.query(TTSProvider).filter(TTSProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="TTS provider not found")

    if not provider.supports_voice_cloning:
        raise HTTPException(
            status_code=400,
            detail="This provider does not support voice cloning"
        )

    voice_clones = TTSProviderManager.get_voice_clones_for_provider(db, provider_id)
    return VoiceCloneList(voice_clones=voice_clones, total=len(voice_clones))


@router.post("/{provider_id}/voice-clones", response_model=VoiceCloneResponse)
async def create_voice_clone(
    provider_id: int,
    name: str = Form(...),
    description: str = Form(None),
    language: str = Form("en"),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a voice clone reference audio for a TTS provider."""
    provider = db.query(TTSProvider).filter(TTSProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="TTS provider not found")

    if not provider.supports_voice_cloning:
        raise HTTPException(
            status_code=400,
            detail="This provider does not support voice cloning"
        )

    # Validate file type
    allowed_types = ["audio/wav", "audio/x-wav", "audio/wave", "audio/mpeg", "audio/mp3"]
    if audio_file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audio format. Allowed: WAV, MP3. Got: {audio_file.content_type}"
        )

    # Generate unique filename
    file_ext = Path(audio_file.filename).suffix or ".wav"
    unique_id = str(uuid.uuid4())
    filename = f"{unique_id}{file_ext}"
    filepath = VOICE_SAMPLES_DIR / filename

    # Save the audio file
    async with aiofiles.open(filepath, "wb") as f:
        content = await audio_file.read()
        await f.write(content)

    # Get audio duration using mutagen
    audio_duration = None
    try:
        audio = MutagenFile(str(filepath))
        if audio and audio.info:
            audio_duration = int(audio.info.length)
    except Exception:
        pass

    # Validate minimum duration for XTTS (6 seconds)
    if audio_duration and audio_duration < 6:
        # Clean up the file
        filepath.unlink()
        raise HTTPException(
            status_code=400,
            detail=f"Audio must be at least 6 seconds for voice cloning. Got: {audio_duration}s"
        )

    # Create voice clone entry
    voice_clone = TTSProviderManager.create_voice_clone(
        db=db,
        name=name,
        provider_id=provider_id,
        reference_audio_path=str(filepath),
        description=description,
        audio_duration=audio_duration,
        language=language,
    )

    return voice_clone


@router.get("/{provider_id}/voice-clones/{clone_id}", response_model=VoiceCloneResponse)
def get_voice_clone(
    provider_id: int,
    clone_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific voice clone."""
    voice_clone = db.query(TTSVoiceClone).filter(
        TTSVoiceClone.id == clone_id,
        TTSVoiceClone.provider_id == provider_id
    ).first()
    if not voice_clone:
        raise HTTPException(status_code=404, detail="Voice clone not found")
    return voice_clone


@router.delete("/{provider_id}/voice-clones/{clone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_voice_clone(
    provider_id: int,
    clone_id: int,
    db: Session = Depends(get_db),
):
    """Delete a voice clone."""
    voice_clone = db.query(TTSVoiceClone).filter(
        TTSVoiceClone.id == clone_id,
        TTSVoiceClone.provider_id == provider_id
    ).first()
    if not voice_clone:
        raise HTTPException(status_code=404, detail="Voice clone not found")

    # Delete the audio file
    if voice_clone.reference_audio_path:
        audio_path = Path(voice_clone.reference_audio_path)
        if audio_path.exists():
            audio_path.unlink()

    db.delete(voice_clone)
    db.commit()


@router.get("/{provider_id}/voice-clones/{clone_id}/audio")
async def get_voice_clone_audio(
    provider_id: int,
    clone_id: int,
    db: Session = Depends(get_db),
):
    """Stream the voice clone reference audio."""
    voice_clone = db.query(TTSVoiceClone).filter(
        TTSVoiceClone.id == clone_id,
        TTSVoiceClone.provider_id == provider_id
    ).first()
    if not voice_clone:
        raise HTTPException(status_code=404, detail="Voice clone not found")

    audio_path = Path(voice_clone.reference_audio_path)
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    # Determine media type
    suffix = audio_path.suffix.lower()
    media_type = "audio/wav" if suffix in [".wav", ".wave"] else "audio/mpeg"

    async def stream_file():
        async with aiofiles.open(audio_path, "rb") as f:
            while chunk := await f.read(8192):
                yield chunk

    return StreamingResponse(
        stream_file(),
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{audio_path.name}"'
        }
    )

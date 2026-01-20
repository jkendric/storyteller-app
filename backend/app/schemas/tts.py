from pydantic import BaseModel, Field
from typing import Optional


class TTSRequest(BaseModel):
    """Schema for TTS generation request."""
    text: str = Field(..., min_length=1)
    voice: Optional[str] = None
    speed: Optional[float] = Field(None, ge=0.5, le=2.0)
    provider_id: Optional[int] = None  # Specific provider to use
    voice_clone_id: Optional[int] = None  # Voice clone reference for XTTS


class TTSResponse(BaseModel):
    """Schema for TTS generation response."""
    audio_url: str
    duration: Optional[float] = None
    provider_id: Optional[int] = None  # Provider that generated the audio


class TTSStreamRequest(BaseModel):
    """Schema for TTS streaming request."""
    text: str = Field(..., min_length=1)
    voice: Optional[str] = None
    speed: Optional[float] = Field(None, ge=0.5, le=2.0)
    provider_id: Optional[int] = None
    voice_clone_id: Optional[int] = None


class VoiceInfo(BaseModel):
    """Schema for voice information."""
    id: str
    name: str
    language: Optional[str] = None
    gender: Optional[str] = None
    provider_id: Optional[int] = None  # Which provider this voice belongs to


class TTSHealthResponse(BaseModel):
    """Schema for TTS health check response."""
    providers: list[dict]  # List of provider health statuses
    default_provider_id: Optional[int] = None

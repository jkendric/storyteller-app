from pydantic import BaseModel, Field
from typing import Optional


class TTSRequest(BaseModel):
    """Schema for TTS generation request."""
    text: str = Field(..., min_length=1)
    voice: Optional[str] = None
    speed: Optional[float] = Field(None, ge=0.5, le=2.0)


class TTSResponse(BaseModel):
    """Schema for TTS generation response."""
    audio_url: str
    duration: Optional[float] = None


class VoiceInfo(BaseModel):
    """Schema for voice information."""
    id: str
    name: str
    language: Optional[str] = None
    gender: Optional[str] = None

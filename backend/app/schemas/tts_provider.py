from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any
from enum import Enum


class TTSProviderType(str, Enum):
    """TTS provider type enumeration."""
    KOKORO = "kokoro"
    PIPER = "piper"
    COQUI_XTTS = "coqui_xtts"
    OPENAI_COMPATIBLE = "openai_compatible"
    CHATTERBOX = "chatterbox"


# TTS Provider Schemas
class TTSProviderBase(BaseModel):
    """Base TTS provider schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    provider_type: TTSProviderType
    base_url: str = Field(..., min_length=1, max_length=255)
    default_voice: Optional[str] = Field(None, max_length=100)
    supports_streaming: bool = False
    supports_voice_cloning: bool = False
    provider_settings: Optional[dict[str, Any]] = None
    is_default: bool = False
    enabled: bool = True


class TTSProviderCreate(TTSProviderBase):
    """Schema for creating a new TTS provider."""
    pass


class TTSProviderUpdate(BaseModel):
    """Schema for updating a TTS provider."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    provider_type: Optional[TTSProviderType] = None
    base_url: Optional[str] = Field(None, min_length=1, max_length=255)
    default_voice: Optional[str] = Field(None, max_length=100)
    supports_streaming: Optional[bool] = None
    supports_voice_cloning: Optional[bool] = None
    provider_settings: Optional[dict[str, Any]] = None
    is_default: Optional[bool] = None
    enabled: Optional[bool] = None


class TTSProviderResponse(TTSProviderBase):
    """Schema for TTS provider response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TTSProviderList(BaseModel):
    """Schema for list of TTS providers."""
    providers: list[TTSProviderResponse]
    total: int


class TTSProviderTestResult(BaseModel):
    """Schema for TTS provider connection test result."""
    status: str  # "ok" or "error"
    message: Optional[str] = None
    voices: Optional[list[str]] = None
    supports_streaming: Optional[bool] = None
    supports_voice_cloning: Optional[bool] = None


class TTSProviderVoicesResponse(BaseModel):
    """Schema for TTS provider voices list response."""
    voices: list[dict]


# Voice Clone Schemas
class VoiceCloneBase(BaseModel):
    """Base voice clone schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    language: str = Field(default="en", max_length=10)


class VoiceCloneCreate(VoiceCloneBase):
    """Schema for creating a voice clone (without audio - uploaded separately)."""
    pass


class VoiceCloneResponse(VoiceCloneBase):
    """Schema for voice clone response."""
    id: int
    provider_id: int
    reference_audio_path: str
    audio_duration: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VoiceCloneList(BaseModel):
    """Schema for list of voice clones."""
    voice_clones: list[VoiceCloneResponse]
    total: int

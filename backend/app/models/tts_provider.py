from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class TTSProviderType(str, enum.Enum):
    """TTS provider type enumeration."""
    KOKORO = "kokoro"
    PIPER = "piper"
    COQUI_XTTS = "coqui_xtts"
    OPENAI_COMPATIBLE = "openai_compatible"
    CHATTERBOX = "chatterbox"


class TTSProvider(Base):
    """TTS provider configuration model."""

    __tablename__ = "tts_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    provider_type = Column(Enum(TTSProviderType), nullable=False)
    base_url = Column(String(255), nullable=False)
    default_voice = Column(String(100), nullable=True)
    supports_streaming = Column(Boolean, default=False)
    supports_voice_cloning = Column(Boolean, default=False)
    provider_settings = Column(JSON, nullable=True)  # Provider-specific config
    is_default = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to voice clones
    voice_clones = relationship("TTSVoiceClone", back_populates="provider", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TTSProvider(id={self.id}, name='{self.name}', type='{self.provider_type}')>"


class TTSVoiceClone(Base):
    """TTS voice clone configuration model for XTTS/Coqui providers."""

    __tablename__ = "tts_voice_clones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    provider_id = Column(Integer, ForeignKey("tts_providers.id"), nullable=False)
    reference_audio_path = Column(String(255), nullable=False)  # data/voice_samples/{id}.wav
    audio_duration = Column(Integer, nullable=True)  # seconds (must be 6+ for XTTS)
    language = Column(String(10), default="en")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to provider
    provider = relationship("TTSProvider", back_populates="voice_clones")

    def __repr__(self):
        return f"<TTSVoiceClone(id={self.id}, name='{self.name}', provider_id={self.provider_id})>"

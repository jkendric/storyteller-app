"""TTS Provider manager for database operations."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.tts_provider import TTSProvider, TTSVoiceClone


class TTSProviderManager:
    """Manager for handling TTS provider selection and queries from database."""

    @staticmethod
    def get_default_provider(db: Session) -> Optional[TTSProvider]:
        """Get the default TTS provider from database."""
        return db.query(TTSProvider).filter(
            TTSProvider.is_default == True,
            TTSProvider.enabled == True
        ).first()

    @staticmethod
    def get_provider_by_id(db: Session, provider_id: int) -> Optional[TTSProvider]:
        """Get a specific TTS provider by ID."""
        return db.query(TTSProvider).filter(
            TTSProvider.id == provider_id,
            TTSProvider.enabled == True
        ).first()

    @staticmethod
    def get_all_providers(db: Session, enabled_only: bool = True) -> list[TTSProvider]:
        """Get all TTS providers."""
        query = db.query(TTSProvider)
        if enabled_only:
            query = query.filter(TTSProvider.enabled == True)
        return query.all()

    @staticmethod
    def get_provider_for_generation(
        db: Session,
        provider_id: Optional[int] = None
    ) -> Optional[TTSProvider]:
        """Get the appropriate provider for TTS generation."""
        if provider_id:
            provider = TTSProviderManager.get_provider_by_id(db, provider_id)
            if provider:
                return provider
        # Fall back to default provider
        return TTSProviderManager.get_default_provider(db)

    @staticmethod
    def get_voice_clone(db: Session, voice_clone_id: int) -> Optional[TTSVoiceClone]:
        """Get a specific voice clone by ID."""
        return db.query(TTSVoiceClone).filter(
            TTSVoiceClone.id == voice_clone_id
        ).first()

    @staticmethod
    def get_voice_clones_for_provider(db: Session, provider_id: int) -> list[TTSVoiceClone]:
        """Get all voice clones for a specific provider."""
        return db.query(TTSVoiceClone).filter(
            TTSVoiceClone.provider_id == provider_id
        ).all()

    @staticmethod
    def create_voice_clone(
        db: Session,
        name: str,
        provider_id: int,
        reference_audio_path: str,
        description: Optional[str] = None,
        audio_duration: Optional[int] = None,
        language: str = "en"
    ) -> TTSVoiceClone:
        """Create a new voice clone entry."""
        voice_clone = TTSVoiceClone(
            name=name,
            description=description,
            provider_id=provider_id,
            reference_audio_path=reference_audio_path,
            audio_duration=audio_duration,
            language=language,
        )
        db.add(voice_clone)
        db.commit()
        db.refresh(voice_clone)
        return voice_clone

    @staticmethod
    def delete_voice_clone(db: Session, voice_clone_id: int) -> bool:
        """Delete a voice clone."""
        voice_clone = db.query(TTSVoiceClone).filter(
            TTSVoiceClone.id == voice_clone_id
        ).first()
        if voice_clone:
            db.delete(voice_clone)
            db.commit()
            return True
        return False

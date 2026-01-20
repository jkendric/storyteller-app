"""Unified TTS service that routes to appropriate providers."""

from typing import Optional, AsyncGenerator
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.tts_provider import TTSProvider, TTSProviderType, TTSVoiceClone
from app.services.tts.base import BaseTTSProvider
from app.services.tts.kokoro import KokoroProvider
from app.services.tts.piper import PiperProvider
from app.services.tts.coqui_xtts import CoquiXTTSProvider
from app.services.tts.openai_compat import OpenAICompatProvider
from app.services.tts.chatterbox import ChatterboxProvider
from app.services.tts.manager import TTSProviderManager

settings = get_settings()


class UnifiedTTSService:
    """Unified TTS service supporting multiple providers."""

    # Provider class mapping
    PROVIDER_CLASSES = {
        TTSProviderType.KOKORO: KokoroProvider,
        TTSProviderType.PIPER: PiperProvider,
        TTSProviderType.COQUI_XTTS: CoquiXTTSProvider,
        TTSProviderType.OPENAI_COMPATIBLE: OpenAICompatProvider,
        TTSProviderType.CHATTERBOX: ChatterboxProvider,
    }

    def __init__(self):
        # Cache for provider instances
        self._provider_cache: dict[int, BaseTTSProvider] = {}

        # Fallback settings when no database provider is configured
        self._fallback_base_url = settings.kokoro_tts_url
        self._fallback_voice = settings.tts_default_voice

    def _get_provider_instance(self, provider: TTSProvider) -> BaseTTSProvider:
        """Get or create a provider instance from database model."""
        # Check cache first
        if provider.id in self._provider_cache:
            cached = self._provider_cache[provider.id]
            # Verify cache is still valid (same URL)
            if cached.base_url == provider.base_url.rstrip("/"):
                return cached

        # Create new provider instance
        provider_class = self.PROVIDER_CLASSES.get(provider.provider_type)
        if not provider_class:
            raise ValueError(f"Unknown provider type: {provider.provider_type}")

        instance = provider_class(
            base_url=provider.base_url,
            default_voice=provider.default_voice,
            settings=provider.provider_settings or {},
        )

        # Cache the instance
        self._provider_cache[provider.id] = instance
        return instance

    def _get_fallback_provider(self) -> BaseTTSProvider:
        """Get fallback Kokoro provider from config settings."""
        return KokoroProvider(
            base_url=self._fallback_base_url,
            default_voice=self._fallback_voice,
        )

    def clear_cache(self, provider_id: Optional[int] = None):
        """Clear provider instance cache."""
        if provider_id:
            self._provider_cache.pop(provider_id, None)
        else:
            self._provider_cache.clear()

    async def generate_audio(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        provider: Optional[TTSProvider] = None,
        voice_clone: Optional[TTSVoiceClone] = None,
    ) -> dict:
        """
        Generate audio from text.

        Args:
            text: Text to convert to speech
            voice: Voice identifier (optional, uses provider default)
            speed: Speech speed multiplier (0.5-2.0)
            provider: TTSProvider model instance (optional, uses default if not specified)
            voice_clone: TTSVoiceClone for voice cloning (XTTS only)

        Returns:
            dict with audio_url and filename
        """
        # Get provider instance
        if provider:
            tts_provider = self._get_provider_instance(provider)
        else:
            tts_provider = self._get_fallback_provider()

        # Determine voice clone path if applicable
        voice_clone_path = None
        if voice_clone and tts_provider.supports_voice_cloning:
            voice_clone_path = voice_clone.reference_audio_path

        result = await tts_provider.generate_audio(
            text=text,
            voice=voice,
            speed=speed,
            voice_clone_path=voice_clone_path,
        )

        # Add provider info to result
        if provider:
            result["provider_id"] = provider.id

        return result

    async def generate_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        provider: Optional[TTSProvider] = None,
        voice_clone: Optional[TTSVoiceClone] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Generate audio as a stream of chunks.

        Args:
            text: Text to convert to speech
            voice: Voice identifier
            speed: Speech speed multiplier
            provider: TTSProvider model instance
            voice_clone: TTSVoiceClone for voice cloning

        Yields:
            Audio data chunks
        """
        # Get provider instance
        if provider:
            tts_provider = self._get_provider_instance(provider)
        else:
            tts_provider = self._get_fallback_provider()

        if not tts_provider.supports_streaming:
            raise ValueError(f"Provider {tts_provider.provider_type} does not support streaming")

        voice_clone_path = None
        if voice_clone and tts_provider.supports_voice_cloning:
            voice_clone_path = voice_clone.reference_audio_path

        async for chunk in tts_provider.generate_stream(
            text=text,
            voice=voice,
            speed=speed,
            voice_clone_path=voice_clone_path,
        ):
            yield chunk

    async def list_voices(
        self,
        provider: Optional[TTSProvider] = None
    ) -> list[dict]:
        """List available voices for a provider."""
        if provider:
            tts_provider = self._get_provider_instance(provider)
        else:
            tts_provider = self._get_fallback_provider()

        voices = await tts_provider.list_voices()

        # Add provider info to each voice
        if provider:
            for voice in voices:
                voice["provider_id"] = provider.id

        return voices

    async def health_check(
        self,
        provider: Optional[TTSProvider] = None
    ) -> bool:
        """Check if a provider is available."""
        try:
            if provider:
                tts_provider = self._get_provider_instance(provider)
            else:
                tts_provider = self._get_fallback_provider()

            return await tts_provider.health_check()
        except Exception:
            return False

    async def health_check_all(self, db: Session) -> list[dict]:
        """Check health of all configured providers."""
        providers = TTSProviderManager.get_all_providers(db, enabled_only=False)
        results = []

        for provider in providers:
            try:
                tts_provider = self._get_provider_instance(provider)
                is_healthy = await tts_provider.health_check()
                results.append({
                    "provider_id": provider.id,
                    "name": provider.name,
                    "provider_type": provider.provider_type.value,
                    "status": "ok" if is_healthy else "error",
                    "enabled": provider.enabled,
                    "is_default": provider.is_default,
                })
            except Exception as e:
                results.append({
                    "provider_id": provider.id,
                    "name": provider.name,
                    "provider_type": provider.provider_type.value,
                    "status": "error",
                    "message": str(e),
                    "enabled": provider.enabled,
                    "is_default": provider.is_default,
                })

        return results

    def get_provider_capabilities(self, provider: TTSProvider) -> dict:
        """Get capabilities of a provider."""
        tts_provider = self._get_provider_instance(provider)
        return {
            "supports_streaming": tts_provider.supports_streaming,
            "supports_voice_cloning": tts_provider.supports_voice_cloning,
        }


# Singleton instance
unified_tts_service = UnifiedTTSService()

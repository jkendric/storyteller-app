"""Base abstract class for TTS providers."""

from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator
from pathlib import Path
import uuid


class BaseTTSProvider(ABC):
    """Abstract base class for TTS providers."""

    def __init__(self, base_url: str, default_voice: Optional[str] = None, settings: Optional[dict] = None):
        self.base_url = base_url.rstrip("/")
        self.default_voice = default_voice
        self.settings = settings or {}
        self.audio_dir = Path("./data/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Return the provider type identifier."""
        pass

    @property
    def supports_streaming(self) -> bool:
        """Whether this provider supports real-time audio streaming."""
        return False

    @property
    def supports_voice_cloning(self) -> bool:
        """Whether this provider supports voice cloning."""
        return False

    @abstractmethod
    async def generate_audio(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        voice_clone_path: Optional[str] = None,
    ) -> dict:
        """
        Generate audio from text.

        Args:
            text: The text to convert to speech
            voice: Voice identifier to use (provider-specific)
            speed: Speech speed multiplier (0.5 to 2.0)
            voice_clone_path: Path to reference audio for voice cloning (XTTS only)

        Returns:
            dict with audio_url, filename, and optionally duration
        """
        pass

    async def generate_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        voice_clone_path: Optional[str] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Generate audio as a stream of chunks.

        Default implementation raises NotImplementedError.
        Override in providers that support streaming.

        Args:
            text: The text to convert to speech
            voice: Voice identifier to use
            speed: Speech speed multiplier
            voice_clone_path: Path to reference audio for voice cloning

        Yields:
            Audio data chunks as bytes
        """
        raise NotImplementedError(f"{self.provider_type} does not support streaming")

    @abstractmethod
    async def list_voices(self) -> list[dict]:
        """
        List available voices for this provider.

        Returns:
            List of voice info dicts with id, name, language, gender
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the TTS provider is available.

        Returns:
            True if provider is reachable and healthy
        """
        pass

    def _generate_filename(self, extension: str = "mp3") -> tuple[str, Path]:
        """Generate a unique filename and filepath for audio output."""
        filename = f"{uuid.uuid4()}.{extension}"
        filepath = self.audio_dir / filename
        return filename, filepath

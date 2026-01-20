"""Piper TTS provider implementation."""

import httpx
import aiofiles
from typing import Optional, AsyncGenerator
from urllib.parse import urlencode

from app.services.tts.base import BaseTTSProvider


class PiperProvider(BaseTTSProvider):
    """Piper TTS provider (CPU-based, no streaming, port 5000)."""

    @property
    def provider_type(self) -> str:
        return "piper"

    @property
    def supports_streaming(self) -> bool:
        return False  # Piper is CPU-based and doesn't support streaming

    @property
    def supports_voice_cloning(self) -> bool:
        return False

    async def generate_audio(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        voice_clone_path: Optional[str] = None,
    ) -> dict:
        """Generate audio from text using Piper TTS."""
        voice = voice or self.default_voice or "en_US-lessac-medium"

        # Piper uses query parameters for /api/tts endpoint
        params = {
            "text": text,
            "voice": voice,
            "speed": speed,
        }

        # Add any extra settings from provider config
        if self.settings.get("length_scale"):
            params["length_scale"] = self.settings["length_scale"]
        if self.settings.get("noise_scale"):
            params["noise_scale"] = self.settings["noise_scale"]

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(
                f"{self.base_url}/api/tts",
                params=params,
            )
            response.raise_for_status()

            # Piper returns WAV audio
            filename, filepath = self._generate_filename("wav")

            async with aiofiles.open(filepath, "wb") as f:
                await f.write(response.content)

            return {
                "audio_url": f"/audio/{filename}",
                "filename": filename,
            }

    async def generate_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        voice_clone_path: Optional[str] = None,
    ) -> AsyncGenerator[bytes, None]:
        """Piper does not support streaming."""
        raise NotImplementedError("Piper TTS does not support real-time streaming")

    async def list_voices(self) -> list[dict]:
        """List available Piper TTS voices."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Piper HTTP server typically exposes voices at /api/voices
                response = await client.get(f"{self.base_url}/api/voices")
                if response.status_code == 200:
                    data = response.json()
                    # Normalize voice format
                    voices = []
                    for voice_id, voice_info in data.items():
                        voices.append({
                            "id": voice_id,
                            "name": voice_info.get("name", voice_id),
                            "language": voice_info.get("language", {}).get("code", "en"),
                            "gender": voice_info.get("gender", "unknown"),
                        })
                    return voices
        except Exception:
            pass

        # Return common Piper voices as fallback
        return [
            {"id": "en_US-lessac-medium", "name": "Lessac (US English)", "language": "en-US", "gender": "female"},
            {"id": "en_US-amy-medium", "name": "Amy (US English)", "language": "en-US", "gender": "female"},
            {"id": "en_US-danny-low", "name": "Danny (US English)", "language": "en-US", "gender": "male"},
            {"id": "en_US-ryan-medium", "name": "Ryan (US English)", "language": "en-US", "gender": "male"},
            {"id": "en_GB-alan-medium", "name": "Alan (British English)", "language": "en-GB", "gender": "male"},
            {"id": "en_GB-alba-medium", "name": "Alba (British English)", "language": "en-GB", "gender": "female"},
        ]

    async def health_check(self) -> bool:
        """Check if Piper TTS is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try voices endpoint
                response = await client.get(f"{self.base_url}/api/voices")
                if response.status_code == 200:
                    return True
                # Fallback to simple request
                response = await client.get(f"{self.base_url}/")
                return response.status_code < 500
        except Exception:
            return False

"""Kokoro TTS provider implementation."""

import httpx
import aiofiles
from typing import Optional, AsyncGenerator

from app.services.tts.base import BaseTTSProvider


class KokoroProvider(BaseTTSProvider):
    """Kokoro TTS provider (OpenAI-compatible API on port 8880)."""

    @property
    def provider_type(self) -> str:
        return "kokoro"

    @property
    def supports_streaming(self) -> bool:
        return True

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
        """Generate audio from text using Kokoro TTS."""
        voice = voice or self.default_voice or "af_bella"

        payload = {
            "model": "kokoro",
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": "mp3",
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/audio/speech",
                json=payload,
            )
            response.raise_for_status()

            # Save audio to file
            filename, filepath = self._generate_filename("mp3")

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
        """Stream audio from Kokoro TTS."""
        voice = voice or self.default_voice or "af_bella"

        payload = {
            "model": "kokoro",
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": "mp3",
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/audio/speech",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes(chunk_size=4096):
                    if chunk:
                        yield chunk

    async def list_voices(self) -> list[dict]:
        """List available Kokoro TTS voices."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/v1/audio/voices")
                if response.status_code == 200:
                    data = response.json()
                    voices = data.get("voices", [])
                    # Normalize: convert string voice IDs to dicts
                    return self._normalize_voices(voices)
        except Exception:
            pass

        # Return default Kokoro voices if API not available
        return self._get_default_voices()

    def _normalize_voices(self, voices: list) -> list[dict]:
        """Normalize voice list - convert strings to dicts if needed."""
        normalized = []
        for v in voices:
            if isinstance(v, str):
                # Convert string voice ID to dict format
                normalized.append(self._voice_id_to_dict(v))
            elif isinstance(v, dict):
                normalized.append(v)
        return normalized

    def _voice_id_to_dict(self, voice_id: str) -> dict:
        """Convert a voice ID string to a dict with name/language/gender."""
        # Parse Kokoro voice ID format: {lang_prefix}_{name}
        # e.g., af_bella -> American Female Bella
        voice_info = {"id": voice_id, "name": voice_id}

        # Known voice prefixes
        prefixes = {
            "af_": ("American Female", "en-US", "female"),
            "am_": ("American Male", "en-US", "male"),
            "bf_": ("British Female", "en-GB", "female"),
            "bm_": ("British Male", "en-GB", "male"),
        }

        for prefix, (type_name, language, gender) in prefixes.items():
            if voice_id.startswith(prefix):
                name_part = voice_id[len(prefix):].replace("_", " ").title()
                voice_info["name"] = f"{name_part} ({type_name})"
                voice_info["language"] = language
                voice_info["gender"] = gender
                break

        return voice_info

    def _get_default_voices(self) -> list[dict]:
        """Return default Kokoro voices."""
        return [
            {"id": "af_bella", "name": "Bella (American Female)", "language": "en-US", "gender": "female"},
            {"id": "af_sarah", "name": "Sarah (American Female)", "language": "en-US", "gender": "female"},
            {"id": "af_nicole", "name": "Nicole (American Female)", "language": "en-US", "gender": "female"},
            {"id": "af_sky", "name": "Sky (American Female)", "language": "en-US", "gender": "female"},
            {"id": "am_adam", "name": "Adam (American Male)", "language": "en-US", "gender": "male"},
            {"id": "am_michael", "name": "Michael (American Male)", "language": "en-US", "gender": "male"},
            {"id": "bf_emma", "name": "Emma (British Female)", "language": "en-GB", "gender": "female"},
            {"id": "bf_isabella", "name": "Isabella (British Female)", "language": "en-GB", "gender": "female"},
            {"id": "bm_george", "name": "George (British Male)", "language": "en-GB", "gender": "male"},
            {"id": "bm_lewis", "name": "Lewis (British Male)", "language": "en-GB", "gender": "male"},
        ]

    async def health_check(self) -> bool:
        """Check if Kokoro TTS is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try health endpoint first
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    return True
                # Fallback to voices endpoint
                response = await client.get(f"{self.base_url}/v1/audio/voices")
                return response.status_code == 200
        except Exception:
            return False

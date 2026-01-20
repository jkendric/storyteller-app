"""Coqui XTTS provider implementation with voice cloning support."""

import httpx
import aiofiles
import base64
from typing import Optional, AsyncGenerator
from pathlib import Path

from app.services.tts.base import BaseTTSProvider


class CoquiXTTSProvider(BaseTTSProvider):
    """Coqui XTTS provider with voice cloning (OpenAI-compatible, port 8000)."""

    @property
    def provider_type(self) -> str:
        return "coqui_xtts"

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_voice_cloning(self) -> bool:
        return True

    async def generate_audio(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        voice_clone_path: Optional[str] = None,
    ) -> dict:
        """Generate audio from text using XTTS."""
        voice = voice or self.default_voice
        language = self.settings.get("language", "en")

        async with httpx.AsyncClient(timeout=180.0) as client:
            # If voice cloning is requested and we have a reference audio
            if voice_clone_path and Path(voice_clone_path).exists():
                # Use XTTS clone endpoint with reference audio
                return await self._generate_with_clone(
                    client, text, voice_clone_path, language, speed
                )
            else:
                # Use OpenAI-compatible endpoint for standard voices
                return await self._generate_standard(
                    client, text, voice, language, speed
                )

    async def _generate_standard(
        self,
        client: httpx.AsyncClient,
        text: str,
        voice: Optional[str],
        language: str,
        speed: float,
    ) -> dict:
        """Generate audio using standard XTTS voice."""
        payload = {
            "model": "xtts",
            "input": text,
            "voice": voice or "default",
            "speed": speed,
            "response_format": "mp3",
        }

        # Add language if supported
        if language:
            payload["language"] = language

        response = await client.post(
            f"{self.base_url}/v1/audio/speech",
            json=payload,
        )
        response.raise_for_status()

        filename, filepath = self._generate_filename("mp3")

        async with aiofiles.open(filepath, "wb") as f:
            await f.write(response.content)

        return {
            "audio_url": f"/audio/{filename}",
            "filename": filename,
        }

    async def _generate_with_clone(
        self,
        client: httpx.AsyncClient,
        text: str,
        reference_audio_path: str,
        language: str,
        speed: float,
    ) -> dict:
        """Generate audio using voice cloning with reference audio."""
        # Read the reference audio file
        async with aiofiles.open(reference_audio_path, "rb") as f:
            reference_audio = await f.read()

        # XTTS clone API expects the reference audio
        # Try the /tts_to_audio endpoint first (common XTTS API)
        try:
            payload = {
                "text": text,
                "speaker_wav": base64.b64encode(reference_audio).decode("utf-8"),
                "language": language,
                "speed": speed,
            }

            response = await client.post(
                f"{self.base_url}/tts_to_audio",
                json=payload,
            )

            if response.status_code == 200:
                filename, filepath = self._generate_filename("wav")
                async with aiofiles.open(filepath, "wb") as f:
                    await f.write(response.content)
                return {
                    "audio_url": f"/audio/{filename}",
                    "filename": filename,
                }
        except Exception:
            pass

        # Fallback: Try /clone endpoint (alternative XTTS API format)
        files = {
            "text": (None, text),
            "language": (None, language),
            "speaker_wav": ("reference.wav", reference_audio, "audio/wav"),
        }

        response = await client.post(
            f"{self.base_url}/clone",
            files=files,
        )
        response.raise_for_status()

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
        """Stream audio from XTTS."""
        voice = voice or self.default_voice
        language = self.settings.get("language", "en")

        payload = {
            "model": "xtts",
            "input": text,
            "voice": voice or "default",
            "speed": speed,
            "response_format": "mp3",
            "stream": True,
        }

        if language:
            payload["language"] = language

        async with httpx.AsyncClient(timeout=180.0) as client:
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
        """List available XTTS voices."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try OpenAI-compatible voices endpoint
                response = await client.get(f"{self.base_url}/v1/audio/voices")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("voices", [])

                # Try XTTS-specific speakers endpoint
                response = await client.get(f"{self.base_url}/speakers")
                if response.status_code == 200:
                    data = response.json()
                    voices = []
                    for speaker in data:
                        if isinstance(speaker, dict):
                            voices.append({
                                "id": speaker.get("name", speaker.get("id")),
                                "name": speaker.get("name", "Unknown"),
                                "language": speaker.get("language", "en"),
                                "gender": speaker.get("gender", "unknown"),
                            })
                        else:
                            voices.append({
                                "id": speaker,
                                "name": speaker,
                                "language": "en",
                                "gender": "unknown",
                            })
                    return voices
        except Exception:
            pass

        # Return default XTTS voices as fallback
        return [
            {"id": "default", "name": "Default XTTS Voice", "language": "en", "gender": "unknown"},
        ]

    async def health_check(self) -> bool:
        """Check if XTTS is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try health endpoint
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    return True
                # Try speakers endpoint
                response = await client.get(f"{self.base_url}/speakers")
                if response.status_code == 200:
                    return True
                # Try voices endpoint
                response = await client.get(f"{self.base_url}/v1/audio/voices")
                return response.status_code == 200
        except Exception:
            return False

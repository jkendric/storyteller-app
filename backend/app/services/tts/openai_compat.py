"""Generic OpenAI-compatible TTS provider implementation."""

import httpx
import aiofiles
from typing import Optional, AsyncGenerator

from app.services.tts.base import BaseTTSProvider


class OpenAICompatProvider(BaseTTSProvider):
    """Generic OpenAI-compatible TTS provider."""

    @property
    def provider_type(self) -> str:
        return "openai_compatible"

    @property
    def supports_streaming(self) -> bool:
        # Can be overridden via settings
        return self.settings.get("supports_streaming", True)

    @property
    def supports_voice_cloning(self) -> bool:
        return self.settings.get("supports_voice_cloning", False)

    async def generate_audio(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        voice_clone_path: Optional[str] = None,
    ) -> dict:
        """Generate audio from text using OpenAI-compatible API."""
        voice = voice or self.default_voice or "default"
        model = self.settings.get("model", "tts-1")
        response_format = self.settings.get("response_format", "mp3")

        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": response_format,
        }

        # Add any extra parameters from settings
        extra_params = self.settings.get("extra_params", {})
        payload.update(extra_params)

        headers = {}
        api_key = self.settings.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/audio/speech",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

            # Determine file extension from response format
            ext = response_format if response_format in ["mp3", "wav", "opus", "aac", "flac"] else "mp3"
            filename, filepath = self._generate_filename(ext)

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
        """Stream audio from OpenAI-compatible API."""
        if not self.supports_streaming:
            raise NotImplementedError("This provider does not support streaming")

        voice = voice or self.default_voice or "default"
        model = self.settings.get("model", "tts-1")
        response_format = self.settings.get("response_format", "mp3")

        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": response_format,
            "stream": True,
        }

        extra_params = self.settings.get("extra_params", {})
        payload.update(extra_params)

        headers = {}
        api_key = self.settings.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/audio/speech",
                json=payload,
                headers=headers,
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes(chunk_size=4096):
                    if chunk:
                        yield chunk

    async def list_voices(self) -> list[dict]:
        """List available voices."""
        try:
            headers = {}
            api_key = self.settings.get("api_key")
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/v1/audio/voices",
                    headers=headers,
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("voices", [])
        except Exception:
            pass

        # Return generic voices if not available from API
        return [
            {"id": "alloy", "name": "Alloy", "language": "en", "gender": "neutral"},
            {"id": "echo", "name": "Echo", "language": "en", "gender": "male"},
            {"id": "fable", "name": "Fable", "language": "en", "gender": "female"},
            {"id": "onyx", "name": "Onyx", "language": "en", "gender": "male"},
            {"id": "nova", "name": "Nova", "language": "en", "gender": "female"},
            {"id": "shimmer", "name": "Shimmer", "language": "en", "gender": "female"},
        ]

    async def health_check(self) -> bool:
        """Check if the TTS provider is available."""
        try:
            headers = {}
            api_key = self.settings.get("api_key")
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try health endpoint first
                response = await client.get(f"{self.base_url}/health", headers=headers)
                if response.status_code == 200:
                    return True
                # Try voices endpoint
                response = await client.get(f"{self.base_url}/v1/audio/voices", headers=headers)
                if response.status_code == 200:
                    return True
                # Try models endpoint (common in OpenAI-compatible APIs)
                response = await client.get(f"{self.base_url}/v1/models", headers=headers)
                return response.status_code == 200
        except Exception:
            return False

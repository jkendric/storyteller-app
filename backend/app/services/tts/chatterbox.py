"""Chatterbox TTS provider implementation with voice cloning support."""

import httpx
import aiofiles
from typing import Optional, AsyncGenerator
from pathlib import Path

from app.services.tts.base import BaseTTSProvider


class ChatterboxProvider(BaseTTSProvider):
    """Chatterbox TTS provider with voice cloning (native API on port 8000)."""

    @property
    def provider_type(self) -> str:
        return "chatterbox"

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
        """Generate audio from text using Chatterbox TTS."""
        # Get settings with defaults
        output_format = self.settings.get("output_format", "wav")
        temperature = self.settings.get("temperature", 1.0)
        exaggeration = self.settings.get("exaggeration", 1.0)
        cfg_weight = self.settings.get("cfg_weight", 0.5)
        language = self.settings.get("language", "en")
        seed = self.settings.get("seed")

        # Build base payload
        payload = {
            "text": text,
            "output_format": output_format,
            "speed_factor": speed,
            "temperature": temperature,
            "exaggeration": exaggeration,
            "cfg_weight": cfg_weight,
            "language": language,
        }

        if seed is not None:
            payload["seed"] = seed

        async with httpx.AsyncClient(timeout=180.0) as client:
            # If voice cloning is requested with a local reference file
            if voice_clone_path and Path(voice_clone_path).exists():
                return await self._generate_with_clone(
                    client, payload, voice_clone_path
                )
            else:
                # Use predefined voice
                voice = voice or self.default_voice
                return await self._generate_with_predefined(client, payload, voice)

    async def _generate_with_predefined(
        self,
        client: httpx.AsyncClient,
        payload: dict,
        voice: Optional[str],
    ) -> dict:
        """Generate audio using a predefined Chatterbox voice.

        Supports both OpenAI-compatible API (travisvn/chatterbox-tts-api)
        and devnen/Chatterbox-TTS-Server endpoints.
        """
        # Try travisvn/chatterbox-tts-api endpoint first, then OpenAI-compatible,
        # then fall back to devnen-style endpoints
        endpoints = ["/audio/speech", "/v1/audio/speech", "/tts", "/generate"]
        last_error = None

        for endpoint in endpoints:
            try:
                if endpoint in ("/audio/speech", "/v1/audio/speech"):
                    # OpenAI-compatible format (travisvn and standard OpenAI APIs)
                    openai_payload = {
                        "model": "chatterbox",
                        "input": payload["text"],
                        "voice": voice or "default",
                        "speed": payload.get("speed_factor", 1.0),
                        "response_format": "mp3",  # Use MP3 for better streaming
                    }
                    response = await client.post(
                        f"{self.base_url}{endpoint}",
                        json=openai_payload,
                    )
                else:
                    # devnen-style payload
                    devnen_payload = payload.copy()
                    devnen_payload["voice_mode"] = "predefined"
                    voice_id = voice or "Abigail.wav"
                    devnen_payload["predefined_voice_id"] = voice_id
                    response = await client.post(
                        f"{self.base_url}{endpoint}",
                        json=devnen_payload,
                    )

                if response.status_code == 200:
                    break
                elif response.status_code in (404, 422):
                    # 404 = endpoint doesn't exist, 422 = wrong payload format
                    continue  # Try next endpoint
                else:
                    response.raise_for_status()
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code not in (404, 422):
                    raise
            except httpx.ConnectError as e:
                raise Exception(f"Cannot connect to Chatterbox server at {self.base_url}: {e}")
        else:
            if last_error:
                raise last_error
            raise Exception(f"No working TTS endpoint found at {self.base_url}")

        response.raise_for_status()

        # Determine file extension based on which endpoint was used
        # OpenAI-compatible endpoints return MP3, devnen endpoints return configured format
        if endpoint in ("/audio/speech", "/v1/audio/speech"):
            extension = "mp3"
        else:
            output_format = payload.get("output_format", "wav")
            extension = "ogg" if output_format == "opus" else output_format

        filename, filepath = self._generate_filename(extension)

        async with aiofiles.open(filepath, "wb") as f:
            await f.write(response.content)

        return {
            "audio_url": f"/audio/{filename}",
            "filename": filename,
        }

    async def _generate_with_clone(
        self,
        client: httpx.AsyncClient,
        payload: dict,
        reference_audio_path: str,
    ) -> dict:
        """Generate audio using voice cloning with uploaded reference audio."""
        # First, upload the reference audio to Chatterbox server
        ref_path = Path(reference_audio_path)

        async with aiofiles.open(reference_audio_path, "rb") as f:
            reference_audio = await f.read()

        # Upload reference file to Chatterbox
        files = {
            "file": (ref_path.name, reference_audio, "audio/wav"),
        }

        upload_response = await client.post(
            f"{self.base_url}/upload_reference",
            files=files,
        )

        if upload_response.status_code == 200:
            # Get the filename from the response or use the original name
            upload_data = upload_response.json()
            reference_filename = upload_data.get("filename", ref_path.name)
        else:
            # Fallback: assume the file is already on the server with same name
            reference_filename = ref_path.name

        # Generate with clone mode
        payload["voice_mode"] = "clone"
        payload["reference_audio_filename"] = reference_filename

        response = await client.post(
            f"{self.base_url}/tts",
            json=payload,
        )
        response.raise_for_status()

        # Determine file extension from output format
        output_format = payload.get("output_format", "wav")
        extension = "ogg" if output_format == "opus" else output_format

        filename, filepath = self._generate_filename(extension)

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
        """Stream audio from Chatterbox TTS.

        Tries multiple endpoints in order:
        1. /audio/speech/stream (travisvn/chatterbox-tts-api dedicated stream endpoint)
        2. /audio/speech with stream=True (travisvn)
        3. /v1/audio/speech with stream=True (OpenAI-compatible)

        Uses MP3 format for proper streaming support with natural frame boundaries.
        """
        voice_id = voice or self.default_voice or "default"

        payload = {
            "model": "chatterbox",
            "input": text,
            "voice": voice_id,
            "speed": speed,
            "response_format": "mp3",
            "stream": True,
        }

        # Try streaming endpoints in order of preference
        stream_endpoints = [
            "/audio/speech/stream",  # travisvn dedicated streaming endpoint
            "/audio/speech",         # travisvn with stream param
            "/v1/audio/speech",      # OpenAI-compatible
        ]

        # Get chunk size from settings (default 4096)
        chunk_size = self.settings.get("chunk_size", 4096)

        async with httpx.AsyncClient(timeout=180.0) as client:
            for endpoint in stream_endpoints:
                try:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}{endpoint}",
                        json=payload,
                    ) as response:
                        if response.status_code in (404, 422):
                            continue  # Try next endpoint
                        response.raise_for_status()
                        async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                            if chunk:
                                yield chunk
                        return  # Successfully streamed
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (404, 422):
                        continue  # Try next endpoint
                    raise

            # If all endpoints failed, raise an error
            raise Exception(f"No working streaming endpoint found at {self.base_url}")

    async def list_voices(self) -> list[dict]:
        """List available Chatterbox predefined voices.

        Supports travisvn/chatterbox-tts-api, OpenAI-compatible APIs,
        and devnen/Chatterbox-TTS-Server endpoints.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try travisvn endpoint first
                response = await client.get(f"{self.base_url}/voices")
                if response.status_code == 200:
                    data = response.json()
                    voices = data.get("voices", [])
                    if voices:
                        return self._normalize_voice_list(voices)

                # Try OpenAI-compatible endpoint
                response = await client.get(f"{self.base_url}/v1/audio/voices")
                if response.status_code == 200:
                    data = response.json()
                    voices = data.get("voices", [])
                    if voices:
                        return self._normalize_voice_list(voices)

                # Fall back to devnen API endpoint
                response = await client.get(f"{self.base_url}/get_predefined_voices")
                if response.status_code == 200:
                    data = response.json()
                    voices = []

                    if isinstance(data, list):
                        for voice in data:
                            voices.append(self._parse_voice(voice))
                    elif isinstance(data, dict):
                        # Check for common wrapper keys
                        if "voices" in data:
                            for voice in data["voices"]:
                                voices.append(self._parse_voice(voice))
                        elif "predefined_voices" in data:
                            for voice in data["predefined_voices"]:
                                voices.append(self._parse_voice(voice))
                        else:
                            # Dict with voice IDs as keys: {"voice_id": {...}, ...}
                            for voice_id, voice_data in data.items():
                                if isinstance(voice_data, dict):
                                    voices.append({
                                        "id": voice_id,
                                        "name": voice_data.get("name", voice_id),
                                        "language": voice_data.get("language", "en"),
                                        "gender": voice_data.get("gender", "unknown"),
                                    })
                                else:
                                    voices.append({
                                        "id": voice_id,
                                        "name": voice_id,
                                        "language": "en",
                                        "gender": "unknown",
                                    })

                    return voices if voices else [{"id": "default", "name": "Default Voice", "language": "en", "gender": "unknown"}]
        except Exception:
            pass

        # Return default placeholder if API fails
        return [
            {"id": "default", "name": "Default Voice", "language": "en", "gender": "unknown"},
        ]

    def _normalize_voice_list(self, voices: list) -> list[dict]:
        """Normalize voice list from OpenAI-compatible API."""
        normalized = []
        for v in voices:
            if isinstance(v, str):
                normalized.append({
                    "id": v,
                    "name": v,
                    "language": "en",
                    "gender": "unknown",
                })
            elif isinstance(v, dict):
                normalized.append({
                    "id": v.get("id", v.get("voice_id", "unknown")),
                    "name": v.get("name", v.get("id", "unknown")),
                    "language": v.get("language", "en"),
                    "gender": v.get("gender", "unknown"),
                })
        return normalized if normalized else [{"id": "default", "name": "Default Voice", "language": "en", "gender": "unknown"}]

    def _parse_voice(self, voice) -> dict:
        """Parse a voice entry from various formats."""
        if isinstance(voice, str):
            return {
                "id": voice,
                "name": voice,
                "language": "en",
                "gender": "unknown",
            }
        elif isinstance(voice, dict):
            # Chatterbox format: {"display_name": "Abigail", "filename": "Abigail.wav"}
            # The predefined_voice_id must be the filename (e.g., "Abigail.wav")
            voice_id = (
                voice.get("filename") or  # Chatterbox uses filename as the ID
                voice.get("id") or
                voice.get("voice_id") or
                voice.get("name") or
                voice.get("voice_name") or
                "unknown"
            )
            voice_name = (
                voice.get("display_name") or  # Chatterbox uses display_name
                voice.get("name") or
                voice.get("voice_name") or
                voice.get("id") or
                voice.get("voice_id") or
                voice_id
            )
            return {
                "id": voice_id,
                "name": voice_name,
                "language": voice.get("language", voice.get("lang", "en")),
                "gender": voice.get("gender", "unknown"),
            }
        else:
            return {
                "id": str(voice),
                "name": str(voice),
                "language": "en",
                "gender": "unknown",
            }

    async def get_reference_files(self) -> list[str]:
        """Get list of uploaded reference audio files from Chatterbox server."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/get_reference_files")
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        return data.get("files", [])
        except Exception:
            pass
        return []

    async def health_check(self) -> bool:
        """Check if Chatterbox TTS is available and model is loaded.

        Supports travisvn/chatterbox-tts-api, OpenAI-compatible APIs,
        and devnen/Chatterbox-TTS-Server endpoints.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try travisvn health endpoint first - checks if model is loaded
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    try:
                        data = response.json()
                        # travisvn API returns model_loaded status
                        if isinstance(data, dict) and "model_loaded" in data:
                            return data.get("model_loaded", False)
                    except Exception:
                        pass
                    return True

                # Try travisvn voices endpoint
                response = await client.get(f"{self.base_url}/voices")
                if response.status_code == 200:
                    return True

                # Try OpenAI-compatible voices endpoint
                response = await client.get(f"{self.base_url}/v1/audio/voices")
                if response.status_code == 200:
                    return True

                # Fallback to devnen API endpoints
                response = await client.get(f"{self.base_url}/api/ui/initial-data")
                if response.status_code == 200:
                    return True

                response = await client.get(f"{self.base_url}/get_predefined_voices")
                if response.status_code == 200:
                    return True

                # Final fallback to root
                response = await client.get(f"{self.base_url}/")
                return response.status_code == 200
        except Exception:
            return False

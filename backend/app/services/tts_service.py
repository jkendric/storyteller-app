import httpx
import uuid
import aiofiles
from pathlib import Path
from typing import Optional
from app.config import get_settings

settings = get_settings()


class TTSService:
    """Service for interacting with Kokoro TTS (OpenAI-compatible API)."""

    def __init__(self):
        self.base_url = settings.kokoro_tts_url
        self.default_voice = settings.tts_default_voice
        self.audio_dir = Path("./data/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    async def generate_audio(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
    ) -> dict:
        """Generate audio from text using Kokoro TTS."""
        voice = voice or self.default_voice

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
            filename = f"{uuid.uuid4()}.mp3"
            filepath = self.audio_dir / filename

            async with aiofiles.open(filepath, "wb") as f:
                await f.write(response.content)

            return {
                "audio_url": f"/audio/{filename}",
                "filename": filename,
            }

    async def list_voices(self) -> list[dict]:
        """List available TTS voices."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/v1/audio/voices")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("voices", [])
        except Exception:
            pass

        # Return default voices if API not available
        return [
            {"id": "af_bella", "name": "Bella (American Female)", "language": "en-US", "gender": "female"},
            {"id": "af_sarah", "name": "Sarah (American Female)", "language": "en-US", "gender": "female"},
            {"id": "am_adam", "name": "Adam (American Male)", "language": "en-US", "gender": "male"},
            {"id": "am_michael", "name": "Michael (American Male)", "language": "en-US", "gender": "male"},
            {"id": "bf_emma", "name": "Emma (British Female)", "language": "en-GB", "gender": "female"},
            {"id": "bm_george", "name": "George (British Male)", "language": "en-GB", "gender": "male"},
        ]

    async def health_check(self) -> bool:
        """Check if Kokoro TTS is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False


# Singleton instance
tts_service = TTSService()

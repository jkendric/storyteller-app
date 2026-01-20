"""TTS service module with multi-provider support."""

from app.services.tts.base import BaseTTSProvider
from app.services.tts.kokoro import KokoroProvider
from app.services.tts.piper import PiperProvider
from app.services.tts.coqui_xtts import CoquiXTTSProvider
from app.services.tts.openai_compat import OpenAICompatProvider
from app.services.tts.chatterbox import ChatterboxProvider
from app.services.tts.unified import UnifiedTTSService
from app.services.tts.manager import TTSProviderManager

__all__ = [
    "BaseTTSProvider",
    "KokoroProvider",
    "PiperProvider",
    "CoquiXTTSProvider",
    "OpenAICompatProvider",
    "ChatterboxProvider",
    "UnifiedTTSService",
    "TTSProviderManager",
]

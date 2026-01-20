from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    server_port: int = 8001

    # Database
    database_url: str = "sqlite:///./data/storyteller.db"

    # Ollama LLM
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # Kokoro TTS
    kokoro_tts_url: str = "http://localhost:8880"
    tts_default_voice: str = "af_bella"

    # Story Generation
    episode_target_words: int = 1250

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import get_settings
from app.database import init_db, SessionLocal
from app.routers import (
    characters_router,
    scenarios_router,
    stories_router,
    episodes_router,
    tts_router,
    settings_router,
    tts_settings_router,
    speed_buttons_router,
)
from app.models.llm_provider import LLMProvider, ProviderType
from app.models.tts_provider import TTSProvider, TTSProviderType
from app.models.speed_button import SpeedButton
from app.services.llm_service import llm_service, ProviderManager
from app.services.tts.unified import unified_tts_service

settings = get_settings()

app = FastAPI(
    title="Storyteller API",
    description="Dynamic Story Generation Platform",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for audio
audio_dir = Path("./data/audio")
audio_dir.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(audio_dir)), name="audio")

# Include routers
app.include_router(characters_router)
app.include_router(scenarios_router)
app.include_router(stories_router)
app.include_router(episodes_router)
app.include_router(tts_router)
app.include_router(settings_router)
app.include_router(tts_settings_router)
app.include_router(speed_buttons_router)


DEFAULT_SPEED_BUTTONS = [
    {
        "label": "Action Scene",
        "guidance": "Focus on dynamic action, tension, and physical conflict. Emphasize movement, stakes, and consequences.",
        "use_alternate": False,
        "display_order": 0,
    },
    {
        "label": "Dialogue Focus",
        "guidance": "Emphasize character conversations and verbal exchanges. Reveal personality through speech patterns and reactions.",
        "use_alternate": False,
        "display_order": 1,
    },
    {
        "label": "Emotional Scene",
        "guidance": "Deep dive into character emotions and internal conflict. Explore feelings, relationships, and personal stakes.",
        "use_alternate": False,
        "display_order": 2,
    },
    {
        "label": "Plot Twist",
        "guidance": "Introduce surprising revelations or unexpected turns. Subvert expectations while maintaining narrative logic.",
        "use_alternate": False,
        "display_order": 3,
    },
]


def init_default_speed_buttons():
    """Create default speed button presets if none exist."""
    db = SessionLocal()
    try:
        if db.query(SpeedButton).count() == 0:
            for button_data in DEFAULT_SPEED_BUTTONS:
                button = SpeedButton(
                    label=button_data["label"],
                    guidance=button_data["guidance"],
                    use_alternate=button_data["use_alternate"],
                    display_order=button_data["display_order"],
                    is_default=True,
                )
                db.add(button)
            db.commit()
    finally:
        db.close()


def init_default_providers():
    """Create default Ollama and Kokoro providers if no providers exist."""
    db = SessionLocal()
    try:
        # Initialize default LLM provider
        if db.query(LLMProvider).count() == 0:
            default_provider = LLMProvider(
                name="Ollama (Default)",
                provider_type=ProviderType.OLLAMA,
                base_url=settings.ollama_base_url,
                default_model=settings.ollama_model,
                is_default=True,
                is_alternate=False,
                enabled=True,
            )
            db.add(default_provider)
            db.commit()

        # Initialize default TTS provider
        if db.query(TTSProvider).count() == 0:
            default_tts_provider = TTSProvider(
                name="Kokoro TTS (Default)",
                provider_type=TTSProviderType.KOKORO,
                base_url=settings.kokoro_tts_url,
                default_voice=settings.tts_default_voice,
                supports_streaming=True,
                supports_voice_cloning=False,
                is_default=True,
                enabled=True,
            )
            db.add(default_tts_provider)
            db.commit()
    finally:
        db.close()


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()
    init_default_providers()
    init_default_speed_buttons()


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    db = SessionLocal()
    try:
        # Check all enabled LLM providers
        llm_providers = db.query(LLMProvider).filter(LLMProvider.enabled == True).all()
        llm_provider_statuses = {}

        for provider in llm_providers:
            status = await llm_service.health_check(provider)
            role = []
            if provider.is_default:
                role.append("default")
            if provider.is_alternate:
                role.append("alternate")
            llm_provider_statuses[provider.name] = {
                "status": "connected" if status else "disconnected",
                "role": role if role else None,
            }

        # Legacy fallback check
        if not llm_providers:
            legacy_status = await llm_service.health_check()
            llm_provider_statuses["ollama (legacy)"] = "connected" if legacy_status else "disconnected"

        # Check all TTS providers
        tts_provider_statuses = await unified_tts_service.health_check_all(db)

        return {
            "status": "healthy",
            "services": {
                "llm_providers": llm_provider_statuses,
                "tts_providers": tts_provider_statuses,
            },
        }
    finally:
        db.close()


@app.get("/api/models")
async def list_models():
    """List available Ollama models."""
    try:
        models = await llm_service.list_models()
        return {"models": models}
    except Exception as e:
        return {"models": [], "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.server_port)

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
)
from app.models.llm_provider import LLMProvider, ProviderType
from app.services.llm_service import llm_service, ProviderManager
from app.services.tts_service import tts_service

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


def init_default_providers():
    """Create default Ollama provider if no providers exist."""
    db = SessionLocal()
    try:
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
    finally:
        db.close()


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()
    init_default_providers()


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    db = SessionLocal()
    try:
        # Check all enabled providers
        providers = db.query(LLMProvider).filter(LLMProvider.enabled == True).all()
        provider_statuses = {}

        for provider in providers:
            status = await llm_service.health_check(provider)
            role = []
            if provider.is_default:
                role.append("default")
            if provider.is_alternate:
                role.append("alternate")
            provider_statuses[provider.name] = {
                "status": "connected" if status else "disconnected",
                "role": role if role else None,
            }

        # Legacy fallback check
        if not providers:
            legacy_status = await llm_service.health_check()
            provider_statuses["ollama (legacy)"] = "connected" if legacy_status else "disconnected"

        tts_status = await tts_service.health_check()

        return {
            "status": "healthy",
            "services": {
                "providers": provider_statuses,
                "tts": "connected" if tts_status else "disconnected",
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
    uvicorn.run(app, host="0.0.0.0", port=8000)

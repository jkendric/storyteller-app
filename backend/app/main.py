from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import get_settings
from app.database import init_db
from app.routers import (
    characters_router,
    scenarios_router,
    stories_router,
    episodes_router,
    tts_router,
)
from app.services.llm_service import llm_service
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


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    ollama_status = await llm_service.health_check()
    tts_status = await tts_service.health_check()

    return {
        "status": "healthy",
        "services": {
            "ollama": "connected" if ollama_status else "disconnected",
            "tts": "connected" if tts_status else "disconnected",
        },
    }


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

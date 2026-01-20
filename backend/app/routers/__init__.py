from app.routers.characters import router as characters_router
from app.routers.scenarios import router as scenarios_router
from app.routers.stories import router as stories_router
from app.routers.episodes import router as episodes_router
from app.routers.tts import router as tts_router

__all__ = [
    "characters_router",
    "scenarios_router",
    "stories_router",
    "episodes_router",
    "tts_router",
]

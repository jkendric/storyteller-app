from app.routers.characters import router as characters_router
from app.routers.scenarios import router as scenarios_router
from app.routers.stories import router as stories_router
from app.routers.episodes import router as episodes_router
from app.routers.tts import router as tts_router
from app.routers.settings import router as settings_router
from app.routers.tts_settings import router as tts_settings_router
from app.routers.speed_buttons import router as speed_buttons_router

__all__ = [
    "characters_router",
    "scenarios_router",
    "stories_router",
    "episodes_router",
    "tts_router",
    "settings_router",
    "tts_settings_router",
    "speed_buttons_router",
]

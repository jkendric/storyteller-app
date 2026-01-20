import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.models import Story, Episode
from app.schemas import (
    EpisodeCreate,
    EpisodeUpdate,
    EpisodeResponse,
    EpisodeList,
    EpisodeGenerateRequest,
)
from app.services.story_service import story_service

router = APIRouter(prefix="/api/stories/{story_id}/episodes", tags=["episodes"])


@router.get("", response_model=EpisodeList)
def list_episodes(
    story_id: int,
    db: Session = Depends(get_db),
):
    """List all episodes for a story."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    episodes = (
        db.query(Episode)
        .filter(Episode.story_id == story_id)
        .order_by(Episode.number)
        .all()
    )
    return EpisodeList(episodes=episodes, total=len(episodes))


@router.get("/{episode_number}", response_model=EpisodeResponse)
def get_episode(
    story_id: int,
    episode_number: int,
    db: Session = Depends(get_db),
):
    """Get a specific episode by number."""
    episode = (
        db.query(Episode)
        .filter(Episode.story_id == story_id, Episode.number == episode_number)
        .first()
    )
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode


@router.put("/{episode_number}", response_model=EpisodeResponse)
def update_episode(
    story_id: int,
    episode_number: int,
    episode_update: EpisodeUpdate,
    db: Session = Depends(get_db),
):
    """Update an episode."""
    episode = (
        db.query(Episode)
        .filter(Episode.story_id == story_id, Episode.number == episode_number)
        .first()
    )
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    update_data = episode_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(episode, field, value)

    if "content" in update_data:
        episode.word_count = len(episode.content.split()) if episode.content else 0

    db.commit()
    db.refresh(episode)
    return episode


@router.delete("/{episode_number}", status_code=status.HTTP_204_NO_CONTENT)
def delete_episode(
    story_id: int,
    episode_number: int,
    db: Session = Depends(get_db),
):
    """Delete an episode (only the last episode can be deleted)."""
    episode = (
        db.query(Episode)
        .filter(Episode.story_id == story_id, Episode.number == episode_number)
        .first()
    )
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Check if this is the last episode
    max_episode = (
        db.query(Episode)
        .filter(Episode.story_id == story_id)
        .order_by(Episode.number.desc())
        .first()
    )
    if max_episode and max_episode.number != episode_number:
        raise HTTPException(
            status_code=400,
            detail="Only the last episode can be deleted",
        )

    db.delete(episode)
    db.commit()


@router.post("/generate")
async def generate_episode(
    story_id: int,
    request: EpisodeGenerateRequest,
    db: Session = Depends(get_db),
):
    """Generate a new episode with SSE streaming."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    async def event_generator():
        async for event in story_service.generate_episode_stream(
            db=db,
            story_id=story_id,
            guidance=request.guidance,
            target_words=request.target_words,
        ):
            event_type = event.get("event", "message")
            data = event.get("data", "")

            if isinstance(data, dict):
                data = json.dumps(data)

            yield {
                "event": event_type,
                "data": data,
            }

    return EventSourceResponse(event_generator())

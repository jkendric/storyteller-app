from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Story, StoryCharacter, Episode
from app.models.story import StoryStatus
from app.schemas import (
    StoryCreate,
    StoryUpdate,
    StoryResponse,
    StoryList,
    StoryCharacterResponse,
    StoryForkRequest,
    StoryTreeResponse,
)
from app.services.story_service import story_service

router = APIRouter(prefix="/api/stories", tags=["stories"])


def _story_to_response(db: Session, story: Story) -> dict:
    """Convert story model to response dict."""
    episode_count = db.query(Episode).filter(Episode.story_id == story.id).count()
    characters = []
    for sc in story.story_characters:
        characters.append(
            StoryCharacterResponse(
                id=sc.id,
                character_id=sc.character_id,
                role=sc.role,
                character_name=sc.character.name if sc.character else None,
            )
        )
    return {
        "id": story.id,
        "title": story.title,
        "scenario_id": story.scenario_id,
        "status": story.status,
        "parent_story_id": story.parent_story_id,
        "fork_from_episode": story.fork_from_episode,
        "created_at": story.created_at,
        "updated_at": story.updated_at,
        "episode_count": episode_count,
        "characters": characters,
    }


@router.get("", response_model=StoryList)
def list_stories(
    skip: int = 0,
    limit: int = 100,
    status_filter: StoryStatus | None = None,
    db: Session = Depends(get_db),
):
    """List all stories with pagination."""
    query = db.query(Story)
    if status_filter:
        query = query.filter(Story.status == status_filter)

    stories = query.offset(skip).limit(limit).all()
    total = query.count()

    story_responses = [_story_to_response(db, s) for s in stories]
    return StoryList(stories=story_responses, total=total)


@router.post("", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
def create_story(
    story: StoryCreate,
    db: Session = Depends(get_db),
):
    """Create a new story with characters."""
    # Create story
    db_story = Story(
        title=story.title,
        scenario_id=story.scenario_id,
        status=StoryStatus.DRAFT,
    )
    db.add(db_story)
    db.commit()
    db.refresh(db_story)

    # Add characters
    for char in story.characters:
        story_char = StoryCharacter(
            story_id=db_story.id,
            character_id=char.character_id,
            role=char.role,
        )
        db.add(story_char)

    db.commit()
    db.refresh(db_story)
    return _story_to_response(db, db_story)


@router.get("/{story_id}", response_model=StoryResponse)
def get_story(
    story_id: int,
    db: Session = Depends(get_db),
):
    """Get a story by ID."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return _story_to_response(db, story)


@router.put("/{story_id}", response_model=StoryResponse)
def update_story(
    story_id: int,
    story_update: StoryUpdate,
    db: Session = Depends(get_db),
):
    """Update a story."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    update_data = story_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(story, field, value)

    db.commit()
    db.refresh(story)
    return _story_to_response(db, story)


@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_story(
    story_id: int,
    db: Session = Depends(get_db),
):
    """Delete a story and all its episodes."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Delete episodes first
    db.query(Episode).filter(Episode.story_id == story_id).delete()
    db.query(StoryCharacter).filter(StoryCharacter.story_id == story_id).delete()

    db.delete(story)
    db.commit()


@router.post("/{story_id}/fork", response_model=StoryResponse)
def fork_story(
    story_id: int,
    fork_request: StoryForkRequest,
    db: Session = Depends(get_db),
):
    """Fork a story from a specific episode."""
    try:
        forked_story = story_service.fork_story(
            db=db,
            story_id=story_id,
            from_episode=fork_request.from_episode,
            new_title=fork_request.new_title,
        )
        return _story_to_response(db, forked_story)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{story_id}/tree", response_model=StoryTreeResponse)
def get_story_tree(
    story_id: int,
    db: Session = Depends(get_db),
):
    """Get the fork tree for a story."""
    try:
        tree = story_service.get_story_tree(db, story_id)
        return StoryTreeResponse(root=tree)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

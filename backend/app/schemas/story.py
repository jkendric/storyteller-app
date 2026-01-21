from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal
from enum import Enum


class StoryStatus(str, Enum):
    """Story status enumeration."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class CharacterRole(str, Enum):
    """Character role in a story."""
    PROTAGONIST = "protagonist"
    SUPPORTING = "supporting"
    ANTAGONIST = "antagonist"


# Story generation settings types
TargetWordPreset = Literal["short", "medium", "long", "epic"]
WritingStyle = Literal["descriptive", "action", "dialogue", "balanced"]
MoodSetting = Literal["light", "moderate", "intense", "dark"]
PacingSetting = Literal["slow", "moderate", "fast"]


class StoryCharacterCreate(BaseModel):
    """Schema for adding a character to a story."""
    character_id: int
    role: CharacterRole = CharacterRole.SUPPORTING


class StoryCharacterResponse(BaseModel):
    """Schema for story character response."""
    id: int
    character_id: int
    role: CharacterRole
    character_name: Optional[str] = None

    class Config:
        from_attributes = True


class StoryBase(BaseModel):
    """Base story schema with common fields."""
    title: str = Field(..., min_length=1, max_length=255)
    scenario_id: int


class StoryCreate(StoryBase):
    """Schema for creating a new story."""
    characters: list[StoryCharacterCreate] = []
    # Generation settings (optional, defaults applied if not provided)
    target_word_preset: Optional[TargetWordPreset] = None
    temperature: Optional[float] = Field(None, ge=0.5, le=1.0)
    writing_style: Optional[WritingStyle] = None
    mood: Optional[MoodSetting] = None
    pacing: Optional[PacingSetting] = None


class StoryUpdate(BaseModel):
    """Schema for updating a story."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[StoryStatus] = None
    # Generation settings
    target_word_preset: Optional[TargetWordPreset] = None
    temperature: Optional[float] = Field(None, ge=0.5, le=1.0)
    writing_style: Optional[WritingStyle] = None
    mood: Optional[MoodSetting] = None
    pacing: Optional[PacingSetting] = None


class StoryResponse(StoryBase):
    """Schema for story response."""
    id: int
    status: StoryStatus
    parent_story_id: Optional[int] = None
    fork_from_episode: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    episode_count: int = 0
    characters: list[StoryCharacterResponse] = []
    # Generation settings
    target_word_preset: TargetWordPreset = "medium"
    temperature: float = 0.7
    writing_style: WritingStyle = "balanced"
    mood: MoodSetting = "moderate"
    pacing: PacingSetting = "moderate"

    class Config:
        from_attributes = True


class StoryList(BaseModel):
    """Schema for list of stories."""
    stories: list[StoryResponse]
    total: int


class StoryForkRequest(BaseModel):
    """Schema for forking a story."""
    from_episode: int = Field(..., ge=1)
    new_title: str = Field(..., min_length=1, max_length=255)


class StoryTreeNode(BaseModel):
    """Schema for a node in the story fork tree."""
    id: int
    title: str
    episode_count: int
    fork_from_episode: Optional[int] = None
    children: list["StoryTreeNode"] = []


class StoryTreeResponse(BaseModel):
    """Schema for story tree response."""
    root: StoryTreeNode

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class StreamEventType(str, Enum):
    """Types of SSE events during episode generation."""
    TOKEN = "token"
    SENTENCE = "sentence"
    COMPLETE = "complete"
    ERROR = "error"


class EpisodeBase(BaseModel):
    """Base episode schema with common fields."""
    title: Optional[str] = Field(None, max_length=255)
    guidance: Optional[str] = None


class EpisodeCreate(EpisodeBase):
    """Schema for creating a new episode."""
    content: Optional[str] = None
    summary: Optional[str] = None


class EpisodeUpdate(BaseModel):
    """Schema for updating an episode."""
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    summary: Optional[str] = None
    guidance: Optional[str] = None
    audio_url: Optional[str] = Field(None, max_length=512)


class EpisodeResponse(EpisodeBase):
    """Schema for episode response."""
    id: int
    story_id: int
    number: int
    content: Optional[str] = None
    summary: Optional[str] = None
    word_count: int
    audio_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EpisodeList(BaseModel):
    """Schema for list of episodes."""
    episodes: list[EpisodeResponse]
    total: int


class EpisodeGenerateRequest(BaseModel):
    """Schema for requesting episode generation."""
    guidance: Optional[str] = None
    target_words: Optional[int] = Field(None, ge=100, le=5000)
    use_alternate: bool = False  # Use alternate/uncensored provider


class EpisodeStreamEvent(BaseModel):
    """Schema for SSE stream events."""
    event: StreamEventType
    data: str
    episode_id: Optional[int] = None

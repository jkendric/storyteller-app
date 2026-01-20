from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MemoryStateBase(BaseModel):
    """Base memory state schema."""
    active_memory: Optional[str] = None
    background_memory: Optional[str] = None
    faded_memory: Optional[str] = None
    character_states: Optional[str] = None
    plot_threads: Optional[str] = None


class MemoryStateCreate(MemoryStateBase):
    """Schema for creating a memory state."""
    story_id: int
    episode_id: int


class MemoryStateUpdate(BaseModel):
    """Schema for updating a memory state."""
    active_memory: Optional[str] = None
    background_memory: Optional[str] = None
    faded_memory: Optional[str] = None
    character_states: Optional[str] = None
    plot_threads: Optional[str] = None


class MemoryStateResponse(MemoryStateBase):
    """Schema for memory state response."""
    id: int
    story_id: int
    episode_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

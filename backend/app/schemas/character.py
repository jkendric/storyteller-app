from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CharacterBase(BaseModel):
    """Base character schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    personality: Optional[str] = None
    motivations: Optional[str] = None
    backstory: Optional[str] = None
    relationships: Optional[str] = None


class CharacterCreate(CharacterBase):
    """Schema for creating a new character."""
    pass


class CharacterUpdate(BaseModel):
    """Schema for updating a character."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    personality: Optional[str] = None
    motivations: Optional[str] = None
    backstory: Optional[str] = None
    relationships: Optional[str] = None


class CharacterResponse(CharacterBase):
    """Schema for character response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CharacterList(BaseModel):
    """Schema for list of characters."""
    characters: list[CharacterResponse]
    total: int

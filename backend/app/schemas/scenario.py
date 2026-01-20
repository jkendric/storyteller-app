from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ScenarioBase(BaseModel):
    """Base scenario schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    setting: Optional[str] = None
    time_period: Optional[str] = Field(None, max_length=255)
    genre: Optional[str] = Field(None, max_length=255)
    tone: Optional[str] = Field(None, max_length=255)
    premise: Optional[str] = None
    themes: Optional[str] = None  # JSON array of themes
    world_rules: Optional[str] = None


class ScenarioCreate(ScenarioBase):
    """Schema for creating a new scenario."""
    pass


class ScenarioUpdate(BaseModel):
    """Schema for updating a scenario."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    setting: Optional[str] = None
    time_period: Optional[str] = Field(None, max_length=255)
    genre: Optional[str] = Field(None, max_length=255)
    tone: Optional[str] = Field(None, max_length=255)
    premise: Optional[str] = None
    themes: Optional[str] = None
    world_rules: Optional[str] = None


class ScenarioResponse(ScenarioBase):
    """Schema for scenario response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScenarioList(BaseModel):
    """Schema for list of scenarios."""
    scenarios: list[ScenarioResponse]
    total: int

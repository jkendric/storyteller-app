from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class SpeedButtonBase(BaseModel):
    """Base speed button schema with common fields."""
    label: str = Field(..., min_length=1, max_length=50)
    guidance: Optional[str] = None
    use_alternate: bool = False


class SpeedButtonCreate(SpeedButtonBase):
    """Schema for creating a new speed button."""
    display_order: Optional[int] = 0


class SpeedButtonUpdate(BaseModel):
    """Schema for updating a speed button."""
    label: Optional[str] = Field(None, min_length=1, max_length=50)
    guidance: Optional[str] = None
    use_alternate: Optional[bool] = None
    display_order: Optional[int] = None


class SpeedButtonResponse(SpeedButtonBase):
    """Schema for speed button response."""
    id: int
    display_order: int
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SpeedButtonList(BaseModel):
    """Schema for list of speed buttons."""
    speed_buttons: list[SpeedButtonResponse]
    total: int


class SpeedButtonReorder(BaseModel):
    """Schema for reordering speed buttons."""
    button_ids: list[int] = Field(..., description="List of button IDs in the desired order")

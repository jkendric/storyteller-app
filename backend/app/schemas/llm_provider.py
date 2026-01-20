from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class ProviderType(str, Enum):
    """LLM provider type enumeration."""
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"
    KOBOLDCPP = "koboldcpp"


class LLMProviderBase(BaseModel):
    """Base LLM provider schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    provider_type: ProviderType
    base_url: str = Field(..., min_length=1, max_length=255)
    default_model: Optional[str] = Field(None, max_length=100)
    is_default: bool = False
    is_alternate: bool = False
    enabled: bool = True


class LLMProviderCreate(LLMProviderBase):
    """Schema for creating a new LLM provider."""
    pass


class LLMProviderUpdate(BaseModel):
    """Schema for updating an LLM provider."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    provider_type: Optional[ProviderType] = None
    base_url: Optional[str] = Field(None, min_length=1, max_length=255)
    default_model: Optional[str] = Field(None, max_length=100)
    is_default: Optional[bool] = None
    is_alternate: Optional[bool] = None
    enabled: Optional[bool] = None


class LLMProviderResponse(LLMProviderBase):
    """Schema for LLM provider response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LLMProviderList(BaseModel):
    """Schema for list of LLM providers."""
    providers: list[LLMProviderResponse]
    total: int


class ProviderTestResult(BaseModel):
    """Schema for provider connection test result."""
    status: str  # "ok" or "error"
    message: Optional[str] = None
    models: Optional[list[str]] = None


class ProviderModelsResponse(BaseModel):
    """Schema for provider models list response."""
    models: list[dict]

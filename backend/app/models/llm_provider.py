from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from datetime import datetime
import enum

from app.database import Base


class ProviderType(str, enum.Enum):
    """LLM provider type enumeration."""
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"
    KOBOLDCPP = "koboldcpp"


class LLMProvider(Base):
    """LLM provider configuration model."""

    __tablename__ = "llm_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    provider_type = Column(Enum(ProviderType), nullable=False)
    base_url = Column(String(255), nullable=False)
    default_model = Column(String(100), nullable=True)
    is_default = Column(Boolean, default=False)
    is_alternate = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<LLMProvider(id={self.id}, name='{self.name}', type='{self.provider_type}')>"

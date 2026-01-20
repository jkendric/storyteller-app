from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Character(Base):
    """Character model for story protagonists, supporting characters, and antagonists."""

    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    personality = Column(Text, nullable=True)
    motivations = Column(Text, nullable=True)
    backstory = Column(Text, nullable=True)
    relationships = Column(Text, nullable=True)  # JSON string of relationships
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    story_characters = relationship("StoryCharacter", back_populates="character")

    def __repr__(self):
        return f"<Character(id={self.id}, name='{self.name}')>"

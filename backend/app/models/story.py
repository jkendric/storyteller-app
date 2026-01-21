from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class StoryStatus(str, enum.Enum):
    """Story status enumeration."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class CharacterRole(str, enum.Enum):
    """Character role in a story."""
    PROTAGONIST = "protagonist"
    SUPPORTING = "supporting"
    ANTAGONIST = "antagonist"


class Story(Base):
    """Story model representing a narrative with episodes."""

    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    status = Column(Enum(StoryStatus), default=StoryStatus.DRAFT)
    parent_story_id = Column(Integer, ForeignKey("stories.id"), nullable=True)
    fork_from_episode = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Generation Settings (nullable - uses defaults if not set)
    target_word_preset = Column(String(20), default="medium")  # short, medium, long, epic
    temperature = Column(Float, default=0.7)
    writing_style = Column(String(20), default="balanced")  # descriptive, action, dialogue, balanced
    mood = Column(String(20), default="moderate")  # light, moderate, intense, dark
    pacing = Column(String(20), default="moderate")  # slow, moderate, fast

    # Relationships
    scenario = relationship("Scenario", back_populates="stories")
    story_characters = relationship("StoryCharacter", back_populates="story")
    episodes = relationship("Episode", back_populates="story", order_by="Episode.number")
    memory_states = relationship("MemoryState", back_populates="story")
    parent_story = relationship("Story", remote_side=[id], backref="forks")

    def __repr__(self):
        return f"<Story(id={self.id}, title='{self.title}')>"


class StoryCharacter(Base):
    """Association table linking characters to stories with roles."""

    __tablename__ = "story_characters"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    role = Column(Enum(CharacterRole), default=CharacterRole.SUPPORTING)

    # Relationships
    story = relationship("Story", back_populates="story_characters")
    character = relationship("Character", back_populates="story_characters")

    def __repr__(self):
        return f"<StoryCharacter(story_id={self.story_id}, character_id={self.character_id})>"

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class MemoryState(Base):
    """Memory state model for the 3-tier memory system."""

    __tablename__ = "memory_states"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=False)

    # Three-tier memory system
    active_memory = Column(Text, nullable=True)  # Full text of last 3 episodes
    background_memory = Column(Text, nullable=True)  # Summaries of episodes 4-10
    faded_memory = Column(Text, nullable=True)  # High-level facts from older episodes

    # State tracking
    character_states = Column(Text, nullable=True)  # JSON: current state of each character
    plot_threads = Column(Text, nullable=True)  # JSON: active plot threads

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    story = relationship("Story", back_populates="memory_states")
    episode = relationship("Episode", back_populates="memory_state")

    def __repr__(self):
        return f"<MemoryState(id={self.id}, story_id={self.story_id}, episode_id={self.episode_id})>"

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Episode(Base):
    """Episode model representing a single installment of a story."""

    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    guidance = Column(Text, nullable=True)  # User-provided narrative guidance
    word_count = Column(Integer, default=0)
    audio_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    story = relationship("Story", back_populates="episodes")
    memory_state = relationship("MemoryState", back_populates="episode", uselist=False)

    def __repr__(self):
        return f"<Episode(id={self.id}, story_id={self.story_id}, number={self.number})>"

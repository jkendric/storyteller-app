from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Scenario(Base):
    """Scenario model defining story settings, genres, and world-building."""

    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    setting = Column(Text, nullable=True)
    time_period = Column(String(255), nullable=True)
    genre = Column(String(255), nullable=True)
    tone = Column(String(255), nullable=True)
    premise = Column(Text, nullable=True)
    themes = Column(Text, nullable=True)  # JSON array of themes
    world_rules = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    stories = relationship("Story", back_populates="scenario")

    def __repr__(self):
        return f"<Scenario(id={self.id}, name='{self.name}')>"

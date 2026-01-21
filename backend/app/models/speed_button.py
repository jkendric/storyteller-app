from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from datetime import datetime

from app.database import Base


class SpeedButton(Base):
    """Speed button preset for quick episode generation."""

    __tablename__ = "speed_buttons"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String(50), nullable=False)
    guidance = Column(Text, nullable=True)
    use_alternate = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SpeedButton(id={self.id}, label='{self.label}')>"

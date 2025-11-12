"""Event model."""
from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.models.base import Base, UUIDMixin, TimestampMixin


class RepeatInterval(str, enum.Enum):
    """Repeat interval enum."""
    NONE = "none"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class Event(Base, UUIDMixin, TimestampMixin):
    """Event model for countdown tracking."""
    
    __tablename__ = "events"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    event_date = Column(DateTime(timezone=True), nullable=False)
    repeat_interval = Column(Enum(RepeatInterval), default=RepeatInterval.NONE, nullable=False)
    next_occurrence = Column(DateTime(timezone=True), nullable=True)
    timezone = Column(String(100), nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="events")
    attachments = relationship("Attachment", back_populates="event", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Event(id={self.id}, title={self.title}, event_date={self.event_date})>"

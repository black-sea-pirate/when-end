"""Attachment model."""
from sqlalchemy import Column, String, Integer, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.models.base import Base, UUIDMixin, TimestampMixin


class AttachmentKind(str, enum.Enum):
    """Attachment kind enum."""
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"


class Attachment(Base, UUIDMixin, TimestampMixin):
    """Attachment model for event media files."""
    
    __tablename__ = "attachments"
    
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(Enum(AttachmentKind, name='attachmentkind', create_constraint=False), nullable=False)
    storage_key = Column(String(500), nullable=False)
    mime = Column(String(100), nullable=False)
    size = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)  # Video duration in seconds
    
    # Relationships
    event = relationship("Event", back_populates="attachments")
    
    def __repr__(self) -> str:
        return f"<Attachment(id={self.id}, kind={self.kind}, storage_key={self.storage_key})>"

"""SharedEvent and ShareToken models."""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base, UUIDMixin, TimestampMixin


class SharedEvent(Base, UUIDMixin, TimestampMixin):
    """SharedEvent model for sharing event templates."""
    
    __tablename__ = "shared_events"
    
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    payload = Column(JSONB, nullable=False)
    include_attachments_default = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="shared_events")
    tokens = relationship("ShareToken", back_populates="shared_event", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<SharedEvent(id={self.id}, owner_user_id={self.owner_user_id})>"


class ShareToken(Base, UUIDMixin, TimestampMixin):
    """ShareToken model for unique sharing links."""
    
    __tablename__ = "share_tokens"
    
    shared_event_id = Column(UUID(as_uuid=True), ForeignKey("shared_events.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    shared_event = relationship("SharedEvent", back_populates="tokens")
    
    def __repr__(self) -> str:
        return f"<ShareToken(id={self.id}, token={self.token})>"

"""User model."""
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    oauth_provider = Column(String(50), nullable=False, default="google")
    oauth_sub = Column(String(255), nullable=False)
    
    # Relationships
    events = relationship("Event", back_populates="owner", cascade="all, delete-orphan")
    shared_events = relationship("SharedEvent", back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"

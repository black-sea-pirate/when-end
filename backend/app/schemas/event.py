"""Event schemas."""
from pydantic import BaseModel, Field, UUID4, validator
from datetime import datetime
from typing import Optional, List, Literal
from app.models.event import RepeatInterval


ColorBucket = Literal["RED", "ORANGE", "YELLOW", "GREEN", "CYAN", "BLUE", "PURPLE"]


class AttachmentResponse(BaseModel):
    """Schema for attachment response."""
    id: UUID4
    name: str
    mime: str
    size: int
    url: str
    thumb_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    
    class Config:
        from_attributes = True


class EventBase(BaseModel):
    """Base event schema."""
    title: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)
    event_date: datetime
    repeat_interval: RepeatInterval = RepeatInterval.NONE
    timezone: Optional[str] = None


class EventCreate(EventBase):
    """Schema for creating an event."""
    
    @validator("event_date")
    def validate_event_date(cls, v):
        """Validate event date is not too far in the past."""
        from datetime import timedelta, timezone
        # Make comparison timezone-aware
        now_utc = datetime.now(timezone.utc)
        # If v is naive, make it aware (assume UTC)
        v_aware = v if v.tzinfo is not None else v.replace(tzinfo=timezone.utc)
        if v_aware < now_utc - timedelta(days=1):
            raise ValueError("Event date cannot be more than 1 day in the past")
        return v_aware


class EventUpdate(BaseModel):
    """Schema for updating an event."""
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)
    event_date: Optional[datetime] = None
    repeat_interval: Optional[RepeatInterval] = None
    timezone: Optional[str] = None
    
    @validator("event_date")
    def validate_event_date(cls, v):
        """Validate event date is not too far in the past."""
        if v is None:
            return v
        from datetime import timedelta, timezone
        # Make comparison timezone-aware
        now_utc = datetime.now(timezone.utc)
        # If v is naive, make it aware (assume UTC)
        v_aware = v if v.tzinfo is not None else v.replace(tzinfo=timezone.utc)
        if v_aware < now_utc - timedelta(days=1):
            raise ValueError("Event date cannot be more than 1 day in the past")
        return v_aware


class EventResponse(EventBase):
    """Schema for event response with computed fields."""
    id: UUID4
    user_id: UUID4
    next_occurrence: Optional[datetime] = None
    effective_due_at: datetime
    remaining_seconds: int
    color_bucket: Optional[ColorBucket] = None
    is_overdue: bool
    attachments: List[AttachmentResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Schema for event list response."""
    server_now: datetime
    items: List[EventResponse]
    next_cursor: Optional[str] = None

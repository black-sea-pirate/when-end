"""Share schemas."""
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, Dict, Any


class ShareCreateResponse(BaseModel):
    """Schema for share creation response."""
    share_url: str
    token: str
    expires_at: Optional[datetime] = None


class SharePreviewResponse(BaseModel):
    """Schema for share preview response."""
    title: str
    description: Optional[str] = None
    event_date: datetime
    repeat_interval: str
    timezone: Optional[str] = None
    has_attachments: bool
    created_at: datetime


class ShareImportRequest(BaseModel):
    """Schema for share import request."""
    include_attachments: bool = False


class ShareImportResponse(BaseModel):
    """Schema for share import response."""
    event_id: UUID4
    message: str

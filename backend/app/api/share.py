"""Share API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_optional
from app.core.config import settings
from app.models.user import User
from app.schemas.share import (
    ShareCreateResponse,
    SharePreviewResponse,
    ShareImportRequest,
    ShareImportResponse,
)
from app.schemas.event import EventCreate
from app.repositories.event_repository import EventRepository
from app.repositories.attachment_repository import AttachmentRepository
from app.repositories.share_repository import SharedEventRepository, ShareTokenRepository
from app.services.event_service import EventService
from app.services.storage_service import get_storage_service
from app.models.event import RepeatInterval

router = APIRouter(tags=["share"])

storage_service = get_storage_service()


@router.post("/events/{event_id}/share", response_model=ShareCreateResponse)
async def create_share_token(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create or rotate share token for an event.
    Returns shareable URL.
    """
    event_repo = EventRepository(db)
    shared_event_repo = SharedEventRepository(db)
    token_repo = ShareTokenRepository(db)
    attachment_repo = AttachmentRepository(db)
    
    # Get event
    event = event_repo.get_by_id(event_id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check ownership
    if event.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to share this event"
        )
    
    # Get attachments
    attachments = attachment_repo.get_by_event(event.id)
    
    # Create payload
    payload = {
        "title": event.title,
        "description": event.description,
        "event_date": event.event_date.isoformat(),
        "repeat_interval": event.repeat_interval.value,
        "timezone": event.timezone,
        "has_attachments": len(attachments) > 0,
        "attachment_keys": [att.storage_key for att in attachments] if attachments else []
    }
    
    # Create or update shared event
    shared_event = shared_event_repo.create(
        owner_user_id=current_user.id,
        payload=payload,
        include_attachments_default=False
    )
    
    # Create new token (rotation)
    token_value = str(uuid.uuid4())
    token = token_repo.create(
        shared_event_id=shared_event.id,
        token=token_value,
        expires_at=None  # No expiration for now
    )
    
    share_url = f"{settings.FRONTEND_URL}/share/{token_value}"
    
    return ShareCreateResponse(
        share_url=share_url,
        token=token_value,
        expires_at=token.expires_at
    )


@router.get("/share/{token}", response_model=SharePreviewResponse)
async def preview_shared_event(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Preview shared event (public endpoint).
    No authentication required.
    """
    token_repo = ShareTokenRepository(db)
    
    # Get token
    share_token = token_repo.get_by_token(token)
    
    if not share_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share link not found or expired"
        )
    
    # Check expiration
    if share_token.expires_at and share_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Share link has expired"
        )
    
    # Get shared event
    shared_event_repo = SharedEventRepository(db)
    shared_event = shared_event_repo.get_by_id(share_token.shared_event_id)
    
    if not shared_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared event not found"
        )
    
    payload = shared_event.payload
    
    return SharePreviewResponse(
        title=payload["title"],
        description=payload.get("description"),
        event_date=datetime.fromisoformat(payload["event_date"]),
        repeat_interval=payload["repeat_interval"],
        timezone=payload.get("timezone"),
        has_attachments=payload.get("has_attachments", False),
        created_at=shared_event.created_at
    )


@router.post("/share/{token}/import", response_model=ShareImportResponse)
async def import_shared_event(
    token: str,
    import_request: ShareImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import shared event into user's event list.
    Requires authentication.
    """
    token_repo = ShareTokenRepository(db)
    event_repo = EventRepository(db)
    attachment_repo = AttachmentRepository(db)
    
    # Get token
    share_token = token_repo.get_by_token(token)
    
    if not share_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share link not found or expired"
        )
    
    # Check expiration
    if share_token.expires_at and share_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Share link has expired"
        )
    
    # Get shared event
    shared_event_repo = SharedEventRepository(db)
    shared_event = shared_event_repo.get_by_id(share_token.shared_event_id)
    
    if not shared_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared event not found"
        )
    
    payload = shared_event.payload
    
    # Create event for current user
    event_data = EventCreate(
        title=payload["title"],
        description=payload.get("description"),
        event_date=datetime.fromisoformat(payload["event_date"]),
        repeat_interval=RepeatInterval(payload["repeat_interval"]),
        timezone=payload.get("timezone")
    )
    
    new_event = event_repo.create(current_user.id, event_data)
    
    # Calculate next occurrence if recurring
    if new_event.repeat_interval.value != "NONE":
        next_occ = EventService.calculate_next_occurrence(
            new_event.event_date,
            new_event.repeat_interval
        )
        new_event.next_occurrence = next_occ
        db.commit()
        db.refresh(new_event)
    
    # Copy attachments if requested (stub - not fully implemented)
    if import_request.include_attachments and payload.get("has_attachments"):
        # TODO: Copy attachment files from storage
        pass
    
    return ShareImportResponse(
        event_id=new_event.id,
        message="Event imported successfully"
    )

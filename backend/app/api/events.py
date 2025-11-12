"""Events API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.event import Event
from app.models.attachment import AttachmentKind
from app.schemas.event import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListResponse,
)
from app.repositories.event_repository import EventRepository
from app.repositories.attachment_repository import AttachmentRepository
from app.services.event_service import EventService
from app.services.storage_service import get_storage_service
from app.core.config import settings

router = APIRouter(prefix="/events", tags=["events"])

# Get storage service instance
storage_service = get_storage_service()


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new event."""
    event_repo = EventRepository(db)
    attachment_repo = AttachmentRepository(db)
    
    # Create event
    event = event_repo.create(current_user.id, event_data)
    
    # Calculate next occurrence if recurring
    if event.repeat_interval.value != "none":
        next_occ = EventService.calculate_next_occurrence(
            event.event_date,
            event.repeat_interval
        )
        event.next_occurrence = next_occ
        db.commit()
        db.refresh(event)
    
    # Get attachments
    attachments = attachment_repo.get_by_event(event.id)
    
    # Enrich and return
    server_now = datetime.now(timezone.utc)
    enriched = EventService.enrich_event(event, server_now, attachments, storage_service)
    
    return EventResponse(**enriched)


@router.get("", response_model=EventListResponse)
async def list_events(
    q: Optional[str] = None,
    include_overdue: bool = False,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's events with filters."""
    event_repo = EventRepository(db)
    attachment_repo = AttachmentRepository(db)
    
    # Get events
    events = event_repo.get_by_user(
        current_user.id,
        include_overdue=include_overdue,
        search_query=q,
        limit=limit,
        offset=offset
    )
    
    # Enrich all events
    server_now = datetime.now(timezone.utc)
    enriched_events = []
    
    for event in events:
        attachments = attachment_repo.get_by_event(event.id)
        enriched = EventService.enrich_event(event, server_now, attachments, storage_service)
        enriched_events.append(enriched)
    
    # Filter overdue if needed
    if not include_overdue:
        enriched_events = [e for e in enriched_events if not e["is_overdue"]]
    
    # Sort by remaining time
    enriched_events = EventService.sort_events_by_remaining_time(enriched_events)
    
    return EventListResponse(
        server_now=server_now,
        items=[EventResponse(**e) for e in enriched_events],
        next_cursor=None  # TODO: Implement pagination
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get event by ID."""
    event_repo = EventRepository(db)
    attachment_repo = AttachmentRepository(db)
    
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
            detail="Not authorized to access this event"
        )
    
    # Get attachments
    attachments = attachment_repo.get_by_event(event.id)
    
    # Enrich and return
    server_now = datetime.now(timezone.utc)
    enriched = EventService.enrich_event(event, server_now, attachments, storage_service)
    
    return EventResponse(**enriched)


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: uuid.UUID,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update event."""
    event_repo = EventRepository(db)
    attachment_repo = AttachmentRepository(db)
    
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
            detail="Not authorized to update this event"
        )
    
    # Update event
    event = event_repo.update(event, event_data)
    
    # Recalculate next occurrence if repeat_interval changed
    if event.repeat_interval.value != "none":
        next_occ = EventService.calculate_next_occurrence(
            event.event_date,
            event.repeat_interval
        )
        event.next_occurrence = next_occ
        db.commit()
        db.refresh(event)
    
    # Get attachments
    attachments = attachment_repo.get_by_event(event.id)
    
    # Enrich and return
    server_now = datetime.now(timezone.utc)
    enriched = EventService.enrich_event(event, server_now, attachments, storage_service)
    
    return EventResponse(**enriched)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete event."""
    event_repo = EventRepository(db)
    attachment_repo = AttachmentRepository(db)
    
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
            detail="Not authorized to delete this event"
        )
    
    # Delete attachments from storage
    attachments = attachment_repo.get_by_event(event.id)
    for attachment in attachments:
        storage_service.delete_file(attachment.storage_key)
    
    # Delete event (cascade deletes attachments from DB)
    event_repo.delete(event)
    
    return None


@router.post("/{event_id}/attachments", status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    event_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload attachment to event."""
    event_repo = EventRepository(db)
    attachment_repo = AttachmentRepository(db)
    
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
            detail="Not authorized to upload to this event"
        )
    
    # Validate file
    content_type = file.content_type or ""
    
    # Determine kind and validate size
    if content_type.startswith("image/"):
        kind = AttachmentKind.IMAGE
        max_size = settings.max_image_size_bytes
    elif content_type.startswith("video/"):
        kind = AttachmentKind.VIDEO
        max_size = settings.max_video_size_bytes
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only images and videos are allowed."
        )
    
    # Read file
    file_data = await file.read()
    file_size = len(file_data)
    
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed ({max_size / 1024 / 1024:.1f} MB)"
        )
    
    # Save to storage
    from io import BytesIO
    storage_key = storage_service.save_file(
        BytesIO(file_data),
        file.filename or "upload",
        content_type
    )
    
    # Create attachment record
    # TODO: Extract width/height for images, duration for videos
    attachment = attachment_repo.create(
        event_id=event.id,
        kind=kind,
        storage_key=storage_key,
        mime=content_type,
        size=file_size
    )
    
    return {
        "id": attachment.id,
        "message": "Attachment uploaded successfully"
    }


@router.delete("/{event_id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    event_id: uuid.UUID,
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete attachment."""
    event_repo = EventRepository(db)
    attachment_repo = AttachmentRepository(db)
    
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
            detail="Not authorized to delete from this event"
        )
    
    attachment = attachment_repo.get_by_id(attachment_id)
    
    if not attachment or attachment.event_id != event.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    # Delete from storage
    storage_service.delete_file(attachment.storage_key)
    
    # Delete from database
    attachment_repo.delete(attachment)
    
    return None

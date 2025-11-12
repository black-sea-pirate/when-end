"""Attachment repository."""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.attachment import Attachment, AttachmentKind
import uuid


class AttachmentRepository:
    """Repository for Attachment model."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, attachment_id: uuid.UUID) -> Optional[Attachment]:
        """Get attachment by ID."""
        return self.db.query(Attachment).filter(Attachment.id == attachment_id).first()
    
    def get_by_event(self, event_id: uuid.UUID) -> List[Attachment]:
        """Get all attachments for an event."""
        return self.db.query(Attachment).filter(Attachment.event_id == event_id).all()
    
    def create(
        self,
        event_id: uuid.UUID,
        kind: AttachmentKind,
        storage_key: str,
        mime: str,
        size: int,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration: Optional[int] = None
    ) -> Attachment:
        """Create a new attachment."""
        attachment = Attachment(
            event_id=event_id,
            kind=kind,
            storage_key=storage_key,
            mime=mime,
            size=size,
            width=width,
            height=height,
            duration=duration
        )
        self.db.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)
        return attachment
    
    def delete(self, attachment: Attachment) -> None:
        """Delete an attachment."""
        self.db.delete(attachment)
        self.db.commit()

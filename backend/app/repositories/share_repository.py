"""Shared event and share token repositories."""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.shared_event import SharedEvent, ShareToken
from datetime import datetime
import uuid


class SharedEventRepository:
    """Repository for SharedEvent model."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, shared_event_id: uuid.UUID) -> Optional[SharedEvent]:
        """Get shared event by ID."""
        return self.db.query(SharedEvent).filter(SharedEvent.id == shared_event_id).first()
    
    def create(
        self,
        owner_user_id: uuid.UUID,
        payload: dict,
        include_attachments_default: bool = False
    ) -> SharedEvent:
        """Create a new shared event."""
        shared_event = SharedEvent(
            owner_user_id=owner_user_id,
            payload=payload,
            include_attachments_default=include_attachments_default
        )
        self.db.add(shared_event)
        self.db.commit()
        self.db.refresh(shared_event)
        return shared_event
    
    def update_payload(self, shared_event: SharedEvent, payload: dict) -> SharedEvent:
        """Update shared event payload."""
        shared_event.payload = payload
        self.db.commit()
        self.db.refresh(shared_event)
        return shared_event
    
    def delete(self, shared_event: SharedEvent) -> None:
        """Delete a shared event."""
        self.db.delete(shared_event)
        self.db.commit()


class ShareTokenRepository:
    """Repository for ShareToken model."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_token(self, token: str) -> Optional[ShareToken]:
        """Get share token by token string."""
        return self.db.query(ShareToken).filter(ShareToken.token == token).first()
    
    def get_by_shared_event(self, shared_event_id: uuid.UUID) -> Optional[ShareToken]:
        """Get share token by shared event ID."""
        return self.db.query(ShareToken).filter(
            ShareToken.shared_event_id == shared_event_id
        ).first()
    
    def create(
        self,
        shared_event_id: uuid.UUID,
        token: str,
        expires_at: Optional[datetime] = None
    ) -> ShareToken:
        """Create a new share token."""
        share_token = ShareToken(
            shared_event_id=shared_event_id,
            token=token,
            expires_at=expires_at
        )
        self.db.add(share_token)
        self.db.commit()
        self.db.refresh(share_token)
        return share_token
    
    def delete(self, share_token: ShareToken) -> None:
        """Delete a share token."""
        self.db.delete(share_token)
        self.db.commit()
    
    def delete_by_shared_event(self, shared_event_id: uuid.UUID) -> None:
        """Delete all tokens for a shared event."""
        self.db.query(ShareToken).filter(
            ShareToken.shared_event_id == shared_event_id
        ).delete()
        self.db.commit()

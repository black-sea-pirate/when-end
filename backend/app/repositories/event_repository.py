"""Event repository."""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
from app.models.event import Event
from app.schemas.event import EventCreate, EventUpdate
import uuid


class EventRepository:
    """Repository for Event model."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, event_id: uuid.UUID) -> Optional[Event]:
        """Get event by ID."""
        return self.db.query(Event).filter(Event.id == event_id).first()
    
    def get_by_user(
        self,
        user_id: uuid.UUID,
        include_overdue: bool = False,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Event]:
        """
        Get events by user with filters.
        
        Args:
            user_id: User ID
            include_overdue: Include overdue events
            search_query: Search by title
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of events
        """
        query = self.db.query(Event).filter(Event.user_id == user_id)
        
        if search_query:
            query = query.filter(Event.title.ilike(f"%{search_query}%"))
        
        # Order by event_date for now (will be sorted by effective_due_at in service)
        query = query.order_by(Event.event_date.asc())
        
        return query.offset(offset).limit(limit).all()
    
    def create(self, user_id: uuid.UUID, event_data: EventCreate) -> Event:
        """Create a new event."""
        event = Event(
            user_id=user_id,
            **event_data.model_dump()
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def update(self, event: Event, event_data: EventUpdate) -> Event:
        """Update an event."""
        update_data = event_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(event, field, value)
        
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def delete(self, event: Event) -> None:
        """Delete an event."""
        self.db.delete(event)
        self.db.commit()
    
    def count_by_user(self, user_id: uuid.UUID) -> int:
        """Count events by user."""
        return self.db.query(Event).filter(Event.user_id == user_id).count()

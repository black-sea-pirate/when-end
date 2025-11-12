"""Event service with business logic for event countdowns and recurrence."""
from typing import List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
import calendar
from app.models.event import Event, RepeatInterval
from app.models.attachment import Attachment
from app.schemas.event import EventResponse, AttachmentResponse, ColorBucket
from app.core.config import settings


class EventService:
    """Service for event business logic."""
    
    @staticmethod
    def calculate_next_occurrence(event_date: datetime, repeat_interval: RepeatInterval) -> Optional[datetime]:
        """
        Calculate next occurrence for recurring events.
        
        Args:
            event_date: Original event date
            repeat_interval: Repeat interval
            
        Returns:
            Next occurrence datetime or None for non-recurring
        """
        if repeat_interval == RepeatInterval.NONE:
            return None
        
        now = datetime.now(timezone.utc)
        
        # If event hasn't passed yet, next occurrence is the event itself
        if event_date > now:
            return event_date
        
        # Calculate next occurrence based on interval
        if repeat_interval == RepeatInterval.DAY:
            next_occ = event_date
            while next_occ <= now:
                next_occ += timedelta(days=1)
            return next_occ
        
        elif repeat_interval == RepeatInterval.WEEK:
            next_occ = event_date
            while next_occ <= now:
                next_occ += timedelta(weeks=1)
            return next_occ
        
        elif repeat_interval == RepeatInterval.MONTH:
            next_occ = event_date
            while next_occ <= now:
                next_occ += relativedelta(months=1)
            return next_occ
        
        elif repeat_interval == RepeatInterval.YEAR:
            next_occ = event_date
            while next_occ <= now:
                # Handle leap year (Feb 29)
                if event_date.month == 2 and event_date.day == 29:
                    next_year = next_occ.year + 1
                    if calendar.isleap(next_year):
                        next_occ = next_occ.replace(year=next_year)
                    else:
                        # Apply leap policy
                        if settings.LEAP_POLICY == "mar01":
                            next_occ = datetime(next_year, 3, 1, next_occ.hour, next_occ.minute, next_occ.second, tzinfo=next_occ.tzinfo)
                        else:  # feb28
                            next_occ = datetime(next_year, 2, 28, next_occ.hour, next_occ.minute, next_occ.second, tzinfo=next_occ.tzinfo)
                else:
                    next_occ += relativedelta(years=1)
            return next_occ
        
        return None
    
    @staticmethod
    def get_effective_due_at(event: Event) -> datetime:
        """
        Get effective due date (next_occurrence for recurring, event_date otherwise).
        
        Args:
            event: Event model
            
        Returns:
            Effective due datetime
        """
        if event.repeat_interval != RepeatInterval.NONE and event.next_occurrence:
            return event.next_occurrence
        return event.event_date
    
    @staticmethod
    def calculate_remaining_seconds(effective_due_at: datetime, server_now: datetime) -> int:
        """
        Calculate remaining seconds until event.
        
        Args:
            effective_due_at: Effective due datetime
            server_now: Current server time
            
        Returns:
            Remaining seconds (negative if overdue)
        """
        delta = effective_due_at - server_now
        return int(delta.total_seconds())
    
    @staticmethod
    def get_color_bucket(remaining_seconds: int) -> Optional[ColorBucket]:
        """
        Get color bucket based on remaining time.
        
        Strict boundaries:
        - RED:     0 <= t < 86_400 (< 1 day)
        - ORANGE:  86_400 <= t < 7*86_400 (1-7 days)
        - YELLOW:  7*86_400 <= t < 30*86_400 (7-30 days)
        - GREEN:   30*86_400 <= t < 90*86_400 (30-90 days)
        - CYAN:    90*86_400 <= t < 365*86_400 (90-365 days)
        - BLUE:    365*86_400 <= t < 3*365*86_400 (1-3 years)
        - PURPLE:  t >= 3*365*86_400 (> 3 years)
        
        Args:
            remaining_seconds: Remaining seconds
            
        Returns:
            Color bucket or None if overdue
        """
        if remaining_seconds < 0:
            return None  # Overdue
        
        if remaining_seconds < 86_400:  # < 1 day
            return "RED"
        elif remaining_seconds < 7 * 86_400:  # < 7 days
            return "ORANGE"
        elif remaining_seconds < 30 * 86_400:  # < 30 days
            return "YELLOW"
        elif remaining_seconds < 90 * 86_400:  # < 90 days
            return "GREEN"
        elif remaining_seconds < 365 * 86_400:  # < 365 days
            return "CYAN"
        elif remaining_seconds < 3 * 365 * 86_400:  # < 3 years
            return "BLUE"
        else:  # >= 3 years
            return "PURPLE"
    
    @staticmethod
    def enrich_event(
        event: Event,
        server_now: datetime,
        attachments: Optional[List[Attachment]] = None,
        storage_service = None
    ) -> dict:
        """
        Enrich event with computed fields for response.
        
        Args:
            event: Event model
            server_now: Current server time
            attachments: Optional list of attachments
            storage_service: Optional storage service for signed URLs
            
        Returns:
            Enriched event dict
        """
        # Calculate next occurrence if recurring
        if event.repeat_interval != RepeatInterval.NONE:
            next_occurrence = EventService.calculate_next_occurrence(
                event.event_date,
                event.repeat_interval
            )
        else:
            next_occurrence = None
        
        # Get effective due date
        effective_due_at = next_occurrence if next_occurrence else event.event_date
        
        # Calculate remaining seconds
        remaining_seconds = EventService.calculate_remaining_seconds(effective_due_at, server_now)
        
        # Get color bucket
        color_bucket = EventService.get_color_bucket(remaining_seconds)
        
        # Check if overdue
        is_overdue = remaining_seconds < 0
        
        # Convert attachments to response format
        attachment_responses = []
        if attachments and storage_service:
            for att in attachments:
                url = storage_service.generate_signed_url(att.storage_key)
                thumb_url = None  # TODO: Implement thumbnail generation
                
                attachment_responses.append(AttachmentResponse(
                    id=att.id,
                    name=att.storage_key.split('/')[-1],
                    mime=att.mime,
                    size=att.size,
                    url=url,
                    thumb_url=thumb_url,
                    width=att.width,
                    height=att.height,
                    duration=att.duration
                ))
        
        return {
            "id": event.id,
            "user_id": event.user_id,
            "title": event.title,
            "description": event.description,
            "event_date": event.event_date,
            "repeat_interval": event.repeat_interval,
            "timezone": event.timezone,
            "next_occurrence": next_occurrence,
            "effective_due_at": effective_due_at,
            "remaining_seconds": remaining_seconds,
            "color_bucket": color_bucket,
            "is_overdue": is_overdue,
            "attachments": attachment_responses,
            "created_at": event.created_at,
            "updated_at": event.updated_at,
        }
    
    @staticmethod
    def sort_events_by_remaining_time(enriched_events: List[dict]) -> List[dict]:
        """
        Sort events by remaining time (ascending).
        
        Args:
            enriched_events: List of enriched event dicts
            
        Returns:
            Sorted list of events
        """
        return sorted(enriched_events, key=lambda e: e["remaining_seconds"])
    
    @staticmethod
    def filter_overdue(enriched_events: List[dict]) -> Tuple[List[dict], List[dict]]:
        """
        Separate upcoming and overdue events.
        
        Args:
            enriched_events: List of enriched event dicts
            
        Returns:
            Tuple of (upcoming_events, overdue_events)
        """
        upcoming = [e for e in enriched_events if not e["is_overdue"]]
        overdue = [e for e in enriched_events if e["is_overdue"]]
        return upcoming, overdue

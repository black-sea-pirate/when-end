"""Tests for event service (color buckets and recurrence)."""
import pytest
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app.services.event_service import EventService
from app.models.event import RepeatInterval


class TestColorBuckets:
    """Test color bucket boundaries."""
    
    def test_red_bucket_less_than_1_day(self):
        """RED: 0 <= t < 86,400 (< 1 day)"""
        # Just under 1 day
        remaining = 86399
        assert EventService.get_color_bucket(remaining) == "RED"
        
        # 12 hours
        remaining = 12 * 3600
        assert EventService.get_color_bucket(remaining) == "RED"
        
        # 1 second
        remaining = 1
        assert EventService.get_color_bucket(remaining) == "RED"
        
        # Exactly 0
        remaining = 0
        assert EventService.get_color_bucket(remaining) == "RED"
    
    def test_orange_bucket_1_to_7_days(self):
        """ORANGE: 86,400 <= t < 7*86,400 (1-7 days)"""
        # Exactly 1 day
        remaining = 86400
        assert EventService.get_color_bucket(remaining) == "ORANGE"
        
        # 3 days
        remaining = 3 * 86400
        assert EventService.get_color_bucket(remaining) == "ORANGE"
        
        # Just under 7 days
        remaining = 7 * 86400 - 1
        assert EventService.get_color_bucket(remaining) == "ORANGE"
    
    def test_yellow_bucket_7_to_30_days(self):
        """YELLOW: 7*86,400 <= t < 30*86,400 (7-30 days)"""
        # Exactly 7 days
        remaining = 7 * 86400
        assert EventService.get_color_bucket(remaining) == "YELLOW"
        
        # 15 days
        remaining = 15 * 86400
        assert EventService.get_color_bucket(remaining) == "YELLOW"
        
        # Just under 30 days
        remaining = 30 * 86400 - 1
        assert EventService.get_color_bucket(remaining) == "YELLOW"
    
    def test_green_bucket_30_to_90_days(self):
        """GREEN: 30*86,400 <= t < 90*86,400 (30-90 days)"""
        # Exactly 30 days
        remaining = 30 * 86400
        assert EventService.get_color_bucket(remaining) == "GREEN"
        
        # 60 days
        remaining = 60 * 86400
        assert EventService.get_color_bucket(remaining) == "GREEN"
        
        # Just under 90 days
        remaining = 90 * 86400 - 1
        assert EventService.get_color_bucket(remaining) == "GREEN"
    
    def test_cyan_bucket_90_to_365_days(self):
        """CYAN: 90*86,400 <= t < 365*86,400 (90-365 days)"""
        # Exactly 90 days
        remaining = 90 * 86400
        assert EventService.get_color_bucket(remaining) == "CYAN"
        
        # 180 days
        remaining = 180 * 86400
        assert EventService.get_color_bucket(remaining) == "CYAN"
        
        # Just under 365 days
        remaining = 365 * 86400 - 1
        assert EventService.get_color_bucket(remaining) == "CYAN"
    
    def test_blue_bucket_1_to_3_years(self):
        """BLUE: 365*86,400 <= t < 3*365*86,400 (1-3 years)"""
        # Exactly 365 days
        remaining = 365 * 86400
        assert EventService.get_color_bucket(remaining) == "BLUE"
        
        # 2 years
        remaining = 2 * 365 * 86400
        assert EventService.get_color_bucket(remaining) == "BLUE"
        
        # Just under 3 years
        remaining = 3 * 365 * 86400 - 1
        assert EventService.get_color_bucket(remaining) == "BLUE"
    
    def test_purple_bucket_over_3_years(self):
        """PURPLE: t >= 3*365*86,400 (> 3 years)"""
        # Exactly 3 years
        remaining = 3 * 365 * 86400
        assert EventService.get_color_bucket(remaining) == "PURPLE"
        
        # 5 years
        remaining = 5 * 365 * 86400
        assert EventService.get_color_bucket(remaining) == "PURPLE"
        
        # 10 years
        remaining = 10 * 365 * 86400
        assert EventService.get_color_bucket(remaining) == "PURPLE"
    
    def test_overdue_returns_none(self):
        """Overdue events (t < 0) return None."""
        remaining = -1
        assert EventService.get_color_bucket(remaining) is None
        
        remaining = -86400  # -1 day
        assert EventService.get_color_bucket(remaining) is None
        
        remaining = -365 * 86400  # -1 year
        assert EventService.get_color_bucket(remaining) is None


class TestRecurrence:
    """Test recurrence calculations."""
    
    def test_no_recurrence(self):
        """Non-recurring events return None."""
        event_date = datetime(2025, 12, 31, 23, 59, 59)
        next_occ = EventService.calculate_next_occurrence(event_date, RepeatInterval.NONE)
        assert next_occ is None
    
    def test_daily_recurrence(self):
        """Daily recurrence adds 1 day."""
        # Past event
        event_date = datetime(2025, 1, 1, 12, 0, 0)
        next_occ = EventService.calculate_next_occurrence(event_date, RepeatInterval.DAY)
        
        # Should be in the future
        assert next_occ > datetime.utcnow()
        
        # Should be on same time
        assert next_occ.hour == 12
        assert next_occ.minute == 0
    
    def test_weekly_recurrence(self):
        """Weekly recurrence adds 7 days."""
        # Past event
        event_date = datetime(2025, 1, 1, 12, 0, 0)
        next_occ = EventService.calculate_next_occurrence(event_date, RepeatInterval.WEEK)
        
        # Should be in the future
        assert next_occ > datetime.utcnow()
        
        # Should be on same day of week and time
        assert next_occ.weekday() == event_date.weekday()
        assert next_occ.hour == 12
    
    def test_monthly_recurrence(self):
        """Monthly recurrence adds 1 month."""
        # Past event
        event_date = datetime(2025, 1, 15, 12, 0, 0)
        next_occ = EventService.calculate_next_occurrence(event_date, RepeatInterval.MONTH)
        
        # Should be in the future
        assert next_occ > datetime.utcnow()
        
        # Should be on same day of month
        assert next_occ.day == 15
        assert next_occ.hour == 12
    
    def test_yearly_recurrence(self):
        """Yearly recurrence adds 1 year."""
        # Past event
        event_date = datetime(2024, 6, 15, 12, 0, 0)
        next_occ = EventService.calculate_next_occurrence(event_date, RepeatInterval.YEAR)
        
        # Should be in the future
        assert next_occ > datetime.utcnow()
        
        # Should be on same month and day
        assert next_occ.month == 6
        assert next_occ.day == 15
        assert next_occ.hour == 12
    
    def test_leap_year_feb_29_non_leap_year(self):
        """Feb 29 in non-leap year defaults to Feb 28."""
        # Feb 29, 2024 (leap year)
        event_date = datetime(2024, 2, 29, 12, 0, 0)
        next_occ = EventService.calculate_next_occurrence(event_date, RepeatInterval.YEAR)
        
        # Should be in the future
        assert next_occ > datetime.utcnow()
        
        # 2025 is not a leap year, should default to Feb 28 or Mar 1
        if next_occ.year == 2025:
            assert next_occ.month == 2 and next_occ.day == 28, "Should default to Feb 28 in non-leap year"
        else:
            # Should be 2026 or later
            assert next_occ.year >= 2026
    
    def test_future_event_returns_itself(self):
        """Future events return themselves as next occurrence."""
        # Event in the future
        event_date = datetime.utcnow() + timedelta(days=30)
        
        next_occ = EventService.calculate_next_occurrence(event_date, RepeatInterval.DAY)
        assert next_occ == event_date
        
        next_occ = EventService.calculate_next_occurrence(event_date, RepeatInterval.WEEK)
        assert next_occ == event_date


class TestRemainingSeconds:
    """Test remaining seconds calculation."""
    
    def test_future_event(self):
        """Future event has positive remaining seconds."""
        server_now = datetime(2025, 1, 1, 12, 0, 0)
        effective_due = datetime(2025, 1, 2, 12, 0, 0)
        
        remaining = EventService.calculate_remaining_seconds(effective_due, server_now)
        assert remaining == 86400  # 1 day
    
    def test_past_event(self):
        """Past event has negative remaining seconds."""
        server_now = datetime(2025, 1, 2, 12, 0, 0)
        effective_due = datetime(2025, 1, 1, 12, 0, 0)
        
        remaining = EventService.calculate_remaining_seconds(effective_due, server_now)
        assert remaining == -86400  # -1 day
    
    def test_current_time(self):
        """Event at current time has 0 remaining seconds."""
        server_now = datetime(2025, 1, 1, 12, 0, 0)
        effective_due = datetime(2025, 1, 1, 12, 0, 0)
        
        remaining = EventService.calculate_remaining_seconds(effective_due, server_now)
        assert remaining == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

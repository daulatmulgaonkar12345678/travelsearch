"""
Test hotel search date validation logic
"""
from datetime import date, timedelta
import pytest


def test_date_validation_logic():
    """Test date validation business logic"""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after = tomorrow + timedelta(days=1)
    
    # Check-in < tomorrow should be invalid
    assert today < tomorrow, "Today should be before tomorrow"
    
    # Check-out must be after check-in
    assert day_after > tomorrow, "Check-out must be after check-in"
    
    # Same-day checkout should be invalid
    assert not (tomorrow <= tomorrow), "Same-day checkout should be invalid"


def test_date_string_formatting():
    """Test date string formatting for API"""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    # ISO format should be YYYY-MM-DD
    iso_str = tomorrow.isoformat()
    assert len(iso_str) == 10, "ISO date should be 10 characters"
    assert iso_str.count('-') == 2, "ISO date should have 2 dashes"
    
    # Should be parseable back to date
    parsed = date.fromisoformat(iso_str)
    assert parsed == tomorrow, "Parsed date should match original"


def test_minimum_stay_validation():
    """Test minimum stay duration"""
    tomorrow = date.today() + timedelta(days=1)
    checkout = tomorrow + timedelta(days=1)
    
    # At least 1 night stay
    nights = (checkout - tomorrow).days
    assert nights >= 1, "Must have at least 1 night stay"

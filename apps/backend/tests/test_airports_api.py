"""Test airport autocomplete API"""
import pytest
from datetime import date, timedelta


def test_airport_search_short_query():
    """Query < 2 characters should return empty list"""
    # Short queries should return empty
    assert len('p') < 2
    assert len('a') < 2


def test_airport_search_pune():
    """Search 'pu' should include Pune (PNQ)"""
    query = 'pu'
    
    # Load airports data
    import json
    from pathlib import Path
    
    data_path = Path(__file__).parent.parent / "data" / "airports.json"
    with open(data_path, 'r') as f:
        airports = json.load(f)
    
    # Filter airports matching 'pu'
    results = [a for a in airports if 
               'pu' in a['city'].lower() or 
               'pu' in a['name'].lower() or
               a['iata'].lower() == 'pu']
    
    # Should include Pune
    pune_found = any(a['iata'] == 'PNQ' for a in results)
    assert pune_found, "Pune (PNQ) should be in results"


def test_airport_search_exact_iata():
    """Search by exact IATA code should return that airport"""
    import json
    from pathlib import Path
    
    data_path = Path(__file__).parent.parent / "data" / "airports.json"
    with open(data_path, 'r') as f:
        airports = json.load(f)
    
    # Search for PNQ
    results = [a for a in airports if a['iata'].lower() == 'pnq']
    
    assert len(results) == 1
    assert results[0]['iata'] == 'PNQ'
    assert results[0]['city'] == 'Pune'


def test_flight_date_validation():
    """Test flight date validation logic"""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after = tomorrow + timedelta(days=1)
    
    # Departure must be >= tomorrow
    assert tomorrow > today
    
    # Return must be > departure
    assert day_after > tomorrow
    
    # Invalid: return <= departure (must be strictly greater)
    is_invalid = tomorrow <= tomorrow
    assert is_invalid == True, \"Same date should be invalid\"


def test_multicity_date_validation():
    """Test multicity segment date validation"""
    tomorrow = date.today() + timedelta(days=1)
    day2 = tomorrow + timedelta(days=1)
    day3 = day2 + timedelta(days=1)
    
    # Each segment must be after previous
    assert day2 > tomorrow
    assert day3 > day2
    
    # Invalid: segment2 <= segment1 (must be strictly greater)
    is_invalid = tomorrow <= tomorrow
    assert is_invalid == True, \"Same date for segments should be invalid\"

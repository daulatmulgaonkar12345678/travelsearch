"""
Unit tests for flight duration validator
"""

import pytest
from datetime import datetime, timedelta
from app.services.flight_validator import (
    haversine_distance,
    compute_segment_duration_minutes,
    validate_segment_duration,
    validate_and_fix_itinerary,
    validate_flight_offers,
    reset_validation_metrics,
    get_validation_metrics,
)
from app.models.flight import FlightOffer, FlightSegment


@pytest.fixture
def airport_data():
    """Sample airport dataset with coordinates"""
    return {
        "BOM": {
            "iata": "BOM",
            "name": "Chhatrapati Shivaji International",
            "city": "Mumbai",
            "lat": 19.0887,
            "lon": 72.8678,
        },
        "DEL": {
            "iata": "DEL",
            "name": "Indira Gandhi International",
            "city": "Delhi",
            "lat": 28.5562,
            "lon": 77.1000,
        },
        "PNQ": {
            "iata": "PNQ",
            "name": "Pune Airport",
            "city": "Pune",
            "lat": 18.5821,
            "lon": 73.9197,
        },
        "IXC": {
            "iata": "IXC",
            "name": "Chandigarh International",
            "city": "Chandigarh",
            "lat": 30.6735,
            "lon": 76.7884,
        },
    }


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset validation metrics before each test"""
    reset_validation_metrics()
    yield
    reset_validation_metrics()


def test_haversine_distance():
    """Test Haversine distance calculation"""
    # BOM to DEL (approximately 1150 km)
    distance = haversine_distance(19.0887, 72.8678, 28.5562, 77.1000)
    assert 1100 < distance < 1200, f"Expected ~1150km, got {distance}km"
    
    # PNQ to BOM (approximately 120 km)
    distance = haversine_distance(18.5821, 73.9197, 19.0887, 72.8678)
    assert 100 < distance < 140, f"Expected ~120km, got {distance}km"


def test_compute_segment_duration():
    """Test segment duration computation from timestamps"""
    # Create a segment with 2 hour duration
    departure = datetime(2025, 12, 15, 10, 0, 0)
    arrival = datetime(2025, 12, 15, 12, 0, 0)
    
    segment = FlightSegment(
        departure_airport="BOM",
        arrival_airport="DEL",
        departure_time=departure,
        arrival_time=arrival,
        carrier_code="AI",
        carrier_name="Air India",
        flight_number="100",
        duration_minutes=0,  # Will be recomputed
    )
    
    minutes = compute_segment_duration_minutes(segment)
    assert minutes == 120, f"Expected 120 minutes, got {minutes}"


def test_unrealistically_short_duration_rejected(airport_data):
    """Test that absurdly short durations (like 15 min for 600 km) are rejected"""
    # BOM to DEL is ~1150 km, 15 minutes is impossible
    departure = datetime(2025, 12, 15, 10, 0, 0)
    arrival = datetime(2025, 12, 15, 10, 15, 0)  # Only 15 minutes!
    
    segment = FlightSegment(
        departure_airport="BOM",
        arrival_airport="DEL",
        departure_time=departure,
        arrival_time=arrival,
        carrier_code="AI",
        carrier_name="Air India",
        flight_number="100",
        duration_minutes=15,
    )
    
    is_valid, reason = validate_segment_duration(segment, airport_data, "test_provider")
    
    assert not is_valid, "15-minute BOM-DEL flight should be rejected"
    assert reason == "duration_too_fast"
    
    # Check metrics
    metrics = get_validation_metrics()
    assert metrics["dropped_too_fast"] == 1


def test_valid_short_haul_accepted(airport_data):
    """Test that valid short-haul flights are accepted"""
    # PNQ to BOM is ~120 km, 45 minutes is reasonable
    departure = datetime(2025, 12, 15, 10, 0, 0)
    arrival = datetime(2025, 12, 15, 10, 45, 0)
    
    segment = FlightSegment(
        departure_airport="PNQ",
        arrival_airport="BOM",
        departure_time=departure,
        arrival_time=arrival,
        carrier_code="AI",
        carrier_name="Air India",
        flight_number="200",
        duration_minutes=45,
    )
    
    is_valid, reason = validate_segment_duration(segment, airport_data, "test_provider")
    
    assert is_valid, "45-minute PNQ-BOM flight should be accepted"
    assert reason is None


def test_valid_long_haul_accepted(airport_data):
    """Test that valid long-haul flights are accepted"""
    # BOM to DEL is ~1150 km, 2 hours is realistic
    departure = datetime(2025, 12, 15, 10, 0, 0)
    arrival = datetime(2025, 12, 15, 12, 0, 0)
    
    segment = FlightSegment(
        departure_airport="BOM",
        arrival_airport="DEL",
        departure_time=departure,
        arrival_time=arrival,
        carrier_code="AI",
        carrier_name="Air India",
        flight_number="100",
        duration_minutes=120,
    )
    
    is_valid, reason = validate_segment_duration(segment, airport_data, "test_provider")
    
    assert is_valid, "2-hour BOM-DEL flight should be accepted"
    assert reason is None


def test_negative_duration_rejected(airport_data):
    """Test that negative durations are rejected"""
    # Arrival before departure
    departure = datetime(2025, 12, 15, 12, 0, 0)
    arrival = datetime(2025, 12, 15, 10, 0, 0)  # Before departure!
    
    segment = FlightSegment(
        departure_airport="BOM",
        arrival_airport="DEL",
        departure_time=departure,
        arrival_time=arrival,
        carrier_code="AI",
        carrier_name="Air India",
        flight_number="100",
        duration_minutes=-120,
    )
    
    is_valid, reason = validate_segment_duration(segment, airport_data, "test_provider")
    
    assert not is_valid, "Negative duration should be rejected"
    assert reason == "negative_duration"
    
    metrics = get_validation_metrics()
    assert metrics["dropped_negative_duration"] == 1


def test_itinerary_with_invalid_segment_dropped(airport_data):
    """Test that entire itinerary is dropped if any segment is invalid"""
    # Create an offer with one invalid segment
    departure = datetime(2025, 12, 15, 10, 0, 0)
    arrival = datetime(2025, 12, 15, 10, 15, 0)  # Impossibly short
    
    segment = FlightSegment(
        departure_airport="BOM",
        arrival_airport="DEL",
        departure_time=departure,
        arrival_time=arrival,
        carrier_code="AI",
        carrier_name="Air India",
        flight_number="100",
        duration_minutes=15,
    )
    
    offer = FlightOffer(
        offer_id="test-123",
        provider="test_provider",
        price=5000.0,
        currency="INR",
        segments=[segment],
        total_duration_minutes=15,
        stops=0,
        deep_link="https://example.com",
        cabin_class="economy",
    )
    
    is_valid, _ = validate_and_fix_itinerary(offer, airport_data)
    
    assert not is_valid, "Itinerary with invalid segment should be dropped"


def test_itinerary_duration_recomputed(airport_data):
    """Test that itinerary total duration is recomputed from segments"""
    # Create a valid segment with incorrect provider duration
    departure = datetime(2025, 12, 15, 10, 0, 0)
    arrival = datetime(2025, 12, 15, 12, 0, 0)  # 2 hours
    
    segment = FlightSegment(
        departure_airport="BOM",
        arrival_airport="DEL",
        departure_time=departure,
        arrival_time=arrival,
        carrier_code="AI",
        carrier_name="Air India",
        flight_number="100",
        duration_minutes=90,  # Provider says 90 min, but actual is 120
    )
    
    offer = FlightOffer(
        offer_id="test-123",
        provider="test_provider",
        price=5000.0,
        currency="INR",
        segments=[segment],
        total_duration_minutes=90,  # Incorrect
        stops=0,
        deep_link="https://example.com",
        cabin_class="economy",
    )
    
    is_valid, updated_offer = validate_and_fix_itinerary(offer, airport_data)
    
    assert is_valid, "Valid flight should be accepted"
    assert updated_offer.total_duration_minutes == 120, "Duration should be recomputed to 120"
    assert updated_offer.segments[0].duration_minutes == 120, "Segment duration should be corrected"


def test_validate_flight_offers_filters_invalid(airport_data):
    """Test that batch validation filters out invalid offers"""
    # Create 3 offers: 2 valid, 1 invalid
    valid_departure = datetime(2025, 12, 15, 10, 0, 0)
    valid_arrival = datetime(2025, 12, 15, 12, 0, 0)
    
    valid_segment = FlightSegment(
        departure_airport="BOM",
        arrival_airport="DEL",
        departure_time=valid_departure,
        arrival_time=valid_arrival,
        carrier_code="AI",
        carrier_name="Air India",
        flight_number="100",
        duration_minutes=120,
    )
    
    invalid_departure = datetime(2025, 12, 15, 10, 0, 0)
    invalid_arrival = datetime(2025, 12, 15, 10, 15, 0)
    
    invalid_segment = FlightSegment(
        departure_airport="BOM",
        arrival_airport="DEL",
        departure_time=invalid_departure,
        arrival_time=invalid_arrival,
        carrier_code="AI",
        carrier_name="Air India",
        flight_number="999",
        duration_minutes=15,
    )
    
    offers = [
        FlightOffer(
            offer_id="valid-1",
            provider="test",
            price=5000.0,
            currency="INR",
            segments=[valid_segment],
            total_duration_minutes=120,
            stops=0,
            deep_link="https://example.com",
            cabin_class="economy",
        ),
        FlightOffer(
            offer_id="invalid-1",
            provider="test",
            price=4000.0,
            currency="INR",
            segments=[invalid_segment],
            total_duration_minutes=15,
            stops=0,
            deep_link="https://example.com",
            cabin_class="economy",
        ),
        FlightOffer(
            offer_id="valid-2",
            provider="test",
            price=5500.0,
            currency="INR",
            segments=[valid_segment],
            total_duration_minutes=120,
            stops=0,
            deep_link="https://example.com",
            cabin_class="economy",
        ),
    ]
    
    valid_offers = validate_flight_offers(offers, airport_data)
    
    assert len(valid_offers) == 2, "Should return only 2 valid offers"
    assert all(o.offer_id.startswith("valid") for o in valid_offers)
    
    metrics = get_validation_metrics()
    assert metrics["total_itineraries"] == 3
    assert metrics["dropped_invalid_duration"] == 1


def test_min_duration_floor():
    """Test that minimum duration is at least 30 minutes even for short distances"""
    # Very short distance (e.g., 50 km)
    # min_allowed = max(30, 50 * 0.004 * 60) = max(30, 12) = 30
    departure = datetime(2025, 12, 15, 10, 0, 0)
    arrival = datetime(2025, 12, 15, 10, 35, 0)  # 35 minutes
    
    segment = FlightSegment(
        departure_airport="XXX",
        arrival_airport="YYY",
        departure_time=departure,
        arrival_time=arrival,
        carrier_code="AI",
        carrier_name="Air India",
        flight_number="100",
        duration_minutes=35,
    )
    
    # Without coordinates, should still require at least 30 min
    is_valid, reason = validate_segment_duration(segment, {}, "test_provider")
    
    assert is_valid, "35-minute flight should be valid (above 30 min floor)"


def test_too_short_without_coordinates():
    """Test that flights under 30 minutes are rejected even without coordinate data"""
    departure = datetime(2025, 12, 15, 10, 0, 0)
    arrival = datetime(2025, 12, 15, 10, 20, 0)  # 20 minutes
    
    segment = FlightSegment(
        departure_airport="XXX",
        arrival_airport="YYY",
        departure_time=departure,
        arrival_time=arrival,
        carrier_code="AI",
        carrier_name="Air India",
        flight_number="100",
        duration_minutes=20,
    )
    
    is_valid, reason = validate_segment_duration(segment, {}, "test_provider")
    
    assert not is_valid, "20-minute flight should be rejected (below 30 min floor)"
    assert reason == "duration_too_short"

"""Unit tests for Amadeus adapter with mock fixtures"""

import pytest
import json
import os
from pathlib import Path
from app.services.adapters.amadeus_production import AmadeusAdapter
from app.models.flight import FlightSearchRequest


@pytest.fixture
def amadeus_sample_response():
    """Load Amadeus API sample response fixture"""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "amadeus_sample_response.json"
    with open(fixture_path, 'r') as f:
        return json.load(f)


@pytest.fixture
def search_request():
    """Sample flight search request"""
    return FlightSearchRequest(
        origin="BOM",
        destination="PNQ",
        departure_date="2025-12-15",
        adults=1,
        children=0,
        infants=0,
        cabin_class="economy"
    )


class TestAmadeusAdapter:
    """Test Amadeus adapter functionality"""
    
    def test_adapter_initializes_in_mock_mode(self):
        """Test adapter initializes correctly in mock mode"""
        adapter = AmadeusAdapter(mock_mode=True)
        assert adapter.mock_mode is True
        assert adapter.access_token is None
    
    def test_parse_iso_duration(self):
        """Test ISO 8601 duration parsing"""
        adapter = AmadeusAdapter(mock_mode=True)
        
        assert adapter._parse_iso_duration("PT1H30M") == 90
        assert adapter._parse_iso_duration("PT2H") == 120
        assert adapter._parse_iso_duration("PT45M") == 45
        assert adapter._parse_iso_duration("PT5H40M") == 340
    
    def test_get_carrier_name(self):
        """Test carrier code to name mapping"""
        adapter = AmadeusAdapter(mock_mode=True)
        
        assert adapter._get_carrier_name("6E") == "IndiGo"
        assert adapter._get_carrier_name("AI") == "Air India"
        assert adapter._get_carrier_name("UNKNOWN") == "UNKNOWN"
    
    def test_parse_amadeus_response_direct_flight(self, amadeus_sample_response, search_request):
        """Test parsing Amadeus response for direct flight"""
        adapter = AmadeusAdapter(mock_mode=True)
        offers = adapter._parse_amadeus_response(amadeus_sample_response, search_request)
        
        assert len(offers) == 2  # Two offers in fixture
        
        # Check first offer (direct flight)
        offer = offers[0]
        assert offer.offer_id == "AMD-1"
        assert offer.provider == "amadeus"
        assert offer.price == 8500.0
        assert offer.currency == "INR"
        assert len(offer.segments) == 1
        assert offer.stops == 0
        assert offer.total_duration_minutes == 90
        
        # Check segment details
        segment = offer.segments[0]
        assert segment.departure_airport == "BOM"
        assert segment.arrival_airport == "PNQ"
        assert segment.carrier_code == "6E"
        assert segment.carrier_name == "IndiGo"
        assert segment.flight_number == "6E-2341"
        assert segment.duration_minutes == 90
    
    def test_parse_amadeus_response_connecting_flight(self, amadeus_sample_response, search_request):
        """Test parsing Amadeus response for connecting flight"""
        adapter = AmadeusAdapter(mock_mode=True)
        offers = adapter._parse_amadeus_response(amadeus_sample_response, search_request)
        
        # Check second offer (connecting flight)
        offer = offers[1]
        assert offer.offer_id == "AMD-2"
        assert offer.price == 4800.0
        assert len(offer.segments) == 2  # Two segments (connecting)
        assert offer.stops == 1
        assert offer.total_duration_minutes == 340  # 1h50m + 1h30m + layover
        
        # Check segments
        assert offer.segments[0].departure_airport == "BOM"
        assert offer.segments[0].arrival_airport == "DEL"
        assert offer.segments[1].departure_airport == "DEL"
        assert offer.segments[1].arrival_airport == "PNQ"
    
    @pytest.mark.asyncio
    async def test_mock_flight_search(self, search_request):
        """Test mock flight search returns valid offers"""
        adapter = AmadeusAdapter(mock_mode=True)
        offers = await adapter.search_flights(search_request)
        
        assert len(offers) > 0
        assert all(isinstance(offer.price, float) for offer in offers)
        assert all(offer.currency == "INR" for offer in offers)
        assert all(offer.provider == "amadeus" for offer in offers)
    
    def test_rate_limit_tracking(self):
        """Test rate limit tracking initialization"""
        adapter = AmadeusAdapter(mock_mode=True)
        
        assert adapter.rate_limit_remaining == 100
        assert adapter.rate_limit_reset_at is None
    
    def test_adapter_with_real_keys_not_in_mock_mode(self):
        """Test adapter detects real keys and disables mock mode"""
        adapter = AmadeusAdapter(
            api_key="real_key_123",
            api_secret="real_secret_456",
            mock_mode=False
        )
        assert adapter.mock_mode is False
        assert adapter.api_key == "real_key_123"
    
    def test_baggage_info_extraction(self):
        """Test baggage info extraction (simplified)"""
        adapter = AmadeusAdapter(mock_mode=True)
        baggage = adapter._extract_baggage_info({})
        
        assert isinstance(baggage, str)
        assert len(baggage) > 0
    
    def test_fare_rules_extraction(self):
        """Test fare rules extraction (simplified)"""
        adapter = AmadeusAdapter(mock_mode=True)
        fare_rules = adapter._extract_fare_rules({})
        
        assert isinstance(fare_rules, str)
        assert len(fare_rules) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

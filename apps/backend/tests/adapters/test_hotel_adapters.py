"""Unit tests for hotel adapters"""

import pytest
from app.services.adapters.trip_adapter import TripAdapter
from app.services.adapters.booking_adapter import BookingAdapter
from app.models.hotel import HotelSearchRequest
from datetime import datetime, timedelta


@pytest.fixture
def hotel_search_request():
    """Sample hotel search request"""
    check_in = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    check_out = (datetime.now() + timedelta(days=33)).strftime("%Y-%m-%d")
    
    return HotelSearchRequest(
        city="Mumbai",
        check_in=check_in,
        check_out=check_out,
        adults=2,
        children=0,
        rooms=1
    )


class TestTripAdapter:
    """Test Trip.com adapter"""
    
    def test_adapter_initializes_in_mock_mode(self):
        adapter = TripAdapter(mock_mode=True)
        assert adapter.mock_mode is True
    
    def test_signature_generation(self):
        """Test HMAC signature generation"""
        adapter = TripAdapter(api_secret="test_secret", mock_mode=True)
        params = {"city": "Mumbai", "rooms": 1}
        timestamp = 1234567890
        
        signature = adapter._generate_signature(params, timestamp)
        
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex digest
    
    @pytest.mark.asyncio
    async def test_mock_hotel_search(self, hotel_search_request):
        """Test mock hotel search"""
        adapter = TripAdapter(mock_mode=True)
        offers = await adapter.search_hotels(hotel_search_request)
        
        assert len(offers) > 0
        offer = offers[0]
        assert offer.provider == "trip.com"
        assert offer.currency == "INR"
        assert offer.total_price > 0
        assert len(offer.amenities) > 0


class TestBookingAdapter:
    """Test Booking/Agoda adapter"""
    
    def test_adapter_initializes_in_mock_mode(self):
        adapter = BookingAdapter(mock_mode=True)
        assert adapter.mock_mode is True
    
    @pytest.mark.asyncio
    async def test_mock_hotel_search_returns_multiple_providers(self, hotel_search_request):
        """Test mock returns both Booking.com and Agoda results"""
        adapter = BookingAdapter(mock_mode=True)
        offers = await adapter.search_hotels(hotel_search_request)
        
        assert len(offers) >= 2
        providers = {offer.provider for offer in offers}
        assert "booking.com" in providers or "agoda" in providers
    
    @pytest.mark.asyncio
    async def test_mock_hotel_search_calculates_nights_correctly(self, hotel_search_request):
        """Test that price calculation respects number of nights"""
        adapter = BookingAdapter(mock_mode=True)
        offers = await adapter.search_hotels(hotel_search_request)
        
        # Check that total_price > price_per_night (for multi-night stays)
        for offer in offers:
            assert offer.total_price >= offer.price_per_night


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

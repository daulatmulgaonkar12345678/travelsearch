from typing import List
from datetime import datetime
from app.models.flight import FlightOffer, FlightSearchRequest, FlightSegment
from app.models.hotel import HotelOffer, HotelSearchRequest
from .base import ProviderAdapter

class LCCAdapter(ProviderAdapter):
    """Low-Cost Carrier API adapter with mock data"""
    
    def __init__(self, api_key: str = None, mock_mode: bool = True):
        super().__init__("lcc", mock_mode)
        self.api_key = api_key
    
    async def search_flights(self, request: FlightSearchRequest) -> List[FlightOffer]:
        """Search LCC flights or mock"""
        if self.mock_mode:
            return self._mock_flight_search(request)
        else:
            # Real LCC API integration goes here
            return self._mock_flight_search(request)
    
    def _mock_flight_search(self, request: FlightSearchRequest) -> List[FlightOffer]:
        """Generate realistic mock LCC flight data"""
        departure = datetime.fromisoformat(request.departure_date)
        
        offers = []
        
        # LCC Offer 1: Early morning super saver
        offers.append(FlightOffer(
            offer_id=f"LCC-{request.origin}-{request.destination}-001",
            provider="lcc",
            price=3999.0,
            currency="INR",
            segments=[
                FlightSegment(
                    departure_airport=request.origin,
                    arrival_airport=request.destination,
                    departure_time=departure.replace(hour=5, minute=0),
                    arrival_time=departure.replace(hour=6, minute=40),
                    carrier_code="G8",
                    carrier_name="GoAir",
                    flight_number="G8-331",
                    aircraft_type="A320neo",
                    duration_minutes=100
                )
            ],
            total_duration_minutes=100,
            stops=0,
            baggage_allowance="7 kg cabin only",
            cabin_class="economy",
            fare_rules="Non-refundable, no changes",
            emissions_kg=71.8,
            deep_link=f"https://mock-lcc.com/book?offer=LCC-001",
            rating=70.0
        ))
        
        # LCC Offer 2: Mid-day flight
        offers.append(FlightOffer(
            offer_id=f"LCC-{request.origin}-{request.destination}-002",
            provider="lcc",
            price=5200.0,
            currency="INR",
            segments=[
                FlightSegment(
                    departure_airport=request.origin,
                    arrival_airport=request.destination,
                    departure_time=departure.replace(hour=13, minute=45),
                    arrival_time=departure.replace(hour=15, minute=20),
                    carrier_code="UK",
                    carrier_name="Vistara",
                    flight_number="UK-965",
                    aircraft_type="A320",
                    duration_minutes=95
                )
            ],
            total_duration_minutes=95,
            stops=0,
            baggage_allowance="15 kg checked",
            cabin_class="economy",
            fare_rules="Refundable with 50% fee",
            emissions_kg=74.2,
            deep_link=f"https://mock-lcc.com/book?offer=LCC-002",
            rating=82.0
        ))
        
        return offers
    
    async def search_hotels(self, request: HotelSearchRequest) -> List[HotelOffer]:
        """Hotels not supported by this adapter"""
        return []

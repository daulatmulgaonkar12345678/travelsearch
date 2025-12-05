from typing import List
from datetime import datetime, timedelta
from app.models.flight import FlightOffer, FlightSearchRequest, FlightSegment
from app.models.hotel import HotelOffer, HotelSearchRequest
from .base import ProviderAdapter
import random

class AmadeusAdapter(ProviderAdapter):
    """Amadeus API adapter with realistic mock data"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, mock_mode: bool = True):
        super().__init__("amadeus", mock_mode)
        self.api_key = api_key
        self.api_secret = api_secret
    
    async def search_flights(self, request: FlightSearchRequest) -> List[FlightOffer]:
        """Search flights via Amadeus API or mock"""
        if self.mock_mode:
            return self._mock_flight_search(request)
        else:
            # Real Amadeus API integration goes here
            # from amadeus import Client
            # amadeus = Client(client_id=self.api_key, client_secret=self.api_secret)
            # response = amadeus.shopping.flight_offers_search.get(...)
            return self._mock_flight_search(request)
    
    def _mock_flight_search(self, request: FlightSearchRequest) -> List[FlightOffer]:
        """Generate realistic mock flight data"""
        departure = datetime.fromisoformat(request.departure_date)
        
        # Generate 3 mock offers
        offers = []
        
        # Offer 1: Direct flight - premium
        offers.append(FlightOffer(
            offer_id=f"AMD-{request.origin}-{request.destination}-001",
            provider="amadeus",
            price=8500.0,
            currency="INR",
            segments=[
                FlightSegment(
                    departure_airport=request.origin,
                    arrival_airport=request.destination,
                    departure_time=departure.replace(hour=9, minute=30),
                    arrival_time=departure.replace(hour=11, minute=0),
                    carrier_code="6E",
                    carrier_name="IndiGo",
                    flight_number="6E-2341",
                    aircraft_type="A320",
                    duration_minutes=90
                )
            ],
            total_duration_minutes=90,
            stops=0,
            baggage_allowance="15 kg checked",
            cabin_class=request.cabin_class,
            fare_rules="Non-refundable, change fee applies",
            emissions_kg=75.5,
            deep_link=f"https://mock-provider.com/book?offer=AMD-001",
            rating=85.0
        ))
        
        # Offer 2: Direct flight - budget
        offers.append(FlightOffer(
            offer_id=f"AMD-{request.origin}-{request.destination}-002",
            provider="amadeus",
            price=6200.0,
            currency="INR",
            segments=[
                FlightSegment(
                    departure_airport=request.origin,
                    arrival_airport=request.destination,
                    departure_time=departure.replace(hour=6, minute=15),
                    arrival_time=departure.replace(hour=7, minute=50),
                    carrier_code="SG",
                    carrier_name="SpiceJet",
                    flight_number="SG-8723",
                    aircraft_type="B737",
                    duration_minutes=95
                )
            ],
            total_duration_minutes=95,
            stops=0,
            baggage_allowance="15 kg checked",
            cabin_class=request.cabin_class,
            fare_rules="Non-refundable",
            emissions_kg=78.2,
            deep_link=f"https://mock-provider.com/book?offer=AMD-002",
            rating=78.0
        ))
        
        # Offer 3: One-stop flight - cheapest
        if not request.direct_only:
            offers.append(FlightOffer(
                offer_id=f"AMD-{request.origin}-{request.destination}-003",
                provider="amadeus",
                price=4800.0,
                currency="INR",
                segments=[
                    FlightSegment(
                        departure_airport=request.origin,
                        arrival_airport="DEL",
                        departure_time=departure.replace(hour=14, minute=20),
                        arrival_time=departure.replace(hour=16, minute=10),
                        carrier_code="AI",
                        carrier_name="Air India",
                        flight_number="AI-445",
                        aircraft_type="A320",
                        duration_minutes=110
                    ),
                    FlightSegment(
                        departure_airport="DEL",
                        arrival_airport=request.destination,
                        departure_time=departure.replace(hour=18, minute=30),
                        arrival_time=departure.replace(hour=20, minute=0),
                        carrier_code="AI",
                        carrier_name="Air India",
                        flight_number="AI-892",
                        aircraft_type="A321",
                        duration_minutes=90
                    )
                ],
                total_duration_minutes=340,  # Including layover
                stops=1,
                baggage_allowance="20 kg checked",
                cabin_class=request.cabin_class,
                fare_rules="Refundable with fee",
                emissions_kg=95.3,
                deep_link=f"https://mock-provider.com/book?offer=AMD-003",
                rating=72.0
            ))
        
        return offers
    
    async def search_hotels(self, request: HotelSearchRequest) -> List[HotelOffer]:
        """Hotels not supported by this adapter"""
        return []

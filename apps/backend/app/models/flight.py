from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class FlightSegment(BaseModel):
    """Single flight segment"""
    departure_airport: str  # IATA code
    arrival_airport: str    # IATA code
    departure_time: datetime
    arrival_time: datetime
    carrier_code: str       # Airline IATA code
    carrier_name: str
    flight_number: str
    aircraft_type: Optional[str] = None
    duration_minutes: int
    
class FlightOffer(BaseModel):
    """Normalized flight offer from any provider"""
    offer_id: str
    provider: str           # amadeus, lcc, etc.
    price: float            # Total price in INR
    currency: str = "INR"
    segments: List[FlightSegment]
    total_duration_minutes: int
    stops: int              # 0 for direct, 1+ for connecting
    baggage_allowance: Optional[str] = None
    cabin_class: str = "economy"  # economy, premium_economy, business, first
    fare_rules: Optional[str] = None
    emissions_kg: Optional[float] = None
    deep_link: str          # Provider booking URL
    rating: Optional[float] = None  # Composite rating 0-100
    
    # Nearby airports metadata
    nearby_origin: bool = False
    nearby_destination: bool = False
    source_airport: Optional[str] = None  # Actual departure airport if different from requested
    
class FlightSearchRequest(BaseModel):
    """Flight search parameters"""
    # Trip configuration
    trip_type: str = "roundtrip"  # oneway, roundtrip, multicity
    
    # Basic route (for oneway/roundtrip)
    origin: Optional[str] = None             # IATA code
    destination: Optional[str] = None        # IATA code
    departure_date: Optional[str] = None     # YYYY-MM-DD
    return_date: Optional[str] = None        # For return trips
    
    # Multi-city segments (for multicity)
    segments: Optional[List[dict]] = None  # [{"origin": "BOM", "destination": "DEL", "date": "2025-12-15"}, ...]
    
    # Passengers
    adults: int = 1
    children: Optional[List[int]] = None  # List of ages
    infants: int = 0
    
    # Cabin & preferences
    cabin_class: str = "economy"  # economy, premium_economy, business, first
    
    # Filters
    direct_only: bool = False
    max_stops: Optional[int] = None
    airlines: Optional[List[str]] = None  # Preferred airlines
    max_price: Optional[float] = None
    max_duration_minutes: Optional[int] = None
    refundable_only: bool = False
    include_red_eye: bool = True
    green_only: bool = False
    
    # Nearby airports
    include_nearby_origin: bool = False
    include_nearby_destination: bool = False
    nearby_radius_km: float = 250.0
    
class FlightSearchResponse(BaseModel):
    """Search response with offers"""
    offers: List[FlightOffer]
    search_id: str
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

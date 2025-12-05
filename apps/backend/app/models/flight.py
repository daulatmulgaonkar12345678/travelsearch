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
    
class FlightSearchRequest(BaseModel):
    """Flight search parameters"""
    origin: str             # IATA code
    destination: str        # IATA code
    departure_date: str     # YYYY-MM-DD
    return_date: Optional[str] = None  # For return trips
    adults: int = 1
    children: int = 0
    infants: int = 0
    cabin_class: str = "economy"
    direct_only: bool = False
    max_stops: Optional[int] = None
    
class FlightSearchResponse(BaseModel):
    """Search response with offers"""
    offers: List[FlightOffer]
    search_id: str
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

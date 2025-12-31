from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date

class BookingPartner(BaseModel):
    """Booking partner for redirects"""
    name: str
    url: str
    priority: int = 1
    is_official: bool = False
    description: Optional[str] = None
    is_fallback: bool = False

class HotelOffer(BaseModel):
    """Normalized hotel offer"""
    offer_id: str
    provider: str           # trip, agoda, booking
    hotel_name: str
    address: str
    city: str
    rating: Optional[float] = None  # 1-5 stars
    review_score: Optional[float] = None  # 0-10
    review_count: Optional[int] = None
    price_per_night: float
    total_price: float
    currency: str = "INR"
    amenities: List[str] = []
    room_type: Optional[str] = None
    cancellation_policy: Optional[str] = None
    images: List[str] = []
    deep_link: str
    booking_partners: Optional[List[Dict[str, Any]]] = None  # List of booking partner options
    
class HotelSearchRequest(BaseModel):
    """Hotel search parameters"""
    city: str
    check_in: str           # YYYY-MM-DD
    check_out: str          # YYYY-MM-DD
    
    # Room configuration (can have multiple rooms)
    rooms: List[dict] = [{"adults": 2, "children": []}]  # [{"adults": 2, "children": [5, 8]}, ...]
    
    # Search type: CITY (default), AREA, or HOTEL
    search_type: Optional[str] = "CITY"
    
    # AREA search parameters
    area: Optional[str] = None        # Area/locality name
    latitude: Optional[float] = None  # For geo-based AREA search
    longitude: Optional[float] = None
    
    # HOTEL search parameters
    hotel_id: Optional[str] = None    # Direct hotel lookup
    hotel_name: Optional[str] = None
    
    # Filters
    min_rating: Optional[float] = None  # Star rating 1-5
    max_rating: Optional[float] = None
    min_review_score: Optional[float] = None  # Guest rating 0-10
    max_price: Optional[float] = None
    min_price: Optional[float] = None
    
    # Room type preferences
    room_types: Optional[List[str]] = None  # ["standard", "deluxe", "suite"]
    ac_required: bool = False
    
    # Amenities
    amenities: Optional[List[str]] = None  # ["wifi", "pool", "gym", "parking", "breakfast", "pet_friendly"]
    
    # Policies
    free_cancellation: bool = False
    pay_at_hotel: bool = False
    
    # Location
    max_distance_km: Optional[float] = None  # Distance from city center or area coordinates
    
class HotelSearchResponse(BaseModel):
    """Hotel search response"""
    offers: List[HotelOffer]
    search_id: str
    cached: bool = False
    timestamp: datetime = datetime.utcnow

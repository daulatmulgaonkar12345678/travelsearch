from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date

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
    
class HotelSearchRequest(BaseModel):
    """Hotel search parameters"""
    city: str
    check_in: str           # YYYY-MM-DD
    check_out: str          # YYYY-MM-DD
    
    # Room configuration (can have multiple rooms)
    rooms: List[dict] = [{"adults": 2, "children": []}]  # [{"adults": 2, "children": [5, 8]}, ...]
    
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
    max_distance_km: Optional[float] = None  # Distance from city center
    
class HotelSearchResponse(BaseModel):
    """Hotel search response"""
    offers: List[HotelOffer]
    search_id: str
    cached: bool = False
    timestamp: datetime = datetime.utcnow

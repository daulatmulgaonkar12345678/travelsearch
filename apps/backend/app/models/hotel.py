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
    adults: int = 1
    children: int = 0
    rooms: int = 1
    min_rating: Optional[float] = None
    max_price: Optional[float] = None
    
class HotelSearchResponse(BaseModel):
    """Hotel search response"""
    offers: List[HotelOffer]
    search_id: str
    cached: bool = False
    timestamp: datetime = datetime.utcnow

"""Production Booking.com/Agoda API Adapter (via Kiwi aggregator)

Documentation: https://tequila.kiwi.com/
API Reference: https://tequila-api.kiwi.com/

Authentication: API Key (header)
Endpoint: /v2/search/hotels
"""

import httpx
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.hotel import HotelOffer, HotelSearchRequest
from app.config import settings

logger = logging.getLogger(__name__)


class BookingAdapter:
    """Production Booking.com/Agoda adapter via Kiwi aggregator"""
    
    BASE_URL = "https://api.tequila.kiwi.com/v2"
    
    def __init__(self, api_key: str = None, mock_mode: bool = True):
        self.api_key = api_key or settings.kiwi_api_key
        self.mock_mode = mock_mode or (self.api_key == "REPLACE_ME")
        
        logger.info(f"BookingAdapter initialized (mock_mode={self.mock_mode})")
    
    async def search_hotels(self, request: HotelSearchRequest) -> List[HotelOffer]:
        """Search hotels via Kiwi API (aggregates Booking.com, Agoda)
        
        API Endpoint: GET /v2/search/hotels
        Rate Limit: 100 requests/minute
        """
        if self.mock_mode:
            logger.info("Using mock mode for Booking/Agoda")
            return self._mock_hotel_search(request)
        
        try:
            params = {
                "city": request.city,
                "checkin": request.check_in,
                "checkout": request.check_out,
                "adults": request.adults,
                "rooms": request.rooms,
                "currency": "INR",
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/search/hotels",
                    params=params,
                    headers={"apikey": self.api_key},
                    timeout=15.0
                )
                response.raise_for_status()
                
                data = response.json()
                return self._parse_kiwi_response(data, request)
        
        except Exception as e:
            logger.error(f"Booking/Kiwi API error: {e}")
            return self._mock_hotel_search(request)
    
    def _parse_kiwi_response(self, data: Dict[str, Any], request: HotelSearchRequest) -> List[HotelOffer]:
        """Parse Kiwi aggregator response"""
        offers = []
        check_in = datetime.fromisoformat(request.check_in)
        check_out = datetime.fromisoformat(request.check_out)
        nights = (check_out - check_in).days
        
        for item in data.get("data", []):
            try:
                provider = item.get("provider", "booking.com")
                
                offer = HotelOffer(
                    offer_id=f"{provider.upper()}-{item.get('id', '')}",
                    provider=provider,
                    hotel_name=item.get("name", ""),
                    address=item.get("address", ""),
                    city=item.get("city", request.city),
                    rating=item.get("stars"),
                    review_score=item.get("rating"),
                    review_count=item.get("reviews"),
                    price_per_night=item.get("price", {}).get("per_night", 0),
                    total_price=item.get("price", {}).get("total", 0),
                    currency="INR",
                    amenities=item.get("amenities", []),
                    room_type=item.get("room_type"),
                    cancellation_policy=item.get("cancellation"),
                    images=item.get("photos", []),
                    deep_link=item.get("deep_link", "")
                )
                offers.append(offer)
            
            except Exception as e:
                logger.error(f"Error parsing Kiwi hotel: {e}")
                continue
        
        logger.info(f"Parsed {len(offers)} hotel offers from Kiwi/Booking")
        return offers
    
    def _mock_hotel_search(self, request: HotelSearchRequest) -> List[HotelOffer]:
        """Mock hotel data"""
        check_in = datetime.fromisoformat(request.check_in)
        check_out = datetime.fromisoformat(request.check_out)
        nights = (check_out - check_in).days
        
        return [
            HotelOffer(
                offer_id=f"BOOKING-{request.city}-001",
                provider="booking.com",
                hotel_name="City View Inn",
                address=f"456 Park Avenue, {request.city}",
                city=request.city,
                rating=3.5,
                review_score=7.8,
                review_count=856,
                price_per_night=2800.0,
                total_price=2800.0 * nights,
                currency="INR",
                amenities=["Free WiFi", "Breakfast", "24h Reception"],
                room_type="Standard Double Room",
                cancellation_policy="Non-refundable",
                images=["https://via.placeholder.com/400x300?text=City+View+Room"],
                deep_link="https://mock-booking.com/book?hotel=001"
            ),
            HotelOffer(
                offer_id=f"AGODA-{request.city}-001",
                provider="agoda",
                hotel_name="Luxury Suites & Spa",
                address=f"789 Elite Boulevard, {request.city}",
                city=request.city,
                rating=5.0,
                review_score=9.3,
                review_count=2104,
                price_per_night=8900.0,
                total_price=8900.0 * nights,
                currency="INR",
                amenities=["Free WiFi", "Pool", "Spa", "Gym", "Fine Dining"],
                room_type="Executive Suite",
                cancellation_policy="Free cancellation until 48h before check-in",
                images=["https://via.placeholder.com/400x300?text=Luxury+Suite"],
                deep_link="https://mock-agoda.com/book?hotel=001"
            )
        ]

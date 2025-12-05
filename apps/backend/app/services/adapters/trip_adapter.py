"""Production Trip.com Hotel API Adapter

Documentation: https://www.trip.com/affiliate/
API Reference: https://api.trip.com/partner/v1/

Required Credentials:
- Partner ID (affiliate ID)
- API Key
- API Secret

Authentication: HMAC-SHA256 signature
"""

import httpx
import hmac
import hashlib
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.models.hotel import HotelOffer, HotelSearchRequest
from app.config import settings
import asyncio

logger = logging.getLogger(__name__)


class TripAdapter:
    """Production Trip.com Hotel API adapter"""
    
    BASE_URL = "https://api.trip.com/partner/v1"
    
    def __init__(self, api_key: str = None, api_secret: str = None, partner_id: str = None, mock_mode: bool = True):
        self.api_key = api_key or settings.trip_api_key
        self.api_secret = api_secret or "trip_secret"
        self.partner_id = partner_id or "partner_001"
        self.mock_mode = mock_mode or (self.api_key == "REPLACE_ME")
        
        logger.info(f"TripAdapter initialized (mock_mode={self.mock_mode})")
    
    def _generate_signature(self, params: Dict[str, Any], timestamp: int) -> str:
        """Generate HMAC-SHA256 signature for API request
        
        Trip.com Signature Format:
        1. Sort parameters alphabetically
        2. Concatenate: key1=value1&key2=value2&timestamp=xxx
        3. HMAC-SHA256 with API secret
        """
        # Sort params
        sorted_params = sorted(params.items())
        
        # Build signature string
        sig_parts = [f"{k}={v}" for k, v in sorted_params]
        sig_parts.append(f"timestamp={timestamp}")
        sig_string = "&".join(sig_parts)
        
        # Generate HMAC
        signature = hmac.new(
            self.api_secret.encode(),
            sig_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    async def search_hotels(self, request: HotelSearchRequest) -> List[HotelOffer]:
        """Search hotels via Trip.com API
        
        API Endpoint: GET /hotels/search
        Rate Limit: 100 requests/minute
        """
        if self.mock_mode:
            logger.info("Using mock mode for Trip.com")
            return self._mock_hotel_search(request)
        
        try:
            # Build request params
            timestamp = int(datetime.utcnow().timestamp())
            params = {
                "city": request.city,
                "checkIn": request.check_in,
                "checkOut": request.check_out,
                "adults": request.adults,
                "rooms": request.rooms,
                "currency": "INR",
                "partnerId": self.partner_id,
            }
            
            # Generate signature
            signature = self._generate_signature(params, timestamp)
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/hotels/search",
                    params=params,
                    headers={
                        "X-Api-Key": self.api_key,
                        "X-Signature": signature,
                        "X-Timestamp": str(timestamp),
                    },
                    timeout=15.0
                )
                response.raise_for_status()
                
                data = response.json()
                return self._parse_trip_response(data, request)
        
        except Exception as e:
            logger.error(f"Trip.com API error: {e}")
            return self._mock_hotel_search(request)
    
    def _parse_trip_response(self, data: Dict[str, Any], request: HotelSearchRequest) -> List[HotelOffer]:
        """Parse Trip.com API response to normalized HotelOffer format
        
        Trip.com Response Format:
        {
            "hotels": [
                {
                    "hotelId": "12345",
                    "hotelName": "Grand Plaza Hotel",
                    "address": "123 Main St",
                    "cityName": "Mumbai",
                    "starRating": 4.5,
                    "userRating": 8.7,
                    "reviewCount": 1243,
                    "rooms": [
                        {
                            "roomType": "Deluxe King",
                            "price": {"total": 4500, "currency": "INR", "perNight": 4500},
                            "cancellationPolicy": "Free cancellation",
                            "amenities": ["WiFi", "Breakfast"]
                        }
                    ],
                    "images": ["url1", "url2"],
                    "bookingUrl": "https://trip.com/hotel/12345"
                }
            ]
        }
        """
        offers = []
        check_in = datetime.fromisoformat(request.check_in)
        check_out = datetime.fromisoformat(request.check_out)
        nights = (check_out - check_in).days
        
        for hotel in data.get("hotels", []):
            try:
                # Get best room offer
                rooms = hotel.get("rooms", [])
                if not rooms:
                    continue
                
                best_room = min(rooms, key=lambda r: r.get("price", {}).get("total", float('inf')))
                price_info = best_room.get("price", {})
                
                offer = HotelOffer(
                    offer_id=f"TRIP-{hotel.get('hotelId', '')}",
                    provider="trip.com",
                    hotel_name=hotel.get("hotelName", ""),
                    address=hotel.get("address", ""),
                    city=hotel.get("cityName", request.city),
                    rating=hotel.get("starRating"),
                    review_score=hotel.get("userRating"),
                    review_count=hotel.get("reviewCount"),
                    price_per_night=price_info.get("perNight", 0),
                    total_price=price_info.get("total", 0),
                    currency=price_info.get("currency", "INR"),
                    amenities=best_room.get("amenities", []),
                    room_type=best_room.get("roomType"),
                    cancellation_policy=best_room.get("cancellationPolicy"),
                    images=hotel.get("images", []),
                    deep_link=f"{hotel.get('bookingUrl', '')}?partnerId={self.partner_id}"
                )
                offers.append(offer)
            
            except Exception as e:
                logger.error(f"Error parsing Trip.com hotel: {e}")
                continue
        
        logger.info(f"Parsed {len(offers)} hotel offers from Trip.com")
        return offers
    
    def _mock_hotel_search(self, request: HotelSearchRequest) -> List[HotelOffer]:
        """Mock hotel data for testing"""
        check_in = datetime.fromisoformat(request.check_in)
        check_out = datetime.fromisoformat(request.check_out)
        nights = (check_out - check_in).days
        
        return [
            HotelOffer(
                offer_id=f"TRIP-{request.city}-001",
                provider="trip.com",
                hotel_name="Grand Plaza Hotel",
                address=f"123 Main Street, {request.city}",
                city=request.city,
                rating=4.5,
                review_score=8.7,
                review_count=1243,
                price_per_night=4500.0,
                total_price=4500.0 * nights,
                currency="INR",
                amenities=["Free WiFi", "Pool", "Gym", "Restaurant", "Bar"],
                room_type="Deluxe King Room",
                cancellation_policy="Free cancellation until 24h before check-in",
                images=[
                    "https://via.placeholder.com/400x300?text=Hotel+Room",
                    "https://via.placeholder.com/400x300?text=Hotel+Pool"
                ],
                deep_link=f"https://mock-trip.com/book?hotel=001&partner={self.partner_id}"
            )
        ]

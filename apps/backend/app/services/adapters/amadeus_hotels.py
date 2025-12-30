"""
Amadeus Hotel Search API Adapter
Handles hotel search with city lookup and offer normalization

IMPORTANT: Uses Travelpayouts deep links (https://aviasales.tpx.lt/eqOxwsZu) 
for proper affiliate tracking. Direct Amadeus booking URLs are NOT supported.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import httpx
import logging
from app.models.hotel import HotelOffer, HotelSearchRequest
from app.config import settings
from app.utils.travelpayouts_deeplinks import generate_hotel_deep_link, generate_hotel_booking_partners

logger = logging.getLogger(__name__)

class AmadeusHotelsAdapter:
    """Real Amadeus Hotel Search API integration"""
    
    def __init__(self):
        self.api_key = settings.amadeus_api_key
        self.api_secret = settings.amadeus_api_secret
        self.base_url = settings.amadeus_base_url
        self.environment = settings.amadeus_environment
        
        # Token caching (shared with flight adapter ideally)
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        
        # Check if in mock mode
        self.mock_mode = (
            self.api_key == "REPLACE_ME" or 
            self.api_secret == "REPLACE_ME"
        )
        
        if not self.mock_mode:
            logger.info(f"Amadeus Hotels adapter initialized in {self.environment} mode")
        else:
            logger.warning("Amadeus Hotels adapter running in MOCK mode")
    
    async def get_access_token(self) -> str:
        """
        Obtain OAuth 2.0 access token using client credentials flow.
        Tokens are cached and reused until 5 minutes before expiry.
        """
        # Check if we have a valid cached token
        if self._access_token and self._token_expiry:
            if datetime.now(timezone.utc) < self._token_expiry - timedelta(minutes=5):
                return self._access_token
        
        # Request new token
        token_url = f"{self.base_url}/v1/security/oauth2/token"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    token_url,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.api_key,
                        "client_secret": self.api_secret
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                
                data = response.json()
                self._access_token = data["access_token"]
                
                expires_in = data.get("expires_in", 1799)
                self._token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                
                logger.info("Amadeus access token obtained for hotels")
                return self._access_token
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Amadeus auth error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"Amadeus authentication failed: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Amadeus auth exception: {str(e)}")
                raise Exception(f"Amadeus authentication error: {str(e)}")
    
    async def search_hotels(self, request: HotelSearchRequest) -> List[HotelOffer]:
        """
        Search hotels using Amadeus Hotel Search API.
        
        Amadeus hotel search is a 2-step process:
        1. Get hotel IDs by city code
        2. Get hotel offers for those IDs
        """
        if self.mock_mode:
            logger.warning("Amadeus Hotels is in mock mode - returning empty results")
            return []
        
        try:
            # Step 1: Get city code from city name
            city_code = await self._get_city_code(request.city)
            if not city_code:
                logger.warning(f"Could not find city code for: {request.city}")
                return []
            
            # Step 2: Search hotels by city
            hotel_ids = await self._get_hotel_ids_by_city(city_code)
            if not hotel_ids:
                logger.warning(f"No hotels found in city: {request.city}")
                return []
            
            # Step 3: Get hotel offers
            offers = await self._get_hotel_offers(
                hotel_ids=hotel_ids[:20],  # Limit to first 20 hotels
                check_in=request.check_in,
                check_out=request.check_out,
                rooms=request.rooms
            )
            
            # Normalize to our model
            normalized_offers = self._normalize_hotels(offers, request)
            
            logger.info(f"Amadeus returned {len(normalized_offers)} hotel offers")
            return normalized_offers
            
        except Exception as e:
            logger.error(f"Amadeus hotel search exception: {str(e)}")
            return []
    
    async def _get_city_code(self, city_name: str) -> Optional[str]:
        """
        Get IATA city code from city name using Amadeus Location API.
        
        Example: "Mumbai" -> "BOM"
        """
        try:
            token = await self.get_access_token()
            
            url = f"{self.base_url}/v1/reference-data/locations"
            params = {
                "keyword": city_name,
                "subType": "CITY",
                "page[limit]": 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    locations = data.get("data", [])
                    if locations:
                        return locations[0].get("iataCode")
                
                logger.warning(f"No city code found for: {city_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting city code: {str(e)}")
            return None
    
    async def _get_hotel_ids_by_city(self, city_code: str) -> List[str]:
        """
        Get list of hotel IDs in a city using Amadeus Hotel List API.
        
        Endpoint: GET /v1/reference-data/locations/hotels/by-city
        """
        try:
            token = await self.get_access_token()
            
            url = f"{self.base_url}/v1/reference-data/locations/hotels/by-city"
            params = {
                "cityCode": city_code,
                "radius": 50,  # 50km radius
                "radiusUnit": "KM"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                    params=params,
                    timeout=15.0
                )
                
                if response.status_code == 401:
                    self._access_token = None
                    token = await self.get_access_token()
                    response = await client.get(
                        url,
                        headers={"Authorization": f"Bearer {token}"},
                        params=params,
                        timeout=15.0
                    )
                
                response.raise_for_status()
                data = response.json()
                
                # Extract hotel IDs
                hotels = data.get("data", [])
                hotel_ids = [h.get("hotelId") for h in hotels if h.get("hotelId")]
                
                logger.info(f"Found {len(hotel_ids)} hotels in {city_code}")
                return hotel_ids
                
        except Exception as e:
            logger.error(f"Error getting hotel IDs: {str(e)}")
            return []
    
    async def _get_hotel_offers(
        self, 
        hotel_ids: List[str], 
        check_in: str, 
        check_out: str,
        rooms: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Get hotel offers for specific hotels.
        
        Endpoint: GET /v3/shopping/hotel-offers
        """
        try:
            token = await self.get_access_token()
            
            # Calculate total adults
            total_adults = sum(room.get("adults", 2) for room in rooms)
            
            url = f"{self.base_url}/v3/shopping/hotel-offers"
            params = {
                "hotelIds": ",".join(hotel_ids),
                "checkInDate": check_in,
                "checkOutDate": check_out,
                "adults": total_adults,
                "roomQuantity": len(rooms),
                "currency": "INR",
                "bestRateOnly": "true"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code == 401:
                    self._access_token = None
                    token = await self.get_access_token()
                    response = await client.get(
                        url,
                        headers={"Authorization": f"Bearer {token}"},
                        params=params,
                        timeout=30.0
                    )
                
                response.raise_for_status()
                data = response.json()
                
                return data.get("data", [])
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Amadeus hotel offers error: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Error getting hotel offers: {str(e)}")
            return []
    
    def _normalize_hotels(
        self, 
        hotels: List[Dict[str, Any]], 
        request: HotelSearchRequest
    ) -> List[HotelOffer]:
        """
        Normalize Amadeus hotel offers to our HotelOffer model.
        
        Amadeus response structure:
        {
            "type": "hotel-offers",
            "hotel": {
                "hotelId": "BMBOM123",
                "name": "Taj Mahal Palace",
                "rating": "5",
                "address": {...},
                "contact": {...}
            },
            "offers": [
                {
                    "id": "OFFER123",
                    "price": {"total": "12500.00", "currency": "INR"},
                    "room": {"type": "DELUXE", "typeEstimated": {...}},
                    "policies": {"cancellation": {...}}
                }
            ]
        }
        """
        normalized = []
        
        # Generate Travelpayouts deep link for this search
        deep_link_result = generate_hotel_deep_link(
            city=request.city,
            check_in=request.check_in,
            check_out=request.check_out,
            adults=2,  # Default
            rooms=len(request.rooms) if request.rooms else 1
        )
        travelpayouts_url = deep_link_result["url"]
        
        # Generate booking partners
        booking_partners = generate_hotel_booking_partners(
            city=request.city,
            check_in=request.check_in,
            check_out=request.check_out,
            adults=2,
            rooms=len(request.rooms) if request.rooms else 1
        )
        
        for hotel_data in hotels:
            try:
                hotel_info = hotel_data.get("hotel", {})
                offers = hotel_data.get("offers", [])
                
                if not offers:
                    continue
                
                # Use the first (best) offer
                best_offer = offers[0]
                
                # Extract hotel details
                hotel_id = hotel_info.get("hotelId", "")
                hotel_name = hotel_info.get("name", "Unknown Hotel")
                
                # Address
                address_data = hotel_info.get("address", {})
                address = ", ".join(filter(None, [
                    address_data.get("lines", [""])[0] if address_data.get("lines") else "",
                    address_data.get("cityName", ""),
                    address_data.get("countryCode", "")
                ]))
                city = address_data.get("cityName", request.city)
                
                # Rating
                rating = float(hotel_info.get("rating", 0))
                
                # Price
                price_data = best_offer.get("price", {})
                total_price = float(price_data.get("total", 0))
                currency = price_data.get("currency", "INR")
                
                # Calculate price per night
                check_in = datetime.fromisoformat(request.check_in)
                check_out = datetime.fromisoformat(request.check_out)
                nights = (check_out - check_in).days
                price_per_night = total_price / nights if nights > 0 else total_price
                
                # Room type
                room_data = best_offer.get("room", {})
                room_type = room_data.get("type", "Standard")
                room_desc = room_data.get("typeEstimated", {})
                
                # Amenities (basic from description)
                description = room_desc.get("categoryEstimated", {})
                amenities = []
                if description:
                    amenities.append("WiFi")  # Most hotels have WiFi
                
                # Cancellation policy
                policies = best_offer.get("policies", {})
                cancellation = policies.get("cancellation", {})
                cancellation_policy = "Check hotel policy"
                if cancellation:
                    deadline = cancellation.get("deadline")
                    if deadline:
                        cancellation_policy = f"Free cancellation until {deadline}"
                
                # Use Travelpayouts deep link (NOT Amadeus direct URL)
                # This ensures proper affiliate tracking and working redirects
                normalized.append(HotelOffer(
                    offer_id=f"AMADEUS-{hotel_id}-{best_offer.get('id')}",
                    provider="amadeus",
                    hotel_name=hotel_name,
                    address=address,
                    city=city,
                    rating=rating if rating > 0 else None,
                    review_score=None,  # Amadeus doesn't provide guest reviews
                    review_count=None,
                    price_per_night=price_per_night,
                    total_price=total_price,
                    currency=currency,
                    amenities=amenities,
                    room_type=room_type,
                    cancellation_policy=cancellation_policy,
                    images=[],  # Amadeus requires separate API call for images
                    deep_link=travelpayouts_url,  # Use Travelpayouts redirect
                    booking_partners=booking_partners  # Multiple booking options
                ))
                
            except Exception as e:
                logger.warning(f"Failed to parse Amadeus hotel offer: {str(e)}")
                continue
        
        return normalized

"""
Kiwi.com (Tequila API) Adapter

Backup flight supplier using Kiwi.com's free Tequila API.
Provides fallback coverage during Amadeus rate limiting or outages.

API Documentation: https://tequila.kiwi.com/docs/
Free API: No authentication required for basic searches
"""

import logging
import httpx
from typing import List, Optional
from datetime import datetime

from app.models.flight import FlightOffer, FlightSegment, FlightSearchRequest
from app.config import settings

logger = logging.getLogger(__name__)

class KiwiAdapter:
    """
    Kiwi.com Tequila API integration for backup flight search.
    
    Free tier includes:
    - Up to 100 requests per minute
    - No authentication required
    - Global flight coverage
    
    Used as fallback when:
    - Amadeus returns 429 (rate limited)
    - Amadeus returns 401 (auth failed)
    - Circuit breaker is open
    """
    
    def __init__(self):
        self.base_url = "https://api.tequila.kiwi.com"
        self.api_key = getattr(settings, 'kiwi_api_key', None)
        self.enabled = bool(self.api_key)  # Only enabled if API key is provided
        
        if self.enabled:
            logger.info("✅ Kiwi.com adapter initialized")
        else:
            logger.info("⚠️  Kiwi.com adapter disabled (no API key)")
    
    async def search_flights(self, request: FlightSearchRequest) -> List[FlightOffer]:
        """
        Search flights using Kiwi.com Tequila API
        
        Args:
            request: Flight search request
            
        Returns:
            List of normalized FlightOffer objects
        """
        if not self.enabled:
            logger.warning("Kiwi.com is disabled")
            return []
        
        try:
            logger.info(
                f"🥝 Kiwi.com search: {request.origin} → {request.destination} "
                f"on {request.departure_date}"
            )
            
            # Build API URL
            url = f"{self.base_url}/v2/search"
            
            # Build params
            params = self._build_params(request)
            
            # Make API request
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
                
                if response.status_code != 200:
                    logger.error(
                        f"Kiwi.com error: {response.status_code} - {response.text[:200]}"
                    )
                    return []
                
                data = response.json()
                
                # Normalize response
                offers = self._normalize_response(data, request)
                
                logger.info(f"✅ Kiwi.com returned {len(offers)} offers")
                return offers
                
        except httpx.TimeoutException:
            logger.error("Kiwi.com request timeout")
            return []
        except Exception as e:
            logger.error(f"Kiwi.com error: {e}", exc_info=True)
            return []
    
    def _build_params(self, request: FlightSearchRequest) -> dict:
        """Build Kiwi.com API parameters."""
        params = {
            "fly_from": request.origin,
            "fly_to": request.destination,
            "date_from": request.departure_date,
            "date_to": request.departure_date,
            "adults": request.adults or 1,
            "curr": "INR",  # Indian Rupees
            "limit": 20,  # Max results
            "sort": "price",  # Sort by price
        }
        
        # Add return date for roundtrip
        if request.trip_type == "roundtrip" and request.return_date:
            params["return_from"] = request.return_date
            params["return_to"] = request.return_date
        
        # Add children/infants
        if request.children:
            params["children"] = request.children
        if request.infants:
            params["infants"] = request.infants
        
        # Cabin class mapping
        if request.cabin_class:
            cabin_map = {
                "economy": "M",
                "premium_economy": "W",
                "business": "C",
                "first": "F"
            }
            params["selected_cabins"] = cabin_map.get(request.cabin_class, "M")
        
        return params
    
    def _normalize_response(
        self,
        data: dict,
        request: FlightSearchRequest
    ) -> List[FlightOffer]:
        """
        Normalize Kiwi.com response to our FlightOffer model.
        
        Kiwi.com Response Format:
        {
            "data": [
                {
                    "id": "...",
                    "price": 150.00,
                    "conversion": {"INR": 12500},
                    "airlines": ["AI"],
                    "route": [
                        {
                            "flyFrom": "BOM",
                            "flyTo": "DEL",
                            "local_departure": "2025-12-20T10:00:00",
                            "local_arrival": "2025-12-20T14:00:00",
                            "airline": "AI",
                            "flight_no": 123,
                            "duration": {"total": 7200}
                        }
                    ],
                    "quality": 50.0,
                    "booking_token": "...",
                    "deep_link": "https://..."
                }
            ]
        }
        """
        offers = []
        
        flights = data.get("data", [])
        
        for idx, flight in enumerate(flights):
            try:
                # Parse segments from route
                segments = self._parse_route(flight.get("route", []))
                
                if not segments:
                    continue
                
                # Get price in INR
                price_inr = flight.get("conversion", {}).get("INR", 0)
                if not price_inr:
                    price_inr = flight.get("price", 0) * 83  # Fallback USD to INR conversion
                
                # Calculate duration (in seconds, convert to minutes)
                duration_seconds = flight.get("duration", {}).get("total", 0)
                duration_minutes = duration_seconds // 60
                
                # Count stops
                stops = len(segments) - 1
                
                # Create offer
                offer = FlightOffer(
                    offer_id=f"KIWI-{flight.get('id', idx)}",
                    provider="kiwi",
                    price=float(price_inr),
                    currency="INR",
                    segments=segments,
                    total_duration_minutes=duration_minutes,
                    stops=stops,
                    cabin_class=request.cabin_class,
                    refundable=False,  # Kiwi usually non-refundable
                    baggage_allowance=None,
                    deep_link=flight.get("deep_link", None),
                    booking_url=flight.get("deep_link", None),
                    rating=flight.get("quality", 0),
                    
                    # Metadata
                    nearby_origin=False,
                    nearby_destination=False,
                    source_airport=request.origin
                )
                
                offers.append(offer)
                
            except Exception as e:
                logger.error(f"Error normalizing Kiwi.com flight: {e}")
                continue
        
        return offers
    
    def _parse_route(self, route_data: list) -> List[FlightSegment]:
        """Parse flight route into segments."""
        segments = []
        
        for seg_data in route_data:
            try:
                # Calculate segment duration
                departure_time = seg_data.get("local_departure", "")
                arrival_time = seg_data.get("local_arrival", "")
                
                duration_minutes = 0
                if "duration" in seg_data:
                    duration_seconds = seg_data["duration"].get("total", 0)
                    duration_minutes = duration_seconds // 60
                
                segment = FlightSegment(
                    departure_airport=seg_data.get("flyFrom", ""),
                    arrival_airport=seg_data.get("flyTo", ""),
                    departure_time=departure_time,
                    arrival_time=arrival_time,
                    carrier_code=seg_data.get("airline", ""),
                    carrier_name=seg_data.get("airline_name", seg_data.get("airline", "")),
                    flight_number=str(seg_data.get("flight_no", "")),
                    duration_minutes=duration_minutes,
                    aircraft_type=seg_data.get("vehicle_type", None)
                )
                segments.append(segment)
                
            except Exception as e:
                logger.error(f"Error parsing Kiwi segment: {e}")
                continue
        
        return segments

# Global Kiwi adapter instance
kiwi_adapter = KiwiAdapter()

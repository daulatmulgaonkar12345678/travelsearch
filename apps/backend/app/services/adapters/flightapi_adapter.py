"""
FlightAPI.io Adapter

Backup flight supplier for when Amadeus is unavailable.
Provides fallback coverage during rate limiting or outages.

API Documentation: https://flightapi.io/docs
"""

import logging
import httpx
from typing import List, Optional
from datetime import datetime

from app.models.flight import FlightOffer, FlightSegment, FlightSearchRequest
from app.config import settings

logger = logging.getLogger(__name__)

class FlightAPIAdapter:
    """
    FlightAPI.io integration for backup flight search.
    
    Used as fallback when:
    - Amadeus returns 429 (rate limited)
    - Amadeus returns 401 (auth failed)
    - Circuit breaker is open
    """
    
    def __init__(self):
        self.base_url = "https://api.flightapi.io"
        self.api_key = getattr(settings, 'flightapi_key', None)
        self.enabled = getattr(settings, 'flightapi_enabled', True)
        
        if self.enabled and not self.api_key:
            logger.warning("⚠️  FlightAPI enabled but no API key configured!")
            self.enabled = False
        
        if self.enabled:
            logger.info(f"✅ FlightAPI adapter initialized (key: {self.api_key[:10]}...)")
    
    async def search_flights(self, request: FlightSearchRequest) -> List[FlightOffer]:
        """
        Search flights using FlightAPI.io
        
        Args:
            request: Flight search request
            
        Returns:
            List of normalized FlightOffer objects
        """
        if not self.enabled:
            logger.warning("FlightAPI is disabled or not configured")
            return []
        
        try:
            logger.info(
                f"🔄 FlightAPI search: {request.origin} → {request.destination} "
                f"on {request.departure_date}"
            )
            
            # Build API URL based on trip type
            if request.trip_type == "roundtrip" and request.return_date:
                url = self._build_roundtrip_url(request)
            else:
                url = self._build_oneway_url(request)
            
            # Make API request
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    logger.error(
                        f"FlightAPI error: {response.status_code} - {response.text}"
                    )
                    return []
                
                data = response.json()
                
                # Normalize response
                offers = self._normalize_response(data, request)
                
                logger.info(f"✅ FlightAPI returned {len(offers)} offers")
                return offers
                
        except httpx.TimeoutException:
            logger.error("FlightAPI request timeout")
            return []
        except Exception as e:
            logger.error(f"FlightAPI error: {e}", exc_info=True)
            return []
    
    def _build_oneway_url(self, request: FlightSearchRequest) -> str:
        """Build URL for oneway search."""
        # Format: /oneway/{API_KEY}/{origin}/{destination}/{date}/{adults}
        url = (
            f"{self.base_url}/oneway/{self.api_key}/"
            f"{request.origin}/{request.destination}/"
            f"{request.departure_date}/{request.adults or 1}"
        )
        
        # Add optional parameters
        params = []
        if request.children:
            params.append(f"children={request.children}")
        if request.cabin_class and request.cabin_class != "economy":
            params.append(f"class={request.cabin_class}")
        
        if params:
            url += "?" + "&".join(params)
        
        return url
    
    def _build_roundtrip_url(self, request: FlightSearchRequest) -> str:
        """Build URL for roundtrip search."""
        # Format: /roundtrip/{API_KEY}/{origin}/{destination}/{depart}/{return}/{adults}
        url = (
            f"{self.base_url}/roundtrip/{self.api_key}/"
            f"{request.origin}/{request.destination}/"
            f"{request.departure_date}/{request.return_date}/"
            f"{request.adults or 1}"
        )
        
        # Add optional parameters
        params = []
        if request.children:
            params.append(f"children={request.children}")
        if request.cabin_class and request.cabin_class != "economy":
            params.append(f"class={request.cabin_class}")
        
        if params:
            url += "?" + "&".join(params)
        
        return url
    
    def _normalize_response(
        self,
        data: dict,
        request: FlightSearchRequest
    ) -> List[FlightOffer]:
        """
        Normalize FlightAPI response to our FlightOffer model.
        
        FlightAPI Response Format:
        {
            "flights": [
                {
                    "id": "...",
                    "price": 150.00,
                    "currency": "USD",
                    "airline": "AA",
                    "airline_name": "American Airlines",
                    "departure": "2025-12-20T10:00:00",
                    "arrival": "2025-12-20T14:00:00",
                    "duration": 240,
                    "stops": 0,
                    "segments": [...]
                }
            ]
        }
        """
        offers = []
        
        flights = data.get("flights", [])
        
        for idx, flight in enumerate(flights):
            try:
                # Parse segments
                segments = self._parse_segments(flight.get("segments", []))
                
                if not segments:
                    # Create single segment if no segment data
                    segments = [self._create_default_segment(flight, request)]
                
                # Calculate duration
                duration_minutes = flight.get("duration", 0)
                if not duration_minutes and segments:
                    # Calculate from segments
                    duration_minutes = sum(seg.duration_minutes or 0 for seg in segments)
                
                # Create offer
                offer = FlightOffer(
                    offer_id=f"FLIGHTAPI-{flight.get('id', idx)}",
                    provider="flightapi",
                    price=float(flight.get("price", 0)),
                    currency=flight.get("currency", "USD"),
                    segments=segments,
                    total_duration_minutes=duration_minutes,
                    stops=flight.get("stops", len(segments) - 1),
                    cabin_class=request.cabin_class,
                    refundable=flight.get("refundable", False),
                    baggage_allowance=flight.get("baggage", None),
                    deep_link=flight.get("booking_url", None),
                    booking_url=flight.get("booking_url", None),
                    
                    # Metadata
                    nearby_origin=False,
                    nearby_destination=False,
                    source_airport=request.origin
                )
                
                offers.append(offer)
                
            except Exception as e:
                logger.error(f"Error normalizing FlightAPI flight: {e}")
                continue
        
        return offers
    
    def _parse_segments(self, segments_data: list) -> List[FlightSegment]:
        """Parse flight segments."""
        segments = []
        
        for seg_data in segments_data:
            try:
                segment = FlightSegment(
                    departure_airport=seg_data.get("departure_airport", ""),
                    arrival_airport=seg_data.get("arrival_airport", ""),
                    departure_time=seg_data.get("departure_time", ""),
                    arrival_time=seg_data.get("arrival_time", ""),
                    carrier_code=seg_data.get("airline", ""),
                    carrier_name=seg_data.get("airline_name", ""),
                    flight_number=seg_data.get("flight_number", ""),
                    duration_minutes=seg_data.get("duration", 0),
                    aircraft_type=seg_data.get("aircraft", None)
                )
                segments.append(segment)
            except Exception as e:
                logger.error(f"Error parsing segment: {e}")
                continue
        
        return segments
    
    def _create_default_segment(
        self,
        flight: dict,
        request: FlightSearchRequest
    ) -> FlightSegment:
        """Create a default segment when segment data is missing."""
        return FlightSegment(
            departure_airport=request.origin,
            arrival_airport=request.destination,
            departure_time=flight.get("departure", ""),
            arrival_time=flight.get("arrival", ""),
            carrier_code=flight.get("airline", ""),
            carrier_name=flight.get("airline_name", "Unknown Airline"),
            flight_number=flight.get("flight_number", ""),
            duration_minutes=flight.get("duration", 0),
            aircraft_type=None
        )

# Global FlightAPI instance
flightapi_adapter = FlightAPIAdapter()

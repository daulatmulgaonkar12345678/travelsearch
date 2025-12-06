"""
Duffel Flight API Adapter (Optional Secondary Source)
Provides alternative flight data for comparison
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
import logging
from app.models.flight import FlightOffer, FlightSearchRequest, FlightSegment
from app.config import settings

logger = logging.getLogger(__name__)

class DuffelFlightsAdapter:
    """Duffel Flight Search API integration"""
    
    def __init__(self):
        self.api_token = settings.duffel_test_token
        self.environment = settings.duffel_environment
        self.base_url = "https://api.duffel.com"
        
        # Check if in mock mode
        self.mock_mode = (
            self.api_token == "REPLACE_ME" or 
            not self.api_token
        )
        
        if not self.mock_mode:
            logger.info(f"Duffel Flights adapter initialized in {self.environment} mode")
        else:
            logger.warning("Duffel Flights adapter running in MOCK mode")
    
    async def search_flights(self, request: FlightSearchRequest) -> List[FlightOffer]:
        """
        Search flights using Duffel Offer Requests API.
        
        Duffel uses a 2-step process:
        1. Create an offer request
        2. Poll for results
        """
        if self.mock_mode:
            logger.warning("Duffel is in mock mode - returning empty results")
            return []
        
        try:
            # Create offer request
            offer_request_id = await self._create_offer_request(request)
            if not offer_request_id:
                return []
            
            # Get offers
            offers = await self._get_offers(offer_request_id)
            
            # Normalize to our model
            normalized = self._normalize_offers(offers, request)
            
            logger.info(f"Duffel returned {len(normalized)} flight offers")
            return normalized
            
        except Exception as e:
            logger.error(f"Duffel search exception: {str(e)}")
            return []
    
    async def _create_offer_request(self, request: FlightSearchRequest) -> Optional[str]:
        """
        Create a Duffel offer request.
        
        Endpoint: POST /air/offer_requests
        """
        try:
            url = f"{self.base_url}/air/offer_requests"
            
            # Build request payload
            slices = []
            
            if request.trip_type in ["oneway", "roundtrip"]:
                # Outbound slice
                slices.append({
                    "origin": request.origin,
                    "destination": request.destination,
                    "departure_date": request.departure_date
                })
                
                # Return slice
                if request.trip_type == "roundtrip" and request.return_date:
                    slices.append({
                        "origin": request.destination,
                        "destination": request.origin,
                        "departure_date": request.return_date
                    })
            
            # Build passengers
            passengers = []
            for i in range(request.adults):
                passengers.append({"type": "adult"})
            
            if request.children:
                for age in request.children:
                    passengers.append({
                        "type": "child",
                        "age": age
                    })
            
            if request.infants > 0:
                for i in range(request.infants):
                    passengers.append({"type": "infant_without_seat"})
            
            # Map cabin class
            cabin_class_map = {
                "economy": "economy",
                "premium_economy": "premium_economy",
                "business": "business",
                "first": "first"
            }
            cabin_class = cabin_class_map.get(request.cabin_class, "economy")
            
            payload = {
                "data": {
                    "slices": slices,
                    "passengers": passengers,
                    "cabin_class": cabin_class
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_token}",
                        "Content-Type": "application/json",
                        "Duffel-Version": "v1"
                    },
                    json=payload,
                    timeout=20.0
                )
                
                response.raise_for_status()
                data = response.json()
                
                offer_request_id = data.get("data", {}).get("id")
                logger.info(f"Duffel offer request created: {offer_request_id}")
                return offer_request_id
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Duffel offer request error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error creating Duffel offer request: {str(e)}")
            return None
    
    async def _get_offers(self, offer_request_id: str) -> List[Dict[str, Any]]:
        """
        Get offers from a Duffel offer request.
        
        Endpoint: GET /air/offers?offer_request_id={id}
        """
        try:
            url = f"{self.base_url}/air/offers"
            params = {
                "offer_request_id": offer_request_id,
                "max_connections": 1  # Limit to 1 stop max
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_token}",
                        "Duffel-Version": "v1"
                    },
                    params=params,
                    timeout=30.0
                )
                
                response.raise_for_status()
                data = response.json()
                
                offers = data.get("data", [])
                logger.info(f"Duffel returned {len(offers)} raw offers")
                return offers
                
        except Exception as e:
            logger.error(f"Error getting Duffel offers: {str(e)}")
            return []
    
    def _normalize_offers(
        self, 
        offers: List[Dict[str, Any]], 
        request: FlightSearchRequest
    ) -> List[FlightOffer]:
        """
        Normalize Duffel offers to our FlightOffer model.
        
        Duffel response structure:
        {
            "id": "off_123",
            "slices": [
                {
                    "segments": [
                        {
                            "origin": {"iata_code": "BOM"},
                            "destination": {"iata_code": "PNQ"},
                            "departing_at": "2025-12-20T09:30:00",
                            "arriving_at": "2025-12-20T11:00:00",
                            "marketing_carrier": {"iata_code": "6E", "name": "IndiGo"},
                            "aircraft": {"name": "Airbus A320"},
                            "duration": "PT1H30M"
                        }
                    ]
                }
            ],
            "total_amount": "8500.00",
            "total_currency": "INR"
        }
        """
        normalized = []
        
        for offer in offers:
            try:
                parsed = self._parse_duffel_offer(offer, request)
                if parsed:
                    normalized.append(parsed)
            except Exception as e:
                logger.warning(f"Failed to parse Duffel offer: {str(e)}")
                continue
        
        return normalized
    
    def _parse_duffel_offer(
        self, 
        offer: Dict[str, Any], 
        request: FlightSearchRequest
    ) -> Optional[FlightOffer]:
        """Parse a single Duffel offer"""
        try:
            offer_id = f"DUFFEL-{offer.get('id')}"
            
            # Price
            total_amount = float(offer.get("total_amount", 0))
            currency = offer.get("total_currency", "INR")
            
            # Parse slices (we'll use the first slice for now)
            slices = offer.get("slices", [])
            if not slices:
                return None
            
            first_slice = slices[0]
            segments = []
            total_duration = 0
            
            for seg_data in first_slice.get("segments", []):
                segment = self._parse_duffel_segment(seg_data)
                if segment:
                    segments.append(segment)
                    total_duration += segment.duration_minutes
            
            if not segments:
                return None
            
            # Calculate stops
            stops = len(segments) - 1
            
            # Baggage (Duffel provides detailed baggage info)
            passengers = offer.get("passengers", [])
            baggage = "Standard baggage"
            if passengers:
                baggage_allowance = passengers[0].get("baggage", [])
                if baggage_allowance:
                    bag = baggage_allowance[0]
                    quantity = bag.get("quantity", 0)
                    baggage = f"{quantity} checked bag(s)"
            
            # Deep link (in production, you'd create a Duffel order)
            deep_link = f"https://duffel.com/book/{offer.get('id')}"
            
            return FlightOffer(
                offer_id=offer_id,
                provider="duffel",
                price=total_amount,
                currency=currency,
                segments=segments,
                total_duration_minutes=total_duration,
                stops=stops,
                baggage_allowance=baggage,
                cabin_class=request.cabin_class,
                fare_rules="Check with airline",
                emissions_kg=None,
                deep_link=deep_link,
                rating=None
            )
            
        except Exception as e:
            logger.error(f"Error parsing Duffel offer: {str(e)}")
            return None
    
    def _parse_duffel_segment(self, seg: Dict[str, Any]) -> Optional[FlightSegment]:
        """Parse a single Duffel segment"""
        try:
            origin = seg.get("origin", {})
            destination = seg.get("destination", {})
            
            # Parse timestamps
            dep_time = datetime.fromisoformat(
                seg.get("departing_at", "").replace("Z", "+00:00")
            )
            arr_time = datetime.fromisoformat(
                seg.get("arriving_at", "").replace("Z", "+00:00")
            )
            
            # Duration
            duration_str = seg.get("duration", "PT0M")
            duration_minutes = self._parse_duration(duration_str)
            
            # Carrier
            carrier = seg.get("marketing_carrier", {})
            carrier_code = carrier.get("iata_code", "")
            carrier_name = carrier.get("name", carrier_code)
            
            flight_number = f"{carrier_code}-{seg.get('marketing_carrier_flight_number', '')}"
            
            # Aircraft
            aircraft = seg.get("aircraft", {})
            aircraft_type = aircraft.get("iata_code", "")
            
            return FlightSegment(
                departure_airport=origin.get("iata_code", ""),
                arrival_airport=destination.get("iata_code", ""),
                departure_time=dep_time,
                arrival_time=arr_time,
                carrier_code=carrier_code,
                carrier_name=carrier_name,
                flight_number=flight_number,
                aircraft_type=aircraft_type,
                duration_minutes=duration_minutes
            )
            
        except Exception as e:
            logger.error(f"Error parsing Duffel segment: {str(e)}")
            return None
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration to minutes"""
        import re
        hours = 0
        minutes = 0
        
        hour_match = re.search(r'(\d+)H', duration_str)
        if hour_match:
            hours = int(hour_match.group(1))
        
        minute_match = re.search(r'(\d+)M', duration_str)
        if minute_match:
            minutes = int(minute_match.group(1))
        
        return hours * 60 + minutes

"""
Amadeus Flight Offers API Adapter
Handles real API integration with OAuth 2.0 authentication
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import httpx
import logging
from app.models.flight import FlightOffer, FlightSearchRequest, FlightSegment
from app.config import settings

logger = logging.getLogger(__name__)

class AmadeusFlightsAdapter:
    """Real Amadeus Flight Offers API integration"""
    
    def __init__(self):
        self.api_key = settings.amadeus_api_key
        self.api_secret = settings.amadeus_api_secret
        self.base_url = settings.amadeus_base_url
        self.environment = settings.amadeus_environment
        
        # Token caching
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        
        # Check if in mock mode
        self.mock_mode = (
            self.api_key == "REPLACE_ME" or 
            self.api_secret == "REPLACE_ME"
        )
        
        if not self.mock_mode:
            logger.info(f"Amadeus Flights adapter initialized in {self.environment} mode")
        else:
            logger.warning("Amadeus Flights adapter running in MOCK mode")
    
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
                
                # Token typically expires in 1799 seconds (30 minutes)
                expires_in = data.get("expires_in", 1799)
                self._token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                
                logger.info("Amadeus access token obtained successfully")
                return self._access_token
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Amadeus auth error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"Amadeus authentication failed: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Amadeus auth exception: {str(e)}")
                raise Exception(f"Amadeus authentication error: {str(e)}")
    
    async def search_flights(self, request: FlightSearchRequest) -> List[FlightOffer]:
        """Search flights using Amadeus Flight Offers API"""
        if self.mock_mode:
            logger.warning("Amadeus is in mock mode - returning empty results")
            return []
        
        try:
            # Get access token
            token = await self.get_access_token()
            
            # Build request parameters
            params = self._build_search_params(request)
            
            # Call Amadeus API
            search_url = f"{self.base_url}/v2/shopping/flight-offers"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    search_url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/json"
                    },
                    params=params,
                    timeout=30.0
                )
                
                # Handle 401 (token expired) by refreshing token
                if response.status_code == 401:
                    logger.info("Token expired, refreshing...")
                    self._access_token = None  # Force token refresh
                    token = await self.get_access_token()
                    
                    # Retry request
                    response = await client.get(
                        search_url,
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Accept": "application/json"
                        },
                        params=params,
                        timeout=30.0
                    )
                
                response.raise_for_status()
                data = response.json()
                
                # Normalize response to our FlightOffer model
                offers = self._normalize_response(data, request)
                
                logger.info(f"Amadeus returned {len(offers)} flight offers")
                return offers
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Amadeus API error: {e.response.status_code} - {e.response.text}")
            return []  # Return empty on error, don't crash the aggregator
        except Exception as e:
            logger.error(f"Amadeus search exception: {str(e)}")
            return []
    
    def _build_search_params(self, request: FlightSearchRequest) -> Dict[str, Any]:
        """Convert internal search request to Amadeus API parameters"""
        params = {
            "originLocationCode": request.origin.upper() if request.origin else "",
            "destinationLocationCode": request.destination.upper() if request.destination else "",
            "departureDate": request.departure_date,
            "adults": request.adults,
            "currencyCode": "INR",
            "max": 50  # Limit results
        }
        
        # Optional parameters
        if request.return_date and request.trip_type == "roundtrip":
            params["returnDate"] = request.return_date
        
        if request.children and len(request.children) > 0:
            params["children"] = len(request.children)
        
        if request.infants > 0:
            params["infants"] = request.infants
        
        if request.cabin_class and request.cabin_class != "economy":
            # Map our cabin class to Amadeus values
            cabin_map = {
                "economy": "ECONOMY",
                "premium_economy": "PREMIUM_ECONOMY",
                "business": "BUSINESS",
                "first": "FIRST"
            }
            params["travelClass"] = cabin_map.get(request.cabin_class, "ECONOMY")
        
        if request.direct_only:
            params["nonStop"] = "true"
        
        if request.max_price:
            params["maxPrice"] = int(request.max_price)
        
        return params
    
    def _normalize_response(self, data: Dict[str, Any], request: FlightSearchRequest) -> List[FlightOffer]:
        """
        Normalize Amadeus API response to our FlightOffer model.
        
        Amadeus response structure:
        {
            "data": [
                {
                    "id": "1",
                    "type": "flight-offer",
                    "price": {"currency": "INR", "total": "8500.00", "base": "7500.00"},
                    "itineraries": [
                        {
                            "segments": [
                                {
                                    "departure": {"iataCode": "BOM", "at": "2025-12-20T09:30:00"},
                                    "arrival": {"iataCode": "PNQ", "at": "2025-12-20T11:00:00"},
                                    "carrierCode": "6E",
                                    "number": "2341",
                                    "aircraft": {"code": "320"},
                                    "duration": "PT1H30M"
                                }
                            ]
                        }
                    ],
                    "travelerPricings": [...]
                }
            ]
        }
        """
        offers = []
        
        for item in data.get("data", []):
            try:
                offer = self._parse_flight_offer(item, request)
                if offer:
                    offers.append(offer)
            except Exception as e:
                logger.warning(f"Failed to parse Amadeus offer: {str(e)}")
                continue
        
        return offers
    
    def _parse_flight_offer(self, item: Dict[str, Any], request: FlightSearchRequest) -> Optional[FlightOffer]:
        """Parse a single Amadeus flight offer"""
        try:
            offer_id = f"AMADEUS-{item['id']}"
            
            # Extract price
            price_data = item.get("price", {})
            total_price = float(price_data.get("total", 0))
            currency = price_data.get("currency", "INR")
            
            # Parse itineraries (typically 1 for oneway, 2 for roundtrip)
            # For now, we'll focus on the outbound itinerary (first one)
            itineraries = item.get("itineraries", [])
            if not itineraries:
                return None
            
            outbound = itineraries[0]
            segments = []
            total_duration = 0
            
            # Parse segments
            for seg in outbound.get("segments", []):
                segment = self._parse_segment(seg)
                if segment:
                    segments.append(segment)
                    total_duration += segment.duration_minutes
            
            if not segments:
                return None
            
            # Calculate stops
            stops = len(segments) - 1
            
            # Extract additional info
            traveler_pricings = item.get("travelerPricings", [])
            baggage_allowance = self._extract_baggage(traveler_pricings)
            fare_rules = self._extract_fare_rules(traveler_pricings)
            
            # Build deep link (Amadeus doesn't provide direct booking URLs in test mode)
            # In production, you'd use the offer ID to create a booking
            deep_link = f"{self.base_url}/booking?offer={item['id']}"
            
            return FlightOffer(
                offer_id=offer_id,
                provider="amadeus",
                price=total_price,
                currency=currency,
                segments=segments,
                total_duration_minutes=total_duration,
                stops=stops,
                baggage_allowance=baggage_allowance,
                cabin_class=request.cabin_class,
                fare_rules=fare_rules,
                emissions_kg=None,  # Amadeus doesn't always provide this
                deep_link=deep_link,
                rating=None  # Could be calculated based on price/duration/stops
            )
            
        except Exception as e:
            logger.error(f"Error parsing Amadeus offer: {str(e)}")
            return None
    
    def _parse_segment(self, seg: Dict[str, Any]) -> Optional[FlightSegment]:
        """Parse a single flight segment"""
        try:
            departure = seg.get("departure", {})
            arrival = seg.get("arrival", {})
            
            # Parse ISO datetime strings
            dep_time = datetime.fromisoformat(departure.get("at", "").replace("Z", "+00:00"))
            arr_time = datetime.fromisoformat(arrival.get("at", "").replace("Z", "+00:00"))
            
            # Calculate duration in minutes
            duration_str = seg.get("duration", "PT0M")  # Format: PT1H30M
            duration_minutes = self._parse_duration(duration_str)
            
            # Get carrier info
            carrier_code = seg.get("carrierCode", "")
            flight_number = f"{carrier_code}-{seg.get('number', '')}"
            
            # Aircraft type
            aircraft = seg.get("aircraft", {}).get("code", "")
            
            return FlightSegment(
                departure_airport=departure.get("iataCode", ""),
                arrival_airport=arrival.get("iataCode", ""),
                departure_time=dep_time,
                arrival_time=arr_time,
                carrier_code=carrier_code,
                carrier_name=self._get_carrier_name(carrier_code),
                flight_number=flight_number,
                aircraft_type=aircraft,
                duration_minutes=duration_minutes
            )
        except Exception as e:
            logger.error(f"Error parsing segment: {str(e)}")
            return None
    
    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse ISO 8601 duration string to minutes.
        Example: PT1H30M -> 90 minutes
        """
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
    
    def _get_carrier_name(self, carrier_code: str) -> str:
        """Map IATA airline codes to names"""
        # Basic mapping - in production, use a comprehensive airline database
        airline_names = {
            "6E": "IndiGo",
            "AI": "Air India",
            "SG": "SpiceJet",
            "UK": "Vistara",
            "G8": "Go First",
            "I5": "AirAsia India",
            "QP": "Akasa Air",
            "BA": "British Airways",
            "EK": "Emirates",
            "QR": "Qatar Airways",
            "EY": "Etihad Airways",
            "AA": "American Airlines",
            "UA": "United Airlines",
            "DL": "Delta Air Lines",
        }
        return airline_names.get(carrier_code, carrier_code)
    
    def _extract_baggage(self, traveler_pricings: List[Dict]) -> str:
        """Extract baggage allowance from traveler pricings"""
        if not traveler_pricings:
            return "Standard baggage"
        
        first_traveler = traveler_pricings[0]
        fare_detail = first_traveler.get("fareDetailsBySegment", [])
        
        if fare_detail:
            included_bags = fare_detail[0].get("includedCheckedBags", {})
            quantity = included_bags.get("quantity", 0)
            weight = included_bags.get("weight", 0)
            weight_unit = included_bags.get("weightUnit", "KG")
            
            if quantity:
                return f"{quantity} bag(s)"
            elif weight:
                return f"{weight} {weight_unit}"
        
        return "Standard baggage"
    
    def _extract_fare_rules(self, traveler_pricings: List[Dict]) -> str:
        """Extract basic fare rules"""
        # Amadeus provides detailed fare rules, but extracting key info
        # In production, you'd parse refundability, change fees, etc.
        return "Check with airline for detailed fare rules"

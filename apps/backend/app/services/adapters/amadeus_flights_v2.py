"""
Amadeus Flight Offers API Adapter V2

KEY FEATURES:
- Uses centralized config (single source of truth)
- Comprehensive debug logging at every step
- Raises exceptions instead of silently returning empty arrays
- No credential caching issues
- Full token request/response logging
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import httpx
import logging
import json
from app.models.flight import FlightOffer, FlightSearchRequest, FlightSegment
from app.core.config import settings

logger = logging.getLogger(__name__)

class AmadeusFlightsAdapterV2:
    """Amadeus Flight Offers API integration with full debug logging"""
    
    def __init__(self):
        # Use centralized config - SINGLE SOURCE OF TRUTH
        self.api_key = settings.amadeus_api_key
        self.api_secret = settings.amadeus_api_secret
        self.base_url = settings.amadeus_base_url
        self.environment = settings.amadeus_environment
        
        # CRITICAL: Log what credentials are being used
        logger.info("""
        ================================================
        AMADEUS ADAPTER V2 INITIALIZATION
        ================================================
        API Key (first 8, last 4): {}...{}
        API Secret (first 4, last 4): {}...{}
        Base URL: {}
        Environment: {}
        ================================================
        """.format(
            self.api_key[:8],
            self.api_key[-4:],
            self.api_secret[:4],
            self.api_secret[-4:],
            self.base_url,
            self.environment
        ))
        
        # Validate credentials are not default/empty
        if not self.api_key or self.api_key == "REPLACE_ME":
            logger.error("❌ CRITICAL: Amadeus API Key is not set or is default value")
            raise ValueError("Amadeus API Key must be configured in .env")
        
        if not self.api_secret or self.api_secret == "REPLACE_ME":
            logger.error("❌ CRITICAL: Amadeus API Secret is not set or is default value")
            raise ValueError("Amadeus API Secret must be configured in .env")
        
        # Token caching
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        
        logger.info("✅ AmadeusFlightsAdapterV2 initialized successfully")
    
    async def get_access_token(self) -> str:
        """
        Obtain OAuth 2.0 access token with FULL DEBUG LOGGING.
        Logs every step of the authentication process.
        """
        # Check if we have a valid cached token
        if self._access_token and self._token_expiry:
            if datetime.now(timezone.utc) < self._token_expiry - timedelta(minutes=5):
                logger.info(f"✅ Using cached token (expires in {(self._token_expiry - datetime.now(timezone.utc)).seconds}s)")
                return self._access_token
        
        # Request new token
        token_url = f"{self.base_url}/v1/security/oauth2/token"
        
        logger.info("""
        ================================================
        REQUESTING NEW AMADEUS ACCESS TOKEN
        ================================================
        Token URL: {}
        Grant Type: client_credentials
        Client ID: {}...{}
        Client Secret: {}...{}
        ================================================
        """.format(
            token_url,
            self.api_key[:8],
            self.api_key[-4:],
            self.api_secret[:4],
            self.api_secret[-4:]
        ))
        
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret
        }
        
        async with httpx.AsyncClient() as client:
            try:
                logger.info("Sending POST request to Amadeus token endpoint...")
                response = await client.post(
                    token_url,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data=payload,
                    timeout=10.0
                )
                
                logger.info(f"Token response status: {response.status_code}")
                logger.info(f"Token response headers: {dict(response.headers)}")
                
                # Log response body (mask token)
                try:
                    response_json = response.json()
                    logger.info(f"Token response body (keys): {list(response_json.keys())}")
                except:
                    logger.error(f"Token response body (raw): {response.text[:200]}")
                
                # Check for errors
                if response.status_code == 401:
                    logger.error("""
                    ================================================
                    ❌ AMADEUS AUTH FAILED - 401 UNAUTHORIZED
                    ================================================
                    This means the credentials are INVALID.
                    
                    Current credentials being used:
                    - API Key: {}...{}
                    - API Secret: {}...{}
                    - Base URL: {}
                    
                    Response: {}
                    ================================================
                    """.format(
                        self.api_key[:8],
                        self.api_key[-4:],
                        self.api_secret[:4],
                        self.api_secret[-4:],
                        self.base_url,
                        response.text
                    ))
                    raise Exception(f"Amadeus authentication failed: 401 - Invalid credentials. Check .env file.")
                
                response.raise_for_status()
                
                data = response.json()
                self._access_token = data["access_token"]
                
                # Token typically expires in 1799 seconds (30 minutes)
                expires_in = data.get("expires_in", 1799)
                self._token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                
                logger.info("""
                ================================================
                ✅ AMADEUS TOKEN OBTAINED SUCCESSFULLY
                ================================================
                Token (first 10, last 6): {}...{}
                Expires in: {} seconds
                Expiry time: {}
                ================================================
                """.format(
                    self._access_token[:10],
                    self._access_token[-6:],
                    expires_in,
                    self._token_expiry
                ))
                
                return self._access_token
                
            except httpx.HTTPStatusError as e:
                logger.error("""
                ================================================
                ❌ AMADEUS AUTH HTTP ERROR
                ================================================
                Status Code: {}
                Response: {}
                Credentials Used:
                - Key: {}...{}
                - Secret: {}...{}
                ================================================
                """.format(
                    e.response.status_code,
                    e.response.text,
                    self.api_key[:8],
                    self.api_key[-4:],
                    self.api_secret[:4],
                    self.api_secret[-4:]
                ))
                raise Exception(f"Amadeus authentication failed: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logger.error(f"❌ Amadeus auth exception: {str(e)}")
                raise Exception(f"Amadeus authentication error: {str(e)}")
    
    async def search_flights(self, request: FlightSearchRequest) -> List[FlightOffer]:
        """Search flights using Amadeus Flight Offers API with full error propagation"""
        logger.info(f"Starting Amadeus flight search: {request.origin} → {request.destination}")
        
        try:
            # Get access token (will raise exception if fails)
            token = await self.get_access_token()
            logger.info("✅ Token obtained, building search parameters...")
            
            # Build request parameters
            params = self._build_search_params(request)
            logger.info(f"Search params: {params}")
            
            # Call Amadeus API
            search_url = f"{self.base_url}/v2/shopping/flight-offers"
            logger.info(f"Calling Amadeus API: {search_url}")
            
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
                
                logger.info(f"Amadeus search response status: {response.status_code}")
                
                # Handle 401 (token expired) by refreshing token
                if response.status_code == 401:
                    logger.info("⚠️  Token expired, refreshing...")
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
                    logger.info(f"Retry response status: {response.status_code}")
                
                # Handle 429 rate limiting
                if response.status_code == 429:
                    logger.error("❌ Amadeus 429 - Rate limit exceeded")
                    raise Exception("Amadeus rate limit exceeded (429)")
                
                # Raise for other errors
                if response.status_code != 200:
                    logger.error(f"❌ Amadeus API error: {response.status_code} - {response.text}")
                    raise Exception(f"Amadeus API error: {response.status_code}")
                
                data = response.json()
                
                # Debug: Log raw data count
                raw_offers = data.get("data", [])
                logger.info(f"✅ Amadeus returned {len(raw_offers)} raw offers")
                
                if len(raw_offers) == 0:
                    logger.warning(f"⚠️  No offers from Amadeus for {request.origin} → {request.destination}")
                    logger.info(f"Full response: {json.dumps(data, indent=2)[:500]}...")
                    return []
                
                # Normalize response to our FlightOffer model
                offers = self._normalize_response(data, request)
                
                logger.info(f"✅ Amadeus search completed: {len(offers)} offers normalized")
                return offers
                
        except Exception as e:
            logger.error(f"❌ Amadeus search FAILED: {str(e)}")
            # IMPORTANT: Raise the exception instead of returning empty array
            raise
    
    def _build_search_params(self, request: FlightSearchRequest) -> Dict[str, Any]:
        """Convert internal search request to Amadeus API parameters"""
        params = {
            "originLocationCode": request.origin.upper() if request.origin else "",
            "destinationLocationCode": request.destination.upper() if request.destination else "",
            "departureDate": request.departure_date,
            "adults": request.adults,
            "currencyCode": "INR",
            "max": 50
        }
        
        # Optional parameters
        if request.return_date and request.trip_type == "roundtrip":
            params["returnDate"] = request.return_date
        
        if request.children and len(request.children) > 0:
            params["children"] = len(request.children)
        
        if request.infants > 0:
            params["infants"] = request.infants
        
        if request.cabin_class and request.cabin_class != "economy":
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
        """Normalize Amadeus API response to our FlightOffer model"""
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
            
            # Parse itineraries
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
            
            stops = len(segments) - 1
            
            traveler_pricings = item.get("travelerPricings", [])
            baggage_allowance = self._extract_baggage(traveler_pricings)
            fare_rules = self._extract_fare_rules(traveler_pricings)
            
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
                emissions_kg=None,
                deep_link=deep_link,
                rating=None
            )
            
        except Exception as e:
            logger.error(f"Error parsing Amadeus offer: {str(e)}")
            return None
    
    def _parse_segment(self, seg: Dict[str, Any]) -> Optional[FlightSegment]:
        """Parse a single flight segment"""
        try:
            departure = seg.get("departure", {})
            arrival = seg.get("arrival", {})
            
            dep_time = datetime.fromisoformat(departure.get("at", "").replace("Z", "+00:00"))
            arr_time = datetime.fromisoformat(arrival.get("at", "").replace("Z", "+00:00"))
            
            duration_str = seg.get("duration", "PT0M")
            duration_minutes = self._parse_duration(duration_str)
            
            carrier_code = seg.get("carrierCode", "")
            flight_number = f"{carrier_code}-{seg.get('number', '')}"
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
        """Parse ISO 8601 duration string to minutes"""
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
        return "Check with airline for detailed fare rules"

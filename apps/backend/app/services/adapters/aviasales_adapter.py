"""
Aviasales / Travelpayouts Data API Adapter

PRIMARY flight search provider. Uses real-time pricing data from Travelpayouts API.

API Documentation: https://support.travelpayouts.com/hc/en-us/articles/203956163-Data-API

Key Endpoints:
- /aviasales/v3/prices_for_dates - Prices for specific dates
- /aviasales/v3/prices_latest - Latest/cheapest prices

CRITICAL:
- API token read from environment (never hardcode)
- Returns real deeplinks with affiliate marker
- No manual link generation for search results
"""

import httpx
import logging
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.flight import FlightOffer, FlightSegment, FlightSearchRequest
from app.core.config import settings

logger = logging.getLogger(__name__)

# Travelpayouts API Configuration
TRAVELPAYOUTS_BASE_URL = "https://api.travelpayouts.com"


class AviasalesAdapter:
    """
    Aviasales/Travelpayouts Data API adapter for real flight pricing.
    
    This is the PRIMARY flight search provider.
    """
    
    def __init__(self):
        # Get API token from settings (loaded from .env) or environment
        self.api_token = (
            getattr(settings, "travelpayouts_api_token", None) or 
            os.environ.get("TRAVELPAYOUTS_API_TOKEN")
        )
        self.marker = (
            getattr(settings, "travelpayouts_marker", None) or 
            os.environ.get("TRAVELPAYOUTS_MARKER", "689331")
        )
        
        if not self.api_token:
            logger.error("❌ TRAVELPAYOUTS_API_TOKEN not set!")
            raise ValueError("TRAVELPAYOUTS_API_TOKEN is required")
        
        self.base_url = TRAVELPAYOUTS_BASE_URL
        self.timeout = 10.0  # 10 second timeout
        
        logger.info(f"✅ AviasalesAdapter initialized with token starting: {self.api_token[:6]}... marker: {self.marker}")
    
    async def search_flights(
        self, 
        request: FlightSearchRequest
    ) -> List[FlightOffer]:
        """
        Search flights using Travelpayouts Data API.
        
        Uses /v2/prices/month-matrix endpoint for specific date searches.
        Falls back to /aviasales/v3/prices_for_dates if needed.
        Returns normalized FlightOffer objects with real deeplinks.
        """
        try:
            logger.info(
                f"🔍 Aviasales search: {request.origin} → {request.destination} "
                f"on {request.departure_date}"
            )
            
            # Try month-matrix endpoint first (more reliable for Indian routes)
            offers = await self._search_month_matrix(request)
            if offers:
                return offers
            
            # Fallback to prices_for_dates
            offers = await self._search_prices_for_dates(request)
            return offers
        
        except httpx.TimeoutException:
            logger.error("❌ Aviasales API timeout")
            return []
        except Exception as e:
            logger.error(f"❌ Aviasales search error: {e}", exc_info=True)
            return []
    
    async def _search_month_matrix(
        self,
        request: FlightSearchRequest
    ) -> List[FlightOffer]:
        """Search using /v2/prices/month-matrix endpoint."""
        try:
            # Extract month from date
            date_parts = request.departure_date.split('-')
            month = f"{date_parts[0]}-{date_parts[1]}"
            
            endpoint = f"{self.base_url}/v2/prices/month-matrix"
            
            params = {
                "origin": request.origin,
                "destination": request.destination,
                "month": month,
                "currency": "INR",
                "token": self.api_token,
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(endpoint, params=params)
                
                logger.info(f"Month-matrix API response: {response.status_code}")
                
                if response.status_code != 200:
                    logger.warning(f"Month-matrix error: {response.status_code}")
                    return []
                
                data = response.json()
            
            flights = data.get("data", [])
            logger.info(f"✅ Month-matrix returned {len(flights)} prices")
            
            if not flights:
                return []
            
            # Filter for requested date (or closest)
            target_date = request.departure_date
            
            # Try exact date match first
            exact_match = [f for f in flights if f.get("depart_date") == target_date]
            if exact_match:
                return self._normalize_flights_v2(exact_match, request)
            
            # Return closest dates
            sorted_flights = sorted(flights, key=lambda x: abs(
                (datetime.strptime(x.get("depart_date", "2099-01-01"), "%Y-%m-%d") - 
                 datetime.strptime(target_date, "%Y-%m-%d")).days
            ))
            
            return self._normalize_flights_v2(sorted_flights[:10], request)
        
        except Exception as e:
            logger.error(f"Month-matrix search error: {e}")
            return []
    
    async def _search_prices_for_dates(
        self,
        request: FlightSearchRequest
    ) -> List[FlightOffer]:
        """Search using /aviasales/v3/prices_for_dates endpoint."""
        try:
            endpoint = f"{self.base_url}/aviasales/v3/prices_for_dates"
            
            params = {
                "origin": request.origin,
                "destination": request.destination,
                "departure_at": request.departure_date,
                "currency": "INR",
                "sorting": "price",
                "direct": "true" if request.direct_only else "false",
                "limit": 30,
                "token": self.api_token,
            }
            
            if request.trip_type == "roundtrip" and request.return_date:
                params["return_at"] = request.return_date
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(endpoint, params=params)
                
                if response.status_code != 200:
                    logger.error(f"Aviasales API error: {response.status_code}")
                    return []
                
                data = response.json()
            
            if data.get("success", True) is not False:
                flights = data.get("data", [])
                logger.info(f"✅ prices_for_dates returned {len(flights)} flights")
                
                if flights:
                    return self._normalize_flights(flights, request)
            
            return []
        
        except Exception as e:
            logger.error(f"prices_for_dates error: {e}")
            return []
    
    async def search_prices_latest(
        self,
        origin: str,
        destination: str,
        limit: int = 30
    ) -> List[Dict]:
        """
        Get latest/cheapest prices for a route (no specific date).
        Useful for price calendars and flexible date searches.
        """
        try:
            endpoint = f"{self.base_url}/aviasales/v3/prices_latest"
            
            params = {
                "origin": origin,
                "destination": destination,
                "currency": "INR",
                "limit": limit,
                "token": self.api_token,
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(endpoint, params=params)
                
                if response.status_code != 200:
                    logger.error(f"Aviasales prices_latest error: {response.status_code}")
                    return []
                
                data = response.json()
                return data.get("data", [])
        
        except Exception as e:
            logger.error(f"Aviasales prices_latest error: {e}")
            return []
    
    def _normalize_flights(
        self,
        flights: List[Dict],
        request: FlightSearchRequest
    ) -> List[FlightOffer]:
        """
        Normalize Aviasales API response to FlightOffer format.
        
        Aviasales response format:
        {
            "origin": "PNQ",
            "destination": "BOM",
            "origin_airport": "PNQ",
            "destination_airport": "BOM",
            "price": 3500,
            "airline": "6E",
            "flight_number": 123,
            "departure_at": "2025-01-15T06:00:00",
            "return_at": "2025-01-20T18:00:00",
            "transfers": 0,
            "duration": 60,
            "duration_to": 60,
            "duration_back": 60,
            "link": "/deep_link_to_aviasales?marker=..."
        }
        """
        offers = []
        
        for idx, flight in enumerate(flights):
            try:
                # Extract flight data
                origin = flight.get("origin_airport", flight.get("origin", request.origin))
                destination = flight.get("destination_airport", flight.get("destination", request.destination))
                price = flight.get("price", 0)
                airline = flight.get("airline", "")
                flight_number = flight.get("flight_number", "")
                departure_at = flight.get("departure_at", "")
                return_at = flight.get("return_at")
                transfers = flight.get("transfers", 0)
                duration_to = flight.get("duration_to", flight.get("duration", 0))
                duration_back = flight.get("duration_back", 0)
                
                # CRITICAL: Always use Travelpayouts redirect gateway
                # NEVER use aviasales.com/search/* directly (causes CORS errors)
                from app.utils.travelpayouts_deeplinks import generate_flight_deep_link
                
                # Extract date from departure_at
                try:
                    dep_date = datetime.fromisoformat(departure_at.replace("Z", "+00:00"))
                    departure_date = dep_date.strftime("%Y-%m-%d")
                except ValueError:
                    departure_date = departure_at[:10] if len(departure_at) >= 10 else departure_at
                
                return_date = None
                if return_at:
                    try:
                        ret_date = datetime.fromisoformat(return_at.replace("Z", "+00:00"))
                        return_date = ret_date.strftime("%Y-%m-%d")
                    except ValueError:
                        return_date = return_at[:10] if len(return_at) >= 10 else None
                
                # Generate proper Travelpayouts deep link
                deep_link_result = generate_flight_deep_link(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date,
                    adults=request.adults or 1
                )
                deeplink = deep_link_result["url"]
                
                # Parse departure time
                try:
                    dep_time = datetime.fromisoformat(departure_at.replace("Z", "+00:00"))
                except ValueError:
                    dep_time = datetime.now()
                
                # Create outbound segment
                outbound_segment = FlightSegment(
                    departure_airport=origin,
                    arrival_airport=destination,
                    departure_time=dep_time,
                    arrival_time=dep_time,
                    duration_minutes=duration_to,
                    carrier_code=airline or "XX",
                    carrier_name=airline or "Multiple Airlines",
                    flight_number=f"{airline}{flight_number}" if flight_number else (airline or "XX"),
                )
                
                segments = [outbound_segment]
                
                # Add return segment for round trips
                if request.trip_type == "roundtrip" and return_at:
                    try:
                        ret_time = datetime.fromisoformat(return_at.replace("Z", "+00:00"))
                    except ValueError:
                        ret_time = dep_time
                    
                    return_segment = FlightSegment(
                        departure_airport=destination,
                        arrival_airport=origin,
                        departure_time=ret_time,
                        arrival_time=ret_time,
                        duration_minutes=duration_back,
                        carrier_code=airline or "XX",
                        carrier_name=airline or "Multiple Airlines",
                        flight_number=f"{airline}R{flight_number}" if flight_number else (airline or "XX"),
                    )
                    segments.append(return_segment)
                
                # Create offer
                total_duration = duration_to + (duration_back if duration_back else 0)
                
                offer = FlightOffer(
                    offer_id=f"aviasales_{origin}_{destination}_{idx}_{int(price)}",
                    provider="aviasales",
                    segments=segments,
                    price=float(price),
                    currency="INR",
                    total_duration_minutes=total_duration,
                    stops=transfers,
                    cabin_class=request.cabin_class or "economy",
                    deep_link=deeplink,
                    booking_url=deeplink,
                    refundable=False,
                    rating=100 - self._calculate_score(flight),
                )
                
                offers.append(offer)
            
            except Exception as e:
                logger.error(f"Error normalizing flight {idx}: {e}")
                continue
        
        # Sort by price
        offers.sort(key=lambda x: x.price)
        
        return offers
    
    def _normalize_flights_v2(
        self,
        flights: List[Dict],
        request: FlightSearchRequest
    ) -> List[FlightOffer]:
        """
        Normalize /v2/prices/month-matrix response to FlightOffer format.
        
        Month-matrix response format:
        {
            "depart_date": "2026-01-19",
            "origin": "DEL",
            "destination": "BOM",
            "gate": "Flightnetwork",
            "return_date": "",
            "found_at": "2025-12-23T17:49:27Z",
            "trip_class": 0,
            "value": 5421,
            "number_of_changes": 0,
            "duration": 125,
            "distance": 1139,
            "show_to_affiliates": true,
            "actual": true
        }
        """
        offers = []
        
        for idx, flight in enumerate(flights):
            try:
                origin = flight.get("origin", request.origin)
                destination = flight.get("destination", request.destination)
                price = flight.get("value", 0)
                depart_date = flight.get("depart_date", "")
                return_date = flight.get("return_date", "")
                transfers = flight.get("number_of_changes", 0)
                duration = flight.get("duration", 0)
                gate = flight.get("gate", "Aviasales")
                
                # Build deeplink using path-based format
                deeplink = self._build_deeplink_from_date(
                    origin, destination, depart_date, return_date
                )
                
                # Parse departure date
                try:
                    dep_time = datetime.strptime(depart_date, "%Y-%m-%d")
                except ValueError:
                    dep_time = datetime.now()
                
                # Create segment
                segment = FlightSegment(
                    departure_airport=origin,
                    arrival_airport=destination,
                    departure_time=dep_time,
                    arrival_time=dep_time,
                    duration_minutes=duration,
                    carrier_code=gate[:2] if gate else "XX",
                    carrier_name=gate or "Multiple Airlines",
                    flight_number=f"{gate[:2]}000" if gate else "XX000",
                )
                
                segments = [segment]
                
                # Add return segment if round trip
                if return_date and request.trip_type == "roundtrip":
                    try:
                        ret_time = datetime.strptime(return_date, "%Y-%m-%d")
                    except ValueError:
                        ret_time = dep_time
                    
                    return_segment = FlightSegment(
                        departure_airport=destination,
                        arrival_airport=origin,
                        departure_time=ret_time,
                        arrival_time=ret_time,
                        duration_minutes=duration,
                        carrier_code=gate[:2] if gate else "XX",
                        carrier_name=gate or "Multiple Airlines",
                        flight_number=f"{gate[:2]}001" if gate else "XX001",
                    )
                    segments.append(return_segment)
                
                offer = FlightOffer(
                    offer_id=f"aviasales_v2_{origin}_{destination}_{idx}_{int(price)}",
                    provider="aviasales",
                    segments=segments,
                    price=float(price),
                    currency="INR",
                    total_duration_minutes=duration * len(segments),
                    stops=transfers,
                    cabin_class=request.cabin_class or "economy",
                    deep_link=deeplink,
                    booking_url=deeplink,
                    refundable=False,
                    rating=100 - self._calculate_score_v2(flight),
                )
                
                offers.append(offer)
            
            except Exception as e:
                logger.error(f"Error normalizing v2 flight {idx}: {e}")
                continue
        
        # Sort by price
        offers.sort(key=lambda x: x.price)
        
        return offers
    
    def _build_deeplink_from_date(
        self,
        origin: str,
        destination: str,
        depart_date: str,
        return_date: Optional[str] = None
    ) -> str:
        """
        Build deeplink from date string (YYYY-MM-DD format).
        
        IMPORTANT: Uses Travelpayouts redirect base URL for proper affiliate tracking.
        """
        from app.utils.travelpayouts_deeplinks import generate_flight_deep_link
        
        result = generate_flight_deep_link(
            origin=origin,
            destination=destination,
            departure_date=depart_date,
            return_date=return_date,
            adults=1
        )
        return result["url"]
    
    def _calculate_score_v2(self, flight: Dict) -> float:
        """Calculate score for v2 API response."""
        score = 0.0
        
        price = flight.get("value", 10000)
        score += min(price / 100, 100)
        
        transfers = flight.get("number_of_changes", 0)
        score += transfers * 20
        
        duration = flight.get("duration", 0)
        if duration > 0:
            score += duration / 10
        
        return score
    
    def _build_fallback_deeplink(
        self,
        origin: str,
        destination: str,
        departure_at: str,
        return_at: Optional[str] = None
    ) -> str:
        """
        Build fallback deeplink if API doesn't return one.
        
        IMPORTANT: Uses Travelpayouts redirect base URL for proper affiliate tracking.
        """
        from app.utils.travelpayouts_deeplinks import generate_flight_deep_link
        
        # Parse datetime to date string
        try:
            dep_date = datetime.fromisoformat(departure_at.replace("Z", "+00:00"))
            departure_date = dep_date.strftime("%Y-%m-%d")
        except ValueError:
            departure_date = departure_at[:10] if len(departure_at) >= 10 else departure_at
        
        return_date = None
        if return_at:
            try:
                ret_date = datetime.fromisoformat(return_at.replace("Z", "+00:00"))
                return_date = ret_date.strftime("%Y-%m-%d")
            except ValueError:
                return_date = return_at[:10] if len(return_at) >= 10 else None
        
        result = generate_flight_deep_link(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=1
        )
        return result["url"]
    
    def _calculate_score(self, flight: Dict) -> float:
        """
        Calculate a relevance score for ranking.
        Lower is better.
        """
        score = 0.0
        
        # Price factor (normalize to 0-100 range for typical prices)
        price = flight.get("price", 10000)
        score += min(price / 100, 100)
        
        # Transfers penalty
        transfers = flight.get("transfers", 0)
        score += transfers * 20
        
        # Duration factor
        duration = flight.get("duration_to", 0)
        if duration > 0:
            score += duration / 10
        
        return score
    
    @staticmethod
    def is_available() -> bool:
        """Check if Aviasales adapter is properly configured."""
        token = (
            getattr(settings, "travelpayouts_api_token", None) or 
            os.environ.get("TRAVELPAYOUTS_API_TOKEN")
        )
        if not token:
            logger.warning("TRAVELPAYOUTS_API_TOKEN not set")
            return False
        return True


# Factory function for easy instantiation
def get_aviasales_adapter() -> Optional[AviasalesAdapter]:
    """Get Aviasales adapter instance if configured."""
    try:
        if AviasalesAdapter.is_available():
            return AviasalesAdapter()
        return None
    except Exception as e:
        logger.error(f"Failed to create AviasalesAdapter: {e}")
        return None

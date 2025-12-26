"""
PROTECTED AMADEUS FLIGHT SEARCH SERVICE
========================================
⚠️ WARNING: This is the ONLY module allowed to make Amadeus flight search API calls.

COST CONTROL RULES:
1. All searches MUST go through should_make_real_search() first
2. Cache results immediately after successful API calls
3. Increment daily counter after each real API call
4. Log every search event with source metadata
5. Never expose API errors to users - use graceful fallbacks

RESPONSE METADATA:
- source: "AMADEUS" (live) or "CACHE" (cached)
- last_live_updated_at: UTC timestamp of last live fetch
- is_live: boolean indicating if data is fresh

This service implements:
- Amadeus OAuth2 authentication
- Flight Offers Search API
- Result normalization with Last Known Live Price
- Error handling with graceful degradation
"""

import httpx
import logging
import time
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

from app.core.config import settings
from app.models.flight import FlightOffer, FlightSegment, FlightSearchRequest
from app.services.search_control import (
    should_make_real_search,
    cache_results,
    increment_search_counter,
    record_ip_search,
    log_search_event,
    get_cache_display_message,
    get_cache_helper_text,
    get_last_known_live_results,
    get_quota_status,
)

logger = logging.getLogger(__name__)

# ============================================================================
# AMADEUS OAUTH2 AUTHENTICATION
# ============================================================================

_amadeus_token_cache = {
    "access_token": None,
    "expires_at": 0
}


async def get_amadeus_access_token() -> str:
    """
    Get valid Amadeus access token, refreshing if expired.
    
    Uses OAuth2 client_credentials flow.
    """
    # Check if current token is still valid (with 60s buffer)
    if _amadeus_token_cache["access_token"] and time.time() < _amadeus_token_cache["expires_at"] - 60:
        return _amadeus_token_cache["access_token"]
    
    # Get new token
    logger.info("🔑 Refreshing Amadeus access token...")
    
    token_url = f"{settings.amadeus_base_url}/v1/security/oauth2/token"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.amadeus_api_key,
                "client_secret": settings.amadeus_api_secret
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            logger.error(f"❌ Amadeus auth failed: {response.status_code} - {response.text[:200]}")
            raise Exception("Amadeus authentication failed")
        
        data = response.json()
        
        _amadeus_token_cache["access_token"] = data["access_token"]
        _amadeus_token_cache["expires_at"] = time.time() + data.get("expires_in", 1799)
        
        logger.info(f"✅ Amadeus token refreshed, expires in {data.get('expires_in', 0)}s")
        
        return _amadeus_token_cache["access_token"]


# ============================================================================
# AMADEUS FLIGHT OFFERS SEARCH
# ============================================================================

async def _call_amadeus_flight_search(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    cabin_class: str = "ECONOMY",
    non_stop: bool = False,
    max_results: int = 30
) -> List[Dict]:
    """
    ⚠️ INTERNAL: Call Amadeus Flight Offers Search API.
    
    This function should ONLY be called from search_flights_protected().
    Direct calls from other modules are FORBIDDEN.
    
    Uses GET endpoint for simpler queries.
    """
    token = await get_amadeus_access_token()
    
    # Build request
    search_url = f"{settings.amadeus_base_url}/v2/shopping/flight-offers"
    
    params = {
        "originLocationCode": origin.upper(),
        "destinationLocationCode": destination.upper(),
        "departureDate": departure_date,
        "adults": adults,
        "travelClass": cabin_class.upper(),
        "nonStop": "true" if non_stop else "false",
        "max": max_results,
        "currencyCode": "INR"
    }
    
    if return_date:
        params["returnDate"] = return_date
    
    logger.info(f"🔍 Amadeus API call: {origin} → {destination} on {departure_date}")
    
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            search_url,
            params=params,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code != 200:
            logger.error(f"❌ Amadeus search failed: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            return []
        
        data = response.json()
        offers = data.get("data", [])
        
        logger.info(f"✅ Amadeus returned {len(offers)} offers in {latency_ms:.0f}ms")
        
        return offers


def _normalize_amadeus_offers(
    raw_offers: List[Dict],
    request: FlightSearchRequest
) -> List[FlightOffer]:
    """
    Normalize Amadeus API response to FlightOffer format.
    """
    offers = []
    
    for idx, raw in enumerate(raw_offers):
        try:
            # Extract price
            price_data = raw.get("price", {})
            price = float(price_data.get("total", 0))
            currency = price_data.get("currency", "INR")
            
            # Extract segments from first itinerary
            itineraries = raw.get("itineraries", [])
            segments = []
            total_duration = 0
            stops = 0
            
            for itinerary in itineraries:
                itinerary_segments = itinerary.get("segments", [])
                stops = max(stops, len(itinerary_segments) - 1)
                
                for seg in itinerary_segments:
                    departure = seg.get("departure", {})
                    arrival = seg.get("arrival", {})
                    
                    # Parse times
                    try:
                        dep_time = datetime.fromisoformat(departure.get("at", "").replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        dep_time = datetime.now(timezone.utc)
                    
                    try:
                        arr_time = datetime.fromisoformat(arrival.get("at", "").replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        arr_time = dep_time
                    
                    # Parse duration (e.g., "PT2H30M")
                    duration_str = seg.get("duration", "PT0M")
                    duration_mins = _parse_duration(duration_str)
                    total_duration += duration_mins
                    
                    segment = FlightSegment(
                        departure_airport=departure.get("iataCode", ""),
                        arrival_airport=arrival.get("iataCode", ""),
                        departure_time=dep_time,
                        arrival_time=arr_time,
                        duration_minutes=duration_mins,
                        carrier_code=seg.get("carrierCode", "XX"),
                        carrier_name=seg.get("carrierCode", "Unknown"),
                        flight_number=f"{seg.get('carrierCode', 'XX')}{seg.get('number', '000')}"
                    )
                    segments.append(segment)
            
            if not segments:
                continue
            
            # Build deeplink (Aviasales format for booking)
            origin = segments[0].departure_airport
            destination = segments[-1].arrival_airport
            dep_date = request.departure_date
            deeplink = _build_booking_deeplink(origin, destination, dep_date)
            
            # Check refundability
            traveler_pricings = raw.get("travelerPricings", [])
            refundable = False
            if traveler_pricings:
                fare_details = traveler_pricings[0].get("fareDetailsBySegment", [])
                if fare_details:
                    cabin = fare_details[0].get("cabin", "ECONOMY")
                    fare_basis = fare_details[0].get("fareBasis", "")
                    refundable = cabin in ["BUSINESS", "FIRST"] or "FLEX" in fare_basis.upper()
            
            offer = FlightOffer(
                offer_id=f"amadeus_{raw.get('id', idx)}",
                provider="amadeus",
                segments=segments,
                price=price,
                currency=currency,
                total_duration_minutes=total_duration,
                stops=stops,
                cabin_class=request.cabin_class or "economy",
                deep_link=deeplink,
                booking_url=deeplink,
                refundable=refundable,
                rating=100 - (stops * 10) - (total_duration / 100)
            )
            
            offers.append(offer)
        
        except Exception as e:
            logger.error(f"Error normalizing Amadeus offer {idx}: {e}")
            continue
    
    # Sort by price
    offers.sort(key=lambda x: x.price)
    
    return offers


def _parse_duration(duration_str: str) -> int:
    """Parse ISO 8601 duration (e.g., PT2H30M) to minutes."""
    import re
    
    total_minutes = 0
    
    # Extract hours
    hours_match = re.search(r'(\d+)H', duration_str)
    if hours_match:
        total_minutes += int(hours_match.group(1)) * 60
    
    # Extract minutes
    mins_match = re.search(r'(\d+)M', duration_str)
    if mins_match:
        total_minutes += int(mins_match.group(1))
    
    return total_minutes


def _build_booking_deeplink(origin: str, destination: str, departure_date: str) -> str:
    """Build Aviasales deeplink for booking redirect."""
    try:
        # Parse date to DDMM format
        date_parts = departure_date.split("-")
        ddmm = f"{date_parts[2]}{date_parts[1]}"
        
        marker = settings.travelpayouts_marker
        
        return f"https://www.aviasales.com/search/{origin}{ddmm}{destination}1?marker={marker}"
    except:
        return f"https://www.aviasales.com?marker={settings.travelpayouts_marker}"


def _format_timestamp_for_display(iso_timestamp: str) -> str:
    """
    Format ISO timestamp to user-friendly display format.
    
    Example: "Last updated at 08:02 AM"
    """
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        return dt.strftime("Last updated at %I:%M %p")
    except:
        return "Last updated recently"


# ============================================================================
# MAIN PROTECTED SEARCH FUNCTION
# ============================================================================

async def search_flights_protected(
    request: FlightSearchRequest,
    headers: Dict,
    client_ip: str
) -> Dict[str, Any]:
    """
    ⚠️ PROTECTED FLIGHT SEARCH - Main entry point for all flight searches.
    
    This function implements all cost control measures:
    1. Checks cache first
    2. Validates search intent header (x-search-intent = "real")
    3. Checks IP rate limit
    4. Checks daily cap
    5. Makes Amadeus API call only if all checks pass
    6. Caches results with Last Known Live Price metadata
    7. Logs search event for trust auditing
    8. Returns graceful fallback if any check fails
    
    RESPONSE METADATA:
    - source: "AMADEUS" (live) or "CACHE" (cached)
    - is_live: boolean
    - last_live_updated_at: UTC timestamp
    - cache_message: User-friendly message for cached results
    - quota_status: Current quota info
    
    Args:
        request: Flight search parameters
        headers: Request headers (must contain x-search-intent = "real" for real search)
        client_ip: Client IP address for rate limiting
    
    Returns:
        Search result dict with offers and metadata
    """
    start_time = time.time()
    search_key = f"{request.origin}-{request.destination}-{request.departure_date}"
    now_utc = datetime.now(timezone.utc).isoformat()
    
    # Decision: Should we make a real API call?
    should_call, reason, cached_data = should_make_real_search(
        headers=headers,
        ip=client_ip,
        origin=request.origin,
        destination=request.destination,
        departure_date=request.departure_date,
        adults=request.adults,
        cabin_class=request.cabin_class
    )
    
    # Case 1: Cache hit - return cached with honest metadata
    if reason == "cache_hit" and cached_data:
        latency_ms = (time.time() - start_time) * 1000
        
        log_search_event(
            search_key=search_key,
            served_source="CACHE",
            ip=client_ip,
            is_real=False,
            result_count=len(cached_data.get("offers", [])),
            last_live_updated_at=cached_data.get("last_live_updated_at"),
            latency_ms=latency_ms
        )
        
        return {
            **cached_data,
            "status": "completed",
            "outcome": "results" if cached_data.get("offers") else "no_results",
            "source": "CACHE",
            "is_live": False,
            "cache_message": get_cache_display_message(),
            "cache_helper_text": get_cache_helper_text(),
            "timestamp_display": _format_timestamp_for_display(cached_data.get("last_live_updated_at", now_utc)),
            "quota_status": get_quota_status(),
            "latency_ms": latency_ms
        }
    
    # Case 2: Not a real search request (prefetch, filter, no intent)
    if not should_call and "no_real_intent" in reason:
        log_search_event(
            search_key=search_key,
            served_source="BLOCKED_NO_INTENT",
            ip=client_ip,
            is_real=False,
            result_count=0
        )
        
        return {
            "status": "completed",
            "outcome": "no_results",
            "message": "Search requires explicit user action.",
            "offers": [],
            "flights": [],
            "source": "BLOCKED",
            "is_live": False,
            "reason": "missing_search_intent"
        }
    
    # Case 3: Rate limited or cap reached - return last known live results
    if not should_call:
        latency_ms = (time.time() - start_time) * 1000
        
        # Try to get last known live results (ignores TTL)
        fallback_data = get_last_known_live_results(
            request.origin, request.destination, request.departure_date,
            request.adults, request.cabin_class
        )
        
        log_search_event(
            search_key=search_key,
            served_source="CACHE",
            ip=client_ip,
            is_real=False,
            result_count=len(fallback_data.get("offers", [])) if fallback_data else 0,
            last_live_updated_at=fallback_data.get("last_live_updated_at") if fallback_data else None,
            latency_ms=latency_ms
        )
        
        if fallback_data:
            return {
                **fallback_data,
                "status": "completed",
                "outcome": "results" if fallback_data.get("offers") else "no_results",
                "source": "CACHE",
                "is_live": False,
                "cache_message": get_cache_display_message(),
                "cache_helper_text": get_cache_helper_text(),
                "timestamp_display": _format_timestamp_for_display(fallback_data.get("last_live_updated_at", now_utc)),
                "quota_status": get_quota_status(),
                "latency_ms": latency_ms
            }
        else:
            # No cached data available - return empty with friendly message
            return {
                "status": "completed",
                "outcome": "no_results",
                "message": get_cache_display_message(),
                "offers": [],
                "flights": [],
                "source": "CACHE",
                "is_live": False,
                "quota_status": get_quota_status(),
                "latency_ms": latency_ms
            }
    
    # Case 4: Make real Amadeus API call
    try:
        # Record IP for rate limiting
        record_ip_search(client_ip)
        
        # Make the API call
        raw_offers = await _call_amadeus_flight_search(
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            return_date=request.return_date,
            adults=request.adults,
            cabin_class=request.cabin_class,
            non_stop=request.direct_only
        )
        
        # Normalize results
        offers = _normalize_amadeus_offers(raw_offers, request)
        
        # Increment daily counter (CRITICAL - must happen after successful call)
        increment_search_counter()
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Prepare result with LIVE metadata
        result = {
            "status": "completed",
            "outcome": "results" if offers else "no_results",
            "offers": [o.dict() for o in offers],
            "flights": [o.dict() for o in offers],
            "source": "AMADEUS",
            "is_live": True,
            "supplier": "amadeus",
            "count": len(offers),
            "latency_ms": latency_ms,
            "last_live_updated_at": now_utc,
            "timestamp_display": "Updated just now",
            "quota_status": get_quota_status()
        }
        
        # Cache results with live metadata
        cache_results(
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            adults=request.adults,
            cabin_class=request.cabin_class,
            results=result,
            is_live=True
        )
        
        # Log the search
        log_search_event(
            search_key=search_key,
            served_source="AMADEUS",
            ip=client_ip,
            is_real=True,
            result_count=len(offers),
            last_live_updated_at=now_utc,
            latency_ms=latency_ms
        )
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Amadeus search error: {e}", exc_info=True)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Try to return last known live results as fallback
        fallback_data = get_last_known_live_results(
            request.origin, request.destination, request.departure_date,
            request.adults, request.cabin_class
        )
        
        log_search_event(
            search_key=search_key,
            served_source="ERROR_FALLBACK",
            ip=client_ip,
            is_real=True,
            result_count=len(fallback_data.get("offers", [])) if fallback_data else 0,
            latency_ms=latency_ms
        )
        
        if fallback_data:
            return {
                **fallback_data,
                "status": "completed",
                "outcome": "results" if fallback_data.get("offers") else "no_results",
                "source": "CACHE",
                "is_live": False,
                "cache_message": get_cache_display_message(),
                "quota_status": get_quota_status()
            }
        
        return {
            "status": "completed",
            "outcome": "fallback",
            "message": get_cache_display_message(),
            "offers": [],
            "flights": [],
            "source": "ERROR_FALLBACK",
            "is_live": False,
            "quota_status": get_quota_status()
        }


# ============================================================================
# AIRPORT LOOKUP (Separate from flight search - doesn't count toward cap)
# ============================================================================

async def search_airports_amadeus(query: str) -> List[Dict]:
    """
    Search airports using Amadeus Airport & City Search API.
    
    This is SEPARATE from flight search and doesn't count toward daily cap.
    Used for autocomplete when local database doesn't have the airport.
    
    ⚠️ Airport lookups are low-cost and don't have the same restrictions.
    """
    if not query or len(query) < 2:
        return []
    
    try:
        token = await get_amadeus_access_token()
        
        search_url = f"{settings.amadeus_base_url}/v1/reference-data/locations"
        
        params = {
            "keyword": query,
            "subType": "AIRPORT,CITY",
            "page[limit]": 10
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                search_url,
                params=params,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code != 200:
                logger.warning(f"Amadeus airport search failed: {response.status_code}")
                return []
            
            data = response.json()
            
            # Normalize results
            airports = []
            for loc in data.get("data", []):
                airports.append({
                    "iata": loc.get("iataCode", ""),
                    "name": loc.get("name", ""),
                    "city": loc.get("address", {}).get("cityName", ""),
                    "country": loc.get("address", {}).get("countryCode", ""),
                    "type": loc.get("subType", "AIRPORT"),
                    "source": "AMADEUS"
                })
            
            logger.info(f"🔍 Airport lookup '{query}' returned {len(airports)} results")
            
            return airports
    
    except Exception as e:
        logger.error(f"Amadeus airport search error: {e}")
        return []

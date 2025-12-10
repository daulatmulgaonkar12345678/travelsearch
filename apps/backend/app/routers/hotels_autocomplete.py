"""
Hotel Autocomplete API (Dynamic)

Provides hotel name autocomplete powered by Amadeus Hotel List API with:
- City-scoped hotel search
- In-memory caching (10-30 minutes)
- No static hotel database
- Production-ready error handling
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
import httpx
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory cache for hotel autocomplete results
hotel_cache: Dict[str, tuple[List[Dict], datetime]] = {}
HOTEL_CACHE_TTL = 1800  # 30 minutes

# Rate limit tracking
amadeus_rate_limited_until: Optional[datetime] = None


def normalize_hotel_data(amadeus_hotel: Dict) -> Dict:
    """
    Normalize Amadeus hotel data to simplified format
    """
    try:
        address = amadeus_hotel.get('address', {})
        geocode = amadeus_hotel.get('geoCode', {})
        
        return {
            'hotel_id': amadeus_hotel.get('hotelId', ''),
            'name': amadeus_hotel.get('name', ''),
            'city': address.get('cityName', ''),
            'country': address.get('countryCode', ''),
            'lat': float(geocode.get('latitude', 0)),
            'lon': float(geocode.get('longitude', 0)),
            'rating': float(amadeus_hotel.get('rating', 0)) if amadeus_hotel.get('rating') else None,
            'address_line': ', '.join(filter(None, [
                address.get('lines', [''])[0] if address.get('lines') else '',
                address.get('cityName', '')
            ]))
        }
    except Exception as e:
        logger.error(f"[HOTELS_AUTO] Error normalizing hotel data: {e}")
        return None


async def search_amadeus_hotels(
    query: str,
    city_code: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    limit: int = 10
) -> Optional[List[Dict]]:
    """
    Search hotels using Amadeus Hotel List API
    
    Parameters:
    - query: Hotel name or partial name
    - city_code: IATA city code (e.g., "MUM" for Mumbai)
    - latitude/longitude: Geographic coordinates
    - limit: Max results
    
    Returns None if error, empty list if no results
    """
    global amadeus_rate_limited_until
    
    # Check if we're rate limited
    if amadeus_rate_limited_until and datetime.utcnow() < amadeus_rate_limited_until:
        logger.info(f"[HOTELS_AUTO] Skipping Amadeus (rate limited until {amadeus_rate_limited_until})")
        return None
    
    try:
        # Import Amadeus adapter
        from app.services.adapters.amadeus_production import AmadeusAdapter
        
        adapter = AmadeusAdapter()
        
        # Get access token
        token = await adapter.get_access_token()
        
        # Build request parameters
        # Amadeus Hotel List API v1 endpoint
        url = f"{adapter.base_url.replace('/v2', '/v1')}/reference-data/locations/hotels/by-hotels"
        
        params = {
            'hotelIds': '',  # We'll use city search instead
        }
        
        # If city code provided, search by city
        if city_code:
            # Use city-based hotel search
            url = f"{adapter.base_url.replace('/v2', '/v1')}/reference-data/locations/hotels/by-city"
            params = {
                'cityCode': city_code.upper(),
                'radius': 50,  # 50km radius
                'radiusUnit': 'KM'
            }
        
        # If coordinates provided, use geographic search
        elif latitude and longitude:
            url = f"{adapter.base_url.replace('/v2', '/v1')}/reference-data/locations/hotels/by-geocode"
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'radius': 50,
                'radiusUnit': 'KM'
            }
        else:
            # No location specified - can't search
            logger.warning("[HOTELS_AUTO] No city_code or coordinates provided")
            return []
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                timeout=10.0
            )
            
            # Handle specific status codes
            if response.status_code == 401:
                logger.error("[HOTELS_AUTO] Amadeus 401 Unauthorized")
                return None
            
            elif response.status_code == 403:
                logger.error("[HOTELS_AUTO] Amadeus 403 Forbidden")
                return None
            
            elif response.status_code == 429:
                # Rate limited - back off for 60 seconds
                amadeus_rate_limited_until = datetime.utcnow() + timedelta(seconds=60)
                logger.warning(f"[HOTELS_AUTO] Amadeus 429 Rate Limited - backing off")
                return None
            
            elif response.status_code == 404:
                # No hotels found for this city
                logger.info(f"[HOTELS_AUTO] No hotels found for city_code={city_code}")
                return []
            
            response.raise_for_status()
            data = response.json()
        
        # Parse Amadeus response
        hotels_data = data.get('data', [])
        
        # Normalize hotel data
        normalized_hotels = []
        for hotel in hotels_data:
            normalized = normalize_hotel_data(hotel)
            if normalized and normalized['hotel_id']:
                normalized_hotels.append(normalized)
        
        # Filter by query (hotel name) if provided
        if query and len(query) >= 2:
            query_lower = query.lower()
            filtered_hotels = [
                h for h in normalized_hotels
                if query_lower in h['name'].lower()
            ]
        else:
            filtered_hotels = normalized_hotels
        
        # Limit results
        results = filtered_hotels[:limit]
        
        logger.info(f"[HOTELS_AUTO] Amadeus returned {len(results)} hotels (filtered from {len(normalized_hotels)})")
        return results
    
    except httpx.HTTPStatusError as e:
        logger.error(f"[HOTELS_AUTO] Amadeus HTTP error: {e.response.status_code}")
        return None
    
    except httpx.RequestError as e:
        logger.error(f"[HOTELS_AUTO] Amadeus request error: {type(e).__name__}")
        return None
    
    except Exception as e:
        logger.error(f"[HOTELS_AUTO] Unexpected error: {type(e).__name__}")
        return None


@router.get("/hotels/autocomplete")
async def autocomplete_hotels(
    query: str = Query("", description="Hotel name or partial name"),
    city_code: Optional[str] = Query(None, description="City IATA code"),
    latitude: Optional[float] = Query(None, description="Latitude"),
    longitude: Optional[float] = Query(None, description="Longitude"),
    limit: int = Query(10, ge=1, le=50, description="Max results")
):
    """
    Hotel name autocomplete (dynamic, powered by Amadeus)
    
    - Searches hotels within a city or geographic area
    - Filters by hotel name if query provided
    - Caches results for 30 minutes
    - No static hotel database
    
    Requires either:
    - city_code (IATA city code), OR
    - latitude + longitude (geographic coordinates)
    """
    try:
        # Validate location parameters
        if not city_code and not (latitude and longitude):
            raise HTTPException(
                status_code=400,
                detail="Either city_code or (latitude, longitude) must be provided"
            )
        
        # Build cache key
        cache_key = f"hotels:{query.lower()}:{city_code or f'{latitude},{longitude}'}"
        
        # Check cache first
        if cache_key in hotel_cache:
            cached_results, cached_at = hotel_cache[cache_key]
            if datetime.utcnow() - cached_at < timedelta(seconds=HOTEL_CACHE_TTL):
                logger.info(f"[HOTELS_AUTO] query=\"{query}\" city_code=\"{city_code}\" cacheHit=true count={len(cached_results)}")
                return {
                    "query": query,
                    "city_code": city_code,
                    "count": len(cached_results),
                    "results": cached_results,
                    "source": "cached"
                }
        
        # Search Amadeus
        results = await search_amadeus_hotels(
            query=query,
            city_code=city_code,
            latitude=latitude,
            longitude=longitude,
            limit=limit
        )
        
        # Handle errors
        if results is None:
            # Provider error - return empty with source
            logger.warning(f"[HOTELS_AUTO] Provider error for query=\"{query}\"")
            return {
                "query": query,
                "city_code": city_code,
                "count": 0,
                "results": [],
                "source": "error",
                "message": "Hotel provider temporarily unavailable. Try searching by city only."
            }
        
        # Cache results (even if empty)
        hotel_cache[cache_key] = (results, datetime.utcnow())
        
        logger.info(f"[HOTELS_AUTO] query=\"{query}\" city_code=\"{city_code}\" source=\"amadeus\" count={len(results)} cacheHit=false")
        
        return {
            "query": query,
            "city_code": city_code,
            "count": len(results),
            "results": results,
            "source": "amadeus"
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"[HOTELS_AUTO] Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Hotel autocomplete failed"
        )


@router.get("/hotels/autocomplete/health")
async def hotels_autocomplete_health():
    """
    Health check for hotel autocomplete endpoint
    """
    return {
        "status": "healthy",
        "cache_entries": len(hotel_cache),
        "cache_ttl_seconds": HOTEL_CACHE_TTL,
        "rate_limited": amadeus_rate_limited_until is not None and datetime.utcnow() < amadeus_rate_limited_until
    }

"""
Hotel City Autocomplete API

Provides city/hotel search for hotel bookings with:
- Amadeus city search (primary, production)
- Curated city list fallback
- In-memory caching
- Production-ready error handling
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Optional
import json
from pathlib import Path
import logging
from datetime import datetime, timedelta
import httpx
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Load curated city dataset
CITIES_PATH = Path("/app/data/hotel-cities.json")
CURATED_CITIES: List[Dict] = []

# In-memory cache for city results
city_cache: Dict[str, tuple[List[Dict], datetime]] = {}
CITY_CACHE_TTL = 600  # 10 minutes

# Rate limit tracking for Amadeus
amadeus_rate_limited_until: Optional[datetime] = None


def load_curated_cities():
    """Load curated city list on startup"""
    global CURATED_CITIES
    
    try:
        with open(CITIES_PATH, 'r', encoding='utf-8') as f:
            CURATED_CITIES = json.load(f)
        
        logger.info(f"✅ Loaded {len(CURATED_CITIES)} curated cities")
    
    except Exception as e:
        logger.error(f"❌ Failed to load curated cities: {e}")
        CURATED_CITIES = []


# Load on module import
load_curated_cities()


def fuzzy_match_cities(query: str, limit: int = 10) -> List[Dict]:
    """
    Search curated cities with fuzzy matching
    Returns cities that match city name or aliases
    """
    if not query or len(query) < 2:
        return []
    
    query_lower = query.lower().strip()
    results = []
    
    for city in CURATED_CITIES:
        score = 0
        
        # Check city name
        city_name = city['city'].lower()
        if city_name == query_lower:
            score = 1.0  # Exact match
        elif city_name.startswith(query_lower):
            score = 0.9  # Starts with
        elif query_lower in city_name:
            score = 0.7  # Contains
        
        # Check aliases
        for alias in city.get('aliases', []):
            alias_lower = alias.lower()
            if alias_lower == query_lower:
                score = max(score, 1.0)
            elif alias_lower.startswith(query_lower):
                score = max(score, 0.9)
            elif query_lower in alias_lower:
                score = max(score, 0.7)
        
        if score >= 0.7:  # Minimum threshold
            results.append({
                'city': city,
                'score': score
            })
    
    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Return top N cities
    return [
        {
            'id': r['city']['id'],
            'type': 'city',
            'label': r['city']['label'],
            'city': r['city']['city'],
            'country': r['city']['country']
        }
        for r in results[:limit]
    ]


async def search_amadeus_cities(query: str, limit: int = 10) -> Optional[List[Dict]]:
    """
    Search cities using Amadeus Reference Data API
    
    Returns None if error, empty list if no results
    Security: Never exposes API keys to client
    """
    global amadeus_rate_limited_until
    
    # Check if we're rate limited
    if amadeus_rate_limited_until and datetime.utcnow() < amadeus_rate_limited_until:
        logger.info(f"[CITIES] Skipping Amadeus (rate limited until {amadeus_rate_limited_until})")
        return None
    
    try:
        # Import Amadeus adapter
        from app.services.adapters.amadeus_production import AmadeusAdapter
        
        adapter = AmadeusAdapter()
        
        # Get access token
        token = await adapter.get_access_token()
        
        # Call Amadeus locations API for cities
        # Using v1 reference-data API for city search
        url = f"{adapter.base_url.replace('/v2', '/v1')}/reference-data/locations"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "subType": "CITY",  # Search for cities
                    "keyword": query,
                    "page[limit]": limit
                },
                timeout=5.0
            )
            
            # Handle specific status codes
            if response.status_code == 401:
                logger.error("[CITIES] Amadeus 401 Unauthorized - check credentials")
                return None
            
            elif response.status_code == 403:
                logger.error("[CITIES] Amadeus 403 Forbidden - check API permissions")
                return None
            
            elif response.status_code == 429:
                # Rate limited - back off for 60 seconds
                amadeus_rate_limited_until = datetime.utcnow() + timedelta(seconds=60)
                logger.warning(f"[CITIES] Amadeus 429 Rate Limited - backing off until {amadeus_rate_limited_until}")
                return None
            
            response.raise_for_status()
            data = response.json()
        
        # Parse Amadeus response
        results = []
        for item in data.get('data', []):
            address = item.get('address', {})
            
            # Build city result
            city_result = {
                'id': item.get('id', ''),
                'type': 'city',
                'label': f"{address.get('cityName', '')}, {address.get('countryName', '')}".strip(', '),
                'city': address.get('cityName', ''),
                'country': address.get('countryCode', ''),
                'iata': item.get('iataCode', '')  # Some cities have IATA codes
            }
            
            # Only include if has city name
            if city_result['city']:
                results.append(city_result)
        
        logger.info(f"[CITIES] Amadeus returned {len(results)} cities for '{query}'")
        return results
    
    except httpx.HTTPStatusError as e:
        logger.error(f"[CITIES] Amadeus HTTP error: {e.response.status_code}")
        return None
    
    except httpx.RequestError as e:
        logger.error(f"[CITIES] Amadeus request error: {type(e).__name__}")
        return None
    
    except Exception as e:
        logger.error(f"[CITIES] Amadeus unexpected error: {type(e).__name__}")
        return None


@router.get("/cities")
async def search_cities(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results")
):
    """
    Search for hotel cities
    
    - Amadeus API (primary, production)
    - Curated city list (fallback)
    - 10-minute cache
    - Production error handling
    """
    try:
        # Normalize query
        query_normalized = query.strip().lower()
        
        # Validation - minimum 2 characters
        if len(query_normalized) < 2:
            return {
                "query": query,
                "count": 0,
                "results": [],
                "source": "none"
            }
        
        # Check cache first
        cache_key = f"cities:{query_normalized}"
        if cache_key in city_cache:
            cached_results, cached_at = city_cache[cache_key]
            if datetime.utcnow() - cached_at < timedelta(seconds=CITY_CACHE_TTL):
                logger.info(f"[CITIES] query=\"{query}\" cacheHit=true count={len(cached_results)}")
                return {
                    "query": query,
                    "count": len(cached_results),
                    "results": cached_results,
                    "source": "cached"
                }
        
        # Try Amadeus first (production)
        amadeus_results = await search_amadeus_cities(query_normalized, limit)
        
        if amadeus_results is not None and len(amadeus_results) > 0:
            # Success - cache and return
            city_cache[cache_key] = (amadeus_results, datetime.utcnow())
            logger.info(f"[CITIES] query=\"{query}\" source=\"amadeus\" count={len(amadeus_results)} cacheHit=false")
            
            return {
                "query": query,
                "count": len(amadeus_results),
                "results": amadeus_results,
                "source": "amadeus"
            }
        
        # Fallback to curated city list
        logger.info(f"[CITIES] Falling back to curated cities for '{query}'")
        fallback_results = fuzzy_match_cities(query_normalized, limit)
        
        # Cache fallback results too
        if fallback_results:
            city_cache[cache_key] = (fallback_results, datetime.utcnow())
        
        logger.info(f"[CITIES] query=\"{query}\" source=\"fallback\" count={len(fallback_results)} cacheHit=false")
        
        return {
            "query": query,
            "count": len(fallback_results),
            "results": fallback_results,
            "source": "fallback"
        }
    
    except Exception as e:
        logger.error(f"[CITIES] Unexpected error: {e}")
        
        # Try fallback even on unexpected errors
        try:
            fallback_results = fuzzy_match_cities(query.strip().lower(), limit)
            return {
                "query": query,
                "count": len(fallback_results),
                "results": fallback_results,
                "source": "fallback"
            }
        except:
            return {
                "query": query,
                "count": 0,
                "results": [],
                "source": "error"
            }


@router.get("/cities/health")
async def cities_health():
    """
    Health check for cities endpoint
    Returns status of data sources
    """
    return {
        "status": "healthy",
        "curated_cities": len(CURATED_CITIES),
        "cache_entries": len(city_cache),
        "rate_limited": amadeus_rate_limited_until is not None and datetime.utcnow() < amadeus_rate_limited_until
    }

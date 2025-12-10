"""
Airport Search API

Provides server-side airport autocomplete with:
- Fast local search using fuzzy matching
- Amadeus API fallback for unmatched queries  
- Nearby airports calculation (within radius)
- Caching for performance
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any
import json
from pathlib import Path
import logging
from datetime import datetime, timedelta
import math
import httpx
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Load airport dataset
AIRPORTS_PATH = Path("/app/data/airports-full.json")
AIRPORTS_DATA: List[Dict] = []
AIRPORTS_BY_IATA: Dict[str, Dict] = {}

# Simple in-memory cache for Amadeus results
amadeus_cache: Dict[str, tuple[List[Dict], datetime]] = {}
AMADEUS_CACHE_TTL = 600  # 10 minutes


def load_airports():
    """Load airports dataset on startup"""
    global AIRPORTS_DATA, AIRPORTS_BY_IATA
    
    try:
        with open(AIRPORTS_PATH, 'r', encoding='utf-8') as f:
            AIRPORTS_DATA = json.load(f)
        
        # Build IATA lookup
        AIRPORTS_BY_IATA = {
            airport['iata']: airport 
            for airport in AIRPORTS_DATA
        }
        
        logger.info(f"✅ Loaded {len(AIRPORTS_DATA)} airports from dataset")
    
    except Exception as e:
        logger.error(f"❌ Failed to load airports: {e}")
        AIRPORTS_DATA = []
        AIRPORTS_BY_IATA = {}


# Load on module import
load_airports()


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula
    Returns distance in kilometers
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in kilometers
    r = 6371
    
    return r * c


def fuzzy_score(query: str, text: str) -> float:
    """
    Simple fuzzy matching score
    Returns 0.0 (no match) to 1.0 (perfect match)
    """
    query = query.lower()
    text = text.lower()
    
    # Exact match
    if query == text:
        return 1.0
    
    # Starts with
    if text.startswith(query):
        return 0.9
    
    # Contains
    if query in text:
        return 0.7
    
    # Word boundary match
    words = text.split()
    for word in words:
        if word.startswith(query):
            return 0.8
    
    # Character matching (simplified Levenshtein)
    matches = sum(1 for c in query if c in text)
    score = matches / len(query) if query else 0
    
    return score * 0.5  # Lower score for partial matches


def search_airports_local(
    query: str,
    limit: int = 10,
    min_score: float = 0.3
) -> List[Dict]:
    """
    Search airports in local dataset using fuzzy matching
    """
    if not query or len(query) < 2:
        return []
    
    results = []
    query_lower = query.lower()
    
    for airport in AIRPORTS_DATA:
        # Calculate scores for different fields
        scores = []
        
        # IATA code (highest weight)
        if airport.get('iata'):
            iata_score = fuzzy_score(query_lower, airport['iata'].lower())
            scores.append(iata_score * 0.9)
        
        # City name
        if airport.get('city'):
            city_score = fuzzy_score(query_lower, airport['city'])
            scores.append(city_score * 0.8)
        
        # Airport name
        if airport.get('name'):
            name_score = fuzzy_score(query_lower, airport['name'])
            scores.append(name_score * 0.7)
        
        # Aliases
        if airport.get('aliases'):
            for alias in airport['aliases']:
                alias_score = fuzzy_score(query_lower, alias)
                scores.append(alias_score * 0.6)
        
        # Get best score
        if scores:
            best_score = max(scores)
            
            if best_score >= min_score:
                results.append({
                    'score': best_score,
                    'airport': airport
                })
    
    # Sort by score (descending)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Return top N
    return [r['airport'] for r in results[:limit]]


def find_nearby_airports(
    iata: str,
    radius_km: float = 250.0,
    limit: int = 10
) -> List[Dict]:
    """
    Find airports within radius of a given airport
    """
    if iata not in AIRPORTS_BY_IATA:
        return []
    
    center_airport = AIRPORTS_BY_IATA[iata]
    center_lat = center_airport.get('lat', 0)
    center_lon = center_airport.get('lon', 0)
    
    if not center_lat or not center_lon:
        return []
    
    nearby = []
    
    for airport in AIRPORTS_DATA:
        # Skip the center airport itself
        if airport.get('iata') == iata:
            continue
        
        # Skip if missing coordinates
        if not airport.get('lat') or not airport.get('lon'):
            continue
        
        # Calculate distance
        distance = calculate_distance(
            center_lat, center_lon,
            airport['lat'], airport['lon']
        )
        
        if distance <= radius_km:
            nearby.append({
                'airport': airport,
                'distance_km': round(distance, 1)
            })
    
    # Sort by distance
    nearby.sort(key=lambda x: x['distance_km'])
    
    # Return top N
    return nearby[:limit]


async def search_amadeus_fallback(query: str) -> List[Dict]:
    """
    Fallback to Amadeus locations API when local search fails
    Only called from backend, never exposes API keys to client
    """
    # Check cache first
    if query in amadeus_cache:
        cached_results, cached_at = amadeus_cache[query]
        if datetime.utcnow() - cached_at < timedelta(seconds=AMADEUS_CACHE_TTL):
            logger.info(f"Amadeus cache hit for '{query}'")
            return cached_results
    
    try:
        # Import Amadeus adapter
        from app.services.adapters.amadeus_production import AmadeusAdapter
        
        adapter = AmadeusAdapter()
        
        # Get access token
        token = await adapter.get_access_token()
        
        # Call Amadeus locations API
        url = f"{adapter.base_url.replace('/v2', '/v1')}/reference-data/locations"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "subType": "AIRPORT",
                    "keyword": query,
                    "page[limit]": 10
                },
                timeout=5.0
            )
            
            response.raise_for_status()
            data = response.json()
        
        # Parse Amadeus response
        results = []
        for item in data.get('data', []):
            address = item.get('address', {})
            
            result = {
                'iata': item.get('iataCode', ''),
                'icao': item.get('icaoCode'),
                'name': item.get('name', ''),
                'city': address.get('cityName', ''),
                'country': address.get('countryName', ''),
                'iso_country': address.get('countryCode', ''),
                'lat': float(item.get('geoCode', {}).get('latitude', 0)),
                'lon': float(item.get('geoCode', {}).get('longitude', 0)),
                'source': 'amadeus'
            }
            
            # Only include if has IATA
            if result['iata']:
                results.append(result)
        
        # Cache results
        amadeus_cache[query] = (results, datetime.utcnow())
        
        logger.info(f"Amadeus fallback returned {len(results)} results for '{query}'")
        return results
    
    except Exception as e:
        logger.error(f"Amadeus fallback error: {e}")
        return []


@router.get("/airports")
async def search_airports(
    query: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    nearby: bool = Query(False, description="Include nearby airports"),
    nearby_iata: Optional[str] = Query(None, description="IATA code for nearby search"),
    radius_km: float = Query(250.0, ge=50, le=500, description="Nearby search radius in km")
):
    """
    Search airports with fuzzy matching
    
    - Local dataset search (fast, primary)
    - Amadeus API fallback (if no local results)
    - Nearby airports calculation (optional)
    """
    try:
        # Search local dataset
        results = search_airports_local(query, limit=limit)
        
        # If no results or low scores, try Amadeus fallback
        if not results:
            logger.info(f"No local results for '{query}', trying Amadeus fallback")
            amadeus_results = await search_amadeus_fallback(query)
            results.extend(amadeus_results)
        
        # Add nearby airports if requested
        if nearby and nearby_iata:
            nearby_airports = find_nearby_airports(
                nearby_iata,
                radius_km=radius_km,
                limit=limit
            )
            
            # Add nearby flag to results
            for item in nearby_airports:
                airport = item['airport'].copy()
                airport['nearby'] = True
                airport['distance_km'] = item['distance_km']
                results.append(airport)
        
        return {
            "query": query,
            "results": results[:limit],
            "count": len(results),
            "source": "local" if results else "none"
        }
    
    except Exception as e:
        logger.error(f"Airport search error: {e}")
        raise HTTPException(status_code=500, detail="Airport search failed")


@router.get("/airports/{iata}/nearby")
async def get_nearby_airports(
    iata: str,
    radius_km: float = Query(250.0, ge=50, le=500),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get airports near a specific airport (by IATA code)
    """
    try:
        nearby_airports = find_nearby_airports(iata, radius_km, limit)
        
        return {
            "center_iata": iata,
            "radius_km": radius_km,
            "results": nearby_airports,
            "count": len(nearby_airports)
        }
    
    except Exception as e:
        logger.error(f"Nearby airports error: {e}")
        raise HTTPException(status_code=500, detail="Nearby airports search failed")

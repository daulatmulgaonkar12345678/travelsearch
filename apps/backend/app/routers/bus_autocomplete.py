"""
Bus Autocomplete API
====================

Provides cascading autocomplete search for BUS mode:
1. Bus stops (same state) - HIGHEST PRIORITY
2. Cities/districts (same state)
3. Nearby districts (same state)
4. Other states (India-wide fallback) - LOWEST PRIORITY

Key features:
- Bus stops searched BEFORE cities
- Exact match > partial match
- is_search_surface = true gets higher rank
- Same state > other states
- Maharashtra/MSRTC stops get priority

Response format:
{
  id,
  type: "bus_stop" | "city",
  label,
  city,
  state,
  operator (for bus_stop)
}
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any, Optional
import logging
import re

# Import MSRTC data loader
from app.data.places import (
    get_all_stops,
    get_all_cities,
    search_stops,
    get_search_surface_stops,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["bus-autocomplete"])


# ============================================================
# RANKING CONFIGURATION
# ============================================================

# Score weights for ranking
SCORE_EXACT_MATCH = 100        # Exact name match
SCORE_STARTS_WITH = 80         # Name starts with query
SCORE_CONTAINS = 50            # Name contains query
SCORE_SEARCH_SURFACE = 30      # is_search_surface = true bonus
SCORE_SAME_STATE = 20          # Same state bonus
SCORE_CITY_MATCH = 10          # City/district match (lower than stop)


# ============================================================
# EXTENDED INDIA CITIES (for fallback)
# ============================================================

# Major cities from other states (for fallback when no MH results)
OTHER_STATE_CITIES = [
    {"id": "DEL", "city": "New Delhi", "state": "Delhi", "normalized": "new delhi"},
    {"id": "BLR", "city": "Bangalore", "state": "Karnataka", "normalized": "bangalore bengaluru"},
    {"id": "CHE", "city": "Chennai", "state": "Tamil Nadu", "normalized": "chennai madras"},
    {"id": "HYD", "city": "Hyderabad", "state": "Telangana", "normalized": "hyderabad"},
    {"id": "AMD", "city": "Ahmedabad", "state": "Gujarat", "normalized": "ahmedabad"},
    {"id": "JAI", "city": "Jaipur", "state": "Rajasthan", "normalized": "jaipur"},
    {"id": "LKO", "city": "Lucknow", "state": "Uttar Pradesh", "normalized": "lucknow"},
    {"id": "GOA", "city": "Panaji", "state": "Goa", "normalized": "goa panaji panjim"},
    {"id": "COK", "city": "Kochi", "state": "Kerala", "normalized": "kochi cochin ernakulam"},
    {"id": "TRV", "city": "Thiruvananthapuram", "state": "Kerala", "normalized": "thiruvananthapuram trivandrum"},
    {"id": "PAT", "city": "Patna", "state": "Bihar", "normalized": "patna"},
    {"id": "BPL", "city": "Bhopal", "state": "Madhya Pradesh", "normalized": "bhopal"},
    {"id": "IND", "city": "Indore", "state": "Madhya Pradesh", "normalized": "indore"},
    {"id": "SUR", "city": "Surat", "state": "Gujarat", "normalized": "surat"},
    {"id": "VAD", "city": "Vadodara", "state": "Gujarat", "normalized": "vadodara baroda"},
    {"id": "CHD", "city": "Chandigarh", "state": "Chandigarh", "normalized": "chandigarh"},
    {"id": "AGR", "city": "Agra", "state": "Uttar Pradesh", "normalized": "agra"},
    {"id": "UDR", "city": "Udaipur", "state": "Rajasthan", "normalized": "udaipur"},
    {"id": "JDP", "city": "Jodhpur", "state": "Rajasthan", "normalized": "jodhpur"},
    # Karnataka cities
    {"id": "MYS", "city": "Mysore", "state": "Karnataka", "normalized": "mysore mysuru"},
    {"id": "HUB", "city": "Hubli", "state": "Karnataka", "normalized": "hubli hubballi dharwad"},
    {"id": "MNG", "city": "Mangalore", "state": "Karnataka", "normalized": "mangalore mangaluru"},
    {"id": "BEL", "city": "Belgaum", "state": "Karnataka", "normalized": "belgaum belagavi"},
    # Tamil Nadu cities
    {"id": "MDU", "city": "Madurai", "state": "Tamil Nadu", "normalized": "madurai"},
    {"id": "CMB", "city": "Coimbatore", "state": "Tamil Nadu", "normalized": "coimbatore kovai"},
    {"id": "TRC", "city": "Trichy", "state": "Tamil Nadu", "normalized": "trichy tiruchirappalli"},
    {"id": "SLM", "city": "Salem", "state": "Tamil Nadu", "normalized": "salem"},
    # Andhra Pradesh
    {"id": "VIZ", "city": "Visakhapatnam", "state": "Andhra Pradesh", "normalized": "visakhapatnam vizag"},
    {"id": "VIJ", "city": "Vijayawada", "state": "Andhra Pradesh", "normalized": "vijayawada"},
    {"id": "TIR", "city": "Tirupati", "state": "Andhra Pradesh", "normalized": "tirupati"},
]


def normalize_query(query: str) -> str:
    """Normalize query for matching."""
    return query.lower().strip()


def calculate_match_score(
    name: str,
    normalized_key: str,
    query: str,
    is_search_surface: bool,
    is_same_state: bool,
    is_stop: bool,
) -> int:
    """
    Calculate ranking score for a result.
    
    Higher score = better match
    """
    score = 0
    query_lower = query.lower()
    name_lower = name.lower()
    
    # 1. Match quality scoring
    if name_lower == query_lower or normalized_key == query_lower:
        score += SCORE_EXACT_MATCH
    elif name_lower.startswith(query_lower) or normalized_key.startswith(query_lower):
        score += SCORE_STARTS_WITH
    elif query_lower in name_lower or query_lower in normalized_key:
        score += SCORE_CONTAINS
    
    # 2. Search surface bonus (for stops)
    if is_stop and is_search_surface:
        score += SCORE_SEARCH_SURFACE
    
    # 3. Same state bonus
    if is_same_state:
        score += SCORE_SAME_STATE
    
    # 4. Stop vs City (stops get more base score implicitly via search order)
    if is_stop:
        score += 5  # Small bonus for being a stop vs city
    
    return score


def search_mh_bus_stops(query: str, limit: int = 20) -> List[Dict]:
    """
    Search Maharashtra bus stops.
    
    Returns list of matching stops with scores.
    """
    results = []
    query_lower = normalize_query(query)
    
    if len(query_lower) < 2:
        return []
    
    # Get all stops from MSRTC data
    all_stops = get_all_stops()
    
    for stop in all_stops:
        name_local = stop.get("name_local", "")
        normalized_key = stop.get("normalized_key", "")
        is_ss = stop.get("is_search_surface", False)
        
        # Check if query matches
        matches = False
        
        # Match against Marathi name
        if query in name_local:
            matches = True
        
        # Match against normalized key (English)
        if query_lower in normalized_key:
            matches = True
        
        if matches:
            score = calculate_match_score(
                name=name_local,
                normalized_key=normalized_key,
                query=query,
                is_search_surface=is_ss,
                is_same_state=True,  # All MH stops are same state
                is_stop=True,
            )
            
            # Get city info
            city_id = stop.get("city_id", 0)
            cities = get_all_cities()
            city_info = next((c for c in cities if c["city_id"] == city_id), None)
            city_name = city_info["name_en"] if city_info else "Maharashtra"
            
            results.append({
                "id": f"stop_{stop['stop_id']}",
                "type": "bus_stop",
                "label": stop["name_local"],
                "label_en": normalized_key.replace("-", " ").title(),
                "city": city_name,
                "city_local": city_info["name_local"] if city_info else "",
                "state": "Maharashtra",
                "state_code": "MH",
                "operator": "MSRTC",
                "is_search_surface": is_ss,
                "stop_role": stop.get("stop_role", "PICKUP_DROP"),
                "score": score,
            })
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results[:limit]


def search_mh_cities(query: str, limit: int = 10) -> List[Dict]:
    """
    Search Maharashtra cities/districts.
    
    Returns list of matching cities with scores.
    """
    results = []
    query_lower = normalize_query(query)
    
    if len(query_lower) < 2:
        return []
    
    # Get all cities from MSRTC data
    cities = get_all_cities()
    
    for city in cities:
        name_en = city.get("name_en", "")
        name_local = city.get("name_local", "")
        normalized_key = city.get("normalized_key", "")
        
        # Check if query matches
        matches = False
        
        if query_lower in name_en.lower():
            matches = True
        if query in name_local:
            matches = True
        if query_lower in normalized_key:
            matches = True
        
        if matches:
            score = calculate_match_score(
                name=name_en,
                normalized_key=normalized_key,
                query=query,
                is_search_surface=True,  # Cities are always search surface
                is_same_state=True,
                is_stop=False,
            )
            
            results.append({
                "id": f"city_{city['city_id']}",
                "type": "city",
                "label": f"{name_en}, Maharashtra",
                "label_en": name_en,
                "city": name_en,
                "city_local": name_local,
                "state": "Maharashtra",
                "state_code": "MH",
                "operator": "MSRTC",
                "is_search_surface": True,
                "score": score,
            })
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results[:limit]


def search_tourist_destinations(query: str, limit: int = 10) -> List[Dict]:
    """
    Search tourist destinations (hill stations, temples, heritage sites).
    
    These destinations are accessible via feeder routes.
    """
    results = []
    query_lower = normalize_query(query)
    
    if len(query_lower) < 2:
        return []
    
    try:
        from app.services.feeder_resolver import get_feeder_resolver
        resolver = get_feeder_resolver()
        
        for dest_id, dest in resolver.destinations.items():
            name_en = dest.get("name_en", "")
            name_local = dest.get("name_local", "")
            
            # Check if query matches
            if (query_lower in name_en.lower() or 
                query_lower in dest_id.lower() or
                query_lower in name_local):
                
                # Calculate score (tourist destinations get bonus for exact match)
                score = 50  # Base score for tourist destinations
                
                if name_en.lower().startswith(query_lower):
                    score += 30  # Prefix match bonus
                if name_en.lower() == query_lower:
                    score += 20  # Exact match bonus
                
                # Type-based bonus
                dest_type = dest.get("type", "")
                if dest_type == "RELIGIOUS":
                    score += 10  # Religious sites are common searches
                elif dest_type == "HILL_STATION":
                    score += 8
                elif dest_type == "HERITAGE":
                    score += 5
                
                # Map destination type to emoji
                type_icons = {
                    "HILL_STATION": "🏔️",
                    "RELIGIOUS": "🛕",
                    "HERITAGE": "🏛️",
                    "BEACH": "🏖️",
                    "RESORT": "🏨",
                }
                type_icon = type_icons.get(dest_type, "📍")
                
                results.append({
                    "id": f"tourist_{dest_id}",
                    "type": "tourist_destination",
                    "label": f"{type_icon} {name_en}",
                    "label_en": name_en,
                    "city": name_en,  # Use destination name as "city" for display
                    "city_local": name_local,
                    "state": "Maharashtra",
                    "state_code": "MH",
                    "operator": None,
                    "is_search_surface": True,
                    "is_tourist": True,
                    "destination_type": dest_type,  # Include destination type
                    "description": dest.get("description"),
                    "score": score,
                })
    except Exception as e:
        logger.error(f"Error searching tourist destinations: {e}")
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results[:limit]


def search_other_states(query: str, limit: int = 10) -> List[Dict]:
    """
    Search cities from other states (fallback).
    
    Only used when no Maharashtra results found.
    """
    results = []
    query_lower = normalize_query(query)
    
    if len(query_lower) < 2:
        return []
    
    for city in OTHER_STATE_CITIES:
        name = city["city"]
        normalized = city["normalized"]
        
        # Check if query matches
        if query_lower in name.lower() or query_lower in normalized:
            score = calculate_match_score(
                name=name,
                normalized_key=normalized,
                query=query,
                is_search_surface=True,
                is_same_state=False,  # Different state = lower score
                is_stop=False,
            )
            
            results.append({
                "id": f"other_{city['id']}",
                "type": "city",
                "label": f"{city['city']}, {city['state']}",
                "label_en": city["city"],
                "city": city["city"],
                "city_local": "",
                "state": city["state"],
                "state_code": city["id"][:2],
                "operator": None,
                "is_search_surface": True,
                "score": score,
            })
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results[:limit]


@router.get("/autocomplete/bus")
async def bus_autocomplete(
    q: str = Query(..., min_length=1, description="Search query"),
    mode: str = Query("bus", description="Transport mode (always 'bus' for this endpoint)"),
    from_city_id: Optional[int] = Query(None, description="Origin city ID for proximity bias"),
    from_state_code: Optional[str] = Query(None, description="Origin state code for state bias"),
    limit: int = Query(15, ge=1, le=50, description="Max results"),
) -> Dict[str, Any]:
    """
    Cascading autocomplete search for BUS mode.
    
    Search Order (STRICT):
    1. Bus stops (same state) - HIGHEST PRIORITY
    2. Cities/districts (same state)
    3. Nearby districts (same state)
    4. Other states (India-wide fallback) - LOWEST PRIORITY
    
    Ranking Priority:
    - Exact stop name match > partial
    - is_search_surface = true gets higher rank
    - Same state > other states
    - City-level match lower than stop-level
    
    Examples:
    - "satara" → Satara ST Stand (Maharashtra)
    - "sangli" → Sangli ST Stand (Maharashtra)
    - "kolh" → Kolhapur (Maharashtra), NOT Kolkata
    """
    try:
        query = q.strip()
        
        if len(query) < 2:
            return {
                "query": query,
                "mode": mode,
                "count": 0,
                "results": [],
                "source": "none",
            }
        
        all_results = []
        
        # ============================================================
        # STEP 1: Search Maharashtra bus stops (HIGHEST PRIORITY)
        # ============================================================
        mh_stops = search_mh_bus_stops(query, limit=limit)
        all_results.extend(mh_stops)
        logger.info(f"[BUS_AUTO] query=\"{query}\" mh_stops={len(mh_stops)}")
        
        # ============================================================
        # STEP 2: Search Maharashtra cities/districts
        # ============================================================
        mh_cities = search_mh_cities(query, limit=limit)
        all_results.extend(mh_cities)
        logger.info(f"[BUS_AUTO] query=\"{query}\" mh_cities={len(mh_cities)}")
        
        # ============================================================
        # STEP 2.5: Search Tourist Destinations (Feeder Routes)
        # ============================================================
        tourist_results = search_tourist_destinations(query)
        all_results.extend(tourist_results)
        logger.info(f"[BUS_AUTO] query=\"{query}\" tourist_dest={len(tourist_results)}")
        
        # ============================================================
        # STEP 3: If no MH results, search other states (FALLBACK)
        # ============================================================
        if len(all_results) == 0:
            other_results = search_other_states(query, limit=limit)
            all_results.extend(other_results)
            logger.info(f"[BUS_AUTO] query=\"{query}\" other_states={len(other_results)}")
        
        # ============================================================
        # STEP 4: De-duplicate and sort by score
        # ============================================================
        
        # Remove duplicates (same city appearing as both stop and city)
        seen_cities = set()
        unique_results = []
        
        for result in sorted(all_results, key=lambda x: x["score"], reverse=True):
            city_key = result["city"].lower()
            result_type = result["type"]
            
            # For stops: always include (they're specific)
            if result_type == "bus_stop":
                unique_results.append(result)
            # For cities: only include if no stop from same city already included
            elif city_key not in seen_cities:
                unique_results.append(result)
                seen_cities.add(city_key)
            
            if len(unique_results) >= limit:
                break
        
        # ============================================================
        # STEP 5: Format response
        # ============================================================
        formatted_results = []
        for r in unique_results[:limit]:
            formatted = {
                "id": r["id"],
                "type": r["type"],
                "label": r["label"],
                "label_en": r.get("label_en", r["label"]),  # CRITICAL: Include English name
                "city": r["city"],
                "state": r["state"],
            }
            
            # Add optional fields
            if r.get("operator"):
                formatted["operator"] = r["operator"]
            if r.get("city_local"):
                formatted["city_local"] = r["city_local"]
            if r.get("is_search_surface") is not None:
                formatted["is_search_surface"] = r["is_search_surface"]
            
            formatted_results.append(formatted)
        
        source = "mh_stops" if mh_stops else ("mh_cities" if mh_cities else "other_states")
        
        logger.info(f"[BUS_AUTO] query=\"{query}\" total={len(formatted_results)} source={source}")
        
        return {
            "query": query,
            "mode": mode,
            "count": len(formatted_results),
            "results": formatted_results,
            "source": source,
        }
    
    except Exception as e:
        logger.error(f"[BUS_AUTO] Error: {e}", exc_info=True)
        raise HTTPException(500, f"Autocomplete search failed: {str(e)}")


@router.get("/autocomplete/bus/health")
async def bus_autocomplete_health():
    """
    Health check for bus autocomplete endpoint.
    """
    try:
        stops = get_all_stops()
        cities = get_all_cities()
        ss_stops = get_search_surface_stops()
        
        return {
            "status": "healthy",
            "mh_stops": len(stops),
            "mh_cities": len(cities),
            "search_surface_stops": len(ss_stops),
            "other_state_cities": len(OTHER_STATE_CITIES),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }

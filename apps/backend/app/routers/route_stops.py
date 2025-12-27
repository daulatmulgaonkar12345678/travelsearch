"""
Route Stops API - "Likely Stops on Route" Feature
==================================================

Provides indicative intermediate stops for MSRTC bus routes.

IMPORTANT DISCLAIMER:
- These are INDICATIVE stops based on geographic corridors
- NOT official MSRTC route schedules
- For precise information, check msrtc.maharashtra.gov.in

Endpoints:
- GET /api/routes/stops - Get likely stops for a route
- GET /api/routes/summary - Get compact route summary
- GET /api/routes/corridors - List all defined corridors
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict
import logging

from app.services.route_corridors import (
    get_likely_stops_on_route,
    get_likely_stops_by_city_names,
    get_route_summary,
    get_city_id_by_name,
    CORRIDORS,
)
from app.data.places import get_all_cities

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/routes", tags=["route-stops"])


# ============================================================
# RESPONSE MODELS
# ============================================================

class StopInfo:
    """Stop information for display."""
    def __init__(self, stop_id: int, stop_name: str, city: str):
        self.stop_id = stop_id
        self.stop_name = stop_name
        self.city = city


# ============================================================
# API ENDPOINTS
# ============================================================

@router.get("/stops")
async def get_route_stops(
    from_city: str = Query(..., description="Origin city name (English, Marathi, or normalized)"),
    to_city: str = Query(..., description="Destination city name"),
    max_stops: int = Query(10, ge=1, le=20, description="Maximum stops to return"),
) -> Dict:
    """
    Get likely intermediate stops for a bus route.
    
    ⚠️ IMPORTANT: These are INDICATIVE stops, not official schedules.
    
    Logic:
    1. Identifies the highway corridor between cities
    2. Selects major MSRTC depots along that corridor
    3. Orders stops geographically
    
    Example:
    - /api/routes/stops?from_city=Mumbai&to_city=Kolhapur
    - Returns: Panvel → Pune → Satara → Karad → Sangli
    
    Response includes:
    - stops: Ordered list of intermediate stops
    - corridor_name: Highway corridor used
    - disclaimer: Legal disclaimer
    """
    try:
        result = get_likely_stops_by_city_names(from_city, to_city, max_stops)
        
        if "error" in result:
            raise HTTPException(400, result["error"])
        
        logger.info(f"[ROUTE_STOPS] {from_city} → {to_city}: {result['stop_count']} stops")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ROUTE_STOPS] Error: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get route stops: {str(e)}")


@router.get("/stops/by-id")
async def get_route_stops_by_id(
    from_city_id: int = Query(..., description="Origin city/district ID"),
    to_city_id: int = Query(..., description="Destination city/district ID"),
    max_stops: int = Query(10, ge=1, le=20, description="Maximum stops to return"),
) -> Dict:
    """
    Get likely intermediate stops using city IDs.
    
    Same as /stops but uses numeric city_id instead of names.
    Useful when city_id is already known from autocomplete.
    """
    try:
        result = get_likely_stops_on_route(from_city_id, to_city_id, max_stops)
        
        logger.info(f"[ROUTE_STOPS] city_{from_city_id} → city_{to_city_id}: {result['stop_count']} stops")
        
        return result
    
    except Exception as e:
        logger.error(f"[ROUTE_STOPS] Error: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get route stops: {str(e)}")


@router.get("/summary")
async def get_route_summary_api(
    from_city: str = Query(..., description="Origin city name"),
    to_city: str = Query(..., description="Destination city name"),
) -> Dict:
    """
    Get compact route summary for display in search results.
    
    Returns:
    - via: List of intermediate city names
    - via_text: Formatted string "City1 → City2 → City3"
    - corridor: Highway corridor name
    - highway: Highway number (e.g., NH48)
    
    Example:
    - /api/routes/summary?from_city=Mumbai&to_city=Kolhapur
    - Returns: {"via": ["Pune", "Satara", "Sangli"], "via_text": "Pune → Satara → Sangli", ...}
    """
    try:
        from_id = get_city_id_by_name(from_city)
        to_id = get_city_id_by_name(to_city)
        
        if not from_id:
            raise HTTPException(400, f"Unknown origin city: {from_city}")
        if not to_id:
            raise HTTPException(400, f"Unknown destination city: {to_city}")
        
        result = get_route_summary(from_id, to_id)
        
        return {
            "from_city": from_city,
            "to_city": to_city,
            **result,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ROUTE_SUMMARY] Error: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to get route summary: {str(e)}")


@router.get("/corridors")
async def list_corridors() -> Dict:
    """
    List all defined highway corridors.
    
    Returns list of corridor info including:
    - ID, name, highway number
    - Districts covered
    - Major stops
    """
    cities = get_all_cities()
    city_map = {c["city_id"]: c["name_en"] for c in cities}
    
    corridors_list = []
    for corridor_id, corridor in CORRIDORS.items():
        # Map district IDs to names
        district_names = [
            city_map.get(d_id, f"District {d_id}") 
            for d_id in corridor["districts"]
        ]
        
        corridors_list.append({
            "id": corridor_id,
            "name": corridor["name"],
            "highway": corridor["highway"],
            "districts": district_names,
            "district_ids": corridor["districts"],
            "major_stops": corridor.get("major_stops", []),
        })
    
    return {
        "count": len(corridors_list),
        "corridors": corridors_list,
    }


@router.get("/cities")
async def list_route_cities() -> Dict:
    """
    List all Maharashtra cities/districts available for routing.
    
    Returns cities with their IDs for use with /stops/by-id endpoint.
    """
    cities = get_all_cities()
    
    return {
        "count": len(cities),
        "cities": [
            {
                "city_id": c["city_id"],
                "name_en": c["name_en"],
                "name_local": c["name_local"],
                "division": c.get("division", ""),
            }
            for c in cities
        ],
    }

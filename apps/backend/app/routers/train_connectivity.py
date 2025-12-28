"""Train Connectivity API Router

Endpoints for rail connectivity resolution and station search.
Uses static graph data - does NOT depend on live IRCTC APIs.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
import logging

from app.services.rail_connectivity import (
    resolve_connectivity,
    get_station_info,
    get_all_hubs,
    search_stations,
    RouteType,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/trains/connectivity")
async def check_connectivity(
    from_station: str = Query(..., alias="from", description="Origin station code or city name"),
    to_station: str = Query(..., alias="to", description="Destination station code or city name"),
):
    """
    Check rail connectivity between two stations.
    
    **Strategy** (Flight-like hub-based routing):
    1. Direct connectivity - same railway line or corridor
    2. Hub-based routing - via major junctions (max 2 hubs)
    3. Local catchment - nearby stations within 50km
    
    **Returns**:
    - route_type: DIRECT, HUB_BASED, LOCAL_CATCHMENT, or NOT_FOUND
    - path: List of stations in the route
    - confidence: HIGH, MEDIUM, or LOW
    - note: Human-readable explanation
    
    **Example**:
    - /api/trains/connectivity?from=PUNE&to=NDLS → Hub-based via Mumbai/Bhopal
    - /api/trains/connectivity?from=CSMT&to=PUNE → Direct route
    - /api/trains/connectivity?from=Satara&to=Pune → Direct route
    """
    try:
        result = resolve_connectivity(from_station, to_station)
        
        logger.info(
            f"🚆 Connectivity check: {from_station} → {to_station} | "
            f"type={result.route_type.value} | confidence={result.confidence.value}"
        )
        
        return {
            "route_type": result.route_type.value,
            "path": result.path,
            "confidence": result.confidence.value,
            "note": result.note,
            "total_distance_km": result.total_distance_km,
            "via_hubs": result.via_hubs or [],
            "zone_changes": result.zone_changes,
            "from_input": from_station,
            "to_input": to_station,
        }
        
    except FileNotFoundError as e:
        logger.error(f"❌ Railway data files not found: {e}")
        raise HTTPException(
            status_code=500,
            detail="Railway connectivity data not available. Please try again later."
        )
    except Exception as e:
        logger.error(f"❌ Connectivity check error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to check rail connectivity. Please try again."
        )


@router.get("/trains/stations/search")
async def search_train_stations(
    q: str = Query(..., min_length=2, description="Search query (station code, name, or city)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
):
    """
    Search for railway stations by code, name, or city.
    
    **Ranking** (by score):
    - Exact code match: highest
    - Code prefix match
    - Exact city match
    - City prefix match
    - Station name contains
    - Alias match
    
    **Boosts**:
    - Railway hubs get +20 score
    - MAJOR stations get +10
    - JUNCTION stations get +5
    
    **Example**:
    - /api/trains/stations/search?q=NDLS → New Delhi
    - /api/trains/stations/search?q=Mumbai → CSMT, BCT, LTT, DR
    - /api/trains/stations/search?q=Pune → PUNE junction
    """
    try:
        results = search_stations(q, limit)
        
        return {
            "query": q,
            "results": results,
            "count": len(results),
        }
        
    except Exception as e:
        logger.error(f"❌ Station search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Station search failed. Please try again."
        )


@router.get("/trains/stations/{station_code}")
async def get_station(station_code: str):
    """
    Get detailed information about a railway station.
    
    **Returns**:
    - Station details (name, city, state, zone)
    - Station type (MAJOR, JUNCTION, LOCAL)
    - Hub information if applicable
    - Known aliases
    """
    try:
        info = get_station_info(station_code)
        
        if not info:
            raise HTTPException(
                status_code=404,
                detail=f"Station not found: {station_code}"
            )
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get station error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get station info. Please try again."
        )


@router.get("/trains/hubs")
async def list_railway_hubs(
    hub_type: Optional[str] = Query(None, description="Filter by hub type: MEGA_HUB, MAJOR_HUB, REGIONAL_HUB"),
    zone: Optional[str] = Query(None, description="Filter by railway zone: NR, WR, CR, etc."),
):
    """
    Get list of all railway hubs.
    
    **Hub Types**:
    - MEGA_HUB: Top 4 metros (NDLS, CSMT, HWH, MAS)
    - MAJOR_HUB: State capitals & zonal HQs
    - REGIONAL_HUB: Important regional junctions
    
    **Use Cases**:
    - Display hub markers on map
    - Suggest hub-based routing
    - Show connectivity options
    """
    try:
        hubs = get_all_hubs()
        
        # Apply filters
        if hub_type:
            hubs = [h for h in hubs if h["hub_type"] == hub_type.upper()]
        
        if zone:
            hubs = [h for h in hubs if h["zone"] == zone.upper()]
        
        # Sort by importance
        hubs.sort(key=lambda x: x["importance_score"], reverse=True)
        
        return {
            "hubs": hubs,
            "count": len(hubs),
            "filters": {
                "hub_type": hub_type,
                "zone": zone,
            }
        }
        
    except Exception as e:
        logger.error(f"❌ List hubs error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to list railway hubs. Please try again."
        )


@router.get("/trains/autocomplete")
async def train_autocomplete(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(8, ge=1, le=20, description="Maximum results"),
):
    """
    Autocomplete endpoint for train station search.
    
    Optimized for quick typeahead suggestions.
    Returns stations sorted by relevance and importance.
    
    **Response format**:
    Each result contains:
    - station_code: Railway station code (e.g., NDLS)
    - display_name: Human-readable name
    - city: City name
    - state: State name
    - is_hub: Whether it's a major hub
    """
    try:
        results = search_stations(q, limit)
        
        # Format for autocomplete
        formatted = []
        for r in results:
            hub_badge = ""
            if r.get("is_hub"):
                hub_badge = " 🚉"
            elif r.get("station_type") == "JUNCTION":
                hub_badge = " ⚡"
            
            formatted.append({
                "station_code": r["station_code"],
                "display_name": f"{r['station_name']} ({r['station_code']}){hub_badge}",
                "city": r["city"],
                "state": r["state"],
                "zone": r["zone"],
                "is_hub": r.get("is_hub", False),
                "station_type": r.get("station_type"),
            })
        
        return {
            "suggestions": formatted,
            "count": len(formatted),
        }
        
    except Exception as e:
        logger.error(f"❌ Autocomplete error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Autocomplete failed. Please try again."
        )

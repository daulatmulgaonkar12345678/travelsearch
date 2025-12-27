"""
Route Stops API - Likely Stops on Route Feature
================================================

Provides indicative intermediate stops for bus routes.

IMPORTANT DISCLAIMER:
- These are INDICATIVE stops based on geographic corridors
- NOT official MSRTC route schedules
- Actual routes may vary by service type

API Endpoints:
- GET /api/routes/stops?from_city_id=X&to_city_id=Y
- GET /api/routes/stops/by-name?from_city=pune&to_city=kolhapur
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
import logging

from app.services.route_corridors import (
    get_likely_stops_on_route,
    get_likely_stops_by_city_names,
    get_route_summary,
    get_city_id_by_name,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# Response Models
# ============================================================

class StopInfo(BaseModel):
    """Information about a stop on the route."""
    stop_id: int
    stop_name: str  # Marathi name
    stop_name_en: str  # English approximation
    city: str  # City/district name
    city_local: str  # City name in Marathi
    district_id: int
    is_major: bool


class LikelyStopsResponse(BaseModel):
    """Response for likely stops on route."""
    from_city: str
    to_city: str
    likely_stops: List[str]  # Simplified list for frontend display
    detailed_stops: List[StopInfo]  # Detailed info if needed
    corridor_name: Optional[str] = None
    highway: Optional[str] = None
    stop_count: int
    note: str
    source: str  # "corridor" or "direct"


class RouteSummaryResponse(BaseModel):
    """Compact route summary for display."""
    via: List[str]  # List of city names
    via_text: str  # "Satara → Karad → Sangli" or "Direct"
    corridor: Optional[str] = None
    highway: Optional[str] = None
    stop_count: int


# ============================================================
# API Endpoints
# ============================================================

@router.get("/routes/stops", response_model=LikelyStopsResponse, tags=["routes"])
async def get_likely_stops(
    from_city_id: Optional[int] = Query(None, description="Origin city/district ID"),
    to_city_id: Optional[int] = Query(None, description="Destination city/district ID"),
    from_city: Optional[str] = Query(None, description="Origin city name (English)"),
    to_city: Optional[str] = Query(None, description="Destination city name (English)"),
    max_stops: int = Query(10, ge=1, le=20, description="Maximum stops to return"),
):
    """
    Get likely intermediate stops for a bus route.
    
    You can specify either:
    - from_city_id & to_city_id (numeric IDs)
    - from_city & to_city (city names in English)
    
    **Important:** These stops are INDICATIVE based on common MSRTC routes.
    Actual stops may vary by service type. Please verify with MSRTC official timetable.
    
    Example response:
    ```json
    {
      "from_city": "Pune",
      "to_city": "Kolhapur",
      "likely_stops": [
        "Satara ST Stand",
        "Karad ST Stand",
        "Sangli ST Stand"
      ],
      "note": "Stops are indicative and may vary by service."
    }
    ```
    """
    try:
        # Determine which method to use
        if from_city_id is not None and to_city_id is not None:
            # Use IDs
            result = get_likely_stops_on_route(from_city_id, to_city_id, max_stops)
        elif from_city and to_city:
            # Use city names
            result = get_likely_stops_by_city_names(from_city, to_city, max_stops)
        else:
            raise HTTPException(
                status_code=400,
                detail="Provide either (from_city_id, to_city_id) or (from_city, to_city)"
            )
        
        # Check for errors
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        # Build response
        return LikelyStopsResponse(
            from_city=result["from_city"],
            to_city=result["to_city"],
            likely_stops=[f"{s['city']} ST Stand" for s in result["stops"]],
            detailed_stops=[
                StopInfo(
                    stop_id=s["stop_id"],
                    stop_name=s["stop_name"],
                    stop_name_en=s["stop_name_en"],
                    city=s["city"],
                    city_local=s["city_local"],
                    district_id=s["district_id"],
                    is_major=s["is_major"],
                )
                for s in result["stops"]
            ],
            corridor_name=result.get("corridor_name"),
            highway=result.get("highway"),
            stop_count=result["stop_count"],
            note="Stops are indicative and may vary by service.",
            source=result["source"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting likely stops: {e}")
        raise HTTPException(status_code=500, detail="Failed to get route stops")


@router.get("/routes/summary", response_model=RouteSummaryResponse, tags=["routes"])
async def get_route_summary_api(
    from_city_id: Optional[int] = Query(None, description="Origin city/district ID"),
    to_city_id: Optional[int] = Query(None, description="Destination city/district ID"),
    from_city: Optional[str] = Query(None, description="Origin city name (English)"),
    to_city: Optional[str] = Query(None, description="Destination city name (English)"),
):
    """
    Get a compact route summary showing via cities.
    
    Returns a simplified summary suitable for display in bus cards.
    
    Example response:
    ```json
    {
      "via": ["Satara", "Karad", "Sangli"],
      "via_text": "Satara → Karad → Sangli",
      "corridor": "Pune-Kolhapur Highway",
      "highway": "NH48",
      "stop_count": 3
    }
    ```
    """
    try:
        # Resolve city IDs if names provided
        resolved_from_id = from_city_id
        resolved_to_id = to_city_id
        
        if from_city and not from_city_id:
            resolved_from_id = get_city_id_by_name(from_city)
            if not resolved_from_id:
                raise HTTPException(status_code=404, detail=f"Unknown city: {from_city}")
        
        if to_city and not to_city_id:
            resolved_to_id = get_city_id_by_name(to_city)
            if not resolved_to_id:
                raise HTTPException(status_code=404, detail=f"Unknown city: {to_city}")
        
        if not resolved_from_id or not resolved_to_id:
            raise HTTPException(
                status_code=400,
                detail="Provide either (from_city_id, to_city_id) or (from_city, to_city)"
            )
        
        result = get_route_summary(resolved_from_id, resolved_to_id)
        
        return RouteSummaryResponse(
            via=result["via"],
            via_text=result["via_text"],
            corridor=result.get("corridor"),
            highway=result.get("highway"),
            stop_count=result["stop_count"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting route summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get route summary")


@router.get("/routes/corridors", tags=["routes"])
async def list_corridors():
    """
    List all supported highway corridors in Maharashtra.
    
    These corridors are used to determine intermediate stops.
    """
    from app.services.route_corridors import CORRIDORS
    
    return {
        "corridors": [
            {
                "id": corridor_id,
                "name": corridor["name"],
                "highway": corridor["highway"],
                "major_stops": corridor.get("major_stops", []),
            }
            for corridor_id, corridor in CORRIDORS.items()
        ],
        "total": len(CORRIDORS),
    }

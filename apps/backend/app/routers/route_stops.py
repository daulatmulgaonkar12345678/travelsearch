"""
Route Stops API - Enhanced Likely Stops on Route Feature
=========================================================

Provides indicative intermediate stops for bus routes.
Separates stops into MAJOR (always shown) and MINOR (expandable).

IMPORTANT DISCLAIMER:
- These are INDICATIVE stops based on geographic corridors
- NOT official MSRTC route schedules
- Actual routes may vary by service type

API Endpoints:
- GET /api/routes/stops - Get stops with MAJOR/MINOR separation
- GET /api/routes/summary - Get compact route summary
- GET /api/routes/corridors - List all supported corridors
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
import logging

from app.services.corridor_resolver import (
    get_likely_stops_enhanced,
    get_likely_stops_by_name_enhanced,
    get_resolver,
    get_city_name,
    get_city_id_by_name,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# Response Models
# ============================================================

class StopDetail(BaseModel):
    """Detailed information about a stop."""
    stop_key: str
    stop_name: str
    city_id: int
    city_name: str
    importance: str  # MAJOR or MINOR
    km_from_origin: int


class LikelyStopsResponse(BaseModel):
    """Response for likely stops on route with MAJOR/MINOR separation."""
    from_city: str
    to_city: str
    major_stops: List[str]  # Always shown - main ST stands
    minor_stops: List[str]  # Shown on expand - smaller stops
    all_stops: List[StopDetail]  # Full details for advanced UI
    corridor_name: Optional[str] = None
    highway: Optional[str] = None
    source: str  # "corridor" or "no_corridor"
    note: str


class RouteSummaryResponse(BaseModel):
    """Compact route summary for inline display."""
    via: List[str]  # Major stops only
    via_text: str  # "Satara → Karad → Sangli" or "Direct"
    corridor: Optional[str] = None
    highway: Optional[str] = None
    has_minor_stops: bool  # Indicates if expandable stops exist
    minor_count: int


class CorridorInfo(BaseModel):
    """Information about a highway corridor."""
    id: str
    name: str
    highway: str
    description: Optional[str] = None


# ============================================================
# API Endpoints
# ============================================================

@router.get("/routes/stops", response_model=LikelyStopsResponse, tags=["routes"])
async def get_route_stops(
    from_city_id: Optional[int] = Query(None, description="Origin city/district ID"),
    to_city_id: Optional[int] = Query(None, description="Destination city/district ID"),
    from_city: Optional[str] = Query(None, description="Origin city name (English)"),
    to_city: Optional[str] = Query(None, description="Destination city name (English)"),
):
    """
    Get likely intermediate stops for a bus route.
    
    **Separates stops by importance:**
    - **MAJOR stops**: Main ST stands and depots - always shown
    - **MINOR stops**: Smaller stops and phatas - shown on user expand
    
    You can specify either:
    - from_city_id & to_city_id (numeric IDs)
    - from_city & to_city (city names in English)
    
    **Example - Mumbai to Ratnagiri:**
    ```json
    {
      "major_stops": ["Panvel", "Mahad", "Chiplun", "Ratnagiri"],
      "minor_stops": ["Pen", "Roha", "Khed", "Kashil", "Sangmeshwar"],
      "corridor_name": "Mumbai-Goa Konkan Highway",
      "highway": "NH66",
      "note": "Stops are indicative and may vary by service."
    }
    ```
    
    **Important:** These stops are INDICATIVE based on common MSRTC routes.
    Actual stops may vary by service type.
    """
    try:
        # Determine which method to use
        if from_city_id is not None and to_city_id is not None:
            result = get_likely_stops_enhanced(from_city_id, to_city_id)
        elif from_city and to_city:
            result = get_likely_stops_by_name_enhanced(from_city, to_city)
        else:
            raise HTTPException(
                status_code=400,
                detail="Provide either (from_city_id, to_city_id) or (from_city, to_city)"
            )
        
        # Check for errors
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return LikelyStopsResponse(
            from_city=result["from_city"],
            to_city=result["to_city"],
            major_stops=result["major_stops"],
            minor_stops=result["minor_stops"],
            all_stops=[
                StopDetail(
                    stop_key=s["stop_key"],
                    stop_name=s["stop_name"],
                    city_id=s["city_id"],
                    city_name=s["city_name"],
                    importance=s["importance"],
                    km_from_origin=s["km_from_origin"],
                )
                for s in result.get("all_stops", [])
            ],
            corridor_name=result.get("corridor_name"),
            highway=result.get("highway"),
            source=result.get("source", "unknown"),
            note=result.get("note", "Stops are indicative and may vary by service."),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting route stops: {e}")
        raise HTTPException(status_code=500, detail="Failed to get route stops")


@router.get("/routes/summary", response_model=RouteSummaryResponse, tags=["routes"])
async def get_route_summary(
    from_city_id: Optional[int] = Query(None, description="Origin city/district ID"),
    to_city_id: Optional[int] = Query(None, description="Destination city/district ID"),
    from_city: Optional[str] = Query(None, description="Origin city name (English)"),
    to_city: Optional[str] = Query(None, description="Destination city name (English)"),
):
    """
    Get a compact route summary showing major via cities.
    
    Returns a simplified summary suitable for inline display in bus cards.
    Also indicates if minor (expandable) stops are available.
    
    **Example response:**
    ```json
    {
      "via": ["Satara", "Karad", "Sangli"],
      "via_text": "Satara → Karad → Sangli",
      "corridor": "Pune-Kolhapur Highway",
      "highway": "NH48",
      "has_minor_stops": true,
      "minor_count": 4
    }
    ```
    """
    try:
        # Resolve city IDs
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
        
        result = get_likely_stops_enhanced(resolved_from_id, resolved_to_id)
        
        major_stops = result.get("major_stops", [])
        minor_stops = result.get("minor_stops", [])
        
        return RouteSummaryResponse(
            via=major_stops,
            via_text=" → ".join(major_stops) if major_stops else "Direct",
            corridor=result.get("corridor_name"),
            highway=result.get("highway"),
            has_minor_stops=len(minor_stops) > 0,
            minor_count=len(minor_stops),
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
    Each corridor includes MAJOR and MINOR stops in geographic sequence.
    """
    resolver = get_resolver()
    
    corridors_info = []
    for corridor_id, corridor in resolver.corridors.items():
        major_count = len([s for s in corridor.get("stops_sequence", []) if s["importance"] == "MAJOR"])
        minor_count = len([s for s in corridor.get("stops_sequence", []) if s["importance"] == "MINOR"])
        
        corridors_info.append({
            "id": corridor_id,
            "name": corridor.get("name"),
            "highway": corridor.get("highway"),
            "description": corridor.get("description"),
            "major_stops_count": major_count,
            "minor_stops_count": minor_count,
            "total_stops": major_count + minor_count,
        })
    
    return {
        "corridors": corridors_info,
        "total": len(corridors_info),
        "disclaimer": "Stop sequences are indicative based on highway geography. Actual bus routes may vary."
    }

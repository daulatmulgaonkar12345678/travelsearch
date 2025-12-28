"""Feeder Routes API - Tourist Destination Connectivity
========================================================

API endpoints for finding routes to tourist destinations
via feeder connections.

Endpoints:
- GET /api/routes/find - Find route between any two locations
- GET /api/routes/destinations - List all tourist destinations
- GET /api/routes/destination/{id} - Get destination info
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
import logging

from app.services.feeder_resolver import (
    get_feeder_resolver,
    find_route,
    is_tourist_destination,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# Response Models
# ============================================================

class RouteSegment(BaseModel):
    """A segment of the route."""
    type: str  # HIGHWAY, FEEDER, DIRECT_FEEDER
    from_: str  # Using from_ due to Python keyword
    to: str
    corridor_name: Optional[str] = None
    highway: Optional[str] = None
    major_stops: Optional[List[str]] = None
    minor_stops: Optional[List[str]] = None
    distance_km: Optional[float] = None
    frequency: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        # Allow using 'from' in JSON output
        fields = {'from_': 'from'}
        populate_by_name = True


class DestinationInfo(BaseModel):
    """Tourist destination information."""
    name: str
    name_local: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None


class RouteResponse(BaseModel):
    """Full route response."""
    connected: bool
    route_type: str  # HIGHWAY_DIRECT, FEEDER, HIGHWAY_PLUS_FEEDER, DIRECT_FEEDER, NO_ROUTE
    from_city: str
    to_city: str
    destination_info: Optional[DestinationInfo] = None
    segments: List[dict]  # Using dict to avoid serialization issues
    via_junction: Optional[str] = None
    total_distance_km: Optional[float] = None
    estimated_time_hrs: Optional[float] = None
    frequency: Optional[str] = None
    note: str


class TouristDestination(BaseModel):
    """Tourist destination model."""
    id: str
    name_en: str
    name_local: Optional[str] = None
    type: str
    district_id: int
    description: Optional[str] = None
    altitude_m: Optional[int] = None


# ============================================================
# API Endpoints
# ============================================================

@router.get("/routes/find", response_model=RouteResponse, tags=["routes"])
async def find_bus_route(
    from_city: str = Query(..., min_length=2, description="Origin city or location"),
    to_city: str = Query(..., min_length=2, description="Destination city or location"),
):
    """
    Find bus route between two locations.
    
    Supports:
    - City to city (highway corridors)
    - City to tourist destination (feeder routes)
    - Tourist destination to city (reverse feeder)
    
    **Examples:**
    - Pune → Mahabaleshwar (hill station)
    - Mumbai → Ganpatipule (coastal temple)
    - Aurangabad → Ajanta Caves (heritage site)
    
    **Response includes:**
    - Connected status
    - Route segments (highway + feeder breakdown)
    - Estimated distance and time
    - Bus frequency information
    
    **Note:** All information is indicative. Actual bus availability
    varies by season and demand.
    """
    try:
        result = find_route(from_city, to_city)
        
        # Convert segments for API response
        segments = []
        for seg in result.get("segments", []):
            segment = {
                "type": seg.get("type"),
                "from": seg.get("from"),
                "to": seg.get("to"),
            }
            if seg.get("corridor_name"):
                segment["corridor_name"] = seg["corridor_name"]
            if seg.get("highway"):
                segment["highway"] = seg["highway"]
            if seg.get("major_stops"):
                segment["major_stops"] = seg["major_stops"]
            if seg.get("minor_stops"):
                segment["minor_stops"] = seg["minor_stops"]
            if seg.get("distance_km"):
                segment["distance_km"] = seg["distance_km"]
            if seg.get("frequency"):
                segment["frequency"] = seg["frequency"]
            if seg.get("description"):
                segment["description"] = seg["description"]
            segments.append(segment)
        
        return RouteResponse(
            connected=result.get("connected", False),
            route_type=result.get("route_type", "UNKNOWN"),
            from_city=result.get("from_city", from_city),
            to_city=result.get("to_city", to_city),
            destination_info=DestinationInfo(**result["destination_info"]) if result.get("destination_info") else None,
            segments=segments,
            via_junction=result.get("via_junction"),
            total_distance_km=result.get("total_distance_km"),
            estimated_time_hrs=result.get("estimated_time_hrs"),
            frequency=result.get("frequency"),
            note=result.get("note", "Route information unavailable."),
        )
        
    except Exception as e:
        logger.error(f"Error finding route: {e}")
        raise HTTPException(status_code=500, detail="Failed to find route")


@router.get("/routes/destinations", tags=["routes"])
async def list_tourist_destinations(
    type: Optional[str] = Query(None, description="Filter by type: HILL_STATION, RELIGIOUS, HERITAGE, BEACH, RESORT"),
):
    """
    List all tourist destinations in Maharashtra.
    
    **Destination Types:**
    - HILL_STATION: Mountain retreats (Mahabaleshwar, Matheran, Lonavala)
    - RELIGIOUS: Temples and pilgrimage sites (Shirdi, Pandharpur, Trimbakeshwar)
    - HERITAGE: UNESCO and historic sites (Ajanta, Ellora, Daulatabad)
    - BEACH: Coastal destinations (Alibaug, Ganpatipule, Tarkarli)
    - RESORT: Recreation areas (Lavasa)
    """
    try:
        resolver = get_feeder_resolver()
        destinations = resolver.list_tourist_destinations(type)
        
        return {
            "destinations": destinations,
            "total": len(destinations),
            "filter": type,
        }
        
    except Exception as e:
        logger.error(f"Error listing destinations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list destinations")


@router.get("/routes/destination/{dest_id}", tags=["routes"])
async def get_destination_info(dest_id: str):
    """
    Get detailed information about a tourist destination.
    
    Also returns available feeder routes to this destination.
    """
    try:
        resolver = get_feeder_resolver()
        dest_info = resolver.destinations.get(dest_id)
        
        if not dest_info:
            raise HTTPException(status_code=404, detail=f"Destination not found: {dest_id}")
        
        # Get available feeders to this destination
        feeders = resolver.dest_feeders.get(dest_id, [])
        
        from_cities = []
        for feeder in feeders:
            from app.services.corridor_resolver import get_city_name
            from_cities.append({
                "city": get_city_name(feeder["from_city_id"]),
                "distance_km": feeder.get("distance_km"),
                "travel_time_hrs": feeder.get("travel_time_hrs"),
                "frequency": feeder.get("frequency"),
            })
        
        return {
            "destination": dest_info,
            "reachable_from": from_cities,
            "total_connections": len(from_cities),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting destination info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get destination info")


@router.get("/routes/check-tourist", tags=["routes"])
async def check_if_tourist_destination(
    name: str = Query(..., min_length=2, description="Location name to check"),
):
    """
    Check if a location is a known tourist destination.
    
    Useful for UI to determine if feeder route logic should be applied.
    """
    try:
        resolver = get_feeder_resolver()
        is_tourist = resolver.is_tourist_destination(name)
        dest_info = resolver.get_destination_info(name) if is_tourist else None
        
        return {
            "name": name,
            "is_tourist_destination": is_tourist,
            "destination_info": dest_info,
        }
        
    except Exception as e:
        logger.error(f"Error checking tourist destination: {e}")
        raise HTTPException(status_code=500, detail="Failed to check destination")

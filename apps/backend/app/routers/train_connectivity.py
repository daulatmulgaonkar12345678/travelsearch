"""Train Connectivity API Router v2.0

City-first search model for Indian Railways:
- City searches return all stations in that city
- Station searches return specific station
- Connectivity expands city to all station pairs

Booking redirects to IRCTC, RailYatri, ConfirmTkt
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
import logging
from datetime import datetime

from app.services.rail_connectivity import (
    resolve_connectivity,
    search_stations_cities,
    resolve_to_station_codes,
    get_station_info,
    get_city_info,
    get_all_cities,
    get_all_hubs,
    generate_booking_links,
    RouteType,
    SearchResultType,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/trains/connectivity")
async def check_connectivity(
    from_station: str = Query(..., alias="from", description="Origin city or station code"),
    to_station: str = Query(..., alias="to", description="Destination city or station code"),
):
    """
    Check rail connectivity between two locations.
    
    **City-First Search Model:**
    - Input "Pune" → expands to [PUNE, SVJR, KJSR, ...]
    - Input "Mumbai" → expands to [CSMT, BCT, LTT, DR, ...]
    - Input "NDLS" → uses specific station
    
    **Route Resolution:**
    - City → City: Finds best route among all station pairs
    - Station → City: Single origin, multiple destinations
    - Station → Station: Direct lookup
    
    **Returns:**
    - route_type: DIRECT, HUB_BASED, LOCAL_CATCHMENT, NOT_FOUND
    - path: List of stations in best route
    - from_stations: All origin station codes considered
    - to_stations: All destination station codes considered
    """
    try:
        result = resolve_connectivity(from_station, to_station)
        
        logger.info(
            f"🚆 Connectivity: {from_station} → {to_station} | "
            f"type={result.route_type.value} | "
            f"from_stations={result.from_stations} | "
            f"to_stations={result.to_stations}"
        )
        
        # Generate booking links using primary stations
        from_primary = result.from_stations[0] if result.from_stations else from_station
        to_primary = result.to_stations[0] if result.to_stations else to_station
        booking_partners = generate_booking_links(from_primary, to_primary)
        
        return {
            "route_type": result.route_type.value,
            "path": result.path,
            "confidence": result.confidence.value,
            "note": result.note,
            "total_distance_km": result.total_distance_km,
            "via_hubs": result.via_hubs,
            "zone_changes": result.zone_changes,
            "from_input": from_station,
            "to_input": to_station,
            "from_stations": result.from_stations,
            "to_stations": result.to_stations,
            "booking_partners": booking_partners,
            "disclaimer": "Schedules are indicative. Check booking partner for live availability."
        }
        
    except FileNotFoundError as e:
        logger.error(f"❌ Railway data files not found: {e}")
        raise HTTPException(
            status_code=500,
            detail="Railway connectivity data not available."
        )
    except Exception as e:
        logger.error(f"❌ Connectivity error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to check rail connectivity."
        )


@router.get("/trains/search")
async def search_trains_locations(
    q: str = Query(..., min_length=1, description="Search query (city name, station name, or code)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
):
    """
    Search for train locations (cities and stations).
    
    **City-First Results:**
    - Typing "Pune" returns City result with all stations listed
    - Typing "Shivaji Nagar" returns specific Station result
    - Typing "NDLS" returns specific Station result
    
    **Alias Support:**
    - "Bombay" → Mumbai
    - "VT" → CSMT
    - "Calcutta" → Kolkata
    - "Madras" → Chennai
    
    **Response Format:**
    ```json
    {
      "results": [
        {
          "result_type": "city",
          "display_name": "Pune",
          "subtitle": "Maharashtra • 5 stations",
          "station_codes": ["PUNE", "SVJR", "KJSR", ...],
          "city_id": "pune"
        },
        {
          "result_type": "station",
          "display_name": "Shivajinagar (SVJR)",
          "subtitle": "Pune, Maharashtra",
          "station_codes": ["SVJR"],
          "station_code": "SVJR"
        }
      ]
    }
    ```
    """
    try:
        results = search_stations_cities(q, limit)
        
        return {
            "query": q,
            "results": [
                {
                    "result_type": r.result_type.value,
                    "display_name": r.display_name,
                    "subtitle": r.subtitle,
                    "station_codes": r.station_codes,
                    "city_id": r.city_id,
                    "station_code": r.station_code,
                    "is_metro": r.is_metro,
                }
                for r in results
            ],
            "count": len(results),
        }
        
    except Exception as e:
        logger.error(f"❌ Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Search failed.")


@router.get("/trains/autocomplete")
async def train_autocomplete(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(8, ge=1, le=20, description="Maximum results"),
):
    """
    Autocomplete endpoint for train search input.
    
    Returns quick typeahead suggestions with:
    - Cities first (if metro/multi-station)
    - Stations for specific queries
    - Badges for metros (🏙️) and hubs (🚉)
    """
    try:
        results = search_stations_cities(q, limit)
        
        suggestions = []
        for r in results:
            badge = ""
            if r.result_type == SearchResultType.CITY:
                if r.is_metro:
                    badge = " 🏙️"
                elif len(r.station_codes) > 1:
                    badge = " 📍"
            else:
                # Station
                if r.station_code and r.station_code in ["NDLS", "CSMT", "HWH", "MAS", "SC", "SBC"]:
                    badge = " 🚉"
            
            suggestions.append({
                "type": r.result_type.value,
                "display_name": f"{r.display_name}{badge}",
                "subtitle": r.subtitle,
                "value": r.city_id if r.result_type == SearchResultType.CITY else r.station_code,
                "station_codes": r.station_codes,
            })
        
        return {
            "suggestions": suggestions,
            "count": len(suggestions),
        }
        
    except Exception as e:
        logger.error(f"❌ Autocomplete error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Autocomplete failed.")


@router.get("/trains/resolve")
async def resolve_location(
    q: str = Query(..., description="City or station input to resolve"),
):
    """
    Resolve a user input to station code(s).
    
    **Use Case:** Before making a train search, resolve inputs to get all relevant station codes.
    
    **Examples:**
    - "Pune" → {"type": "city", "station_codes": ["PUNE", "SVJR", ...]}
    - "NDLS" → {"type": "station", "station_codes": ["NDLS"]}
    - "Bombay" → {"type": "city", "station_codes": ["CSMT", "BCT", "LTT", ...]}
    """
    try:
        input_type, station_codes = resolve_to_station_codes(q)
        
        return {
            "input": q,
            "type": input_type,
            "station_codes": station_codes,
            "count": len(station_codes),
        }
        
    except Exception as e:
        logger.error(f"❌ Resolve error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Resolution failed.")


@router.get("/trains/stations/{station_code}")
async def get_station(station_code: str):
    """
    Get detailed information about a railway station.
    
    **Returns:**
    - Station details (name, city, state, zone)
    - Whether it's a major station
    - Number of trains passing through
    - Other stations in the same city
    """
    try:
        info = get_station_info(station_code)
        
        if not info:
            raise HTTPException(status_code=404, detail=f"Station not found: {station_code}")
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get station error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get station info.")


@router.get("/trains/cities/{city_id}")
async def get_city(city_id: str):
    """
    Get city information with all its railway stations.
    
    **Returns:**
    - City details (name, state, is_metro)
    - List of all stations with train counts
    - Primary station marked
    """
    try:
        info = get_city_info(city_id)
        
        if not info:
            raise HTTPException(status_code=404, detail=f"City not found: {city_id}")
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get city error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get city info.")


@router.get("/trains/cities")
async def list_cities(
    metro_only: bool = Query(False, description="Return only metro cities"),
    state: Optional[str] = Query(None, description="Filter by state name"),
    limit: int = Query(100, ge=1, le=200, description="Maximum results"),
):
    """
    Get list of all cities with railway stations.
    
    Sorted by population rank (major metros first).
    """
    try:
        cities = get_all_cities()
        
        if metro_only:
            cities = [c for c in cities if c["is_metro"]]
        
        if state:
            cities = [c for c in cities if state.lower() in c["state"].lower()]
        
        return {
            "cities": cities[:limit],
            "count": len(cities[:limit]),
            "filters": {
                "metro_only": metro_only,
                "state": state,
            }
        }
        
    except Exception as e:
        logger.error(f"❌ List cities error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list cities.")


@router.get("/trains/hubs")
async def list_railway_hubs(
    hub_type: Optional[str] = Query(None, description="Filter: MEGA_HUB, MAJOR_HUB, REGIONAL_HUB"),
    zone: Optional[str] = Query(None, description="Filter by railway zone"),
):
    """
    Get list of all railway hubs (major junction stations).
    """
    try:
        hubs = get_all_hubs()
        
        if hub_type:
            hubs = [h for h in hubs if h.get("hub_type") == hub_type.upper()]
        
        if zone:
            hubs = [h for h in hubs if h.get("zone") == zone.upper()]
        
        hubs.sort(key=lambda x: x.get("importance_score", 0), reverse=True)
        
        return {
            "hubs": hubs,
            "count": len(hubs),
        }
        
    except Exception as e:
        logger.error(f"❌ List hubs error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list hubs.")


@router.get("/trains/booking-links")
async def get_booking_links(
    from_station: str = Query(..., alias="from", description="Origin station code"),
    to_station: str = Query(..., alias="to", description="Destination station code"),
    date: Optional[str] = Query(None, description="Travel date (YYYY-MM-DD)"),
):
    """
    Get booking partner deep links for a route.
    
    **Partners:**
    - IRCTC (Official)
    - RailYatri
    - ConfirmTkt
    - Paytm
    
    **Note:** User will be redirected to partner site for actual booking.
    """
    try:
        links = generate_booking_links(from_station, to_station, date)
        
        return {
            "from_station": from_station,
            "to_station": to_station,
            "date": date,
            "booking_partners": links,
            "disclaimer": "You will be redirected to the partner's website for live availability and booking."
        }
        
    except Exception as e:
        logger.error(f"❌ Booking links error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate booking links.")


# Legacy endpoint for backwards compatibility
@router.get("/trains/stations/search")
async def search_stations_legacy(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
):
    """
    Legacy station search endpoint (redirects to new search).
    """
    return await search_trains_locations(q=q, limit=limit)

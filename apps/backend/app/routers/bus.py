"""Bus Search API Router

Endpoints for searching bus routes in India.
Uses static data from State RTC schedules and industry standards.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import date, timedelta
import logging

from app.models.transport import BusSearchRequest, BusSearchResponse
from app.services.bus_search import search_buses

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search/buses", response_model=BusSearchResponse)
async def search_buses_endpoint(
    origin: str = Query(..., description="Origin city name"),
    destination: str = Query(..., description="Destination city name"),
    departure_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    
    # Optional filters
    bus_type: Optional[str] = Query(None, description="Filter by bus type (ordinary, ac_seater, ac_sleeper, volvo)"),
    ac_only: bool = Query(False, description="Show only AC buses"),
    sleeper_only: bool = Query(False, description="Show only sleeper buses"),
    passengers: int = Query(1, ge=1, le=6, description="Number of passengers"),
):
    """
    Search for buses between two cities.
    
    **Data Source**: State RTC published schedules and industry standards.
    
    **Important**:
    - All fares shown are AVERAGE/ESTIMATED based on distance and bus type
    - Actual prices vary by operator, time of day, and availability
    - This is a metasearch - click through to booking partners for live availability
    
    **Returns**:
    - List of bus options with average fares by type, OR
    - A fallback redirect card if route not in database
    - Never returns empty results
    
    **Booking Partners** (in priority order):
    1. redBus (Market leader)
    2. AbhiBus
    3. Paytm Bus
    """
    try:
        # Validate date
        try:
            dep_date = date.fromisoformat(departure_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD."
            )
        
        # Date must be today or future
        today = date.today()
        if dep_date < today:
            raise HTTPException(
                status_code=400,
                detail="Departure date cannot be in the past."
            )
        
        # Date shouldn't be too far in future (60 days for buses)
        max_date = today + timedelta(days=60)
        if dep_date > max_date:
            raise HTTPException(
                status_code=400,
                detail="Bus bookings typically open 60 days in advance. Please select an earlier date."
            )
        
        # Validate origin != destination
        if origin.lower().strip() == destination.lower().strip():
            raise HTTPException(
                status_code=400,
                detail="Origin and destination cannot be the same."
            )
        
        # Build request
        request = BusSearchRequest(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            bus_type=bus_type,
            ac_only=ac_only,
            sleeper_only=sleeper_only,
            passengers=passengers,
        )
        
        # Execute search
        response = await search_buses(request)
        
        logger.info(
            f"🚌 Bus search completed: {origin} → {destination} | "
            f"{len(response.offers)} results | fallback={response.is_fallback}"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Bus search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Bus search temporarily unavailable. Please try again."
        )


@router.get("/buses/routes")
async def get_available_routes():
    """
    Get list of popular bus routes available in our database.
    
    Useful for suggesting routes or showing coverage.
    """
    from app.data.bus_routes import BUS_ROUTES
    
    routes = []
    for route_key, route in BUS_ROUTES.items():
        routes.append({
            "route_key": route_key,
            "origin_city": route.origin_city,
            "destination_city": route.destination_city,
            "distance_km": route.distance_km,
            "avg_duration_hours": round(route.avg_duration_minutes / 60, 1),
            "operators_count": len(route.operators),
            "bus_types": list(route.fares.keys()),
        })
    
    return {
        "routes": routes,
        "total": len(routes),
        "message": "These are popular routes with pre-loaded data. Other routes will show redirect options.",
    }

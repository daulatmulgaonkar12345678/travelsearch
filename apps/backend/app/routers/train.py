"""Train Search API Router

Endpoints for searching train routes in India.
Uses static data from Indian Railways public timetable.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import date, timedelta
import logging

from app.models.transport import TrainSearchRequest, TrainSearchResponse
from app.services.train_search import search_trains

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search/trains", response_model=TrainSearchResponse)
async def search_trains_endpoint(
    origin: str = Query(..., description="Origin station code or city name"),
    destination: str = Query(..., description="Destination station code or city name"),
    departure_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    
    # Optional filters
    train_class: Optional[str] = Query(None, description="Filter by class (SL, 3A, 2A, 1A, CC)"),
    train_type: Optional[str] = Query(None, description="Filter by train type (Rajdhani, Shatabdi, etc.)"),
    passengers: int = Query(1, ge=1, le=6, description="Number of passengers"),
):
    """
    Search for trains between two stations.
    
    **Data Source**: Static Indian Railways public timetable data.
    
    **Important**:
    - All fares shown are AVERAGE/ESTIMATED based on distance
    - Actual prices depend on class, quota, and availability
    - This is a metasearch - click through to booking partners for live availability
    
    **Returns**:
    - List of trains with schedules and average fares, OR
    - A fallback redirect card if route not in database
    - Never returns empty results
    
    **Booking Partners** (in priority order):
    1. IRCTC (Official)
    2. ixigo Trains
    3. Paytm Trains
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
        
        # Date shouldn't be too far in future (120 days for trains)
        max_date = today + timedelta(days=120)
        if dep_date > max_date:
            raise HTTPException(
                status_code=400,
                detail="Train bookings open 120 days in advance. Please select an earlier date."
            )
        
        # Validate origin != destination
        if origin.upper() == destination.upper():
            raise HTTPException(
                status_code=400,
                detail="Origin and destination cannot be the same."
            )
        
        # Build request
        request = TrainSearchRequest(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            train_class=train_class,
            train_type=train_type,
            passengers=passengers,
        )
        
        # Execute search
        response = await search_trains(request)
        
        logger.info(
            f"🚆 Train search completed: {origin} → {destination} | "
            f"{len(response.offers)} results | fallback={response.is_fallback}"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Train search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Train search temporarily unavailable. Please try again."
        )


@router.get("/trains/routes")
async def get_available_routes():
    """
    Get list of popular train routes available in our database.
    
    Useful for suggesting routes or showing coverage.
    """
    from app.data.train_routes import TRAIN_ROUTES
    from app.services.train_search import get_city_name
    
    routes = []
    for route_key in TRAIN_ROUTES.keys():
        parts = route_key.split("-")
        if len(parts) == 2:
            origin, dest = parts
            routes.append({
                "route_key": route_key,
                "origin_code": origin,
                "origin_city": get_city_name(origin),
                "destination_code": dest,
                "destination_city": get_city_name(dest),
                "trains_count": len(TRAIN_ROUTES[route_key]),
            })
    
    return {
        "routes": routes,
        "total": len(routes),
        "message": "These are popular routes with pre-loaded schedules. Other routes will show redirect options.",
    }

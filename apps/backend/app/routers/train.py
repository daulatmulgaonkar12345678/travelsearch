"""Train Search API Router - STATION-FIRST ARCHITECTURE

🔴 CONTRACT (NON-NEGOTIABLE):
- Only accepts station codes (CSMT, PUNE) or _ALL tokens (MUMBAI_ALL)
- Rejects raw city names with explicit error
- Frontend MUST enforce dropdown selection
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any
from datetime import date, timedelta
import logging

from app.models.transport import TrainSearchRequest, TrainSearchResponse
from app.services.train_search import search_trains, TrainSearchError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search/trains")
async def search_trains_endpoint(
    origin: str = Query(..., description="Origin station code, city name, or alias (e.g., 'Pune', 'Bombay', 'CSMT')"),
    destination: str = Query(..., description="Destination station code, city name, or alias"),
    departure_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    
    # Optional filters
    train_class: Optional[str] = Query(None, description="Filter by class (SL, 3A, 2A, 1A, CC)"),
    train_type: Optional[str] = Query(None, description="Filter by train type (Rajdhani, Shatabdi, etc.)"),
    passengers: int = Query(1, ge=1, le=6, description="Number of passengers"),
) -> Dict[str, Any]:
    """
    Search for trains between two locations.
    
    **DEFENSIVE BACKEND**:
    - Accepts ANY input: city names, aliases (Bombay, Calcutta), or station codes
    - Internally resolves to station codes and expands cities to all their stations
    - Returns city-level abstraction, not raw station-pair explosions
    - Invalid inputs return structured error with suggestions (never 500)
    
    **Data Source**: Static Indian Railways public timetable data.
    
    **Important**:
    - All fares shown are AVERAGE/ESTIMATED based on distance
    - Actual prices depend on class, quota, and availability
    - This is a metasearch - click through to booking partners for live availability
    
    **Returns**:
    - List of trains with schedules and average fares, OR
    - A fallback redirect card if route not in database
    - Structured error with suggestions for invalid inputs
    - Never returns empty results or 500 for bad user input
    
    **Booking Partners** (in priority order):
    1. IRCTC (Official)
    2. ixigo Trains
    3. Paytm Trains
    """
    try:
        # ============================================================
        # VALIDATE DATE (Basic validation before expensive operations)
        # ============================================================
        try:
            dep_date = date.fromisoformat(departure_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "error_type": "INVALID_DATE_FORMAT",
                    "message": "Invalid date format. Use YYYY-MM-DD.",
                    "invalid_input": departure_date,
                    "suggestions": []
                }
            )
        
        # Date must be today or future
        today = date.today()
        if dep_date < today:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "error_type": "DATE_IN_PAST",
                    "message": "Departure date cannot be in the past.",
                    "invalid_input": departure_date,
                    "suggestions": [{"display_name": today.isoformat(), "subtitle": "Today"}]
                }
            )
        
        # Date shouldn't be too far in future (120 days for trains)
        max_date = today + timedelta(days=120)
        if dep_date > max_date:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "error_type": "DATE_TOO_FAR",
                    "message": "Train bookings open 120 days in advance. Please select an earlier date.",
                    "invalid_input": departure_date,
                    "suggestions": [{"display_name": max_date.isoformat(), "subtitle": "Maximum date"}]
                }
            )
        
        # ============================================================
        # VALIDATE ORIGIN != DESTINATION
        # ============================================================
        if origin.lower().strip() == destination.lower().strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "error_type": "SAME_ORIGIN_DESTINATION",
                    "message": "Origin and destination cannot be the same.",
                    "invalid_input": f"{origin} → {destination}",
                    "suggestions": []
                }
            )
        
        # ============================================================
        # BUILD REQUEST AND EXECUTE SEARCH
        # ============================================================
        request = TrainSearchRequest(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            train_class=train_class,
            train_type=train_type,
            passengers=passengers,
        )
        
        # Execute search - this handles all input resolution internally
        response = await search_trains(request)
        
        logger.info(
            f"🚆 Train search completed: {response.origin_city} → {response.destination_city} | "
            f"{len(response.offers)} results | fallback={response.is_fallback}"
        )
        
        # ============================================================
        # BUILD SUCCESS RESPONSE (City-level abstraction)
        # ============================================================
        return {
            "status": "success",
            "search_id": response.search_id,
            "timestamp": response.timestamp.isoformat(),
            
            # City-level route info (NOT station-level)
            "route": {
                "origin_city": response.origin_city,
                "destination_city": response.destination_city,
                "distance_km": response.distance_km,
            },
            
            "offers": [
                {
                    "offer_id": o.offer_id,
                    "mode": o.mode.value,
                    
                    # Train info
                    "train_number": o.train_number,
                    "train_name": o.train_name,
                    "train_type": o.train_type,
                    
                    # Route (station-level for this specific train)
                    "from_station": o.from_station,
                    "from_station_name": o.from_station_name,
                    "from_city": o.from_city,
                    "to_station": o.to_station,
                    "to_station_name": o.to_station_name,
                    "to_city": o.to_city,
                    
                    # Schedule
                    "departure_time": o.departure_time.isoformat(),
                    "arrival_time": o.arrival_time.isoformat(),
                    "duration_minutes": o.duration_minutes,
                    "days_of_operation": o.days_of_operation,
                    "frequency": o.frequency,
                    
                    # Stops
                    "stops_count": o.stops_count,
                    "intermediate_stops": o.intermediate_stops,
                    
                    # Pricing (ALWAYS AVERAGE)
                    "avg_price": o.avg_price,
                    "currency": o.currency,
                    "price_label": o.price_label,
                    "price_disclaimer": o.price_disclaimer,
                    "available_classes": o.available_classes,
                    
                    # Amenities
                    "has_pantry": o.has_pantry,
                    
                    # Distance
                    "distance_km": o.distance_km,
                    
                    # Booking
                    "booking_partners": o.booking_partners,
                    "is_fallback": o.is_fallback,
                }
                for o in response.offers
            ],
            
            "total_results": len(response.offers),
            "is_fallback": response.is_fallback,
            "fallback_message": response.fallback_message,
            
            # Important disclaimer
            "disclaimer": "Prices shown are average fares for reference only. Actual prices depend on availability and may vary. Please book on official sites for accurate pricing.",
        }
    
    # ============================================================
    # HANDLE VALIDATION ERRORS (Graceful failure with suggestions)
    # ============================================================
    except TrainSearchError as e:
        logger.warning(f"Train search validation error: {e.error_type} - {e.message}")
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "error_type": e.error_type,
                "message": e.message,
                "invalid_input": e.invalid_input,
                "suggestions": e.suggestions,
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Train search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error_type": "INTERNAL_ERROR",
                "message": "Train search temporarily unavailable. Please try again.",
                "invalid_input": None,
                "suggestions": []
            }
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

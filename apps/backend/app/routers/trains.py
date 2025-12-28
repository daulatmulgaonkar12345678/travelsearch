"""Train Search API Router

Provides train search endpoints with static/official data only.
No live pricing, no seat availability - just average fares and schedules.

ARCHITECTURE PRINCIPLE:
- Frontend is dumb, backend is smart
- All input resolution (city names, aliases, station codes) happens here
- Invalid inputs return structured errors with suggestions, not 500s
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
import uuid
import logging

from app.models.transport import TrainSearchRequest, TrainSearchResponse
from app.services.train_search import search_trains, TrainSearchError, validate_and_resolve_input
from app.data.stations import get_all_railway_stations, get_railway_station, RAILWAY_STATIONS

logger = logging.getLogger(__name__)
router = APIRouter(tags=["trains"])


@router.get("/search/trains")
async def search_trains_endpoint(
    origin: str = Query(..., description="Origin station code, city name, or alias (e.g., 'Pune', 'Bombay', 'CSMT')"),
    destination: str = Query(..., description="Destination station code, city name, or alias"),
    departure_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    train_class: Optional[str] = Query(None, description="Preferred class: SL, 3A, 2A, 1A, CC"),
    train_type: Optional[str] = Query(None, description="Train type: Rajdhani, Shatabdi, Express"),
    passengers: int = Query(1, ge=1, le=6, description="Number of passengers"),
) -> Dict[str, Any]:
    """
    Search for trains between two locations.
    
    DEFENSIVE BACKEND:
    - Accepts ANY input: city names, aliases (Bombay, Calcutta), or station codes
    - Internally resolves to station codes and expands cities to all their stations
    - Returns city-level abstraction, not raw station-pair explosions
    - Invalid inputs return structured error with suggestions (never 500)
    
    IMPORTANT:
    - All prices shown are AVERAGE/ESTIMATED fares
    - No live seat availability
    - No live pricing
    - Users must book on official sites (IRCTC, etc.)
    
    Returns:
        Train offers with average fares and booking partner links
        OR structured error with suggestions for invalid inputs
    """
    
    try:
        # ============================================================
        # VALIDATE DATE (Basic validation before expensive operations)
        # ============================================================
        try:
            dep_date = datetime.strptime(departure_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail={
                    "error_type": "INVALID_DATE_FORMAT",
                    "message": "Invalid date format. Use YYYY-MM-DD",
                    "invalid_input": departure_date,
                    "suggestions": []
                }
            )
        
        today = date.today()
        if dep_date < today:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_type": "DATE_IN_PAST",
                    "message": "Departure date cannot be in the past",
                    "invalid_input": departure_date,
                    "suggestions": [{"display_name": today.isoformat(), "subtitle": "Today"}]
                }
            )
        
        if dep_date > today + timedelta(days=120):
            max_date = (today + timedelta(days=120)).isoformat()
            raise HTTPException(
                status_code=400,
                detail={
                    "error_type": "DATE_TOO_FAR",
                    "message": "Can only search up to 120 days in advance",
                    "invalid_input": departure_date,
                    "suggestions": [{"display_name": max_date, "subtitle": "Maximum date"}]
                }
            )
        
        # ============================================================
        # VALIDATE ORIGIN != DESTINATION
        # ============================================================
        if origin.lower().strip() == destination.lower().strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "error_type": "SAME_ORIGIN_DESTINATION",
                    "message": "Origin and destination must be different",
                    "invalid_input": f"{origin} → {destination}",
                    "suggestions": []
                }
            )
        
        # ============================================================
        # CREATE SEARCH REQUEST AND EXECUTE
        # ============================================================
        request = TrainSearchRequest(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            train_class=train_class,
            train_type=train_type,
            passengers=passengers,
        )
        
        # This will raise TrainSearchError for invalid inputs
        response = await search_trains(request)
        
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
        logger.error(f"Unexpected train search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail={
                "status": "error",
                "error_type": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again.",
                "invalid_input": None,
                "suggestions": []
            }
        )


@router.get("/stations/railway")
async def get_railway_stations_endpoint(
    query: Optional[str] = Query(None, description="Search query for station name or code"),
) -> Dict[str, Any]:
    """
    Get list of railway stations for autocomplete.
    """
    
    stations = get_all_railway_stations()
    
    if query:
        query_lower = query.lower()
        stations = [
            s for s in stations
            if query_lower in s["name"].lower() 
            or query_lower in s["city"].lower()
            or query_lower in s["code"].lower()
        ]
    
    return {
        "stations": stations[:20],  # Limit to 20 results
        "total": len(stations),
    }


@router.get("/stations/railway/{code}")
async def get_station_details(
    code: str,
) -> Dict[str, Any]:
    """
    Get details for a specific railway station.
    """
    
    station = RAILWAY_STATIONS.get(code.upper())
    
    if not station:
        raise HTTPException(404, f"Station not found: {code}")
    
    return {
        "code": station.code,
        "name": station.name,
        "city": station.city,
        "state": station.state,
        "zone": station.zone,
        "is_major": station.is_major,
    }

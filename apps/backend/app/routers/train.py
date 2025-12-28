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
    origin: str = Query(..., description="Station code (CSMT, PUNE) or ALL token (MUMBAI_ALL)"),
    destination: str = Query(..., description="Station code or ALL token"),
    departure_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    
    # Optional filters
    train_class: Optional[str] = Query(None, description="Filter by class (SL, 3A, 2A, 1A, CC)"),
    train_type: Optional[str] = Query(None, description="Filter by train type (Rajdhani, Shatabdi, etc.)"),
    passengers: int = Query(1, ge=1, le=6, description="Number of passengers"),
) -> Dict[str, Any]:
    """
    Search for trains between two stations.
    
    🔴 **STATION-FIRST CONTRACT** (STRICT):
    
    **Valid inputs:**
    - Station codes: `CSMT`, `PUNE`, `NDLS`
    - ALL tokens: `MUMBAI_ALL`, `PUNE_ALL`, `DELHI_ALL`
    
    **Invalid inputs (will be REJECTED):**
    - Raw city names: `Mumbai`, `Pune`, `Delhi`
    - Free text not matching station codes
    
    **Examples:**
    - ✅ `origin=CSMT&destination=PUNE`
    - ✅ `origin=MUMBAI_ALL&destination=PUNE`
    - ❌ `origin=Mumbai&destination=Pune` (REJECTED)
    
    **Frontend must:**
    - Show dropdown with stations and "City (All Stations)" options
    - Never allow free text submission
    - Disable search until valid selection made
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
            }
        )


@router.get("/trains/autocomplete")
async def train_autocomplete_station_first(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=20, description="Max results"),
):
    """
    Station-first autocomplete for train search.
    
    🔴 **STATION-FIRST DROPDOWN FORMAT**:
    
    When user types "Mumbai", returns:
    ```
    [
      {"value": "MUMBAI_ALL", "label": "Mumbai (All Stations) ⭐", "type": "city_all", "stations": 9},
      {"value": "CSMT", "label": "CSMT – Chhatrapati Shivaji Maharaj Terminus", "type": "station"},
      {"value": "BCT", "label": "BCT – Mumbai Central", "type": "station"},
      {"value": "LTT", "label": "LTT – Lokmanya Tilak Terminus", "type": "station"},
      ...
    ]
    ```
    
    When user types "CSMT", returns:
    ```
    [
      {"value": "CSMT", "label": "CSMT – Chhatrapati Shivaji Maharaj Terminus", "type": "station"}
    ]
    ```
    
    **Frontend must:**
    - Only allow selection from this dropdown
    - Use the `value` field for API submission
    - Never allow free text submission
    """
    from app.services.rail_connectivity import (
        _load_data, _cities, _stations, _station_to_city
    )
    
    _load_data()
    
    query_lower = q.lower().strip()
    query_upper = q.upper().strip()
    results = []
    seen_values = set()
    
    # ============================================================
    # 1. Check for exact station code match first
    # ============================================================
    if query_upper in _stations:
        station = _stations[query_upper]
        results.append({
            "value": query_upper,
            "label": f"{query_upper} – {station.station_name}",
            "type": "station",
            "city": station.city,
            "is_major": station.is_major,
        })
        seen_values.add(query_upper)
    
    # ============================================================
    # 2. Check for city match -> show CITY_ALL first, then stations
    # ============================================================
    matched_city = None
    for city_id, city in _cities.items():
        city_name_lower = city.city_name.lower()
        
        if query_lower == city_name_lower or query_lower == city_id:
            matched_city = city
            break
        elif city_name_lower.startswith(query_lower):
            if not matched_city or city.population_rank < matched_city.population_rank:
                matched_city = city
    
    if matched_city:
        city_all_value = f"{matched_city.city_id.upper()}_ALL"
        
        if city_all_value not in seen_values:
            # Add "City (All Stations)" option FIRST with star
            results.insert(0, {
                "value": city_all_value,
                "label": f"{matched_city.city_name} (All Stations) ⭐",
                "type": "city_all",
                "city": matched_city.city_name,
                "station_count": len(matched_city.station_codes),
                "is_recommended": True,
            })
            seen_values.add(city_all_value)
        
        # Add individual stations for this city
        for station_code in matched_city.station_codes:
            if station_code in _stations and station_code not in seen_values:
                station = _stations[station_code]
                results.append({
                    "value": station_code,
                    "label": f"{station_code} – {station.station_name}",
                    "type": "station",
                    "city": matched_city.city_name,
                    "is_major": station.is_major,
                })
                seen_values.add(station_code)
    
    # ============================================================
    # 3. Search stations by name/code prefix
    # ============================================================
    for station_code, station in _stations.items():
        if station_code in seen_values:
            continue
        
        station_name_lower = station.station_name.lower()
        code_lower = station_code.lower()
        
        match = False
        if code_lower.startswith(query_lower):
            match = True
        elif station_name_lower.startswith(query_lower):
            match = True
        elif query_lower in station_name_lower:
            match = True
        
        if match:
            results.append({
                "value": station_code,
                "label": f"{station_code} – {station.station_name}",
                "type": "station",
                "city": station.city,
                "is_major": station.is_major,
            })
            seen_values.add(station_code)
        
        if len(results) >= limit:
            break
    
    # ============================================================
    # 4. Search other cities by name
    # ============================================================
    if len(results) < limit:
        for city_id, city in _cities.items():
            city_all_value = f"{city_id.upper()}_ALL"
            if city_all_value in seen_values:
                continue
            
            city_name_lower = city.city_name.lower()
            
            if query_lower in city_name_lower:
                results.append({
                    "value": city_all_value,
                    "label": f"{city.city_name} (All Stations)",
                    "type": "city_all",
                    "city": city.city_name,
                    "station_count": len(city.station_codes),
                })
                seen_values.add(city_all_value)
            
            if len(results) >= limit:
                break
    
    return {
        "results": results[:limit],
        "query": q,
        "total": len(results[:limit]),
    }


@router.get("/trains/routes")
async def get_available_routes():
    """
    Get list of popular train routes available in our database.
    
    Useful for suggesting routes or showing coverage.
    """
    from app.data.train_routes import TRAIN_ROUTES
    from app.services.train_search import get_city_name_for_station
    
    routes = []
    for route_key in TRAIN_ROUTES.keys():
        parts = route_key.split("-")
        if len(parts) == 2:
            origin, dest = parts
            routes.append({
                "route_key": route_key,
                "origin_code": origin,
                "origin_city": get_city_name_for_station(origin),
                "destination_code": dest,
                "destination_city": get_city_name_for_station(dest),
                "trains_count": len(TRAIN_ROUTES[route_key]),
            })
    
    return {
        "routes": routes,
        "total": len(routes),
        "message": "These are popular routes with pre-loaded schedules. Other routes will show redirect options.",
    }

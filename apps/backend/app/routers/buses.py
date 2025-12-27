"""Bus Search API Router

Provides bus search endpoints with static/official data only.
No live pricing, no seat availability - just average fares and route info.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
import uuid
import logging

from app.models.transport import BusSearchRequest, BusSearchResponse
from app.services.bus_search import search_buses
from app.data.stations import get_all_bus_stops, get_bus_stop, BUS_STOPS

logger = logging.getLogger(__name__)
router = APIRouter(tags=["buses"])


@router.get("/search/buses")
async def search_buses_endpoint(
    origin: str = Query(..., description="Origin city name"),
    destination: str = Query(..., description="Destination city name"),
    departure_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    bus_type: Optional[str] = Query(None, description="Bus type: ordinary, ac_seater, ac_sleeper, volvo"),
    ac_only: bool = Query(False, description="Show only AC buses"),
    sleeper_only: bool = Query(False, description="Show only sleeper buses"),
    passengers: int = Query(1, ge=1, le=6, description="Number of passengers"),
) -> Dict[str, Any]:
    """
    Search for buses between two cities.
    
    IMPORTANT:
    - All prices shown are AVERAGE/ESTIMATED fares
    - No live seat availability
    - No live pricing
    - Users must book on official sites (redBus, AbhiBus, etc.)
    
    Returns:
        Bus offers with average fares and booking partner links
    """
    
    try:
        # Validate date
        try:
            dep_date = datetime.strptime(departure_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")
        
        today = date.today()
        if dep_date < today:
            raise HTTPException(400, "Departure date cannot be in the past")
        
        if dep_date > today + timedelta(days=90):
            raise HTTPException(400, "Can only search up to 90 days in advance")
        
        # Validate origin != destination
        if origin.lower() == destination.lower():
            raise HTTPException(400, "Origin and destination must be different")
        
        # Create search request
        request = BusSearchRequest(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            bus_type=bus_type,
            ac_only=ac_only,
            sleeper_only=sleeper_only,
            passengers=passengers,
        )
        
        # Perform search
        response = await search_buses(request)
        
        # Convert to dict for JSON response
        return {
            "status": "success",
            "search_id": response.search_id,
            "timestamp": response.timestamp.isoformat(),
            
            "route": {
                "origin_city": response.origin_city,
                "destination_city": response.destination_city,
                "distance_km": response.distance_km,
            },
            
            "offers": [
                {
                    "offer_id": o.offer_id,
                    "mode": o.mode.value,
                    
                    # Operator info
                    "operator_name": o.operator_name,
                    "operator_type": o.operator_type,
                    
                    # Bus type
                    "bus_type": o.bus_type.value,
                    "bus_type_label": o.bus_type_label,
                    
                    # Route
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
                    "frequency": o.frequency,
                    "departure_window": o.departure_window,
                    
                    # Amenities
                    "is_ac": o.is_ac,
                    "is_sleeper": o.is_sleeper,
                    "has_charging_point": o.has_charging_point,
                    "has_wifi": o.has_wifi,
                    
                    # Pricing (ALWAYS AVERAGE)
                    "avg_price": o.avg_price,
                    "currency": o.currency,
                    "price_label": o.price_label,
                    "price_disclaimer": o.price_disclaimer,
                    
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
            "disclaimer": "Prices shown are average fares for reference only. Actual prices depend on operator and availability. Please book on official sites for accurate pricing.",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bus search error: {e}", exc_info=True)
        raise HTTPException(500, f"Bus search failed: {str(e)}")


@router.get("/stations/bus")
async def get_bus_stops_endpoint(
    query: Optional[str] = Query(None, description="Search query for city or stop name"),
) -> Dict[str, Any]:
    """
    Get list of bus stops/terminals for autocomplete.
    """
    
    stops = get_all_bus_stops()
    
    if query:
        query_lower = query.lower()
        stops = [
            s for s in stops
            if query_lower in s["name"].lower() 
            or query_lower in s["city"].lower()
        ]
    
    return {
        "stops": stops[:20],  # Limit to 20 results
        "total": len(stops),
    }


@router.get("/cities/bus")
async def get_bus_cities() -> Dict[str, Any]:
    """
    Get list of cities with bus service for autocomplete.
    Returns unique cities from bus stops.
    """
    
    cities = set()
    for stop in BUS_STOPS.values():
        cities.add(stop.city)
    
    # Add common cities that might not have stops defined
    common_cities = [
        "Delhi", "Mumbai", "Bangalore", "Chennai", "Hyderabad",
        "Pune", "Goa", "Jaipur", "Ahmedabad", "Chandigarh",
        "Agra", "Mysore", "Coimbatore", "Lucknow", "Varanasi",
    ]
    for city in common_cities:
        cities.add(city)
    
    return {
        "cities": sorted(list(cities)),
        "total": len(cities),
    }

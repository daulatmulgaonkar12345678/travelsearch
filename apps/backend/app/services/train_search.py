"""Train Search Service

Provides train search functionality using static official data.
No scraping, no live availability - only average fares from government sources.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.models.transport import TrainOffer, TrainSearchRequest, TrainSearchResponse, TransportMode
from app.data.stations import get_railway_station, CITY_TO_RAIL_STATION, RAILWAY_STATIONS
from app.data.train_routes import (
    get_trains_for_route, 
    get_distance, 
    calculate_average_fare,
    TrainSchedule
)

logger = logging.getLogger(__name__)

# Booking partner URLs for trains
TRAIN_BOOKING_PARTNERS = [
    {
        "name": "IRCTC",
        "url": "https://www.irctc.co.in/nget/train-search",
        "priority": 1,
        "description": "Official Indian Railways booking"
    },
    {
        "name": "Paytm Trains",
        "url": "https://paytm.com/trains",
        "priority": 2,
        "description": "Fast booking with Paytm"
    },
    {
        "name": "ixigo Trains",
        "url": "https://www.ixigo.com/trains",
        "priority": 3,
        "description": "Compare & book trains"
    },
    {
        "name": "redBus Trains",
        "url": "https://www.redbus.in/trains",
        "priority": 4,
        "description": "Book train tickets online"
    },
]


def resolve_station_code(query: str) -> Optional[str]:
    """Resolve city name or station code to a station code"""
    query_lower = query.lower().strip()
    query_upper = query.upper().strip()
    
    # Direct station code match
    if query_upper in RAILWAY_STATIONS:
        return query_upper
    
    # City name match
    if query_lower in CITY_TO_RAIL_STATION:
        return CITY_TO_RAIL_STATION[query_lower]
    
    # Fuzzy match on station/city names
    station = get_railway_station(query)
    if station:
        return station.code
    
    return None


def convert_schedule_to_offer(
    schedule: TrainSchedule,
    departure_date: str,
    origin_station: str,
    destination_station: str
) -> TrainOffer:
    """Convert a TrainSchedule to a TrainOffer"""
    
    # Parse departure date and time
    dep_hour, dep_min = map(int, schedule.departure_time.split(':'))
    arr_hour, arr_min = map(int, schedule.arrival_time.split(':'))
    
    dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
    dep_datetime = dep_date.replace(hour=dep_hour, minute=dep_min)
    
    # Calculate arrival datetime (may be next day)
    arr_datetime = dep_date.replace(hour=arr_hour, minute=arr_min)
    if arr_datetime <= dep_datetime:
        arr_datetime += timedelta(days=1)
    
    # Get station info
    origin_info = RAILWAY_STATIONS.get(origin_station, None)
    dest_info = RAILWAY_STATIONS.get(destination_station, None)
    
    # Get the lowest fare from available classes
    avg_price = min(schedule.fares.values()) if schedule.fares else 500
    
    # Build available classes list
    available_classes = [
        {"class": cls, "avg_fare": fare}
        for cls, fare in schedule.fares.items()
    ]
    
    return TrainOffer(
        offer_id=f"train_{schedule.train_number}_{departure_date}",
        mode=TransportMode.TRAIN,
        provider="indian_railways_static",
        
        # Route info
        from_station=origin_station,
        from_city=origin_info.city if origin_info else origin_station,
        from_station_name=origin_info.name if origin_info else origin_station,
        to_station=destination_station,
        to_city=dest_info.city if dest_info else destination_station,
        to_station_name=dest_info.name if dest_info else destination_station,
        
        # Timing
        departure_time=dep_datetime,
        arrival_time=arr_datetime,
        duration_minutes=schedule.duration_minutes,
        
        # Pricing
        avg_price=avg_price,
        currency="INR",
        price_label="Average Fare",
        price_disclaimer="Average fare shown for reference. Actual price may vary based on class and availability.",
        
        # Distance
        distance_km=schedule.distance_km,
        
        # Train specific
        train_number=schedule.train_number,
        train_name=schedule.train_name,
        train_type=schedule.train_type,
        days_of_operation=schedule.days_of_operation,
        frequency="Daily" if "Daily" in schedule.days_of_operation else f"{len(schedule.days_of_operation)} days/week",
        stops_count=schedule.stops_count,
        intermediate_stops=schedule.intermediate_stops,
        available_classes=available_classes,
        has_pantry=schedule.has_pantry,
        
        # Booking partners
        booking_partners=TRAIN_BOOKING_PARTNERS,
        
        # Not a fallback - we have real schedule data
        is_fallback=False,
    )


def create_fallback_offer(
    origin: str,
    destination: str,
    departure_date: str,
    distance_km: Optional[int] = None
) -> TrainOffer:
    """Create a fallback offer when no route data is available"""
    
    origin_info = RAILWAY_STATIONS.get(origin, None)
    dest_info = RAILWAY_STATIONS.get(destination, None)
    
    # Estimate distance if not provided (rough calculation)
    if not distance_km:
        distance_km = get_distance(origin, destination) or 500  # Default 500km
    
    # Calculate average fare based on distance
    avg_price = calculate_average_fare(distance_km, "SL")
    
    dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
    dep_datetime = dep_date.replace(hour=8, minute=0)  # Placeholder time
    arr_datetime = dep_datetime + timedelta(hours=int(distance_km / 60))  # ~60 km/h avg
    
    return TrainOffer(
        offer_id=f"train_fallback_{origin}_{destination}_{departure_date}",
        mode=TransportMode.TRAIN,
        provider="fallback",
        
        # Route info
        from_station=origin,
        from_city=origin_info.city if origin_info else origin,
        from_station_name=origin_info.name if origin_info else origin,
        to_station=destination,
        to_city=dest_info.city if dest_info else destination,
        to_station_name=dest_info.name if dest_info else destination,
        
        # Timing (placeholder)
        departure_time=dep_datetime,
        arrival_time=arr_datetime,
        duration_minutes=int(distance_km * 1.2),  # Rough estimate
        
        # Pricing
        avg_price=avg_price,
        currency="INR",
        price_label="Estimated Fare",
        price_disclaimer="Estimated fare based on distance. Please check official sites for accurate prices and availability.",
        
        # Distance
        distance_km=distance_km,
        
        # Train specific (unknown)
        train_number="",
        train_name="View train options",
        train_type="Various",
        days_of_operation=[],
        available_classes=[
            {"class": "SL", "avg_fare": calculate_average_fare(distance_km, "SL")},
            {"class": "3A", "avg_fare": calculate_average_fare(distance_km, "3A")},
            {"class": "2A", "avg_fare": calculate_average_fare(distance_km, "2A")},
        ],
        
        # Booking partners
        booking_partners=TRAIN_BOOKING_PARTNERS,
        
        # This is a fallback
        is_fallback=True,
    )


async def search_trains(request: TrainSearchRequest) -> TrainSearchResponse:
    """Search for trains between two stations"""
    
    logger.info(f"🚆 Train search: {request.origin} → {request.destination} on {request.departure_date}")
    
    # Resolve station codes
    origin_code = resolve_station_code(request.origin)
    destination_code = resolve_station_code(request.destination)
    
    if not origin_code:
        logger.warning(f"Could not resolve origin station: {request.origin}")
        origin_code = request.origin.upper()
    
    if not destination_code:
        logger.warning(f"Could not resolve destination station: {request.destination}")
        destination_code = request.destination.upper()
    
    # Get station info for response
    origin_info = RAILWAY_STATIONS.get(origin_code)
    dest_info = RAILWAY_STATIONS.get(destination_code)
    
    origin_city = origin_info.city if origin_info else request.origin
    dest_city = dest_info.city if dest_info else request.destination
    
    # Try to find trains for this route
    schedules = get_trains_for_route(origin_code, destination_code)
    
    offers: List[TrainOffer] = []
    is_fallback = False
    fallback_message = None
    
    if schedules:
        # We have schedule data - convert to offers
        for schedule in schedules:
            # Check if train runs on the selected day
            dep_date = datetime.strptime(request.departure_date, "%Y-%m-%d")
            day_name = dep_date.strftime("%a")  # "Mon", "Tue", etc.
            
            if "Daily" in schedule.days_of_operation or day_name in schedule.days_of_operation:
                offer = convert_schedule_to_offer(
                    schedule,
                    request.departure_date,
                    origin_code,
                    destination_code
                )
                offers.append(offer)
        
        if not offers:
            # No trains on this day
            fallback_message = f"No trains available on {day_name}. Check alternate days or booking partners for other options."
            is_fallback = True
            offers.append(create_fallback_offer(
                origin_code,
                destination_code,
                request.departure_date,
                schedules[0].distance_km if schedules else None
            ))
    else:
        # No schedule data - create fallback
        logger.info(f"No schedule data for {origin_code} → {destination_code}, showing fallback")
        is_fallback = True
        fallback_message = "Detailed schedule not available for this route. Please check official booking sites."
        offers.append(create_fallback_offer(
            origin_code,
            destination_code,
            request.departure_date
        ))
    
    # Sort by departure time
    offers.sort(key=lambda x: x.departure_time)
    
    # Get distance
    distance_km = get_distance(origin_code, destination_code)
    
    return TrainSearchResponse(
        offers=offers,
        search_id=str(uuid.uuid4()),
        cached=False,
        timestamp=datetime.utcnow(),
        origin_city=origin_city,
        destination_city=dest_city,
        distance_km=distance_km,
        is_fallback=is_fallback,
        fallback_message=fallback_message,
    )

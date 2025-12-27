"""Train Search Service

Handles train search logic using static route data.
Always returns results OR a fallback redirect card - never empty.

Data Source: Static Indian Railways timetable data
Fare Strategy: Distance-based average fares (clearly labeled)
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.models.transport import (
    TrainOffer,
    TrainSearchRequest,
    TrainSearchResponse,
    TransportMode,
)
from app.data.train_routes import (
    get_trains_for_route,
    get_distance,
    calculate_average_fare,
    TrainSchedule,
    TRAIN_ROUTES,
)

logger = logging.getLogger(__name__)

# ============================================================
# BOOKING PARTNERS - Priority Order (User Approved)
# ============================================================
TRAIN_BOOKING_PARTNERS = [
    {
        "name": "IRCTC",
        "priority": 1,
        "url_template": "https://www.irctc.co.in/nget/train-search",
        "description": "Official Indian Railways booking",
        "is_official": True,
    },
    {
        "name": "ixigo Trains",
        "priority": 2,
        "url_template": "https://www.ixigo.com/search/result/train/{origin}/{destination}/{date}",
        "description": "Best train UX & PNR tracking",
        "is_official": False,
    },
    {
        "name": "Paytm Trains",
        "priority": 3,
        "url_template": "https://paytm.com/trains/{origin}-to-{destination}-train-tickets",
        "description": "Cashback & easy booking",
        "is_official": False,
    },
]

# ============================================================
# STATION CODE MAPPINGS
# ============================================================
CITY_TO_STATION = {
    # Major cities
    "delhi": "NDLS",
    "new delhi": "NDLS",
    "mumbai": "CSMT",
    "bombay": "CSMT",
    "bangalore": "SBC",
    "bengaluru": "SBC",
    "chennai": "MAS",
    "madras": "MAS",
    "kolkata": "HWH",
    "calcutta": "HWH",
    "hyderabad": "SC",
    "secunderabad": "SC",
    "pune": "PUNE",
    "jaipur": "JP",
    "ahmedabad": "ADI",
    "goa": "MAO",
    "panaji": "MAO",
    "lucknow": "LKO",
    "varanasi": "BSB",
    "patna": "PNBE",
    "bhopal": "BPL",
    "agra": "AGC",
    "chandigarh": "CDG",
    "kochi": "ERS",
    "cochin": "ERS",
    "trivandrum": "TVC",
    "thiruvananthapuram": "TVC",
    "visakhapatnam": "VSKP",
    "vizag": "VSKP",
}

# Station code to city name mapping (for display)
STATION_TO_CITY = {
    "NDLS": "New Delhi",
    "CSMT": "Mumbai CST",
    "BCT": "Mumbai Central",
    "SBC": "Bangalore",
    "MAS": "Chennai Central",
    "HWH": "Howrah (Kolkata)",
    "SDAH": "Sealdah (Kolkata)",
    "SC": "Secunderabad",
    "PUNE": "Pune",
    "JP": "Jaipur",
    "ADI": "Ahmedabad",
    "MAO": "Madgaon (Goa)",
    "LKO": "Lucknow",
    "BSB": "Varanasi",
    "PNBE": "Patna",
    "BPL": "Bhopal",
    "AGC": "Agra Cantt",
    "CDG": "Chandigarh",
    "ERS": "Ernakulam (Kochi)",
    "TVC": "Trivandrum",
    "VSKP": "Visakhapatnam",
    "HNZM": "Hazrat Nizamuddin (Delhi)",
}


def normalize_station_code(input_str: str) -> str:
    """Convert city name or station code to standard station code"""
    input_lower = input_str.lower().strip()
    
    # Check if it's a city name
    if input_lower in CITY_TO_STATION:
        return CITY_TO_STATION[input_lower]
    
    # Assume it's already a station code
    return input_str.upper().strip()


def get_city_name(station_code: str) -> str:
    """Get city name for a station code"""
    return STATION_TO_CITY.get(station_code.upper(), station_code)


def schedule_to_offer(
    schedule: TrainSchedule,
    departure_date: str,
    search_id: str,
) -> TrainOffer:
    """Convert a TrainSchedule to TrainOffer"""
    
    # Parse times
    dep_hour, dep_min = map(int, schedule.departure_time.split(":"))
    arr_hour, arr_min = map(int, schedule.arrival_time.split(":"))
    
    # Create datetime objects
    dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
    departure_dt = dep_date.replace(hour=dep_hour, minute=dep_min)
    
    # Calculate arrival (may be next day)
    arrival_dt = dep_date.replace(hour=arr_hour, minute=arr_min)
    if schedule.duration_minutes > 0:
        arrival_dt = departure_dt + timedelta(minutes=schedule.duration_minutes)
    elif arrival_dt <= departure_dt:
        arrival_dt += timedelta(days=1)
    
    # Convert fares dict to available_classes list
    available_classes = [
        {"class": cls, "avg_fare": fare}
        for cls, fare in schedule.fares.items()
    ]
    
    # Get lowest fare for display
    lowest_fare = min(schedule.fares.values()) if schedule.fares else 0
    
    # Build booking partner URLs
    booking_partners = []
    for partner in TRAIN_BOOKING_PARTNERS:
        partner_url = partner["url_template"]
        # Note: Most train booking sites don't support deep linking well
        booking_partners.append({
            "name": partner["name"],
            "url": partner_url,
            "priority": partner["priority"],
            "is_official": partner.get("is_official", False),
        })
    
    return TrainOffer(
        offer_id=f"{search_id}-{schedule.train_number}",
        mode=TransportMode.TRAIN,
        provider="indian_railways",
        
        # Route
        from_station=schedule.departure_station,
        from_city=get_city_name(schedule.departure_station),
        from_station_name=f"{get_city_name(schedule.departure_station)} ({schedule.departure_station})",
        to_station=schedule.arrival_station,
        to_city=get_city_name(schedule.arrival_station),
        to_station_name=f"{get_city_name(schedule.arrival_station)} ({schedule.arrival_station})",
        
        # Timing
        departure_time=departure_dt,
        arrival_time=arrival_dt,
        duration_minutes=schedule.duration_minutes,
        
        # Pricing
        avg_price=float(lowest_fare),
        currency="INR",
        price_label="Average Fare (Lowest Class)",
        price_disclaimer="Average fare shown for reference. Actual price depends on class, quota, and availability. Book on official partner sites.",
        
        # Distance
        distance_km=float(schedule.distance_km),
        
        # Booking
        booking_partners=booking_partners,
        is_fallback=False,
        
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
    )


def create_fallback_offer(
    origin: str,
    destination: str,
    departure_date: str,
    search_id: str,
    distance_km: Optional[int] = None,
) -> TrainOffer:
    """Create a fallback redirect offer when no route data exists"""
    
    origin_city = get_city_name(origin)
    dest_city = get_city_name(destination)
    
    # Estimate distance if not provided
    if not distance_km:
        distance_km = get_distance(origin, destination) or 500  # Default estimate
    
    # Calculate estimated fares
    estimated_sl = calculate_average_fare(distance_km, "SL")
    estimated_3a = calculate_average_fare(distance_km, "3A")
    estimated_2a = calculate_average_fare(distance_km, "2A")
    
    dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
    
    booking_partners = []
    for partner in TRAIN_BOOKING_PARTNERS:
        booking_partners.append({
            "name": partner["name"],
            "url": partner["url_template"],
            "priority": partner["priority"],
            "is_official": partner.get("is_official", False),
            "description": partner["description"],
        })
    
    return TrainOffer(
        offer_id=f"{search_id}-fallback",
        mode=TransportMode.TRAIN,
        provider="redirect",
        
        # Route
        from_station=origin,
        from_city=origin_city,
        from_station_name=f"{origin_city} ({origin})",
        to_station=destination,
        to_city=dest_city,
        to_station_name=f"{dest_city} ({destination})",
        
        # Timing (placeholder - actual times vary)
        departure_time=dep_date.replace(hour=0, minute=0),
        arrival_time=dep_date.replace(hour=0, minute=0),
        duration_minutes=0,
        
        # Pricing (estimated range)
        avg_price=float(estimated_sl),
        currency="INR",
        price_label="Estimated Fare Range",
        price_disclaimer=f"Route not in our database. Estimated fares: SL ₹{estimated_sl}, 3A ₹{estimated_3a}, 2A ₹{estimated_2a}. Check official booking partners for exact schedules and prices.",
        
        # Distance
        distance_km=float(distance_km),
        
        # Booking
        booking_partners=booking_partners,
        is_fallback=True,
        
        # Train specific (unknown for fallback)
        train_number="CHECK_IRCTC",
        train_name=f"Trains from {origin_city} to {dest_city}",
        train_type="Various",
        days_of_operation=[],
        frequency="Check booking partner",
        stops_count=0,
        intermediate_stops=[],
        available_classes=[
            {"class": "SL", "avg_fare": estimated_sl},
            {"class": "3A", "avg_fare": estimated_3a},
            {"class": "2A", "avg_fare": estimated_2a},
        ],
        has_pantry=False,
    )


async def search_trains(request: TrainSearchRequest) -> TrainSearchResponse:
    """
    Search for trains between two stations.
    
    Returns:
        - Real offers if route exists in database
        - Fallback redirect offer if route not found
        - Never returns empty results
    """
    search_id = str(uuid.uuid4())
    
    # Normalize inputs
    origin = normalize_station_code(request.origin)
    destination = normalize_station_code(request.destination)
    
    logger.info(f"🚆 Train search: {origin} → {destination} on {request.departure_date}")
    
    # Try to find trains for this route
    schedules = get_trains_for_route(origin, destination)
    
    if schedules:
        # Convert schedules to offers
        offers = [
            schedule_to_offer(schedule, request.departure_date, search_id)
            for schedule in schedules
        ]
        
        # Apply optional filters
        if request.train_class:
            offers = [
                o for o in offers
                if any(c["class"] == request.train_class for c in o.available_classes)
            ]
        
        if request.train_type:
            offers = [
                o for o in offers
                if o.train_type and request.train_type.lower() in o.train_type.lower()
            ]
        
        # Sort by departure time
        offers.sort(key=lambda o: o.departure_time)
        
        logger.info(f"✅ Found {len(offers)} trains for {origin} → {destination}")
        
        distance = get_distance(origin, destination)
        
        return TrainSearchResponse(
            offers=offers,
            search_id=search_id,
            cached=False,
            timestamp=datetime.utcnow(),
            origin_city=get_city_name(origin),
            destination_city=get_city_name(destination),
            distance_km=float(distance) if distance else None,
            is_fallback=False,
            fallback_message=None,
        )
    
    else:
        # No route data - return fallback
        logger.info(f"⚠️ No route data for {origin} → {destination}, returning fallback")
        
        distance = get_distance(origin, destination)
        fallback_offer = create_fallback_offer(
            origin=origin,
            destination=destination,
            departure_date=request.departure_date,
            search_id=search_id,
            distance_km=distance,
        )
        
        return TrainSearchResponse(
            offers=[fallback_offer],
            search_id=search_id,
            cached=False,
            timestamp=datetime.utcnow(),
            origin_city=get_city_name(origin),
            destination_city=get_city_name(destination),
            distance_km=float(distance) if distance else None,
            is_fallback=True,
            fallback_message="We don't have detailed schedule data for this route. Please check our booking partners (IRCTC, ixigo, Paytm) for current trains, timings, and prices.",
        )

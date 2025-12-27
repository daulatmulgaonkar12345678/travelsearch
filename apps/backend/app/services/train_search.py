"""Train Search Service - Variant-Level Results

ARCHITECTURE PRINCIPLE:
- One route ≠ one result
- One train × multiple classes = multiple results
- Each class variant = separate card (like flights)

Data Source: Static Indian Railways timetable data
Fare Strategy: Distance-based average fares with slight variations
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
import random

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
# CLASS DISPLAY NAMES
# ============================================================
CLASS_DISPLAY_NAMES = {
    "SL": "Sleeper",
    "3A": "AC 3-Tier",
    "2A": "AC 2-Tier",
    "1A": "AC First Class",
    "CC": "Chair Car",
    "2S": "Second Sitting",
    "FC": "First Class",
    "EC": "Executive Chair",
}

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
    
    if input_lower in CITY_TO_STATION:
        return CITY_TO_STATION[input_lower]
    
    return input_str.upper().strip()


def get_city_name(station_code: str) -> str:
    """Get city name for a station code"""
    return STATION_TO_CITY.get(station_code.upper(), station_code)


def add_fare_variation(base_fare: int, train_type: str) -> int:
    """Add slight realistic variation to fares based on train type"""
    # Base variation ±3%
    variation = random.uniform(-0.03, 0.03)
    
    # Train type adjustments
    if train_type and "Rajdhani" in train_type:
        variation += 0.05  # Premium trains cost more
    elif train_type and "Shatabdi" in train_type:
        variation += 0.07
    elif train_type and "Duronto" in train_type:
        variation += 0.04
    elif train_type and ("Passenger" in train_type or "Local" in train_type):
        variation -= 0.05  # Slow trains cost less
    
    return int(base_fare * (1 + variation))


def schedule_to_class_offers(
    schedule: TrainSchedule,
    departure_date: str,
    search_id: str,
) -> List[TrainOffer]:
    """
    VARIANT-LEVEL EXPANSION:
    Convert ONE train schedule into MULTIPLE offers - one per class.
    
    Example: Mumbai Rajdhani with classes [SL, 3A, 2A, 1A] becomes 4 separate cards.
    """
    offers = []
    
    # Parse times
    dep_hour, dep_min = map(int, schedule.departure_time.split(":"))
    arr_hour, arr_min = map(int, schedule.arrival_time.split(":"))
    
    dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
    departure_dt = dep_date.replace(hour=dep_hour, minute=dep_min)
    
    # Calculate arrival (may be next day)
    arrival_dt = dep_date.replace(hour=arr_hour, minute=arr_min)
    if schedule.duration_minutes > 0:
        arrival_dt = departure_dt + timedelta(minutes=schedule.duration_minutes)
    elif arrival_dt <= departure_dt:
        arrival_dt += timedelta(days=1)
    
    # Build booking partner URLs
    booking_partners = []
    for partner in TRAIN_BOOKING_PARTNERS:
        booking_partners.append({
            "name": partner["name"],
            "url": partner["url_template"],
            "priority": partner["priority"],
            "is_official": partner.get("is_official", False),
        })
    
    # CREATE ONE CARD PER CLASS
    for travel_class, base_fare in schedule.fares.items():
        # Add variation so fares differ slightly
        fare_with_variation = add_fare_variation(base_fare, schedule.train_type)
        
        class_display = CLASS_DISPLAY_NAMES.get(travel_class, travel_class)
        
        offer = TrainOffer(
            offer_id=f"{search_id}-{schedule.train_number}-{travel_class}",
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
            
            # Pricing - THIS CLASS ONLY
            avg_price=float(fare_with_variation),
            currency="INR",
            price_label=f"Avg Fare • {class_display}",
            price_disclaimer=f"Average {class_display} fare. Actual price depends on quota and availability.",
            
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
            
            # THIS CARD IS FOR ONE CLASS ONLY
            available_classes=[{"class": travel_class, "avg_fare": fare_with_variation}],
            selected_class=travel_class,
            selected_class_display=class_display,
            has_pantry=schedule.has_pantry,
        )
        
        offers.append(offer)
    
    return offers


def create_fallback_offers(
    origin: str,
    destination: str,
    departure_date: str,
    search_id: str,
    distance_km: Optional[int] = None,
) -> List[TrainOffer]:
    """Create fallback redirect offers for unknown routes - one per common class"""
    
    origin_city = get_city_name(origin)
    dest_city = get_city_name(destination)
    
    if not distance_km:
        distance_km = get_distance(origin, destination) or 500
    
    dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
    
    booking_partners = [
        {
            "name": partner["name"],
            "url": partner["url_template"],
            "priority": partner["priority"],
            "is_official": partner.get("is_official", False),
            "description": partner["description"],
        }
        for partner in TRAIN_BOOKING_PARTNERS
    ]
    
    # Create one fallback card (single redirect, not multiple)
    estimated_sl = calculate_average_fare(distance_km, "SL")
    estimated_3a = calculate_average_fare(distance_km, "3A")
    estimated_2a = calculate_average_fare(distance_km, "2A")
    
    fallback = TrainOffer(
        offer_id=f"{search_id}-fallback",
        mode=TransportMode.TRAIN,
        provider="redirect",
        
        from_station=origin,
        from_city=origin_city,
        from_station_name=f"{origin_city} ({origin})",
        to_station=destination,
        to_city=dest_city,
        to_station_name=f"{dest_city} ({destination})",
        
        departure_time=dep_date.replace(hour=0, minute=0),
        arrival_time=dep_date.replace(hour=0, minute=0),
        duration_minutes=0,
        
        avg_price=float(estimated_sl),
        currency="INR",
        price_label="Estimated Fare Range",
        price_disclaimer=f"Route not in database. Estimated: SL ₹{estimated_sl}, 3A ₹{estimated_3a}, 2A ₹{estimated_2a}. Check booking partners.",
        
        distance_km=float(distance_km),
        booking_partners=booking_partners,
        is_fallback=True,
        
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
        selected_class=None,
        selected_class_display=None,
        has_pantry=False,
    )
    
    return [fallback]


async def search_trains(request: TrainSearchRequest) -> TrainSearchResponse:
    """
    Search for trains between two stations.
    
    VARIANT-LEVEL RESULTS:
    - Each train × each class = separate card
    - If Mumbai Rajdhani has SL, 3A, 2A, 1A → returns 4 cards
    - Never returns 1 card for a valid route with multiple options
    """
    search_id = str(uuid.uuid4())
    
    # Normalize inputs (station → city handling)
    origin = normalize_station_code(request.origin)
    destination = normalize_station_code(request.destination)
    
    logger.info(f"🚆 Train search: {origin} → {destination} on {request.departure_date}")
    
    # Try to find trains for this route
    schedules = get_trains_for_route(origin, destination)
    
    if schedules:
        # EXPAND each train into multiple class variants
        all_offers = []
        for schedule in schedules:
            class_offers = schedule_to_class_offers(schedule, request.departure_date, search_id)
            all_offers.extend(class_offers)
        
        # Apply optional class filter
        if request.train_class:
            all_offers = [o for o in all_offers if o.selected_class == request.train_class]
        
        # Apply optional train type filter
        if request.train_type:
            all_offers = [
                o for o in all_offers
                if o.train_type and request.train_type.lower() in o.train_type.lower()
            ]
        
        # Sort by departure time, then by price
        all_offers.sort(key=lambda o: (o.departure_time, o.avg_price))
        
        logger.info(f"✅ Found {len(all_offers)} train+class variants for {origin} → {destination}")
        
        distance = get_distance(origin, destination)
        
        return TrainSearchResponse(
            offers=all_offers,
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
        fallback_offers = create_fallback_offers(
            origin=origin,
            destination=destination,
            departure_date=request.departure_date,
            search_id=search_id,
            distance_km=distance,
        )
        
        return TrainSearchResponse(
            offers=fallback_offers,
            search_id=search_id,
            cached=False,
            timestamp=datetime.utcnow(),
            origin_city=get_city_name(origin),
            destination_city=get_city_name(destination),
            distance_km=float(distance) if distance else None,
            is_fallback=True,
            fallback_message="We don't have detailed schedule data for this route. Please check our booking partners (IRCTC, ixigo, Paytm) for current trains, timings, and prices.",
        )

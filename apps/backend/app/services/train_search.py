"""Train Search Service - Variant-Level Results

ARCHITECTURE PRINCIPLE:
- One route ≠ one result
- One train × multiple classes = multiple results
- Each class variant = separate card (like flights)
- Backend is smart, frontend is dumb: ALL input resolution happens here

Data Source: Static Indian Railways timetable data
Fare Strategy: Distance-based average fares with slight variations
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
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
from app.services.rail_connectivity import (
    resolve_to_station_codes,
    search_stations_cities,
    get_city_info,
    get_station_info,
    _load_data,
    _cities,
    _stations,
    _aliases,
    _station_to_city,
)

logger = logging.getLogger(__name__)

# ============================================================
# RESOLUTION ERROR MODELS
# ============================================================

@dataclass
class ResolutionResult:
    """Result of resolving user input to station codes"""
    success: bool
    input_type: str  # "city", "station", "alias", "unknown"
    station_codes: List[str]
    city_name: Optional[str]  # Resolved city name for display
    city_id: Optional[str]  # City ID if resolved to city
    error_message: Optional[str] = None
    suggestions: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []

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
# DEFENSIVE INPUT RESOLUTION
# ============================================================

def validate_and_resolve_input(user_input: str) -> ResolutionResult:
    """
    Defensively resolve ANY user input to valid station codes.
    
    This is the SINGLE source of truth for input resolution.
    Backend owns this - never trust frontend input.
    
    Handles:
    - City names: "Pune", "Mumbai", "Delhi"
    - Aliases: "Bombay", "Calcutta", "Madras", "Poona"
    - Station codes: "CSMT", "PUNE", "NDLS"
    - Station names: "Shivaji Nagar", "Anand Vihar"
    
    Returns:
    - ResolutionResult with success=True and station_codes if valid
    - ResolutionResult with success=False, error_message, and suggestions if invalid
    """
    _load_data()  # Ensure data is loaded
    
    if not user_input or not user_input.strip():
        return ResolutionResult(
            success=False,
            input_type="unknown",
            station_codes=[],
            city_name=None,
            city_id=None,
            error_message="Location cannot be empty",
            suggestions=[]
        )
    
    user_input = user_input.strip()
    input_lower = user_input.lower()
    input_upper = user_input.upper()
    
    # 1. Try resolution via rail_connectivity service
    input_type, station_codes = resolve_to_station_codes(user_input)
    
    if input_type != "unknown" and station_codes:
        # Successfully resolved - determine city name
        city_name = None
        city_id = None
        
        if input_type == "city":
            # Find the city
            for cid, city in _cities.items():
                if input_lower == city.city_name.lower() or input_lower == cid:
                    city_name = city.city_name
                    city_id = cid
                    break
            
            # Check aliases for city resolution
            if not city_name and input_lower in _aliases:
                alias_info = _aliases[input_lower]
                if alias_info.get("resolves_to_city"):
                    resolved_city_id = alias_info["resolves_to_city"]
                    if resolved_city_id in _cities:
                        city_name = _cities[resolved_city_id].city_name
                        city_id = resolved_city_id
        
        elif input_type == "station":
            # Single station - get its city
            station_code = station_codes[0]
            if station_code in _station_to_city:
                city_id = _station_to_city[station_code]
                if city_id in _cities:
                    city_name = _cities[city_id].city_name
            elif station_code in _stations:
                city_name = _stations[station_code].city
        
        # Fallback city name derivation
        if not city_name and station_codes:
            first_station = station_codes[0]
            if first_station in _stations:
                city_name = _stations[first_station].city
            else:
                city_name = user_input.title()
        
        return ResolutionResult(
            success=True,
            input_type=input_type,
            station_codes=station_codes,
            city_name=city_name,
            city_id=city_id
        )
    
    # 2. Input not found - generate suggestions
    suggestions = _generate_suggestions(user_input)
    
    return ResolutionResult(
        success=False,
        input_type="unknown",
        station_codes=[],
        city_name=None,
        city_id=None,
        error_message=f"'{user_input}' is not a recognized city, station, or alias",
        suggestions=suggestions
    )


def _generate_suggestions(user_input: str) -> List[Dict[str, Any]]:
    """Generate helpful suggestions for invalid input using fuzzy matching"""
    _load_data()
    
    suggestions = []
    input_lower = user_input.lower()
    
    # Use the existing search function which does fuzzy matching
    search_results = search_stations_cities(user_input, limit=5)
    
    for result in search_results:
        suggestions.append({
            "type": result.result_type.value,
            "display_name": result.display_name,
            "subtitle": result.subtitle,
            "station_codes": result.station_codes,
        })
    
    # If no results from search, try character-level similarity
    if not suggestions:
        # Simple prefix/substring matching on cities
        for city_id, city in _cities.items():
            city_lower = city.city_name.lower()
            
            # Check prefix match
            if city_lower.startswith(input_lower[:2]) if len(input_lower) >= 2 else False:
                suggestions.append({
                    "type": "city",
                    "display_name": city.city_name,
                    "subtitle": f"{city.state} • {len(city.station_codes)} stations",
                    "station_codes": city.station_codes,
                })
            
            if len(suggestions) >= 5:
                break
    
    return suggestions[:5]


def get_city_name_for_display(station_codes: List[str], resolved_city_name: Optional[str]) -> str:
    """Get display-friendly city name from station codes"""
    if resolved_city_name:
        return resolved_city_name
    
    if not station_codes:
        return "Unknown"
    
    _load_data()
    
    # Try to get city from first station
    first_station = station_codes[0]
    
    if first_station in _station_to_city:
        city_id = _station_to_city[first_station]
        if city_id in _cities:
            return _cities[city_id].city_name
    
    if first_station in _stations:
        return _stations[first_station].city
    
    return first_station


# ============================================================
# LEGACY COMPATIBILITY (for existing code that uses these)
# ============================================================

def get_city_name(station_code: str) -> str:
    """Get city name for a station code - uses new resolution system"""
    _load_data()
    
    if station_code in _station_to_city:
        city_id = _station_to_city[station_code]
        if city_id in _cities:
            return _cities[city_id].city_name
    
    if station_code in _stations:
        return _stations[station_code].city
    
    return station_code


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
    Search for trains between two locations.
    
    DEFENSIVE BACKEND:
    - Resolves ANY input (city, alias, station code) to valid station codes
    - Returns city-level abstraction, NOT raw station-pair explosions
    - Gracefully handles invalid inputs with suggestions
    
    VARIANT-LEVEL RESULTS:
    - Each train × each class = separate card
    - If Mumbai Rajdhani has SL, 3A, 2A, 1A → returns 4 cards
    """
    search_id = str(uuid.uuid4())
    
    # ============================================================
    # STEP 1: DEFENSIVE INPUT RESOLUTION (Backend-owned)
    # ============================================================
    origin_result = validate_and_resolve_input(request.origin)
    dest_result = validate_and_resolve_input(request.destination)
    
    # Check for resolution failures
    if not origin_result.success:
        raise TrainSearchError(
            error_type="INVALID_ORIGIN",
            message=origin_result.error_message,
            suggestions=origin_result.suggestions,
            invalid_input=request.origin
        )
    
    if not dest_result.success:
        raise TrainSearchError(
            error_type="INVALID_DESTINATION", 
            message=dest_result.error_message,
            suggestions=dest_result.suggestions,
            invalid_input=request.destination
        )
    
    # Get station codes (may be multiple for city inputs)
    origin_stations = origin_result.station_codes
    dest_stations = dest_result.station_codes
    
    # Get display names (city-level)
    origin_city_display = origin_result.city_name or get_city_name_for_display(origin_stations, None)
    dest_city_display = dest_result.city_name or get_city_name_for_display(dest_stations, None)
    
    logger.info(f"🚆 Train search: {origin_city_display} ({origin_stations}) → {dest_city_display} ({dest_stations}) on {request.departure_date}")
    
    # ============================================================
    # STEP 2: SEARCH ALL STATION PAIRS (City expansion)
    # ============================================================
    all_offers = []
    searched_pairs = set()
    
    # Search all combinations of origin and destination stations
    for origin_code in origin_stations:
        for dest_code in dest_stations:
            if origin_code == dest_code:
                continue
            
            pair_key = f"{origin_code}-{dest_code}"
            if pair_key in searched_pairs:
                continue
            searched_pairs.add(pair_key)
            
            # Try to find trains for this station pair
            schedules = get_trains_for_route(origin_code, dest_code)
            
            if schedules:
                for schedule in schedules:
                    class_offers = schedule_to_class_offers(schedule, request.departure_date, search_id)
                    all_offers.extend(class_offers)
    
    # ============================================================
    # STEP 3: APPLY FILTERS
    # ============================================================
    if request.train_class:
        all_offers = [o for o in all_offers if o.selected_class == request.train_class]
    
    if request.train_type:
        all_offers = [
            o for o in all_offers
            if o.train_type and request.train_type.lower() in o.train_type.lower()
        ]
    
    # ============================================================
    # STEP 4: DEDUPLICATE AND SORT
    # ============================================================
    # Remove duplicate train+class combinations (same train serving multiple stations in same city)
    seen_train_class = set()
    unique_offers = []
    for offer in all_offers:
        key = f"{offer.train_number}-{offer.selected_class}"
        if key not in seen_train_class:
            seen_train_class.add(key)
            unique_offers.append(offer)
    
    all_offers = unique_offers
    
    # Sort by departure time, then by price
    all_offers.sort(key=lambda o: (o.departure_time, o.avg_price))
    
    # ============================================================
    # STEP 5: BUILD RESPONSE (City-level abstraction)
    # ============================================================
    # Calculate representative distance (from primary stations)
    primary_origin = origin_stations[0]
    primary_dest = dest_stations[0]
    distance = get_distance(primary_origin, primary_dest)
    
    if all_offers:
        logger.info(f"✅ Found {len(all_offers)} train+class variants for {origin_city_display} → {dest_city_display}")
        
        return TrainSearchResponse(
            offers=all_offers,
            search_id=search_id,
            cached=False,
            timestamp=datetime.utcnow(),
            origin_city=origin_city_display,
            destination_city=dest_city_display,
            distance_km=float(distance) if distance else None,
            is_fallback=False,
            fallback_message=None,
        )
    
    else:
        # No route data - return fallback with booking partner links
        logger.info(f"⚠️ No route data for {origin_city_display} → {dest_city_display}, returning fallback")
        
        fallback_offers = create_fallback_offers(
            origin=primary_origin,
            destination=primary_dest,
            departure_date=request.departure_date,
            search_id=search_id,
            distance_km=distance,
            origin_city_override=origin_city_display,
            dest_city_override=dest_city_display,
        )
        
        return TrainSearchResponse(
            offers=fallback_offers,
            search_id=search_id,
            cached=False,
            timestamp=datetime.utcnow(),
            origin_city=origin_city_display,
            destination_city=dest_city_display,
            distance_km=float(distance) if distance else None,
            is_fallback=True,
            fallback_message=f"We don't have detailed schedule data for {origin_city_display} to {dest_city_display}. Please check our booking partners (IRCTC, ixigo, Paytm) for current trains, timings, and prices.",
        )


# ============================================================
# CUSTOM EXCEPTION FOR SEARCH ERRORS
# ============================================================

class TrainSearchError(Exception):
    """Custom exception for train search validation errors"""
    def __init__(
        self, 
        error_type: str, 
        message: str, 
        suggestions: List[Dict[str, Any]] = None,
        invalid_input: str = None
    ):
        self.error_type = error_type
        self.message = message
        self.suggestions = suggestions or []
        self.invalid_input = invalid_input
        super().__init__(message)

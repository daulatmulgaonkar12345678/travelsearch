"""Train Search Service - STATION-FIRST ARCHITECTURE

🔴 ARCHITECTURE RULE (NON-NEGOTIABLE):
- Train search inputs must resolve to STATIONS only
- City names are NEVER valid inputs
- Only two valid input types:
  1. Station codes (e.g., CSMT, PUNE, NDLS)
  2. City ALL tokens (e.g., MUMBAI_ALL, PUNE_ALL)

Frontend MUST submit:
  ✅ Station codes: "CSMT", "PUNE"
  ✅ ALL tokens: "MUMBAI_ALL", "PUNE_ALL"
  ❌ NEVER: "Mumbai", "Pune" (raw city names)

Backend MUST:
  - Accept ONLY station codes or _ALL tokens
  - Resolve _ALL tokens to station arrays internally
  - REJECT raw city names explicitly
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
    _load_data,
    _cities,
    _stations,
    _station_to_city,
)

logger = logging.getLogger(__name__)

# ============================================================
# STATION-FIRST RESOLUTION
# ============================================================

@dataclass
class StationResolutionResult:
    """Result of station-first resolution"""
    success: bool
    input_type: str  # "station", "city_all", "invalid_city", "unknown"
    station_codes: List[str]
    display_name: str  # For response (e.g., "Mumbai (All Stations)" or "CSMT")
    error_message: Optional[str] = None


def resolve_station_input(user_input: str) -> StationResolutionResult:
    """
    STATION-FIRST RESOLUTION (STRICT CONTRACT)
    
    Valid inputs:
      ✅ Station codes: CSMT, PUNE, NDLS, etc.
      ✅ ALL tokens: MUMBAI_ALL, PUNE_ALL, DELHI_ALL, etc.
    
    Invalid inputs:
      ❌ Raw city names: Mumbai, Pune, Delhi, etc.
      ❌ Free text: anything not matching above
    
    Returns:
      - success=True with station_codes for valid inputs
      - success=False with error_message for invalid inputs
    """
    _load_data()
    
    if not user_input or not user_input.strip():
        return StationResolutionResult(
            success=False,
            input_type="unknown",
            station_codes=[],
            display_name="",
            error_message="Location cannot be empty"
        )
    
    user_input = user_input.strip()
    input_upper = user_input.upper()
    
    # ============================================================
    # CASE 1: _ALL Token (e.g., MUMBAI_ALL, PUNE_ALL)
    # ============================================================
    if input_upper.endswith("_ALL"):
        city_id = input_upper.replace("_ALL", "").lower()
        
        if city_id in _cities:
            city = _cities[city_id]
            return StationResolutionResult(
                success=True,
                input_type="city_all",
                station_codes=city.station_codes,
                display_name=f"{city.city_name} (All Stations)"
            )
        else:
            return StationResolutionResult(
                success=False,
                input_type="unknown",
                station_codes=[],
                display_name="",
                error_message=f"Unknown city: {city_id}. Use valid city_ALL token."
            )
    
    # ============================================================
    # CASE 2: Direct Station Code (e.g., CSMT, PUNE, NDLS)
    # ============================================================
    if input_upper in _stations:
        station = _stations[input_upper]
        return StationResolutionResult(
            success=True,
            input_type="station",
            station_codes=[input_upper],
            display_name=f"{station.station_name} ({input_upper})"
        )
    
    # ============================================================
    # CASE 3: Raw City Name (REJECT)
    # ============================================================
    input_lower = user_input.lower()
    
    # Check if input matches a city name
    for city_id, city in _cities.items():
        if input_lower == city.city_name.lower() or input_lower == city_id:
            # This is a raw city name - REJECT IT
            return StationResolutionResult(
                success=False,
                input_type="invalid_city",
                station_codes=[],
                display_name="",
                error_message=f"City names are not allowed. Please select a station or '{city.city_name} (All Stations)' from the dropdown."
            )
    
    # ============================================================
    # CASE 4: Unknown Input
    # ============================================================
    return StationResolutionResult(
        success=False,
        input_type="unknown",
        station_codes=[],
        display_name="",
        error_message=f"'{user_input}' is not a valid station code. Please select from the dropdown."
    )


def get_city_name_for_station(station_code: str) -> str:
    """Get city name for a station code"""
    _load_data()
    
    if station_code in _station_to_city:
        city_id = _station_to_city[station_code]
        if city_id in _cities:
            return _cities[city_id].city_name
    
    if station_code in _stations:
        return _stations[station_code].city
    
    return station_code


# ============================================================
# BOOKING PARTNERS
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


def generate_train_booking_partners(
    from_station: str,
    to_station: str,
    departure_date: str,
) -> list:
    """
    Generate booking partner links for a train route.
    
    Properly populates URL templates with actual route data.
    
    Args:
        from_station: Origin station code (e.g., 'CSTM', 'PUNE')
        to_station: Destination station code
        departure_date: Date in YYYY-MM-DD format
    
    Returns:
        List of booking partners with valid URLs
    """
    # Normalize station codes for URLs
    origin_slug = from_station.lower().replace('_', '-')
    dest_slug = to_station.lower().replace('_', '-')
    
    # Get city names for better URL formatting
    origin_city = get_city_name_for_station(from_station).lower().replace(' ', '-')
    dest_city = get_city_name_for_station(to_station).lower().replace(' ', '-')
    
    booking_partners = []
    for partner in TRAIN_BOOKING_PARTNERS:
        url = partner["url_template"]
        
        # Replace placeholders with actual values
        if partner.get("is_official"):
            # IRCTC doesn't support deep linking to specific routes
            pass
        else:
            url = url.format(
                origin=origin_city,
                destination=dest_city,
                date=departure_date,
            )
        
        booking_partners.append({
            "name": partner["name"],
            "url": url,
            "priority": partner["priority"],
            "is_official": partner.get("is_official", False),
            "description": partner.get("description", ""),
        })
    
    return booking_partners

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


def add_fare_variation(base_fare: int, train_type: str) -> int:
    """Add slight realistic variation to fares based on train type"""
    variation = random.uniform(-0.03, 0.03)
    
    if train_type and "Rajdhani" in train_type:
        variation += 0.05
    elif train_type and "Shatabdi" in train_type:
        variation += 0.07
    elif train_type and "Duronto" in train_type:
        variation += 0.04
    elif train_type and ("Passenger" in train_type or "Local" in train_type):
        variation -= 0.05
    
    return int(base_fare * (1 + variation))


def schedule_to_class_offers(
    schedule: TrainSchedule,
    departure_date: str,
    search_id: str,
) -> List[TrainOffer]:
    """Convert ONE train schedule into MULTIPLE offers - one per class."""
    offers = []
    
    dep_hour, dep_min = map(int, schedule.departure_time.split(":"))
    arr_hour, arr_min = map(int, schedule.arrival_time.split(":"))
    
    dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
    departure_dt = dep_date.replace(hour=dep_hour, minute=dep_min)
    
    arrival_dt = dep_date.replace(hour=arr_hour, minute=arr_min)
    if schedule.duration_minutes > 0:
        arrival_dt = departure_dt + timedelta(minutes=schedule.duration_minutes)
    elif arrival_dt <= departure_dt:
        arrival_dt += timedelta(days=1)
    
    # Generate properly populated booking partner URLs
    booking_partners = generate_train_booking_partners(
        from_station=schedule.departure_station,
        to_station=schedule.arrival_station,
        departure_date=departure_date,
    )
    
    for travel_class, base_fare in schedule.fares.items():
        fare_with_variation = add_fare_variation(base_fare, schedule.train_type)
        class_display = CLASS_DISPLAY_NAMES.get(travel_class, travel_class)
        
        offer = TrainOffer(
            offer_id=f"{search_id}-{schedule.train_number}-{travel_class}",
            mode=TransportMode.TRAIN,
            provider="indian_railways",
            
            from_station=schedule.departure_station,
            from_city=get_city_name_for_station(schedule.departure_station),
            from_station_name=f"{get_city_name_for_station(schedule.departure_station)} ({schedule.departure_station})",
            to_station=schedule.arrival_station,
            to_city=get_city_name_for_station(schedule.arrival_station),
            to_station_name=f"{get_city_name_for_station(schedule.arrival_station)} ({schedule.arrival_station})",
            
            departure_time=departure_dt,
            arrival_time=arrival_dt,
            duration_minutes=schedule.duration_minutes,
            
            avg_price=float(fare_with_variation),
            currency="INR",
            price_label=f"Avg Fare • {class_display}",
            price_disclaimer=f"Average {class_display} fare. Actual price depends on quota and availability.",
            
            distance_km=float(schedule.distance_km),
            booking_partners=booking_partners,
            is_fallback=False,
            
            train_number=schedule.train_number,
            train_name=schedule.train_name,
            train_type=schedule.train_type,
            days_of_operation=schedule.days_of_operation,
            frequency="Daily" if "Daily" in schedule.days_of_operation else f"{len(schedule.days_of_operation)} days/week",
            stops_count=schedule.stops_count,
            intermediate_stops=schedule.intermediate_stops,
            
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
    origin_display: str,
    dest_display: str,
    distance_km: Optional[int] = None,
) -> List[TrainOffer]:
    """Create fallback redirect offers for routes not in database."""
    
    if not distance_km:
        distance_km = get_distance(origin, destination) or 500
    
    dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
    
    # Generate properly populated booking partner URLs
    booking_partners = generate_train_booking_partners(
        from_station=origin,
        to_station=destination,
        departure_date=departure_date,
    )
    
    estimated_sl = calculate_average_fare(distance_km, "SL")
    estimated_3a = calculate_average_fare(distance_km, "3A")
    estimated_2a = calculate_average_fare(distance_km, "2A")
    
    fallback = TrainOffer(
        offer_id=f"{search_id}-fallback",
        mode=TransportMode.TRAIN,
        provider="redirect",
        
        from_station=origin,
        from_city=origin_display,
        from_station_name=origin_display,
        to_station=destination,
        to_city=dest_display,
        to_station_name=dest_display,
        
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
        train_name=f"Trains from {origin_display} to {dest_display}",
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


# ============================================================
# CUSTOM EXCEPTION
# ============================================================

class TrainSearchError(Exception):
    """Custom exception for train search validation errors"""
    def __init__(
        self, 
        error_type: str, 
        message: str, 
        invalid_input: str = None
    ):
        self.error_type = error_type
        self.message = message
        self.invalid_input = invalid_input
        super().__init__(message)


# ============================================================
# MAIN SEARCH FUNCTION
# ============================================================

async def search_trains(request: TrainSearchRequest) -> TrainSearchResponse:
    """
    Search for trains between two stations.
    
    🔴 STATION-FIRST CONTRACT:
    - Only accepts station codes (CSMT, PUNE) or _ALL tokens (MUMBAI_ALL)
    - Rejects raw city names (Mumbai, Pune)
    - Frontend must enforce dropdown selection
    """
    search_id = str(uuid.uuid4())
    
    # ============================================================
    # STEP 1: STRICT INPUT VALIDATION
    # ============================================================
    origin_result = resolve_station_input(request.origin)
    dest_result = resolve_station_input(request.destination)
    
    if not origin_result.success:
        raise TrainSearchError(
            error_type="INVALID_ORIGIN",
            message=origin_result.error_message,
            invalid_input=request.origin
        )
    
    if not dest_result.success:
        raise TrainSearchError(
            error_type="INVALID_DESTINATION",
            message=dest_result.error_message,
            invalid_input=request.destination
        )
    
    origin_stations = origin_result.station_codes
    dest_stations = dest_result.station_codes
    origin_display = origin_result.display_name
    dest_display = dest_result.display_name
    
    logger.info(
        f"🚆 Train search: {origin_display} ({origin_stations}) → "
        f"{dest_display} ({dest_stations}) on {request.departure_date}"
    )
    
    # ============================================================
    # STEP 2: SEARCH ALL STATION PAIRS
    # ============================================================
    all_offers = []
    searched_pairs = set()
    
    for origin_code in origin_stations:
        for dest_code in dest_stations:
            if origin_code == dest_code:
                continue
            
            pair_key = f"{origin_code}-{dest_code}"
            if pair_key in searched_pairs:
                continue
            searched_pairs.add(pair_key)
            
            schedules = get_trains_for_route(origin_code, dest_code)
            
            if schedules:
                for schedule in schedules:
                    class_offers = schedule_to_class_offers(
                        schedule, request.departure_date, search_id
                    )
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
    # STEP 4: DEDUPLICATE
    # ============================================================
    seen_train_class = set()
    unique_offers = []
    for offer in all_offers:
        key = f"{offer.train_number}-{offer.selected_class}"
        if key not in seen_train_class:
            seen_train_class.add(key)
            unique_offers.append(offer)
    
    all_offers = unique_offers
    all_offers.sort(key=lambda o: (o.departure_time, o.avg_price))
    
    # ============================================================
    # STEP 5: BUILD RESPONSE
    # ============================================================
    primary_origin = origin_stations[0]
    primary_dest = dest_stations[0]
    distance = get_distance(primary_origin, primary_dest)
    
    if all_offers:
        logger.info(f"✅ Found {len(all_offers)} train+class variants")
        
        return TrainSearchResponse(
            offers=all_offers,
            search_id=search_id,
            cached=False,
            timestamp=datetime.utcnow(),
            origin_city=origin_display,
            destination_city=dest_display,
            distance_km=float(distance) if distance else None,
            is_fallback=False,
            fallback_message=None,
        )
    
    else:
        logger.info("⚠️ No route data, returning fallback")
        
        fallback_offers = create_fallback_offers(
            origin=primary_origin,
            destination=primary_dest,
            departure_date=request.departure_date,
            search_id=search_id,
            origin_display=origin_display,
            dest_display=dest_display,
            distance_km=distance,
        )
        
        return TrainSearchResponse(
            offers=fallback_offers,
            search_id=search_id,
            cached=False,
            timestamp=datetime.utcnow(),
            origin_city=origin_display,
            destination_city=dest_display,
            distance_km=float(distance) if distance else None,
            is_fallback=True,
            fallback_message=f"Route not in database. Check booking partners for {origin_display} to {dest_display}.",
        )

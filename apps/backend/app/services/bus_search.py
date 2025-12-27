"""Bus Search Service - Variant-Level Results

ARCHITECTURE PRINCIPLE:
- One route ≠ one result
- One route × multiple bus types = multiple results
- Each bus type variant = separate card (like flights)

Data Source: State RTC published schedules and industry standards
Fare Strategy: Distance-based average fares with realistic variations
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
import random

from app.models.transport import (
    BusOffer,
    BusSearchRequest,
    BusSearchResponse,
    TransportMode,
    BusType,
)
from app.data.bus_routes import (
    get_bus_route,
    get_distance,
    calculate_average_fare,
    BusRoute,
    BUS_ROUTES,
)

logger = logging.getLogger(__name__)

# ============================================================
# BOOKING PARTNERS - Priority Order (User Approved)
# ============================================================
BUS_BOOKING_PARTNERS = [
    {
        "name": "redBus",
        "priority": 1,
        "url_template": "https://www.redbus.in/bus-tickets/{origin}-to-{destination}",
        "description": "India's largest bus booking platform",
        "is_official": False,
    },
    {
        "name": "AbhiBus",
        "priority": 2,
        "url_template": "https://www.abhibus.com/bus-tickets/{origin}-to-{destination}",
        "description": "Wide operator coverage",
        "is_official": False,
    },
    {
        "name": "Paytm Bus",
        "priority": 3,
        "url_template": "https://paytm.com/bus-tickets/{origin}-to-{destination}",
        "description": "Cashback & easy booking",
        "is_official": False,
    },
]

# ============================================================
# BUS TYPE CONFIGURATIONS
# ============================================================
BUS_TYPE_CONFIGS = {
    "ordinary": {
        "enum": BusType.ORDINARY,
        "label": "Non-AC Seater",
        "is_ac": False,
        "is_sleeper": False,
        "has_wifi": False,
        "has_charging": False,
        "fare_key": "ordinary",
        "departure_offset": 0,  # minutes from base time
    },
    "semi_deluxe": {
        "enum": BusType.SEMI_DELUXE,
        "label": "Semi Deluxe",
        "is_ac": False,
        "is_sleeper": False,
        "has_wifi": False,
        "has_charging": False,
        "fare_key": "semi_deluxe",
        "departure_offset": 30,
    },
    "deluxe": {
        "enum": BusType.DELUXE,
        "label": "Deluxe",
        "is_ac": False,
        "is_sleeper": False,
        "has_wifi": False,
        "has_charging": True,
        "fare_key": "deluxe",
        "departure_offset": 60,
    },
    "ac_seater": {
        "enum": BusType.AC_SEATER,
        "label": "AC Seater",
        "is_ac": True,
        "is_sleeper": False,
        "has_wifi": False,
        "has_charging": True,
        "fare_key": "ac_seater",
        "departure_offset": 90,
    },
    "non_ac_sleeper": {
        "enum": BusType.NON_AC_SLEEPER,
        "label": "Non-AC Sleeper",
        "is_ac": False,
        "is_sleeper": True,
        "has_wifi": False,
        "has_charging": False,
        "fare_key": "non_ac_sleeper",
        "departure_offset": 120,
    },
    "ac_sleeper": {
        "enum": BusType.AC_SLEEPER,
        "label": "AC Sleeper",
        "is_ac": True,
        "is_sleeper": True,
        "has_wifi": True,
        "has_charging": True,
        "fare_key": "ac_sleeper",
        "departure_offset": 150,
    },
    "volvo": {
        "enum": BusType.VOLVO,
        "label": "Volvo / Premium AC",
        "is_ac": True,
        "is_sleeper": False,
        "has_wifi": True,
        "has_charging": True,
        "fare_key": "volvo",
        "departure_offset": 180,
    },
    "multi_axle": {
        "enum": BusType.MULTI_AXLE,
        "label": "Multi-Axle AC",
        "is_ac": True,
        "is_sleeper": True,
        "has_wifi": True,
        "has_charging": True,
        "fare_key": "multi_axle",
        "departure_offset": 210,
    },
}

# ============================================================
# CITY MAPPINGS
# ============================================================
CITY_NORMALIZE = {
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "bangalore": "Bangalore",
    "bengaluru": "Bangalore",
    "chennai": "Chennai",
    "madras": "Chennai",
    "kolkata": "Kolkata",
    "calcutta": "Kolkata",
    "hyderabad": "Hyderabad",
    "pune": "Pune",
    "poona": "Pune",
    "jaipur": "Jaipur",
    "ahmedabad": "Ahmedabad",
    "goa": "Goa",
    "panaji": "Goa",
    "mysore": "Mysore",
    "mysuru": "Mysore",
    "coimbatore": "Coimbatore",
    "agra": "Agra",
    "chandigarh": "Chandigarh",
    "lucknow": "Lucknow",
    "indore": "Indore",
    "surat": "Surat",
    "vadodara": "Vadodara",
    "nagpur": "Nagpur",
    "vijayawada": "Vijayawada",
    "madurai": "Madurai",
    "thiruvananthapuram": "Trivandrum",
    "trivandrum": "Trivandrum",
    "kochi": "Kochi",
    "cochin": "Kochi",
}

CITY_TO_CODE = {
    "delhi": "DEL",
    "mumbai": "MUM",
    "bangalore": "BLR",
    "chennai": "CHE",
    "hyderabad": "HYD",
    "pune": "PUN",
    "jaipur": "JAI",
    "ahmedabad": "AMD",
    "goa": "GOA",
    "mysore": "MYS",
    "coimbatore": "COI",
    "agra": "AGR",
    "chandigarh": "CHD",
}


def normalize_city(city: str) -> str:
    """Normalize city name to standard format"""
    city_lower = city.lower().strip()
    return CITY_NORMALIZE.get(city_lower, city.title())


def get_city_code(city: str) -> str:
    """Get city code from city name"""
    city_lower = city.lower().strip()
    return CITY_TO_CODE.get(city_lower, city.upper()[:3])


def add_fare_variation(base_fare: int, operator_type: str) -> int:
    """Add slight realistic variation to fares"""
    # Base variation ±5%
    variation = random.uniform(-0.05, 0.05)
    
    # Operator type adjustments
    if operator_type == "government":
        variation -= 0.03  # RTC slightly cheaper
    elif operator_type == "private":
        variation += 0.02  # Private slightly more
    
    return int(base_fare * (1 + variation))


def route_to_type_offers(
    route: BusRoute,
    departure_date: str,
    search_id: str,
) -> List[BusOffer]:
    """
    VARIANT-LEVEL EXPANSION:
    Convert ONE bus route into MULTIPLE offers - one per bus type.
    
    Example: Mumbai→Pune with fares for [ordinary, ac_seater, ac_sleeper, volvo]
    becomes 4 separate cards with different prices and departure times.
    """
    offers = []
    dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
    
    # Parse base departure time
    first_dep_hour, first_dep_min = map(int, route.first_departure.split(":"))
    base_departure = dep_date.replace(hour=first_dep_hour, minute=first_dep_min)
    
    # Build booking partner URLs
    origin_slug = route.origin_city.lower().replace(" ", "-")
    dest_slug = route.destination_city.lower().replace(" ", "-")
    
    booking_partners = []
    for partner in BUS_BOOKING_PARTNERS:
        url = partner["url_template"].format(
            origin=origin_slug,
            destination=dest_slug,
        )
        booking_partners.append({
            "name": partner["name"],
            "url": url,
            "priority": partner["priority"],
            "is_official": partner.get("is_official", False),
        })
    
    # CREATE ONE CARD PER BUS TYPE
    for bus_type_key, base_fare in route.fares.items():
        config = BUS_TYPE_CONFIGS.get(bus_type_key)
        if not config:
            continue
        
        # Add fare variation so prices differ
        fare_with_variation = add_fare_variation(base_fare, "private")
        
        # Stagger departure times for different types
        departure_dt = base_departure + timedelta(minutes=config["departure_offset"])
        arrival_dt = departure_dt + timedelta(minutes=route.avg_duration_minutes)
        
        # Find operator for this bus type
        operator_name = "Multiple Operators"
        operator_type = "private"
        for op in route.operators:
            if bus_type_key in op.get("bus_types", []):
                operator_name = op["name"]
                operator_type = op["type"]
                break
        
        offer = BusOffer(
            offer_id=f"{search_id}-{route.route_id}-{bus_type_key}",
            mode=TransportMode.BUS,
            provider="static_data",
            
            # Route
            from_station=get_city_code(route.origin_city),
            from_city=route.origin_city,
            from_station_name=route.origin_stop,
            to_station=get_city_code(route.destination_city),
            to_city=route.destination_city,
            to_station_name=route.destination_stop,
            
            # Timing - EACH TYPE HAS DIFFERENT DEPARTURE
            departure_time=departure_dt,
            arrival_time=arrival_dt,
            duration_minutes=route.avg_duration_minutes,
            
            # Pricing - THIS TYPE ONLY
            avg_price=float(fare_with_variation),
            currency="INR",
            price_label=f"Avg Fare • {config['label']}",
            price_disclaimer=f"Average {config['label']} fare. Actual price varies by operator.",
            
            # Distance
            distance_km=float(route.distance_km),
            
            # Booking
            booking_partners=booking_partners,
            is_fallback=False,
            
            # Bus specific - THIS CARD IS FOR ONE TYPE ONLY
            operator_name=operator_name,
            operator_type=operator_type,
            bus_type=config["enum"],
            bus_type_label=config["label"],
            is_ac=config["is_ac"],
            is_sleeper=config["is_sleeper"],
            has_charging_point=config["has_charging"],
            has_wifi=config["has_wifi"],
            frequency=route.frequency,
            departure_window=f"{route.first_departure} - {route.last_departure}",
            stops_count=0,
            intermediate_stops=[],
        )
        
        offers.append(offer)
    
    return offers


def create_fallback_offers(
    origin: str,
    destination: str,
    departure_date: str,
    search_id: str,
    distance_km: Optional[int] = None,
) -> List[BusOffer]:
    """Create fallback redirect offers for unknown routes"""
    
    origin_city = normalize_city(origin)
    dest_city = normalize_city(destination)
    
    if not distance_km:
        distance_km = get_distance(origin, destination) or 300
    
    dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
    
    # Build booking partner URLs
    origin_slug = origin_city.lower().replace(" ", "-")
    dest_slug = dest_city.lower().replace(" ", "-")
    
    booking_partners = []
    for partner in BUS_BOOKING_PARTNERS:
        url = partner["url_template"].format(
            origin=origin_slug,
            destination=dest_slug,
        )
        booking_partners.append({
            "name": partner["name"],
            "url": url,
            "priority": partner["priority"],
            "is_official": partner.get("is_official", False),
            "description": partner["description"],
        })
    
    # Estimated fares for display
    estimated_ordinary = calculate_average_fare(distance_km, "ordinary")
    estimated_ac = calculate_average_fare(distance_km, "ac_seater")
    estimated_sleeper = calculate_average_fare(distance_km, "ac_sleeper")
    
    fallback = BusOffer(
        offer_id=f"{search_id}-fallback",
        mode=TransportMode.BUS,
        provider="redirect",
        
        from_station=get_city_code(origin),
        from_city=origin_city,
        from_station_name=f"{origin_city} Bus Stand",
        to_station=get_city_code(destination),
        to_city=dest_city,
        to_station_name=f"{dest_city} Bus Stand",
        
        departure_time=dep_date.replace(hour=0, minute=0),
        arrival_time=dep_date.replace(hour=0, minute=0),
        duration_minutes=0,
        
        avg_price=float(estimated_ordinary),
        currency="INR",
        price_label="Estimated Fare Range",
        price_disclaimer=f"Route not in database. Estimated: Non-AC ₹{estimated_ordinary}, AC ₹{estimated_ac}, Sleeper ₹{estimated_sleeper}. Check partners.",
        
        distance_km=float(distance_km),
        booking_partners=booking_partners,
        is_fallback=True,
        
        operator_name="Multiple Operators",
        operator_type="private",
        bus_type=BusType.ORDINARY,
        bus_type_label="Various",
        is_ac=False,
        is_sleeper=False,
        has_charging_point=False,
        has_wifi=False,
        frequency="Check booking partner",
        departure_window=None,
        stops_count=0,
        intermediate_stops=[],
    )
    
    return [fallback]


async def search_buses(request: BusSearchRequest) -> BusSearchResponse:
    """
    Search for buses between two cities.
    
    VARIANT-LEVEL RESULTS:
    - Each route × each bus type = separate card
    - If Mumbai→Pune has [ordinary, ac_seater, ac_sleeper, volvo] → returns 4 cards
    - Never returns 1 card for a valid route with multiple options
    
    PRIORITY ORDER:
    1. Check MSRTC (Maharashtra State) routes first
    2. Fall back to generic bus routes
    """
    search_id = str(uuid.uuid4())
    
    # Normalize inputs
    origin = normalize_city(request.origin)
    destination = normalize_city(request.destination)
    
    logger.info(f"🚌 Bus search: {origin} → {destination} on {request.departure_date}")
    
    # PRIORITY 1: Check MSRTC routes first (Maharashtra State)
    try:
        from app.scrapers.msrtc_service import search_msrtc_buses
        from app.models.transport import BusSearchRequest as MSRTCRequest
        
        # Convert to MSRTC request format
        msrtc_request = MSRTCRequest(
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            passengers=request.passengers or 1
        )
        
        msrtc_response = await search_msrtc_buses(msrtc_request)
        
        # If MSRTC has results, return them
        if msrtc_response.offers and not msrtc_response.is_fallback:
            logger.info(f"✅ Found {len(msrtc_response.offers)} MSRTC bus variants for {origin} → {destination}")
            
            # Apply filters to MSRTC results
            filtered_offers = msrtc_response.offers
            
            if request.ac_only:
                filtered_offers = [o for o in filtered_offers if o.is_ac]
            
            if request.sleeper_only:
                filtered_offers = [o for o in filtered_offers if o.is_sleeper]
            
            if request.bus_type:
                filtered_offers = [
                    o for o in filtered_offers
                    if request.bus_type.lower() in o.bus_type_label.lower() or
                       request.bus_type.lower().replace("_", " ") in o.bus_type_label.lower()
                ]
            
            # Return MSRTC results with original search_id
            return BusSearchResponse(
                offers=filtered_offers,
                search_id=search_id,
                cached=False,
                timestamp=datetime.utcnow(),
                origin_city=msrtc_response.origin,
                destination_city=msrtc_response.destination,
                distance_km=None,  # MSRTC provides this in individual offers
                is_fallback=False,
                fallback_message=None,
            )
    
    except Exception as e:
        logger.warning(f"MSRTC search failed for {origin} → {destination}: {e}")
    
    # PRIORITY 2: Fall back to generic bus routes
    route = get_bus_route(origin, destination)
    
    if route:
        # EXPAND route into multiple bus type variants
        all_offers = route_to_type_offers(route, request.departure_date, search_id)
        
        # Apply optional filters
        if request.ac_only:
            all_offers = [o for o in all_offers if o.is_ac]
        
        if request.sleeper_only:
            all_offers = [o for o in all_offers if o.is_sleeper]
        
        if request.bus_type:
            # Map request bus_type to our configs
            all_offers = [
                o for o in all_offers
                if request.bus_type.lower() in o.bus_type_label.lower() or
                   request.bus_type.lower().replace("_", " ") in o.bus_type_label.lower()
            ]
        
        # Sort by price (cheapest first for buses)
        all_offers.sort(key=lambda o: o.avg_price)
        
        logger.info(f"✅ Found {len(all_offers)} bus type variants for {origin} → {destination}")
        
        return BusSearchResponse(
            offers=all_offers,
            search_id=search_id,
            cached=False,
            timestamp=datetime.utcnow(),
            origin_city=origin,
            destination_city=destination,
            distance_km=float(route.distance_km),
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
        
        return BusSearchResponse(
            offers=fallback_offers,
            search_id=search_id,
            cached=False,
            timestamp=datetime.utcnow(),
            origin_city=origin,
            destination_city=destination,
            distance_km=float(distance) if distance else None,
            is_fallback=True,
            fallback_message="We don't have detailed schedule data for this route. Please check our booking partners (redBus, AbhiBus, Paytm) for current buses, timings, and prices.",
        )

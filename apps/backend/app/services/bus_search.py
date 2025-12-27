"""Bus Search Service

Handles bus search logic using static route data.
Always returns results OR a fallback redirect card - never empty.

Data Source: State RTC published schedules, industry standards
Fare Strategy: Distance-based average fares (clearly labeled)
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

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

# City code mappings
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


def bus_type_to_enum(bus_type_str: str) -> BusType:
    """Convert string bus type to enum"""
    mapping = {
        "ordinary": BusType.ORDINARY,
        "semi_deluxe": BusType.SEMI_DELUXE,
        "deluxe": BusType.DELUXE,
        "ac_seater": BusType.AC_SEATER,
        "ac_sleeper": BusType.AC_SLEEPER,
        "non_ac_sleeper": BusType.NON_AC_SLEEPER,
        "volvo": BusType.VOLVO,
        "multi_axle": BusType.MULTI_AXLE,
        "shivneri": BusType.VOLVO,  # MSRTC premium
        "airavat": BusType.VOLVO,   # KSRTC premium
        "ashwamedh": BusType.DELUXE,
        "rajahamsa": BusType.DELUXE,
        "garuda": BusType.VOLVO,    # TSRTC premium
        "corona": BusType.VOLVO,
        "flybus": BusType.VOLVO,
    }
    return mapping.get(bus_type_str.lower(), BusType.ORDINARY)


def get_bus_type_label(bus_type: BusType) -> str:
    """Get human-readable bus type label"""
    labels = {
        BusType.ORDINARY: "Ordinary",
        BusType.SEMI_DELUXE: "Semi Deluxe",
        BusType.DELUXE: "Deluxe",
        BusType.AC_SEATER: "AC Seater",
        BusType.AC_SLEEPER: "AC Sleeper",
        BusType.NON_AC_SLEEPER: "Non-AC Sleeper",
        BusType.VOLVO: "Volvo / Premium AC",
        BusType.MULTI_AXLE: "Multi-Axle AC",
    }
    return labels.get(bus_type, "Standard")


def route_to_offers(
    route: BusRoute,
    departure_date: str,
    search_id: str,
) -> List[BusOffer]:
    """Convert a BusRoute to multiple BusOffers (one per bus type)"""
    
    offers = []
    dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
    
    # Create offers for each fare type
    for bus_type_str, fare in route.fares.items():
        bus_type = bus_type_to_enum(bus_type_str)
        
        # Parse first departure time
        first_dep_hour, first_dep_min = map(int, route.first_departure.split(":"))
        departure_dt = dep_date.replace(hour=first_dep_hour, minute=first_dep_min)
        
        # Calculate arrival
        arrival_dt = departure_dt + timedelta(minutes=route.avg_duration_minutes)
        
        # Determine if AC/sleeper based on bus type
        is_ac = bus_type in [BusType.AC_SEATER, BusType.AC_SLEEPER, BusType.VOLVO, BusType.MULTI_AXLE]
        is_sleeper = bus_type in [BusType.AC_SLEEPER, BusType.NON_AC_SLEEPER]
        
        # Find primary operator for this bus type
        operator_name = "Multiple Operators"
        operator_type = "private"
        for op in route.operators:
            if bus_type_str in op.get("bus_types", []):
                operator_name = op["name"]
                operator_type = op["type"]
                break
        
        # Build booking partner URLs
        booking_partners = []
        origin_slug = route.origin_city.lower().replace(" ", "-")
        dest_slug = route.destination_city.lower().replace(" ", "-")
        
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
        
        offer = BusOffer(
            offer_id=f"{search_id}-{route.route_id}-{bus_type_str}",
            mode=TransportMode.BUS,
            provider="static_data",
            
            # Route
            from_station=get_city_code(route.origin_city),
            from_city=route.origin_city,
            from_station_name=route.origin_stop,
            to_station=get_city_code(route.destination_city),
            to_city=route.destination_city,
            to_station_name=route.destination_stop,
            
            # Timing
            departure_time=departure_dt,
            arrival_time=arrival_dt,
            duration_minutes=route.avg_duration_minutes,
            
            # Pricing
            avg_price=float(fare),
            currency="INR",
            price_label="Average Fare",
            price_disclaimer="Average fare shown for reference. Actual price varies by operator and availability. Book on official partner sites.",
            
            # Distance
            distance_km=float(route.distance_km),
            
            # Booking
            booking_partners=booking_partners,
            is_fallback=False,
            
            # Bus specific
            operator_name=operator_name,
            operator_type=operator_type,
            bus_type=bus_type,
            bus_type_label=get_bus_type_label(bus_type),
            is_ac=is_ac,
            is_sleeper=is_sleeper,
            has_charging_point=is_ac,  # Assume AC buses have charging
            has_wifi=bus_type in [BusType.VOLVO, BusType.MULTI_AXLE],
            frequency=route.frequency,
            departure_window=f"{route.first_departure} - {route.last_departure}",
            stops_count=0,  # Not tracked in static data
            intermediate_stops=[],
        )
        
        offers.append(offer)
    
    return offers


def create_fallback_offer(
    origin: str,
    destination: str,
    departure_date: str,
    search_id: str,
    distance_km: Optional[int] = None,
) -> BusOffer:
    """Create a fallback redirect offer when no route data exists"""
    
    origin_city = normalize_city(origin)
    dest_city = normalize_city(destination)
    
    # Estimate distance if not provided
    if not distance_km:
        distance_km = get_distance(origin, destination) or 300  # Default estimate
    
    # Calculate estimated fares
    estimated_ordinary = calculate_average_fare(distance_km, "ordinary")
    estimated_ac = calculate_average_fare(distance_km, "ac_seater")
    estimated_sleeper = calculate_average_fare(distance_km, "ac_sleeper")
    
    dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
    
    # Build booking partner URLs
    booking_partners = []
    origin_slug = origin_city.lower().replace(" ", "-")
    dest_slug = dest_city.lower().replace(" ", "-")
    
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
    
    return BusOffer(
        offer_id=f"{search_id}-fallback",
        mode=TransportMode.BUS,
        provider="redirect",
        
        # Route
        from_station=get_city_code(origin),
        from_city=origin_city,
        from_station_name=f"{origin_city} Bus Stand",
        to_station=get_city_code(destination),
        to_city=dest_city,
        to_station_name=f"{dest_city} Bus Stand",
        
        # Timing (placeholder)
        departure_time=dep_date.replace(hour=0, minute=0),
        arrival_time=dep_date.replace(hour=0, minute=0),
        duration_minutes=0,
        
        # Pricing (estimated range)
        avg_price=float(estimated_ordinary),
        currency="INR",
        price_label="Estimated Fare Range",
        price_disclaimer=f"Route not in our database. Estimated fares: Ordinary ₹{estimated_ordinary}, AC ₹{estimated_ac}, Sleeper ₹{estimated_sleeper}. Check booking partners for exact prices.",
        
        # Distance
        distance_km=float(distance_km),
        
        # Booking
        booking_partners=booking_partners,
        is_fallback=True,
        
        # Bus specific (unknown for fallback)
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


async def search_buses(request: BusSearchRequest) -> BusSearchResponse:
    """
    Search for buses between two cities.
    
    Returns:
        - Real offers if route exists in database
        - Fallback redirect offer if route not found
        - Never returns empty results
    """
    search_id = str(uuid.uuid4())
    
    # Normalize inputs
    origin = normalize_city(request.origin)
    destination = normalize_city(request.destination)
    
    logger.info(f"🚌 Bus search: {origin} → {destination} on {request.departure_date}")
    
    # Try to find route data
    route = get_bus_route(origin, destination)
    
    if route:
        # Convert route to offers
        offers = route_to_offers(route, request.departure_date, search_id)
        
        # Apply optional filters
        if request.ac_only:
            offers = [o for o in offers if o.is_ac]
        
        if request.sleeper_only:
            offers = [o for o in offers if o.is_sleeper]
        
        if request.bus_type:
            target_type = bus_type_to_enum(request.bus_type)
            offers = [o for o in offers if o.bus_type == target_type]
        
        # Sort by price (lowest first)
        offers.sort(key=lambda o: o.avg_price)
        
        logger.info(f"✅ Found {len(offers)} bus options for {origin} → {destination}")
        
        return BusSearchResponse(
            offers=offers,
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
        fallback_offer = create_fallback_offer(
            origin=origin,
            destination=destination,
            departure_date=request.departure_date,
            search_id=search_id,
            distance_km=distance,
        )
        
        return BusSearchResponse(
            offers=[fallback_offer],
            search_id=search_id,
            cached=False,
            timestamp=datetime.utcnow(),
            origin_city=origin,
            destination_city=destination,
            distance_km=float(distance) if distance else None,
            is_fallback=True,
            fallback_message=f"We don't have detailed schedule data for this route. Please check our booking partners (redBus, AbhiBus, Paytm) for current buses, timings, and prices.",
        )

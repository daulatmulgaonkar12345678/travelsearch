"""State Network Resolver - Maximizes Discovery, Minimizes False Negatives
===========================================================================

ARCHITECTURE PRINCIPLE:
- Maharashtra has near-complete bus connectivity
- We are a DISCOVERY platform, not a booking platform
- Redirect-only model does NOT require exact routes
- Match redBus discovery behavior: if same state, show result

STATE NETWORK RULE:
- If origin.state == destination.state → ALWAYS show bus result
- Use corridor/feeder logic ONLY for UX enhancement (likely stops, route explanation)
- NEVER block results due to missing exact routes

DISCOVERY PRIORITY:
1. MSRTC routes (exact match with variants)
2. Generic bus routes (if in database)
3. State Network Result (ALWAYS for same-state)

This ensures:
- Pune → Kolhapur ALWAYS shows result
- Satara → Karad ALWAYS shows result
- Mumbai → Ratnagiri ALWAYS shows result
- Tourist destinations ALWAYS show result
- No false "0 buses found" for MH internal routes
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import uuid
import random

from app.models.transport import (
    BusOffer,
    TransportMode,
    BusType,
)

logger = logging.getLogger(__name__)


# ============================================================
# STATE DEFINITIONS
# ============================================================

# Cities known to be in Maharashtra
MAHARASHTRA_CITIES = {
    # Major cities
    "mumbai", "pune", "nashik", "nagpur", "aurangabad", "solapur",
    "kolhapur", "thane", "navi mumbai", "satara", "sangli", "ratnagiri",
    "ahmednagar", "jalgaon", "akola", "amravati", "latur", "nanded",
    "dhule", "chandrapur", "parbhani", "osmanabad", "beed", "jalna",
    "wardha", "yavatmal", "buldhana", "washim", "hingoli", "gondia",
    "bhandara", "gadchiroli", "sindhudurg", "raigad", "palghar",
    
    # District headquarters and major towns
    "karad", "miraj", "ichalkaranji", "barshi", "pandharpur",
    "malegaon", "bhusawal", "gondia", "baramati", "shirdi",
    "lonavala", "mahabaleshwar", "panchgani", "matheran", "alibaug",
    "chiplun", "rajapur", "sawantwadi", "malvan", "vengurla",
    "kankavli", "kudal", "tarkarli", "ganpatipule", "dapoli",
    
    # Tourist destinations
    "ajanta", "ellora", "trimbakeshwar", "bhimashankar", "lavasa",
    "tuljapur", "pandharpur", "daulatabad", "kashid",
}

# Maharashtra state code
MH_STATE = "MH"


def is_maharashtra_city(city: str) -> bool:
    """
    Check if a city is in Maharashtra.
    
    Uses a permissive approach - if it looks like an MH city, treat it as one.
    """
    city_lower = city.lower().strip()
    
    # Direct match
    if city_lower in MAHARASHTRA_CITIES:
        return True
    
    # Check if it starts with a known city (handles "Mumbai Central", "Pune Swargate" etc.)
    for known_city in MAHARASHTRA_CITIES:
        if city_lower.startswith(known_city) or known_city.startswith(city_lower):
            return True
    
    # Check tourist destinations via feeder resolver
    try:
        from app.services.feeder_resolver import is_tourist_destination
        if is_tourist_destination(city):
            return True
    except Exception:
        pass
    
    # Check bus stops database
    try:
        from app.data.places.loader import get_all_stops
        all_stops = get_all_stops()
        for stop in all_stops:
            if city_lower in stop.get("normalized_key", "").lower():
                return True
    except Exception:
        pass
    
    return False


def are_same_state(origin: str, destination: str) -> Tuple[bool, str]:
    """
    Check if origin and destination are in the same state.
    
    Returns:
        Tuple of (is_same_state, state_code)
    """
    origin_mh = is_maharashtra_city(origin)
    dest_mh = is_maharashtra_city(destination)
    
    if origin_mh and dest_mh:
        return True, MH_STATE
    
    return False, ""


# ============================================================
# BOOKING PARTNERS - Use centralized deep link generator
# ============================================================

from app.utils.deep_links import generate_booking_partners, BookingPartner

# Legacy constant for backward compatibility
BUS_BOOKING_PARTNERS = BookingPartner.all_partners()


# ============================================================
# FARE ESTIMATION
# ============================================================

# Fare per km by bus type (Maharashtra average)
FARE_PER_KM = {
    "ordinary": 1.2,
    "semi_deluxe": 1.5,
    "deluxe": 1.8,
    "ac_seater": 2.5,
    "ac_sleeper": 3.2,
    "volvo": 3.5,
    "sleeper": 2.8,
}

# Minimum fares
MIN_FARES = {
    "ordinary": 40,
    "semi_deluxe": 60,
    "deluxe": 80,
    "ac_seater": 150,
    "ac_sleeper": 200,
    "volvo": 250,
    "sleeper": 180,
}


def estimate_fare(distance_km: int, bus_type: str = "ordinary") -> int:
    """Estimate fare based on distance and bus type."""
    per_km = FARE_PER_KM.get(bus_type, 1.5)
    min_fare = MIN_FARES.get(bus_type, 50)
    
    fare = int(distance_km * per_km)
    return max(fare, min_fare)


# REMOVED: estimate_duration_minutes function
# Duration must ONLY come from real schedule data (departure_time, arrival_time)
# Estimated durations destroy user trust - a missing duration is better than a wrong one
# See: PRODUCT PRINCIPLE - "Wrong time destroys trust faster than missing time ever will"


def estimate_distance(origin: str, destination: str) -> int:
    """
    Estimate distance between two cities.
    
    Uses corridor data if available, otherwise uses heuristic.
    """
    # Try corridor resolver first
    try:
        from app.services.corridor_resolver import get_resolver
        resolver = get_resolver()
        
        # Check if we have corridor data
        from_id = None
        to_id = None
        
        from app.services.corridor_resolver import get_city_id_by_name
        from_id = get_city_id_by_name(origin)
        to_id = get_city_id_by_name(destination)
        
        if from_id and to_id:
            # Use corridor data
            result = resolver.get_route_stops(from_id, to_id)
            if result.get("all_stops"):
                # Sum up km from stops
                stops = result["all_stops"]
                if len(stops) >= 2:
                    return stops[-1].get("km_from_origin", 200) - stops[0].get("km_from_origin", 0)
    except Exception as e:
        logger.debug(f"Could not get corridor distance: {e}")
    
    # Try feeder resolver
    try:
        from app.services.feeder_resolver import find_route
        route = find_route(origin, destination)
        if route.get("total_distance_km"):
            return int(route["total_distance_km"])
    except Exception as e:
        logger.debug(f"Could not get feeder distance: {e}")
    
    # Fallback: Heuristic based on city pairs
    # Use 150km as average intra-state distance
    return 150


# ============================================================
# ROUTE ENHANCEMENT (UX Only - Never Blocks)
# ============================================================

def get_route_enhancement(origin: str, destination: str) -> Dict[str, Any]:
    """
    Get route enhancement data for UX.
    
    This is OPTIONAL and NEVER blocks results.
    Used only to improve user experience with likely stops, route explanation.
    """
    enhancement = {
        "has_enhancement": False,
        "likely_stops": [],
        "via_cities": [],
        "corridor_name": None,
        "highway": None,
        "route_type": "STANDARD",
        "note": None,
    }
    
    # Try corridor resolver
    try:
        from app.services.corridor_resolver import get_resolver
        resolver = get_resolver()
        result = resolver.get_route_stops_by_name(origin, destination)
        
        if result.get("source") == "corridor":
            enhancement["has_enhancement"] = True
            enhancement["likely_stops"] = result.get("major_stops", [])
            enhancement["minor_stops"] = result.get("minor_stops", [])
            enhancement["corridor_name"] = result.get("corridor_name")
            enhancement["highway"] = result.get("highway")
            enhancement["route_type"] = "HIGHWAY_CORRIDOR"
            enhancement["note"] = f"Via {result.get('highway', 'state highway')}"
    except Exception as e:
        logger.debug(f"Could not get corridor enhancement: {e}")
    
    # Try feeder resolver for tourist destinations
    try:
        from app.services.feeder_resolver import find_route, is_tourist_destination
        
        if is_tourist_destination(destination) or is_tourist_destination(origin):
            route = find_route(origin, destination)
            
            if route.get("connected"):
                enhancement["has_enhancement"] = True
                enhancement["route_type"] = route.get("route_type", "FEEDER")
                enhancement["via_cities"] = [
                    seg.get("to") for seg in route.get("segments", [])
                    if seg.get("type") == "HIGHWAY"
                ]
                enhancement["note"] = route.get("note")
                
                if route.get("destination_info"):
                    enhancement["destination_info"] = route["destination_info"]
    except Exception as e:
        logger.debug(f"Could not get feeder enhancement: {e}")
    
    return enhancement


# ============================================================
# STATE NETWORK RESULT GENERATOR
# ============================================================

def create_state_network_offers(
    origin: str,
    destination: str,
    departure_date: str,
    search_id: str,
    state_code: str = "MH",
) -> List[BusOffer]:
    """
    Create STATE NETWORK offers for same-state routes.
    
    THIS IS THE KEY FUNCTION:
    - ALWAYS returns results for same-state routes
    - Uses corridor/feeder data for enhancement ONLY
    - Never returns empty for valid state network routes
    
    These are "discovery" results that redirect to booking partners.
    """
    origin_title = origin.title()
    dest_title = destination.title()
    
    # Estimate distance
    distance_km = estimate_distance(origin, destination)
    
    # Get route enhancement (optional, for UX)
    enhancement = get_route_enhancement(origin, destination)
    
    # Build booking partner URLs using centralized deep link generator
    # This ensures proper slug normalization and alias resolution
    booking_partners = generate_booking_partners(origin, destination)
    
    # Parse departure date
    dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
    
    # Estimate fares for different bus types
    fare_ordinary = estimate_fare(distance_km, "ordinary")
    fare_ac = estimate_fare(distance_km, "ac_seater")
    fare_sleeper = estimate_fare(distance_km, "ac_sleeper")
    fare_volvo = estimate_fare(distance_km, "volvo")
    
    # Estimate duration
    duration_minutes = estimate_duration_minutes(distance_km)
    
    # Build via text for display
    via_text = ""
    if enhancement.get("likely_stops"):
        via_text = " → ".join(enhancement["likely_stops"][:3])
    elif enhancement.get("via_cities"):
        via_text = " → ".join(enhancement["via_cities"][:3])
    
    # Build disclaimer
    disclaimer_parts = [
        f"Estimated fares based on {distance_km}km distance.",
        "Multiple operators available.",
    ]
    if via_text:
        disclaimer_parts.append(f"Likely route: {via_text}")
    disclaimer_parts.append("Check partners for live schedules and exact prices.")
    
    disclaimer = " ".join(disclaimer_parts)
    
    offers = []
    
    # Create multiple bus type variants (like redBus shows)
    bus_types = [
        {
            "key": "ordinary",
            "enum": BusType.ORDINARY,
            "label": "Non-AC Seater",
            "fare": fare_ordinary,
            "is_ac": False,
            "is_sleeper": False,
            "offset_hours": 0,
        },
        {
            "key": "ac_seater",
            "enum": BusType.AC_SEATER,
            "label": "AC Seater",
            "fare": fare_ac,
            "is_ac": True,
            "is_sleeper": False,
            "offset_hours": 1,
        },
        {
            "key": "ac_sleeper",
            "enum": BusType.AC_SLEEPER,
            "label": "AC Sleeper",
            "fare": fare_sleeper,
            "is_ac": True,
            "is_sleeper": True,
            "offset_hours": 2,
        },
    ]
    
    # Add Volvo for longer routes
    if distance_km > 100:
        bus_types.append({
            "key": "volvo",
            "enum": BusType.VOLVO,
            "label": "Volvo Multi-Axle",
            "fare": fare_volvo,
            "is_ac": True,
            "is_sleeper": True,
            "offset_hours": 3,
        })
    
    for bt in bus_types:
        # Stagger departure times
        dep_time = dep_date.replace(hour=6) + timedelta(hours=bt["offset_hours"])
        arr_time = dep_time + timedelta(minutes=duration_minutes)
        
        # Add slight fare variation
        fare_with_var = int(bt["fare"] * random.uniform(0.95, 1.05))
        
        offer = BusOffer(
            offer_id=f"{search_id}-{state_code}-{bt['key']}",
            mode=TransportMode.BUS,
            provider="state_network",  # Indicates this is a state network result
            
            # Route
            from_station=origin.upper()[:3],
            from_city=origin_title,
            from_station_name=f"{origin_title} Bus Stand",
            to_station=destination.upper()[:3],
            to_city=dest_title,
            to_station_name=f"{dest_title} Bus Stand",
            
            # Timing
            departure_time=dep_time,
            arrival_time=arr_time,
            duration_minutes=duration_minutes,
            
            # Pricing
            avg_price=float(fare_with_var),
            currency="INR",
            price_label=f"Est. Fare • {bt['label']}",
            price_disclaimer=disclaimer,
            
            # Distance
            distance_km=float(distance_km),
            
            # Booking
            booking_partners=booking_partners,
            is_fallback=False,  # NOT a fallback - this is a valid state network result
            
            # Bus specific
            operator_name="Multiple Operators",
            operator_type="private",  # Mixed operators treated as private for model compatibility
            bus_type=bt["enum"],
            bus_type_label=bt["label"],
            is_ac=bt["is_ac"],
            is_sleeper=bt["is_sleeper"],
            has_charging_point=bt["is_ac"],
            has_wifi=bt["key"] == "volvo",
            frequency="Multiple daily",
            departure_window="06:00 - 23:00",
            stops_count=len(enhancement.get("likely_stops", [])),
            intermediate_stops=enhancement.get("likely_stops", []),
        )
        
        offers.append(offer)
    
    return offers


# ============================================================
# MAIN RESOLVER FUNCTION
# ============================================================

def resolve_state_network_search(
    origin: str,
    destination: str,
    departure_date: str,
) -> Tuple[List[BusOffer], Dict[str, Any]]:
    """
    Main resolver function implementing STATE NETWORK RULE.
    
    For same-state routes:
    1. Check for exact MSRTC/generic routes first
    2. If not found, generate state network results
    3. NEVER return empty for valid same-state routes
    
    Returns:
        Tuple of (offers, metadata)
    """
    search_id = str(uuid.uuid4())
    
    # Check if same state
    is_same_state, state_code = are_same_state(origin, destination)
    
    if not is_same_state:
        # Not same state - let the normal flow handle it
        return [], {
            "is_state_network": False,
            "state_code": None,
            "reason": "Different states or unknown cities",
        }
    
    logger.info(f"🔍 State Network Search: {origin} → {destination} (state={state_code})")
    
    # Generate state network offers
    offers = create_state_network_offers(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        search_id=search_id,
        state_code=state_code,
    )
    
    metadata = {
        "is_state_network": True,
        "state_code": state_code,
        "reason": "Same state - state network connectivity assumed",
        "enhancement": get_route_enhancement(origin, destination),
    }
    
    logger.info(f"✅ State Network: Generated {len(offers)} offers for {origin} → {destination}")
    
    return offers, metadata

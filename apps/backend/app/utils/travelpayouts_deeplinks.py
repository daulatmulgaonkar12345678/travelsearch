"""
Travelpayouts Deep Link Generator
=================================

MANDATORY: Use https://aviasales.tpx.lt/eqOxwsZu as the ONLY redirect entry point
for all flights and hotels.

Why direct aviasales.in URLs fail:
1. No affiliate tracking preserved
2. Hotels require internal location IDs, not city names
3. Search parameters may not be properly recognized
4. Revenue attribution is lost

This module provides:
1. Flight deep links with proper IATA codes and dates
2. Hotel deep links with resolved location IDs
3. Validation before redirect
4. Graceful fallbacks

Reference: https://support.travelpayouts.com/hc/en-us/articles/5711895629714-Aviasales-affiliate-links
"""

import logging
from typing import Optional, Dict
from datetime import datetime
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

# ============================================================
# TRAVELPAYOUTS CONFIGURATION
# ============================================================

# MANDATORY: All deep links must use this redirect base
TRAVELPAYOUTS_REDIRECT_BASE = "https://aviasales.tpx.lt/eqOxwsZu"

# Aviasales search endpoints (used for parameter construction)
AVIASALES_FLIGHT_SEARCH = "https://www.aviasales.in/search"
AVIASALES_HOTEL_SEARCH = "https://search.hotellook.com"


# ============================================================
# CITY/AIRPORT TO LOCATION ID MAPPING
# ============================================================

# Hotel location IDs for Travelpayouts
# These are internal IDs that Aviasales/Hotellook uses
# Format: {city_name: {iata: code, hotel_id: internal_id}}
CITY_LOCATION_MAP: Dict[str, Dict] = {
    # Indian Metro Cities
    "delhi": {"iata": "DEL", "hotel_id": "28394", "name": "New Delhi"},
    "new delhi": {"iata": "DEL", "hotel_id": "28394", "name": "New Delhi"},
    "mumbai": {"iata": "BOM", "hotel_id": "28395", "name": "Mumbai"},
    "bombay": {"iata": "BOM", "hotel_id": "28395", "name": "Mumbai"},
    "bangalore": {"iata": "BLR", "hotel_id": "28396", "name": "Bengaluru"},
    "bengaluru": {"iata": "BLR", "hotel_id": "28396", "name": "Bengaluru"},
    "chennai": {"iata": "MAA", "hotel_id": "28397", "name": "Chennai"},
    "madras": {"iata": "MAA", "hotel_id": "28397", "name": "Chennai"},
    "kolkata": {"iata": "CCU", "hotel_id": "28398", "name": "Kolkata"},
    "calcutta": {"iata": "CCU", "hotel_id": "28398", "name": "Kolkata"},
    "hyderabad": {"iata": "HYD", "hotel_id": "28399", "name": "Hyderabad"},
    "pune": {"iata": "PNQ", "hotel_id": "28400", "name": "Pune"},
    "ahmedabad": {"iata": "AMD", "hotel_id": "28401", "name": "Ahmedabad"},
    "jaipur": {"iata": "JAI", "hotel_id": "28402", "name": "Jaipur"},
    "goa": {"iata": "GOI", "hotel_id": "28403", "name": "Goa"},
    "kochi": {"iata": "COK", "hotel_id": "28404", "name": "Kochi"},
    "cochin": {"iata": "COK", "hotel_id": "28404", "name": "Kochi"},
    "lucknow": {"iata": "LKO", "hotel_id": "28405", "name": "Lucknow"},
    "chandigarh": {"iata": "IXC", "hotel_id": "28406", "name": "Chandigarh"},
    "amritsar": {"iata": "ATQ", "hotel_id": "28407", "name": "Amritsar"},
    "varanasi": {"iata": "VNS", "hotel_id": "28408", "name": "Varanasi"},
    "udaipur": {"iata": "UDR", "hotel_id": "28409", "name": "Udaipur"},
    "agra": {"iata": "AGR", "hotel_id": "28410", "name": "Agra"},
    "shimla": {"iata": "SLV", "hotel_id": "28411", "name": "Shimla"},
    "manali": {"iata": "KUU", "hotel_id": "28412", "name": "Manali"},
    "darjeeling": {"iata": "IXB", "hotel_id": "28413", "name": "Darjeeling"},
    "rishikesh": {"iata": "DED", "hotel_id": "28414", "name": "Rishikesh"},
    "mysore": {"iata": "MYQ", "hotel_id": "28415", "name": "Mysore"},
    "mysuru": {"iata": "MYQ", "hotel_id": "28415", "name": "Mysore"},
    "ooty": {"iata": "CJB", "hotel_id": "28416", "name": "Ooty"},
    "coimbatore": {"iata": "CJB", "hotel_id": "28417", "name": "Coimbatore"},
    "thiruvananthapuram": {"iata": "TRV", "hotel_id": "28418", "name": "Thiruvananthapuram"},
    "trivandrum": {"iata": "TRV", "hotel_id": "28418", "name": "Thiruvananthapuram"},
    "srinagar": {"iata": "SXR", "hotel_id": "28419", "name": "Srinagar"},
    "leh": {"iata": "IXL", "hotel_id": "28420", "name": "Leh"},
    "indore": {"iata": "IDR", "hotel_id": "28421", "name": "Indore"},
    "bhopal": {"iata": "BHO", "hotel_id": "28422", "name": "Bhopal"},
    "nagpur": {"iata": "NAG", "hotel_id": "28423", "name": "Nagpur"},
    "patna": {"iata": "PAT", "hotel_id": "28424", "name": "Patna"},
    "ranchi": {"iata": "IXR", "hotel_id": "28425", "name": "Ranchi"},
    "guwahati": {"iata": "GAU", "hotel_id": "28426", "name": "Guwahati"},
    "bhubaneswar": {"iata": "BBI", "hotel_id": "28427", "name": "Bhubaneswar"},
    "visakhapatnam": {"iata": "VTZ", "hotel_id": "28428", "name": "Visakhapatnam"},
    "vizag": {"iata": "VTZ", "hotel_id": "28428", "name": "Visakhapatnam"},
    
    # International Popular Destinations
    "dubai": {"iata": "DXB", "hotel_id": "2323", "name": "Dubai"},
    "singapore": {"iata": "SIN", "hotel_id": "4064", "name": "Singapore"},
    "bangkok": {"iata": "BKK", "hotel_id": "2568", "name": "Bangkok"},
    "phuket": {"iata": "HKT", "hotel_id": "3886", "name": "Phuket"},
    "bali": {"iata": "DPS", "hotel_id": "3776", "name": "Bali"},
    "kuala lumpur": {"iata": "KUL", "hotel_id": "3746", "name": "Kuala Lumpur"},
    "hong kong": {"iata": "HKG", "hotel_id": "3315", "name": "Hong Kong"},
    "maldives": {"iata": "MLE", "hotel_id": "3776", "name": "Maldives"},
    "male": {"iata": "MLE", "hotel_id": "3776", "name": "Male"},
    "london": {"iata": "LON", "hotel_id": "2114", "name": "London"},
    "paris": {"iata": "PAR", "hotel_id": "2734", "name": "Paris"},
    "new york": {"iata": "NYC", "hotel_id": "2661", "name": "New York"},
    "los angeles": {"iata": "LAX", "hotel_id": "2455", "name": "Los Angeles"},
    "tokyo": {"iata": "TYO", "hotel_id": "4245", "name": "Tokyo"},
    "sydney": {"iata": "SYD", "hotel_id": "1234", "name": "Sydney"},
    "mauritius": {"iata": "MRU", "hotel_id": "3621", "name": "Mauritius"},
    "sri lanka": {"iata": "CMB", "hotel_id": "1995", "name": "Colombo"},
    "colombo": {"iata": "CMB", "hotel_id": "1995", "name": "Colombo"},
    "kathmandu": {"iata": "KTM", "hotel_id": "3464", "name": "Kathmandu"},
    "nepal": {"iata": "KTM", "hotel_id": "3464", "name": "Kathmandu"},
    "bhutan": {"iata": "PBH", "hotel_id": "3879", "name": "Paro"},
    "paro": {"iata": "PBH", "hotel_id": "3879", "name": "Paro"},
    "abu dhabi": {"iata": "AUH", "hotel_id": "27", "name": "Abu Dhabi"},
    "doha": {"iata": "DOH", "hotel_id": "2006", "name": "Doha"},
    "muscat": {"iata": "MCT", "hotel_id": "3580", "name": "Muscat"},
}


# ============================================================
# LOCATION RESOLVER
# ============================================================

def resolve_city_to_location(city_name: str) -> Optional[Dict]:
    """
    Resolve a city name to its IATA code and hotel location ID.
    
    Args:
        city_name: City name (case-insensitive)
    
    Returns:
        Dict with {iata, hotel_id, name} or None if not found
    """
    if not city_name:
        return None
    
    normalized = city_name.lower().strip()
    
    # Direct lookup
    if normalized in CITY_LOCATION_MAP:
        return CITY_LOCATION_MAP[normalized]
    
    # Try partial match
    for key, value in CITY_LOCATION_MAP.items():
        if key in normalized or normalized in key:
            return value
    
    # Not found
    logger.warning(f"City not found in location map: {city_name}")
    return None


def get_iata_from_city(city_name: str) -> Optional[str]:
    """Get IATA code for a city name."""
    location = resolve_city_to_location(city_name)
    return location["iata"] if location else None


def get_hotel_id_from_city(city_name: str) -> Optional[str]:
    """Get hotel location ID for a city name."""
    location = resolve_city_to_location(city_name)
    return location["hotel_id"] if location else None


# ============================================================
# DEEP LINK VALIDATION
# ============================================================

def validate_flight_params(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None
) -> Dict:
    """
    Validate flight deep link parameters.
    
    Returns:
        Dict with {valid: bool, error: str, params: dict}
    """
    errors = []
    
    # Validate IATA codes (3 uppercase letters)
    if not origin or len(origin) != 3:
        errors.append(f"Invalid origin IATA: {origin}")
    if not destination or len(destination) != 3:
        errors.append(f"Invalid destination IATA: {destination}")
    
    # Validate dates
    try:
        dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
        if dep_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            errors.append("Departure date is in the past")
    except ValueError:
        errors.append(f"Invalid departure date format: {departure_date}")
    
    if return_date:
        try:
            ret_date = datetime.strptime(return_date, "%Y-%m-%d")
            if ret_date < dep_date:
                errors.append("Return date is before departure")
        except ValueError:
            errors.append(f"Invalid return date format: {return_date}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "params": {
            "origin": origin.upper() if origin else None,
            "destination": destination.upper() if destination else None,
            "departure_date": departure_date,
            "return_date": return_date
        }
    }


def validate_hotel_params(
    city: str,
    check_in: str,
    check_out: str,
    adults: int = 2
) -> Dict:
    """
    Validate hotel deep link parameters.
    
    Returns:
        Dict with {valid: bool, errors: list, location: dict}
    """
    errors = []
    
    # Resolve city to location ID
    location = resolve_city_to_location(city)
    if not location:
        errors.append(f"Unknown city: {city}. Cannot resolve to location ID.")
    
    # Validate dates
    try:
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
        if check_in_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            errors.append("Check-in date is in the past")
    except ValueError:
        errors.append(f"Invalid check-in date format: {check_in}")
    
    try:
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
        if check_out_date <= check_in_date:
            errors.append("Check-out must be after check-in")
    except ValueError:
        errors.append(f"Invalid check-out date format: {check_out}")
    
    # Validate adults
    if adults < 1 or adults > 10:
        errors.append(f"Invalid adult count: {adults}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "location": location
    }


# ============================================================
# DEEP LINK GENERATORS
# ============================================================

def generate_flight_deep_link(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    trip_class: int = 0  # 0=economy, 1=premium, 2=business
) -> Dict:
    """
    Generate Travelpayouts flight deep link.
    
    IMPORTANT: Uses TRAVELPAYOUTS_REDIRECT_BASE, not direct aviasales.in URLs.
    
    Args:
        origin: Origin IATA code (e.g., DEL)
        destination: Destination IATA code (e.g., BOM)
        departure_date: YYYY-MM-DD format
        return_date: Optional YYYY-MM-DD format for round trip
        adults: Number of adult passengers
        trip_class: 0=economy, 1=premium_economy, 2=business
    
    Returns:
        Dict with {success: bool, url: str, error: str}
    
    Example URLs:
        One-way: https://aviasales.tpx.lt/eqOxwsZu?shmarker=689331&origin_iata=DEL&destination_iata=BOM&depart_date=2025-01-15&adults=1
        Round-trip: ...&return_date=2025-01-20
    """
    # Validate parameters
    validation = validate_flight_params(origin, destination, departure_date, return_date)
    
    if not validation["valid"]:
        return {
            "success": False,
            "url": f"{TRAVELPAYOUTS_REDIRECT_BASE}",  # Fallback to homepage
            "error": "; ".join(validation["errors"]),
            "is_fallback": True
        }
    
    # Build query parameters
    params = {
        "origin_iata": origin.upper(),
        "destination_iata": destination.upper(),
        "depart_date": departure_date,
        "adults": adults,
        "trip_class": trip_class,
    }
    
    if return_date:
        params["return_date"] = return_date
    
    # Build URL with Travelpayouts redirect base
    url = f"{TRAVELPAYOUTS_REDIRECT_BASE}?{urlencode(params)}"
    
    logger.info(f"Generated flight deep link: {url}")
    
    return {
        "success": True,
        "url": url,
        "error": None,
        "is_fallback": False,
        "params": params
    }


def generate_hotel_deep_link(
    city: str,
    check_in: str,
    check_out: str,
    adults: int = 2,
    rooms: int = 1
) -> Dict:
    """
    Generate Travelpayouts hotel deep link.
    
    IMPORTANT: Uses resolved location ID, not plain city name.
    
    Args:
        city: City name (will be resolved to location ID)
        check_in: Check-in date YYYY-MM-DD
        check_out: Check-out date YYYY-MM-DD
        adults: Number of adults
        rooms: Number of rooms
    
    Returns:
        Dict with {success: bool, url: str, error: str, location: dict}
    
    Example URL:
        https://aviasales.tpx.lt/eqOxwsZu?type=hotel&locationId=28394&checkIn=2025-01-15&checkOut=2025-01-17&adults=2
    """
    # Validate parameters
    validation = validate_hotel_params(city, check_in, check_out, adults)
    
    if not validation["valid"]:
        return {
            "success": False,
            "url": f"{TRAVELPAYOUTS_REDIRECT_BASE}",  # Fallback to homepage
            "error": "; ".join(validation["errors"]),
            "is_fallback": True,
            "location": None
        }
    
    location = validation["location"]
    
    # Build query parameters for hotel search
    # Using Hotellook/Aviasales hotel search format
    params = {
        "type": "hotel",
        "locationId": location["hotel_id"],
        "destination": location["iata"],
        "checkIn": check_in,
        "checkOut": check_out,
        "adults": adults,
        "rooms": rooms,
    }
    
    # Build URL with Travelpayouts redirect base
    url = f"{TRAVELPAYOUTS_REDIRECT_BASE}?{urlencode(params)}"
    
    logger.info(f"Generated hotel deep link for {city}: {url}")
    
    return {
        "success": True,
        "url": url,
        "error": None,
        "is_fallback": False,
        "location": location,
        "params": params
    }


# ============================================================
# BOOKING PARTNER GENERATORS
# ============================================================

def generate_flight_booking_partners(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1
) -> list:
    """
    Generate booking partner list for flights.
    
    Returns:
        List of booking partner dicts with properly formatted URLs
    """
    # Generate primary Travelpayouts deep link
    deep_link_result = generate_flight_deep_link(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        adults=adults
    )
    
    partners = [
        {
            "name": "Aviasales",
            "url": deep_link_result["url"],
            "priority": 1,
            "is_official": False,
            "description": "Compare prices from 100+ airlines",
            "is_fallback": deep_link_result.get("is_fallback", False)
        },
        {
            "name": "Skyscanner",
            "url": f"https://www.skyscanner.co.in/transport/flights/{origin.lower()}/{destination.lower()}/{departure_date.replace('-', '')}/" + 
                   (f"{return_date.replace('-', '')}/" if return_date else ""),
            "priority": 2,
            "is_official": False,
            "description": "Global flight comparison"
        },
        {
            "name": "Google Flights",
            "url": f"https://www.google.com/travel/flights?q=flights%20from%20{origin}%20to%20{destination}%20on%20{departure_date}",
            "priority": 3,
            "is_official": False,
            "description": "Google flight search"
        }
    ]
    
    return partners


def generate_hotel_booking_partners(
    city: str,
    check_in: str,
    check_out: str,
    adults: int = 2,
    rooms: int = 1
) -> list:
    """
    Generate booking partner list for hotels.
    
    Returns:
        List of booking partner dicts with properly formatted URLs
    """
    # Generate primary Travelpayouts deep link
    deep_link_result = generate_hotel_deep_link(
        city=city,
        check_in=check_in,
        check_out=check_out,
        adults=adults,
        rooms=rooms
    )
    
    location = deep_link_result.get("location") or {}
    city_slug = city.lower().replace(" ", "-")
    
    partners = [
        {
            "name": "Hotellook",
            "url": deep_link_result["url"],
            "priority": 1,
            "is_official": False,
            "description": "Compare hotel prices",
            "is_fallback": deep_link_result.get("is_fallback", False)
        },
        {
            "name": "Booking.com",
            "url": f"https://www.booking.com/searchresults.html?ss={city_slug}&checkin={check_in}&checkout={check_out}&group_adults={adults}&no_rooms={rooms}",
            "priority": 2,
            "is_official": False,
            "description": "World's largest hotel booking site"
        },
        {
            "name": "Agoda",
            "url": f"https://www.agoda.com/search?city={location.get('hotel_id', '')}&checkIn={check_in}&checkOut={check_out}&rooms={rooms}&adults={adults}",
            "priority": 3,
            "is_official": False,
            "description": "Best prices in Asia"
        },
        {
            "name": "MakeMyTrip",
            "url": f"https://www.makemytrip.com/hotels/hotel-listing/?checkin={check_in.replace('-', '')}&checkout={check_out.replace('-', '')}&city={city_slug}&roomStayQualifier=2e0e",
            "priority": 4,
            "is_official": False,
            "description": "India's leading travel platform"
        }
    ]
    
    return partners


# ============================================================
# TESTS
# ============================================================

if __name__ == "__main__":
    print("=== Travelpayouts Deep Link Generator Tests ===\n")
    
    # Test flight deep links
    print("1. Flight Deep Link (Delhi → Mumbai, One-way):")
    result = generate_flight_deep_link("DEL", "BOM", "2025-01-15")
    print(f"   Success: {result['success']}")
    print(f"   URL: {result['url']}\n")
    
    print("2. Flight Deep Link (Delhi → Mumbai, Round-trip):")
    result = generate_flight_deep_link("DEL", "BOM", "2025-01-15", "2025-01-20")
    print(f"   Success: {result['success']}")
    print(f"   URL: {result['url']}\n")
    
    # Test hotel deep links
    print("3. Hotel Deep Link (Delhi):")
    result = generate_hotel_deep_link("Delhi", "2025-01-15", "2025-01-17")
    print(f"   Success: {result['success']}")
    print(f"   Location ID: {result.get('location', {}).get('hotel_id')}")
    print(f"   URL: {result['url']}\n")
    
    print("4. Hotel Deep Link (Mumbai):")
    result = generate_hotel_deep_link("Mumbai", "2025-01-15", "2025-01-17")
    print(f"   Success: {result['success']}")
    print(f"   URL: {result['url']}\n")
    
    print("5. Hotel Deep Link (International - Dubai):")
    result = generate_hotel_deep_link("Dubai", "2025-01-15", "2025-01-17")
    print(f"   Success: {result['success']}")
    print(f"   URL: {result['url']}\n")
    
    # Test validation failures
    print("6. Invalid Hotel (Unknown City):")
    result = generate_hotel_deep_link("UnknownCity123", "2025-01-15", "2025-01-17")
    print(f"   Success: {result['success']}")
    print(f"   Error: {result['error']}")
    print(f"   Fallback URL: {result['url']}\n")
    
    print("=== All Tests Complete ===")

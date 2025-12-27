"""Bus Search Service

Provides bus search functionality using static official data.
No scraping, no live availability - only average fares from government sources.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.models.transport import BusOffer, BusSearchRequest, BusSearchResponse, TransportMode, BusType
from app.data.stations import get_bus_stop, CITY_TO_BUS_STOP, BUS_STOPS
from app.data.bus_routes import (
    get_bus_route,
    get_distance,
    calculate_average_fare,
    BusRoute
)

logger = logging.getLogger(__name__)

# Booking partner URLs for buses
BUS_BOOKING_PARTNERS = [
    {
        "name": "redBus",
        "url": "https://www.redbus.in",
        "priority": 1,
        "description": "India's largest bus booking platform"
    },
    {
        "name": "AbhiBus",
        "url": "https://www.abhibus.com",
        "priority": 2,
        "description": "Book bus tickets online"
    },
    {
        "name": "Paytm Bus",
        "url": "https://paytm.com/bus-tickets",
        "priority": 3,
        "description": "Fast booking with Paytm"
    },
    {
        "name": "PhonePe Bus",
        "url": "https://www.phonepe.com/bus",
        "priority": 4,
        "description": "Book with PhonePe"
    },
]

# Bus type display names
BUS_TYPE_LABELS = {
    "ordinary": "Ordinary",
    "deluxe": "Deluxe",
    "semi_deluxe": "Semi Deluxe",
    "ac_seater": "AC Seater",
    "ac_sleeper": "AC Sleeper",
    "non_ac_sleeper": "Non-AC Sleeper",
    "volvo": "Volvo Multi-Axle",
    "multi_axle": "Multi-Axle",
    "shivneri": "Shivneri (MSRTC)",
    "airavat": "Airavat (KSRTC)",
    "rajahamsa": "Rajahamsa (KSRTC)",
    "garuda": "Garuda (TSRTC)",
}


def normalize_city(city: str) -> str:
    """Normalize city name to route key format"""
    city_map = {
        "delhi": "DEL", "new delhi": "DEL",
        "mumbai": "MUM", "bombay": "MUM",
        "bangalore": "BLR", "bengaluru": "BLR",
        "chennai": "CHE", "madras": "CHE",
        "hyderabad": "HYD",
        "pune": "PUN",
        "goa": "GOA", "panaji": "GOA",
        "jaipur": "JAI",
        "agra": "AGR",
        "chandigarh": "CHD",
        "ahmedabad": "AMD",
        "mysore": "MYS", "mysuru": "MYS",
        "coimbatore": "COI",
    }
    return city_map.get(city.lower().strip(), city.upper()[:3])


def get_bus_type_enum(bus_type_str: str) -> BusType:
    """Convert string bus type to BusType enum"""
    mapping = {
        "ordinary": BusType.ORDINARY,
        "deluxe": BusType.DELUXE,
        "semi_deluxe": BusType.SEMI_DELUXE,
        "ac_seater": BusType.AC_SEATER,
        "ac_sleeper": BusType.AC_SLEEPER,
        "non_ac_sleeper": BusType.NON_AC_SLEEPER,
        "volvo": BusType.VOLVO,
        "multi_axle": BusType.MULTI_AXLE,
        "shivneri": BusType.AC_SEATER,
        "airavat": BusType.VOLVO,
        "rajahamsa": BusType.DELUXE,
        "garuda": BusType.VOLVO,
    }
    return mapping.get(bus_type_str, BusType.ORDINARY)


def convert_route_to_offers(
    route: BusRoute,
    departure_date: str
) -> List[BusOffer]:
    """Convert a BusRoute to multiple BusOffers (one per bus type)"""
    
    offers = []
    dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
    
    # Create an offer for each fare type
    for bus_type, fare in route.fares.items():
        # Parse first departure time
        first_hour, first_min = map(int, route.first_departure.split(':'))
        dep_datetime = dep_date.replace(hour=first_hour, minute=first_min)
        arr_datetime = dep_datetime + timedelta(minutes=route.avg_duration_minutes)
        
        bus_type_enum = get_bus_type_enum(bus_type)
        is_ac = bus_type in ["ac_seater", "ac_sleeper", "volvo", "multi_axle", "shivneri", "airavat"]
        is_sleeper = "sleeper" in bus_type
        
        # Find operator for this bus type
        operator_name = "Various"
        operator_type = "private"
        for op in route.operators:
            if bus_type in op.get("bus_types", []):
                operator_name = op["name"]
                operator_type = op.get("type", "private")
                break
        
        offer = BusOffer(
            offer_id=f"bus_{route.route_id}_{bus_type}_{departure_date}",
            mode=TransportMode.BUS,
            provider="static_rtc_data",
            
            # Route info
            from_station=route.origin_stop,
            from_city=route.origin_city,
            from_station_name=route.origin_stop,
            to_station=route.destination_stop,
            to_city=route.destination_city,
            to_station_name=route.destination_stop,
            
            # Timing
            departure_time=dep_datetime,
            arrival_time=arr_datetime,
            duration_minutes=route.avg_duration_minutes,
            
            # Pricing
            avg_price=fare,
            currency="INR",
            price_label="Average Fare",
            price_disclaimer="Average fare shown for reference. Actual price may vary based on operator and availability.",
            
            # Distance
            distance_km=route.distance_km,
            
            # Bus specific
            operator_name=operator_name,
            operator_type=operator_type,
            bus_type=bus_type_enum,
            bus_type_label=BUS_TYPE_LABELS.get(bus_type, bus_type.replace('_', ' ').title()),
            is_ac=is_ac,
            is_sleeper=is_sleeper,
            frequency=route.frequency,
            departure_window=f"{route.first_departure} - {route.last_departure}",
            
            # Booking partners
            booking_partners=BUS_BOOKING_PARTNERS,
            
            # Not a fallback
            is_fallback=False,
        )
        offers.append(offer)
    
    return offers


def create_fallback_offer(
    origin: str,
    destination: str,
    departure_date: str,
    distance_km: Optional[int] = None
) -> BusOffer:
    """Create a fallback offer when no route data is available"""
    
    # Estimate distance if not provided
    if not distance_km:
        distance_km = get_distance(origin, destination) or 300  # Default 300km
    
    # Calculate average fare
    avg_price = calculate_average_fare(distance_km, "ordinary")
    
    dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
    dep_datetime = dep_date.replace(hour=6, minute=0)  # Placeholder
    arr_datetime = dep_datetime + timedelta(hours=int(distance_km / 50))  # ~50 km/h avg
    
    return BusOffer(
        offer_id=f"bus_fallback_{origin}_{destination}_{departure_date}",
        mode=TransportMode.BUS,
        provider="fallback",
        
        # Route info
        from_station="Bus Terminal",
        from_city=origin.title(),
        from_station_name=f"{origin.title()} Bus Stand",
        to_station="Bus Terminal",
        to_city=destination.title(),
        to_station_name=f"{destination.title()} Bus Stand",
        
        # Timing (placeholder)
        departure_time=dep_datetime,
        arrival_time=arr_datetime,
        duration_minutes=int((distance_km / 50) * 60),
        
        # Pricing
        avg_price=avg_price,
        currency="INR",
        price_label="Estimated Fare",
        price_disclaimer="Estimated fare based on distance. Please check booking sites for accurate prices.",
        
        # Distance
        distance_km=distance_km,
        
        # Bus specific (generic)
        operator_name="Various Operators",
        operator_type="private",
        bus_type=BusType.ORDINARY,
        bus_type_label="View bus options",
        is_ac=False,
        is_sleeper=False,
        frequency="Multiple services available",
        departure_window="05:00 - 23:00",
        
        # Booking partners
        booking_partners=BUS_BOOKING_PARTNERS,
        
        # This is a fallback
        is_fallback=True,
    )


async def search_buses(request: BusSearchRequest) -> BusSearchResponse:
    """Search for buses between two cities"""
    
    logger.info(f"🚌 Bus search: {request.origin} → {request.destination} on {request.departure_date}")
    
    # Normalize city names
    origin = request.origin.strip()
    destination = request.destination.strip()
    
    # Try to find bus route
    route = get_bus_route(origin, destination)
    
    offers: List[BusOffer] = []
    is_fallback = False
    fallback_message = None
    
    if route:
        # We have route data
        offers = convert_route_to_offers(route, request.departure_date)
        
        # Apply filters if specified
        if request.ac_only:
            offers = [o for o in offers if o.is_ac]
        if request.sleeper_only:
            offers = [o for o in offers if o.is_sleeper]
        if request.bus_type:
            offers = [o for o in offers if request.bus_type.lower() in o.bus_type_label.lower()]
        
        if not offers:
            # Filters removed all options
            fallback_message = "No buses match your filters. Showing all available options on booking sites."
            is_fallback = True
            offers.append(create_fallback_offer(
                origin,
                destination,
                request.departure_date,
                route.distance_km
            ))
    else:
        # No route data - create fallback
        logger.info(f"No route data for {origin} → {destination}, showing fallback")
        is_fallback = True
        fallback_message = "Detailed schedule not available for this route. Please check official booking sites."
        offers.append(create_fallback_offer(
            origin,
            destination,
            request.departure_date
        ))
    
    # Sort by price (cheapest first)
    offers.sort(key=lambda x: x.avg_price)
    
    # Get distance
    distance_km = route.distance_km if route else get_distance(origin, destination)
    
    return BusSearchResponse(
        offers=offers,
        search_id=str(uuid.uuid4()),
        cached=False,
        timestamp=datetime.utcnow(),
        origin_city=origin.title(),
        destination_city=destination.title(),
        distance_km=distance_km,
        is_fallback=is_fallback,
        fallback_message=fallback_message,
    )

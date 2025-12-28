"""MSRTC Service - Integrates scraper with application

Provides:
- Variant-level bus offers from MSRTC data
- Integration with existing bus search
- DB operations for stops and schedules
- Search matching for Marathi/English queries
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import random

from app.scrapers.msrtc_seed_data import (
    MSRTCRoute,
    MSRTC_BUS_TYPES,
    MSRTC_STOPS,
    get_msrtc_route,
    get_msrtc_stop,
    calculate_msrtc_fare,
    get_all_msrtc_stops,
    get_all_msrtc_routes,
)
from app.models.transport import (
    BusOffer,
    TransportMode,
    BusType,
)
from app.utils.deep_links import generate_booking_partners

logger = logging.getLogger(__name__)


# ============================================================
# BOOKING PARTNER - Now uses centralized deep_links.py
# ============================================================
# Note: MSRTC_BOOKING_PARTNERS constant removed in favor of
# generate_booking_partners() from app.utils.deep_links
# This ensures proper slug normalization and alias resolution


# Map MSRTC bus types to app's BusType enum
MSRTC_TO_APP_BUS_TYPE = {
    "ST": BusType.ORDINARY,
    "SEMI_LUX": BusType.SEMI_DELUXE,
    "ASIAD": BusType.AC_SEATER,
    "SHIVNERI": BusType.VOLVO,
    "SHIVSHAHI": BusType.AC_SLEEPER,
    "ASHWAMEDH": BusType.MULTI_AXLE,
}


def add_fare_variation(base_fare: int) -> int:
    """Add slight realistic variation to fares (±3%)"""
    variation = random.uniform(-0.03, 0.03)
    return int(base_fare * (1 + variation))


def msrtc_route_to_offers(
    route: MSRTCRoute,
    departure_date: str,
    search_id: str,
) -> List[BusOffer]:
    """
    VARIANT-LEVEL EXPANSION:
    Convert ONE MSRTC route into MULTIPLE offers - one per bus type.
    
    Example: Pune→Mumbai with bus_types=[ST, ASIAD, SHIVNERI, SHIVSHAHI]
    becomes 4 separate cards with different prices and features.
    """
    offers = []
    dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
    
    # Parse base departure time
    first_hour, first_min = map(int, route.first_departure.split(":"))
    base_departure = dep_date.replace(hour=first_hour, minute=first_min)
    
    # Build booking partner URLs using centralized deep link generator
    # This ensures proper slug normalization, alias resolution, and no undefined values
    booking_partners = generate_booking_partners(
        route.origin_english,
        route.destination_english
    )
    
    # CREATE ONE CARD PER BUS TYPE
    offset_minutes = 0
    for bus_type_key in route.bus_types:
        config = MSRTC_BUS_TYPES.get(bus_type_key)
        if not config:
            continue
        
        # Calculate fare for this bus type
        base_fare = calculate_msrtc_fare(route.base_fare, bus_type_key)
        fare_with_variation = add_fare_variation(base_fare)
        
        # Stagger departure times for different types
        departure_dt = base_departure + timedelta(minutes=offset_minutes)
        arrival_dt = departure_dt + timedelta(minutes=route.avg_duration_minutes)
        offset_minutes += 30  # 30 min between different bus types
        
        # Map to app's BusType enum
        app_bus_type = MSRTC_TO_APP_BUS_TYPE.get(bus_type_key, BusType.ORDINARY)
        
        offer = BusOffer(
            offer_id=f"{search_id}-{route.route_id}-{bus_type_key}",
            mode=TransportMode.BUS,
            provider="msrtc",
            
            # Route - with Marathi and English names
            from_station=route.origin_code,
            from_city=route.origin_english,
            from_station_name=f"{route.origin_station} ({route.origin_english})",
            to_station=route.destination_code,
            to_city=route.destination_english,
            to_station_name=f"{route.destination_station} ({route.destination_english})",
            
            # Timing - EACH TYPE HAS DIFFERENT DEPARTURE
            departure_time=departure_dt,
            arrival_time=arrival_dt,
            duration_minutes=route.avg_duration_minutes,
            
            # Pricing - THIS TYPE ONLY
            avg_price=float(fare_with_variation),
            currency="INR",
            price_label=f"Avg Fare • MSRTC {config['name_english']}",
            price_disclaimer=f"Average MSRTC {config['name_english']} fare. Book on official MSRTC site for exact price.",
            
            # Distance
            distance_km=float(route.distance_km),
            
            # Booking
            booking_partners=booking_partners,
            is_fallback=False,
            
            # Bus specific - THIS CARD IS FOR ONE TYPE ONLY
            operator_name="MSRTC",
            operator_type="government",
            bus_type=app_bus_type,
            bus_type_label=f"MSRTC {config['name_english']} ({config['name_marathi']})",
            is_ac=config["is_ac"],
            is_sleeper=config["is_sleeper"],
            has_charging_point=config["is_ac"],  # AC buses typically have charging
            has_wifi=bus_type_key in ["SHIVNERI", "ASHWAMEDH"],  # Premium buses
            frequency=route.frequency,
            departure_window=f"{route.first_departure} - {route.last_departure}",
            stops_count=len(route.via_stops),
            intermediate_stops=route.via_stops,
        )
        
        offers.append(offer)
    
    return offers


def search_msrtc_buses(
    origin: str,
    destination: str,
    departure_date: str,
) -> List[BusOffer]:
    """
    Search for MSRTC buses between two cities.
    
    Returns variant-level results (one card per bus type).
    Accepts Marathi, English, or code for origin/destination.
    
    Args:
        origin: Origin city (Marathi/English/code)
        destination: Destination city (Marathi/English/code)
        departure_date: Date in YYYY-MM-DD format
    
    Returns:
        List of BusOffer objects (one per bus type)
    """
    search_id = str(uuid.uuid4())
    
    logger.info(f"🚌 MSRTC search: {origin} → {destination} on {departure_date}")
    
    # Try to find MSRTC route
    route = get_msrtc_route(origin, destination)
    
    if route:
        offers = msrtc_route_to_offers(route, departure_date, search_id)
        logger.info(f"✅ Found {len(offers)} MSRTC bus type variants for {origin} → {destination}")
        return offers
    
    # No MSRTC route found
    logger.info(f"⚠️ No MSRTC route data for {origin} → {destination}")
    return []


# ============================================================
# DATABASE OPERATIONS (Async)
# ============================================================

async def save_msrtc_stops_to_db(db) -> int:
    """Save all MSRTC stops to MongoDB."""
    from datetime import datetime, timezone
    
    collection = db.msrtc_stops
    count = 0
    
    for stop in MSRTC_STOPS:
        stop_doc = {
            **stop,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }
        
        result = await collection.update_one(
            {"value": stop["value"]},
            {"$set": stop_doc},
            upsert=True,
        )
        if result.upserted_id or result.modified_count:
            count += 1
    
    logger.info(f"Saved {count} MSRTC stops to database")
    return count


async def save_msrtc_routes_to_db(db) -> int:
    """Save all MSRTC routes to MongoDB."""
    from datetime import datetime, timezone
    from dataclasses import asdict
    
    collection = db.msrtc_routes
    all_routes = get_all_msrtc_routes()
    count = 0
    
    for route in all_routes:
        route_doc = asdict(route)
        route_doc["scraped_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await collection.update_one(
            {"route_id": route.route_id},
            {"$set": route_doc},
            upsert=True,
        )
        if result.upserted_id or result.modified_count:
            count += 1
    
    logger.info(f"Saved {count} MSRTC routes to database")
    return count


async def get_msrtc_stops_from_db(db) -> List[Dict]:
    """Get all MSRTC stops from MongoDB."""
    collection = db.msrtc_stops
    stops = await collection.find({}, {"_id": 0}).to_list(1000)
    return stops


async def get_msrtc_routes_from_db(db) -> List[Dict]:
    """Get all MSRTC routes from MongoDB."""
    collection = db.msrtc_routes
    routes = await collection.find({}, {"_id": 0}).to_list(100)
    return routes


async def search_msrtc_stops(db, query: str) -> List[Dict]:
    """Search MSRTC stops by query (supports Marathi and English)."""
    collection = db.msrtc_stops
    
    # Case-insensitive search on English name and normalized name
    results = await collection.find(
        {
            "$or": [
                {"name_english": {"$regex": query, "$options": "i"}},
                {"name_normalized": {"$regex": query.lower(), "$options": "i"}},
                {"name_marathi": {"$regex": query}},
            ]
        },
        {"_id": 0}
    ).to_list(50)
    
    return results

"""
MSRTC Places Data Loader
========================
Loads and provides access to MSRTC bus stops data for Maharashtra.

This module provides:
- Loading of state, cities, and bus stops data
- Search functionality for stops (Marathi and English)
- Filtering by district, stop type, and search surface
- Distance-based fare calculation helpers

Data Structure:
- state.json: Maharashtra state info
- cities.json: All 36 districts
- bus_stops.json: 1000+ MSRTC stops with Marathi names

Usage:
    from app.data.places.loader import (
        get_all_stops,
        search_stops,
        get_stops_by_district,
        get_search_surface_stops,
    )
    
    # Get all stops
    stops = get_all_stops()
    
    # Search by query (Marathi or English)
    results = search_stops("पुणे")  # or search_stops("pune")
    
    # Get stops for a district
    pune_stops = get_stops_by_district(8)  # city_id=8 is Pune
"""

import json
import os
from typing import List, Dict, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Data directory path
DATA_DIR = os.path.join(os.path.dirname(__file__), "states", "MH")


@lru_cache(maxsize=1)
def load_state_data() -> Dict:
    """Load Maharashtra state data."""
    state_file = os.path.join(DATA_DIR, "state.json")
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load state data: {e}")
        return {"state_code": "MH", "state_name_en": "Maharashtra", "state_name_local": "महाराष्ट्र"}


@lru_cache(maxsize=1)
def load_cities_data() -> List[Dict]:
    """Load all Maharashtra districts/cities."""
    cities_file = os.path.join(DATA_DIR, "cities.json")
    try:
        with open(cities_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load cities data: {e}")
        return []


@lru_cache(maxsize=1)
def load_bus_stops_data() -> List[Dict]:
    """Load all MSRTC bus stops."""
    stops_file = os.path.join(DATA_DIR, "bus_stops.json")
    try:
        with open(stops_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load bus stops data: {e}")
        return []


# ============================================================
# PUBLIC API
# ============================================================

def get_state() -> Dict:
    """Get Maharashtra state info."""
    return load_state_data()


def get_all_cities() -> List[Dict]:
    """Get all Maharashtra districts/cities."""
    return load_cities_data()


def get_city_by_id(city_id: int) -> Optional[Dict]:
    """Get a city/district by ID."""
    for city in load_cities_data():
        if city["city_id"] == city_id:
            return city
    return None


def get_all_stops() -> List[Dict]:
    """Get all MSRTC bus stops."""
    return load_bus_stops_data()


def get_stop_by_id(stop_id: int) -> Optional[Dict]:
    """Get a stop by ID."""
    for stop in load_bus_stops_data():
        if stop["stop_id"] == stop_id:
            return stop
    return None


def get_stops_by_district(city_id: int) -> List[Dict]:
    """Get all stops in a district/city."""
    return [s for s in load_bus_stops_data() if s["city_id"] == city_id]


def get_search_surface_stops() -> List[Dict]:
    """
    Get only search surface stops (major depots/stations).
    These are the stops that should appear in origin/destination dropdowns.
    """
    return [s for s in load_bus_stops_data() if s["is_search_surface"]]


def get_stops_by_role(role: str) -> List[Dict]:
    """
    Get stops by role.
    
    Args:
        role: ORIGIN, TERMINAL, or PICKUP_DROP
    """
    return [s for s in load_bus_stops_data() if s["stop_role"] == role]


def search_stops(
    query: str,
    search_surface_only: bool = False,
    city_id: Optional[int] = None,
    limit: int = 50,
) -> List[Dict]:
    """
    Search for MSRTC stops.
    
    Supports:
    - Marathi text search (name_local)
    - English/normalized text search (normalized_key)
    - Partial matching
    
    Args:
        query: Search query (Marathi or English)
        search_surface_only: If True, only return major stops
        city_id: Filter by district/city
        limit: Maximum results to return
    
    Returns:
        List of matching stops
    """
    query_lower = query.lower().strip()
    results = []
    
    for stop in load_bus_stops_data():
        # Apply filters
        if search_surface_only and not stop["is_search_surface"]:
            continue
        if city_id is not None and stop["city_id"] != city_id:
            continue
        
        # Search in Marathi name
        if query in stop["name_local"]:
            results.append(stop)
            continue
        
        # Search in normalized key
        if query_lower in stop["normalized_key"]:
            results.append(stop)
            continue
        
        if len(results) >= limit:
            break
    
    return results[:limit]


def get_stops_for_route(
    origin_stop_id: int,
    destination_stop_id: int,
) -> List[Dict]:
    """
    Get intermediate stops between origin and destination.
    
    Note: This is a placeholder. In production, this would use
    actual route data from MSRTC to determine intermediate stops.
    """
    # TODO: Implement using actual route data
    return []


# ============================================================
# FARE CALCULATION HELPERS
# ============================================================

# MSRTC base fare per km (approximate)
MSRTC_BASE_FARE_PER_KM = 1.20  # INR

# Fare multipliers by bus type
MSRTC_FARE_MULTIPLIERS = {
    "ST": 1.0,
    "SEMI_LUX": 1.3,
    "ASIAD": 1.8,
    "SHIVNERI": 2.2,
    "SHIVSHAHI": 2.0,
    "ASHWAMEDH": 2.5,
}


def calculate_fare(distance_km: float, bus_type: str = "ST") -> float:
    """
    Calculate MSRTC fare based on distance.
    
    MSRTC uses distance-based fare calculation, not fixed origin-destination fares.
    
    Args:
        distance_km: Distance in kilometers
        bus_type: Type of bus (ST, SEMI_LUX, ASIAD, SHIVNERI, SHIVSHAHI, ASHWAMEDH)
    
    Returns:
        Estimated fare in INR
    """
    multiplier = MSRTC_FARE_MULTIPLIERS.get(bus_type, 1.0)
    base_fare = distance_km * MSRTC_BASE_FARE_PER_KM
    return round(base_fare * multiplier, 2)


# ============================================================
# STATISTICS
# ============================================================

def get_stats() -> Dict:
    """Get statistics about the loaded data."""
    stops = load_bus_stops_data()
    cities = load_cities_data()
    
    return {
        "total_stops": len(stops),
        "total_cities": len(cities),
        "search_surface_stops": len([s for s in stops if s["is_search_surface"]]),
        "origin_stops": len([s for s in stops if s["stop_role"] == "ORIGIN"]),
        "terminal_stops": len([s for s in stops if s["stop_role"] == "TERMINAL"]),
        "pickup_drop_stops": len([s for s in stops if s["stop_role"] == "PICKUP_DROP"]),
        "stops_by_city": {
            city["name_en"]: len([s for s in stops if s["city_id"] == city["city_id"]])
            for city in cities
        },
    }


# ============================================================
# INITIALIZATION
# ============================================================

def init():
    """Initialize and validate data on module load."""
    try:
        state = load_state_data()
        cities = load_cities_data()
        stops = load_bus_stops_data()
        
        logger.info(f"MSRTC Data Loaded: {len(stops)} stops across {len(cities)} districts")
        logger.info(f"Search surface stops: {len([s for s in stops if s['is_search_surface']])}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to initialize MSRTC data: {e}")
        return False


# Auto-initialize on import
if __name__ != "__main__":
    init()

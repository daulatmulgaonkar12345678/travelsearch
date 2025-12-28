"""
Corridor Resolver - Enhanced Stop Detection Service
====================================================

Resolves corridor stops between any two cities in Maharashtra.
Separates stops by importance (MAJOR vs MINOR) for UI display.

USAGE:
    from app.services.corridor_resolver import CorridorResolver
    
    resolver = CorridorResolver()
    result = resolver.get_route_stops(from_city_id=1, to_city_id=6)
    
    # Returns:
    # {
    #   "major_stops": ["Panvel", "Mahad", "Chiplun", "Ratnagiri"],
    #   "minor_stops": ["Pen", "Roha", "Kashil", "Sangmeshwar"],
    #   "corridor_name": "Mumbai-Goa Konkan Highway",
    #   "highway": "NH66"
    # }

DISCLAIMER:
    - Stops are INDICATIVE based on highway corridors
    - NOT official MSRTC schedules
    - Actual routes may vary by service type
"""

import json
import os
from typing import List, Dict, Optional, Tuple
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Data paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "places", "states", "MH")
CORRIDORS_FILE = os.path.join(DATA_DIR, "highway_corridors.json")
CITIES_FILE = os.path.join(DATA_DIR, "cities.json")


@lru_cache(maxsize=1)
def load_corridors() -> Dict:
    """Load highway corridors configuration."""
    try:
        with open(CORRIDORS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load corridors: {e}")
        return {"corridors": {}, "city_corridor_map": {}}


@lru_cache(maxsize=1)
def load_cities() -> List[Dict]:
    """Load cities data."""
    try:
        with open(CITIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load cities: {e}")
        return []


def get_city_name(city_id: int) -> str:
    """Get city name by ID."""
    for city in load_cities():
        if city["city_id"] == city_id:
            return city["name_en"]
    return f"City_{city_id}"


def get_city_id_by_name(name: str) -> Optional[int]:
    """Get city ID from name (English or normalized)."""
    name_lower = name.lower().strip()
    for city in load_cities():
        if (city["name_en"].lower() == name_lower or 
            city["normalized_key"] == name_lower):
            return city["city_id"]
    return None


class CorridorResolver:
    """
    Resolves corridor stops between two cities.
    
    Separates stops into MAJOR (always shown) and MINOR (expandable).
    Uses static highway corridor data - no live API calls.
    """
    
    def __init__(self):
        self.data = load_corridors()
        self.corridors = self.data.get("corridors", {})
        self.city_corridor_map = self.data.get("city_corridor_map", {})
    
    def find_common_corridor(
        self, 
        from_city_id: int, 
        to_city_id: int,
        from_stop_key: str = None,
        to_stop_key: str = None
    ) -> Optional[str]:
        """
        Find the best corridor connecting two cities.
        
        If stop_keys are provided, uses them for precise matching.
        This enables Satara → Karad routing (both in same district).
        
        Returns corridor ID or None if no direct corridor exists.
        """
        from_corridors = set(self.city_corridor_map.get(str(from_city_id), []))
        to_corridors = set(self.city_corridor_map.get(str(to_city_id), []))
        
        common = from_corridors & to_corridors
        
        if not common:
            return None
        
        # If multiple corridors, prefer the one with shortest path
        best_corridor = None
        best_distance = float('inf')
        
        for corridor_id in common:
            corridor = self.corridors.get(corridor_id, {})
            stops = corridor.get("stops_sequence", [])
            
            # Find indices of from/to stops
            from_idx = None
            to_idx = None
            
            for i, stop in enumerate(stops):
                # If stop_key provided, use exact match
                if from_stop_key:
                    if stop["stop_key"] == from_stop_key and from_idx is None:
                        from_idx = i
                # Otherwise match by city_id
                elif stop["city_id"] == from_city_id and from_idx is None:
                    from_idx = i
                    
                if to_stop_key:
                    if stop["stop_key"] == to_stop_key:
                        to_idx = i
                elif stop["city_id"] == to_city_id:
                    to_idx = i
            
            if from_idx is not None and to_idx is not None:
                distance = abs(to_idx - from_idx)
                if distance < best_distance:
                    best_distance = distance
                    best_corridor = corridor_id
        
        return best_corridor
    
    def extract_segment(
        self,
        corridor_id: str,
        from_city_id: int,
        to_city_id: int
    ) -> Tuple[List[Dict], bool]:
        """
        Extract the segment of stops between two cities.
        
        Returns (stops_list, is_reversed) tuple.
        """
        corridor = self.corridors.get(corridor_id, {})
        all_stops = corridor.get("stops_sequence", [])
        
        # Find first occurrence of from_city and last of to_city
        from_idx = None
        to_idx = None
        
        for i, stop in enumerate(all_stops):
            if stop["city_id"] == from_city_id and from_idx is None:
                from_idx = i
            if stop["city_id"] == to_city_id:
                to_idx = i
        
        if from_idx is None or to_idx is None:
            return [], False
        
        # Determine direction
        if from_idx <= to_idx:
            # Forward direction
            segment = all_stops[from_idx:to_idx + 1]
            return segment, False
        else:
            # Reverse direction
            segment = all_stops[to_idx:from_idx + 1]
            segment.reverse()
            return segment, True
    
    def get_route_stops(
        self,
        from_city_id: int,
        to_city_id: int,
        include_endpoints: bool = False,
        from_stop_key: str = None,
        to_stop_key: str = None
    ) -> Dict:
        """
        Get intermediate stops for a route, separated by importance.
        
        Args:
            from_city_id: Origin city/district ID
            to_city_id: Destination city/district ID
            include_endpoints: Whether to include origin/destination stops
            from_stop_key: Optional specific stop key for origin
            to_stop_key: Optional specific stop key for destination
        
        Returns:
            Dict with major_stops, minor_stops, corridor info, and disclaimer
        """
        # Find common corridor (with optional stop_key precision)
        corridor_id = self.find_common_corridor(
            from_city_id, to_city_id,
            from_stop_key, to_stop_key
        )
        
        if not corridor_id:
            # No direct corridor found
            return {
                "from_city": get_city_name(from_city_id),
                "to_city": get_city_name(to_city_id),
                "major_stops": [],
                "minor_stops": [],
                "all_stops": [],
                "corridor_name": None,
                "highway": None,
                "source": "no_corridor",
                "note": "No direct highway corridor found for this route."
            }
        
        corridor = self.corridors.get(corridor_id, {})
        
        # Extract segment
        segment, is_reversed = self.extract_segment(corridor_id, from_city_id, to_city_id)
        
        # Separate by importance, excluding endpoints if requested
        major_stops = []
        minor_stops = []
        all_stops_detailed = []
        
        for i, stop in enumerate(segment):
            # Skip endpoints unless requested
            if not include_endpoints and (i == 0 or i == len(segment) - 1):
                continue
            
            stop_info = {
                "stop_key": stop["stop_key"],
                "stop_name": self._format_stop_name(stop["stop_key"]),
                "city_id": stop["city_id"],
                "city_name": get_city_name(stop["city_id"]),
                "importance": stop["importance"],
                "km_from_origin": stop.get("km_from_start", 0),
            }
            
            all_stops_detailed.append(stop_info)
            
            if stop["importance"] == "MAJOR":
                major_stops.append(stop_info["stop_name"])
            else:
                minor_stops.append(stop_info["stop_name"])
        
        return {
            "from_city": get_city_name(from_city_id),
            "to_city": get_city_name(to_city_id),
            "major_stops": major_stops,
            "minor_stops": minor_stops,
            "all_stops": all_stops_detailed,
            "corridor_name": corridor.get("name"),
            "highway": corridor.get("highway"),
            "source": "corridor",
            "is_reversed": is_reversed,
            "note": "Stops are indicative and may vary by service."
        }
    
    def get_route_stops_by_name(
        self,
        from_city: str,
        to_city: str,
        include_endpoints: bool = False
    ) -> Dict:
        """
        Get route stops using city names instead of IDs.
        
        Handles same-district routes (e.g., Satara → Karad)
        by using stop_key matching.
        """
        from_id = get_city_id_by_name(from_city)
        to_id = get_city_id_by_name(to_city)
        
        # Get stop keys for more precise matching
        from_stop_key = self._get_stop_key_from_name(from_city)
        to_stop_key = self._get_stop_key_from_name(to_city)
        
        if not from_id:
            return {"error": f"Unknown origin city: {from_city}"}
        if not to_id:
            return {"error": f"Unknown destination city: {to_city}"}
        
        # Use stop-key based routing for better accuracy
        return self.get_route_stops(
            from_id, to_id, include_endpoints,
            from_stop_key=from_stop_key,
            to_stop_key=to_stop_key
        )
    
    def _get_stop_key_from_name(self, name: str) -> Optional[str]:
        """
        Get the stop_key from a city/stop name.
        E.g., 'Satara' -> 'satara-bus-stand'
        """
        name_lower = name.lower().strip()
        
        # Search all corridors for matching stop
        for corridor_id, corridor in self.corridors.items():
            for stop in corridor.get("stops_sequence", []):
                stop_key = stop["stop_key"]
                # Check if name matches the beginning of stop_key
                if stop_key.startswith(name_lower) or \
                   stop_key.replace("-bus-stand", "").replace("-cbs", "") == name_lower:
                    return stop_key
        
        return None
    
    def _format_stop_name(self, stop_key: str) -> str:
        """
        Format stop key into readable name.
        
        Example: "kashil" -> "Kashil"
                 "chiplun-bus-stand" -> "Chiplun"
        """
        name = stop_key.replace("-bus-stand", "").replace("-cbs", "").replace("-bs-depo", "")
        name = name.replace("-", " ")
        return name.title()


# Singleton instance
_resolver = None

def get_resolver() -> CorridorResolver:
    """Get singleton CorridorResolver instance."""
    global _resolver
    if _resolver is None:
        _resolver = CorridorResolver()
    return _resolver


# ============================================================
# CONVENIENCE FUNCTIONS (for backward compatibility)
# ============================================================

def get_likely_stops_enhanced(
    from_city_id: int,
    to_city_id: int,
) -> Dict:
    """
    Get likely stops with MAJOR/MINOR separation.
    
    This is the main entry point for the enhanced corridor logic.
    """
    return get_resolver().get_route_stops(from_city_id, to_city_id)


def get_likely_stops_by_name_enhanced(
    from_city: str,
    to_city: str,
) -> Dict:
    """
    Get likely stops using city names.
    """
    return get_resolver().get_route_stops_by_name(from_city, to_city)

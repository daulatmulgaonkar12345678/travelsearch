"""Feeder Route Resolver - Tourist Destination Connectivity
============================================================

Resolves bus connectivity for tourist destinations that are not
directly on main highway corridors.

ARCHITECTURE:
- Highway corridors = main arterial routes (NH48, NH66, etc.)
- Feeder links = connections from highway junctions to tourist spots
- Combined = complete route from origin to tourist destination

SEARCH LOGIC:
1) Try direct highway graph path (origin → destination)
2) If not found, try feeder route:
   - origin → highway → junction → feeder → destination
3) If path exists, treat route as CONNECTED
4) Only if both fail, show "No connectivity found"

CONSTRAINTS:
- No live schedules (static data only)
- No guaranteed halts (indicative only)
- All data is auditable and version-controlled

USAGE:
    from app.services.feeder_resolver import FeederResolver
    
    resolver = FeederResolver()
    result = resolver.find_route("Pune", "Mahabaleshwar")
    
    # Returns:
    # {
    #   "connected": True,
    #   "route_type": "FEEDER",
    #   "segments": [
    #     {"type": "HIGHWAY", "from": "Pune", "to": "Satara", ...},
    #     {"type": "FEEDER", "from": "Satara", "to": "Mahabaleshwar", ...}
    #   ],
    #   "total_distance_km": 120,
    #   "estimated_time_hrs": 3.5
    # }
"""

import json
import os
from typing import Dict, List, Optional, Any
from functools import lru_cache
import logging

from app.services.corridor_resolver import (
    CorridorResolver,
    get_city_id_by_name,
    get_city_name,
    load_cities,
)

logger = logging.getLogger(__name__)

# Data paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "places", "states", "MH")
FEEDER_FILE = os.path.join(DATA_DIR, "feeder_links.json")


@lru_cache(maxsize=1)
def load_feeder_data() -> Dict:
    """Load feeder links and tourist destinations."""
    try:
        with open(FEEDER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load feeder data: {e}")
        return {"tourist_destinations": [], "feeder_links": []}


class FeederResolver:
    """
    Resolves routes to tourist destinations via feeder connections.
    
    Combines highway corridor data with feeder links to provide
    complete connectivity information.
    """
    
    def __init__(self):
        self.data = load_feeder_data()
        self.destinations = {d["id"]: d for d in self.data.get("tourist_destinations", [])}
        self.feeder_links = self.data.get("feeder_links", [])
        self.corridor_resolver = CorridorResolver()
        
        # Build lookup indexes
        self._build_indexes()
    
    def _build_indexes(self):
        """Build lookup indexes for fast access."""
        # Index: destination_id -> [feeder_links from various origins]
        self.dest_feeders = {}
        for link in self.feeder_links:
            dest_id = link["to_destination"]
            if dest_id not in self.dest_feeders:
                self.dest_feeders[dest_id] = []
            self.dest_feeders[dest_id].append(link)
        
        # Index: origin_city_id -> [feeder_links to various destinations]
        self.origin_feeders = {}
        for link in self.feeder_links:
            origin_id = link["from_city_id"]
            if origin_id not in self.origin_feeders:
                self.origin_feeders[origin_id] = []
            self.origin_feeders[origin_id].append(link)
        
        # Index: destination name (normalized) -> destination_id
        self.dest_name_index = {}
        for dest_id, dest in self.destinations.items():
            # Index by English name
            self.dest_name_index[dest["name_en"].lower()] = dest_id
            # Index by ID
            self.dest_name_index[dest_id.lower()] = dest_id
            # Index by common variations
            name_parts = dest["name_en"].lower().split()
            if len(name_parts) > 1:
                self.dest_name_index[name_parts[0]] = dest_id
    
    def is_tourist_destination(self, name: str) -> bool:
        """Check if a name refers to a tourist destination."""
        return name.lower().strip() in self.dest_name_index
    
    def get_destination_info(self, name: str) -> Optional[Dict]:
        """Get tourist destination info by name."""
        dest_id = self.dest_name_index.get(name.lower().strip())
        if dest_id:
            return self.destinations.get(dest_id)
        return None
    
    def find_route(
        self,
        from_city: str,
        to_city: str,
    ) -> Dict[str, Any]:
        """
        Find route between two locations.
        
        SEARCH ORDER:
        1) Direct highway corridor (if both are on highway)
        2) Feeder route (if destination is tourist spot)
        3) Reverse feeder (if origin is tourist spot)
        4) No connectivity found
        
        Args:
            from_city: Origin city/destination name
            to_city: Destination city/destination name
        
        Returns:
            Dict with connectivity info, segments, and estimated times
        """
        from_city = from_city.strip()
        to_city = to_city.strip()
        
        # Check if destination is a tourist spot
        to_dest_info = self.get_destination_info(to_city)
        from_dest_info = self.get_destination_info(from_city)
        
        # CASE 1: Both are regular cities - try highway corridor
        if not to_dest_info and not from_dest_info:
            return self._try_highway_route(from_city, to_city)
        
        # CASE 2: Destination is tourist spot - find feeder route
        if to_dest_info:
            return self._find_feeder_to_destination(from_city, to_dest_info)
        
        # CASE 3: Origin is tourist spot - find reverse feeder route
        if from_dest_info:
            return self._find_feeder_from_destination(from_dest_info, to_city)
        
        # CASE 4: No route found
        return self._no_route_response(from_city, to_city)
    
    def _try_highway_route(self, from_city: str, to_city: str) -> Dict:
        """
        Try to find a direct highway corridor route.
        """
        result = self.corridor_resolver.get_route_stops_by_name(from_city, to_city)
        
        if result.get("source") == "corridor":
            return {
                "connected": True,
                "route_type": "HIGHWAY_DIRECT",
                "from_city": from_city.title(),
                "to_city": to_city.title(),
                "segments": [
                    {
                        "type": "HIGHWAY",
                        "from": from_city.title(),
                        "to": to_city.title(),
                        "corridor_name": result.get("corridor_name"),
                        "highway": result.get("highway"),
                        "major_stops": result.get("major_stops", []),
                        "minor_stops": result.get("minor_stops", []),
                    }
                ],
                "total_distance_km": None,  # Not available in corridor data
                "estimated_time_hrs": None,
                "note": "Direct highway route available."
            }
        
        return self._no_route_response(from_city, to_city)
    
    def _find_feeder_to_destination(
        self,
        from_city: str,
        dest_info: Dict
    ) -> Dict:
        """
        Find feeder route from origin city to tourist destination.
        
        Strategy:
        1) Look for direct feeder from origin to destination
        2) If not found, find feeder via nearest highway junction
        """
        dest_id = dest_info["id"]
        from_city_id = get_city_id_by_name(from_city)
        
        # Get all feeders to this destination
        feeders = self.dest_feeders.get(dest_id, [])
        
        # PRIORITY 1: Direct feeder from this origin
        direct_feeder = None
        for feeder in feeders:
            if feeder["from_city_id"] == from_city_id:
                direct_feeder = feeder
                break
        
        if direct_feeder:
            return self._build_feeder_response(from_city, dest_info, direct_feeder)
        
        # PRIORITY 2: Find best feeder via highway connection
        best_route = None
        best_score = float('inf')
        
        for feeder in feeders:
            # Check if we can reach the feeder's origin via highway
            feeder_origin_city = get_city_name(feeder["from_city_id"])
            highway_result = self.corridor_resolver.get_route_stops_by_name(
                from_city, feeder_origin_city
            )
            
            if highway_result.get("source") == "corridor":
                # Score = feeder distance (prefer shorter feeders)
                score = feeder.get("distance_km", 1000)
                if score < best_score:
                    best_score = score
                    best_route = {
                        "feeder": feeder,
                        "highway_segment": highway_result,
                        "feeder_origin": feeder_origin_city,
                    }
        
        if best_route:
            return self._build_combined_response(
                from_city, dest_info, best_route
            )
        
        # PRIORITY 3: Check if destination's junction is reachable
        for feeder in feeders:
            via_junction = feeder.get("via_junction")
            if via_junction:
                # Extract city name from junction stop_key
                junction_city = via_junction.replace("-bus-stand", "").replace("-cbs", "").replace("-", " ").title()
                highway_result = self.corridor_resolver.get_route_stops_by_name(
                    from_city, junction_city
                )
                
                if highway_result.get("source") == "corridor":
                    return self._build_combined_response(
                        from_city, dest_info,
                        {
                            "feeder": feeder,
                            "highway_segment": highway_result,
                            "feeder_origin": junction_city,
                        }
                    )
        
        # No route found
        return self._no_route_response(from_city, dest_info["name_en"])
    
    def _find_feeder_from_destination(
        self,
        dest_info: Dict,
        to_city: str
    ) -> Dict:
        """
        Find route from tourist destination to a city.
        This is the reverse of _find_feeder_to_destination.
        """
        # Find the reverse route and swap
        result = self.find_route(to_city, dest_info["name_en"])
        
        if result.get("connected"):
            # Reverse the segments
            result["from_city"] = dest_info["name_en"]
            result["to_city"] = to_city.title()
            result["segments"] = list(reversed(result.get("segments", [])))
            for seg in result["segments"]:
                seg["from"], seg["to"] = seg["to"], seg["from"]
        
        return result
    
    def _build_feeder_response(
        self,
        from_city: str,
        dest_info: Dict,
        feeder: Dict
    ) -> Dict:
        """
        Build response for a direct feeder route.
        """
        freq_map = {"HIGH": "Frequent", "MEDIUM": "Regular", "LOW": "Limited"}
        
        segments = []
        
        # If there's a via junction, split into highway + feeder
        if feeder.get("via_junction") and feeder.get("via_city_id"):
            via_city = get_city_name(feeder["via_city_id"])
            
            # Highway segment
            highway_result = self.corridor_resolver.get_route_stops_by_name(
                from_city, via_city
            )
            if highway_result.get("source") == "corridor":
                segments.append({
                    "type": "HIGHWAY",
                    "from": from_city.title(),
                    "to": via_city,
                    "corridor_name": highway_result.get("corridor_name"),
                    "highway": highway_result.get("highway"),
                    "major_stops": highway_result.get("major_stops", []),
                    "minor_stops": highway_result.get("minor_stops", []),
                })
            
            # Feeder segment
            segments.append({
                "type": "FEEDER",
                "from": via_city,
                "to": dest_info["name_en"],
                "distance_km": feeder.get("feeder_segment_km"),
                "frequency": freq_map.get(feeder.get("frequency"), "Varies"),
                "description": feeder.get("description"),
            })
        else:
            # Direct feeder (no highway segment)
            segments.append({
                "type": "DIRECT_FEEDER",
                "from": from_city.title(),
                "to": dest_info["name_en"],
                "distance_km": feeder.get("distance_km"),
                "frequency": freq_map.get(feeder.get("frequency"), "Varies"),
                "description": feeder.get("description"),
            })
        
        return {
            "connected": True,
            "route_type": "FEEDER" if feeder.get("via_junction") else "DIRECT_FEEDER",
            "from_city": from_city.title(),
            "to_city": dest_info["name_en"],
            "destination_info": {
                "name": dest_info["name_en"],
                "name_local": dest_info.get("name_local"),
                "type": dest_info.get("type"),
                "description": dest_info.get("description"),
            },
            "segments": segments,
            "total_distance_km": feeder.get("distance_km"),
            "estimated_time_hrs": feeder.get("travel_time_hrs"),
            "frequency": freq_map.get(feeder.get("frequency"), "Varies"),
            "note": f"{feeder.get('description', 'Feeder route available.')} Bus availability may vary by season."
        }
    
    def _build_combined_response(
        self,
        from_city: str,
        dest_info: Dict,
        route_data: Dict
    ) -> Dict:
        """
        Build response for combined highway + feeder route.
        """
        feeder = route_data["feeder"]
        highway = route_data["highway_segment"]
        feeder_origin = route_data["feeder_origin"]
        freq_map = {"HIGH": "Frequent", "MEDIUM": "Regular", "LOW": "Limited"}
        
        segments = [
            # Highway segment
            {
                "type": "HIGHWAY",
                "from": from_city.title(),
                "to": feeder_origin,
                "corridor_name": highway.get("corridor_name"),
                "highway": highway.get("highway"),
                "major_stops": highway.get("major_stops", []),
                "minor_stops": highway.get("minor_stops", []),
            },
            # Feeder segment
            {
                "type": "FEEDER",
                "from": feeder_origin,
                "to": dest_info["name_en"],
                "distance_km": feeder.get("feeder_segment_km"),
                "frequency": freq_map.get(feeder.get("frequency"), "Varies"),
                "description": feeder.get("description"),
            }
        ]
        
        return {
            "connected": True,
            "route_type": "HIGHWAY_PLUS_FEEDER",
            "from_city": from_city.title(),
            "to_city": dest_info["name_en"],
            "destination_info": {
                "name": dest_info["name_en"],
                "name_local": dest_info.get("name_local"),
                "type": dest_info.get("type"),
                "description": dest_info.get("description"),
            },
            "segments": segments,
            "via_junction": feeder_origin,
            "total_distance_km": feeder.get("distance_km"),
            "estimated_time_hrs": feeder.get("travel_time_hrs"),
            "frequency": freq_map.get(feeder.get("frequency"), "Varies"),
            "note": f"Take bus to {feeder_origin}, then {feeder.get('description', 'local bus to destination')}. Schedules are indicative."
        }
    
    def _no_route_response(self, from_city: str, to_city: str) -> Dict:
        """Return no connectivity response."""
        return {
            "connected": False,
            "route_type": "NO_ROUTE",
            "from_city": from_city.title(),
            "to_city": to_city.title() if isinstance(to_city, str) else to_city,
            "segments": [],
            "total_distance_km": None,
            "estimated_time_hrs": None,
            "note": "No reasonable bus connectivity found. Consider private transport or checking with local operators."
        }
    
    def list_tourist_destinations(self, dest_type: str = None) -> List[Dict]:
        """
        List all tourist destinations, optionally filtered by type.
        
        Args:
            dest_type: Filter by type (HILL_STATION, RELIGIOUS, HERITAGE, BEACH, RESORT)
        
        Returns:
            List of destination info dicts
        """
        destinations = list(self.destinations.values())
        
        if dest_type:
            destinations = [d for d in destinations if d.get("type") == dest_type]
        
        return destinations


# Singleton instance
_feeder_resolver = None

def get_feeder_resolver() -> FeederResolver:
    """Get singleton FeederResolver instance."""
    global _feeder_resolver
    if _feeder_resolver is None:
        _feeder_resolver = FeederResolver()
    return _feeder_resolver


# Convenience functions
def find_route(from_city: str, to_city: str) -> Dict:
    """Find route between two locations."""
    return get_feeder_resolver().find_route(from_city, to_city)


def is_tourist_destination(name: str) -> bool:
    """Check if name is a known tourist destination."""
    return get_feeder_resolver().is_tourist_destination(name)

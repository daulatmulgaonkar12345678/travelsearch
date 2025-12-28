"""Rail Connectivity Resolver Service

Flight-like hub-based routing for Indian Railways.
Works even when no direct train exists by using:
1. Direct connectivity (same line/corridor)
2. Hub-based routing (via junctions)
3. Local catchment (nearby stations)

Does NOT depend on live IRCTC APIs - uses static graph.
"""

import json
import logging
import os
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from collections import deque
import math

logger = logging.getLogger(__name__)

# ============================================================
# DATA MODELS
# ============================================================

class RouteType(str, Enum):
    DIRECT = "DIRECT"
    HUB_BASED = "HUB_BASED"
    LOCAL_CATCHMENT = "LOCAL_CATCHMENT"
    NOT_FOUND = "NOT_FOUND"

class Confidence(str, Enum):
    HIGH = "HIGH"       # Direct line or single hub
    MEDIUM = "MEDIUM"   # Two hubs or regional
    LOW = "LOW"         # Complex routing

@dataclass
class Station:
    station_id: str
    station_code: str
    station_name: str
    city: str
    district: str
    state: str
    zone: str
    latitude: float
    longitude: float
    station_type: str  # MAJOR, JUNCTION, LOCAL
    aliases: List[str]

@dataclass
class RailHub:
    hub_code: str
    hub_name: str
    hub_type: str  # MEGA_HUB, MAJOR_HUB, REGIONAL_HUB
    zone: str
    city: str
    state: str
    importance_score: int
    connected_zones: List[str]
    is_zonal_hq: bool
    is_capital: bool

@dataclass
class RailEdge:
    from_station: str
    to_station: str
    distance_km: int
    importance: str  # PRIMARY, SECONDARY
    line: str

@dataclass
class ConnectivityResult:
    route_type: RouteType
    path: List[Dict]
    confidence: Confidence
    note: str
    total_distance_km: Optional[int] = None
    via_hubs: List[str] = None
    zone_changes: int = 0

# ============================================================
# DATA LOADING
# ============================================================

_stations: Dict[str, Station] = {}
_hubs: Dict[str, RailHub] = {}
_edges: List[RailEdge] = []
_graph: Dict[str, List[Tuple[str, int, str]]] = {}  # adjacency list
_station_to_city: Dict[str, str] = {}
_city_to_stations: Dict[str, List[str]] = {}
_corridors: List[Dict] = []
_loaded = False

def _get_data_path(filename: str) -> str:
    """Get path to railway data file"""
    base_paths = [
        "/app/apps/backend/app/data/places/railways",
        "/app/backend/app/data/places/railways",
        os.path.join(os.path.dirname(__file__), "..", "data", "places", "railways"),
    ]
    
    for base in base_paths:
        path = os.path.join(base, filename)
        if os.path.exists(path):
            return path
    
    raise FileNotFoundError(f"Railway data file not found: {filename}")

def _load_data():
    """Load all railway data files"""
    global _stations, _hubs, _edges, _graph, _station_to_city, _city_to_stations, _corridors, _loaded
    
    if _loaded:
        return
    
    try:
        # Load stations
        with open(_get_data_path("stations.json"), "r") as f:
            data = json.load(f)
            for s in data.get("stations", []):
                station = Station(
                    station_id=s["station_id"],
                    station_code=s["station_code"],
                    station_name=s["station_name"],
                    city=s["city"],
                    district=s["district"],
                    state=s["state"],
                    zone=s["zone"],
                    latitude=s["latitude"],
                    longitude=s["longitude"],
                    station_type=s["station_type"],
                    aliases=s.get("aliases", [])
                )
                _stations[station.station_code] = station
                _station_to_city[station.station_code] = station.city
                
                # Build city to stations mapping
                city_key = station.city.lower()
                if city_key not in _city_to_stations:
                    _city_to_stations[city_key] = []
                _city_to_stations[city_key].append(station.station_code)
        
        # Load hubs
        with open(_get_data_path("rail_hubs.json"), "r") as f:
            data = json.load(f)
            for h in data.get("hubs", []):
                hub = RailHub(
                    hub_code=h["hub_code"],
                    hub_name=h["hub_name"],
                    hub_type=h["hub_type"],
                    zone=h["zone"],
                    city=h["city"],
                    state=h["state"],
                    importance_score=h["importance_score"],
                    connected_zones=h.get("connected_zones", []),
                    is_zonal_hq=h.get("is_zonal_hq", False),
                    is_capital=h.get("is_capital", False)
                )
                _hubs[hub.hub_code] = hub
        
        # Load edges and build graph
        with open(_get_data_path("rail_edges.json"), "r") as f:
            data = json.load(f)
            _corridors = data.get("corridors", [])
            
            for e in data.get("edges", []):
                edge = RailEdge(
                    from_station=e["from"],
                    to_station=e["to"],
                    distance_km=e["distance_km"],
                    importance=e["importance"],
                    line=e["line"]
                )
                _edges.append(edge)
                
                # Build bidirectional graph
                if edge.from_station not in _graph:
                    _graph[edge.from_station] = []
                if edge.to_station not in _graph:
                    _graph[edge.to_station] = []
                
                _graph[edge.from_station].append((edge.to_station, edge.distance_km, edge.line))
                _graph[edge.to_station].append((edge.from_station, edge.distance_km, edge.line))
        
        _loaded = True
        logger.info(f"✅ Loaded {len(_stations)} stations, {len(_hubs)} hubs, {len(_edges)} edges")
        
    except Exception as e:
        logger.error(f"❌ Failed to load railway data: {e}")
        raise

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _normalize_station_code(input_str: str) -> Optional[str]:
    """Convert city name or station code to standard station code"""
    _load_data()
    
    input_upper = input_str.upper().strip()
    input_lower = input_str.lower().strip()
    
    # Direct station code match
    if input_upper in _stations:
        return input_upper
    
    # City name match - return primary station
    if input_lower in _city_to_stations:
        stations = _city_to_stations[input_lower]
        # Prefer MAJOR > JUNCTION > LOCAL
        for station_code in stations:
            if _stations[station_code].station_type == "MAJOR":
                return station_code
        for station_code in stations:
            if _stations[station_code].station_type == "JUNCTION":
                return station_code
        return stations[0] if stations else None
    
    # Alias match
    for code, station in _stations.items():
        if input_lower in [a.lower() for a in station.aliases]:
            return code
        if input_lower == station.station_name.lower():
            return code
        if input_lower == station.city.lower():
            return code
    
    return None

def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in km"""
    R = 6371  # Earth's radius in km
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def _get_nearby_stations(station_code: str, radius_km: float = 50) -> List[str]:
    """Find stations within radius (for local catchment)"""
    _load_data()
    
    if station_code not in _stations:
        return []
    
    origin = _stations[station_code]
    nearby = []
    
    for code, station in _stations.items():
        if code == station_code:
            continue
        
        dist = _haversine_distance(
            origin.latitude, origin.longitude,
            station.latitude, station.longitude
        )
        
        if dist <= radius_km:
            nearby.append((code, dist))
    
    # Sort by distance
    nearby.sort(key=lambda x: x[1])
    return [s[0] for s in nearby]

def _find_nearest_hub(station_code: str) -> Optional[str]:
    """Find the nearest railway hub to a station"""
    _load_data()
    
    if station_code in _hubs:
        return station_code
    
    if station_code not in _stations:
        return None
    
    origin = _stations[station_code]
    nearest_hub = None
    min_dist = float('inf')
    
    for hub_code, hub in _hubs.items():
        if hub_code not in _stations:
            continue
        
        hub_station = _stations[hub_code]
        dist = _haversine_distance(
            origin.latitude, origin.longitude,
            hub_station.latitude, hub_station.longitude
        )
        
        # Weight by hub importance (prefer MEGA > MAJOR > REGIONAL)
        if hub.hub_type == "MEGA_HUB":
            dist *= 0.7
        elif hub.hub_type == "MAJOR_HUB":
            dist *= 0.85
        
        if dist < min_dist:
            min_dist = dist
            nearest_hub = hub_code
    
    return nearest_hub

def _bfs_find_path(start: str, end: str, max_depth: int = 6) -> Optional[List[str]]:
    """BFS to find shortest path in graph"""
    _load_data()
    
    if start not in _graph or end not in _graph:
        return None
    
    if start == end:
        return [start]
    
    queue = deque([(start, [start])])
    visited = {start}
    
    while queue:
        current, path = queue.popleft()
        
        if len(path) > max_depth:
            continue
        
        for neighbor, dist, line in _graph.get(current, []):
            if neighbor == end:
                return path + [neighbor]
            
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    return None

def _is_on_same_corridor(station1: str, station2: str) -> Optional[str]:
    """Check if two stations are on the same corridor"""
    _load_data()
    
    for corridor in _corridors:
        stations = corridor.get("stations", [])
        if station1 in stations and station2 in stations:
            return corridor.get("corridor_name")
    
    return None

def _calculate_path_distance(path: List[str]) -> int:
    """Calculate total distance of a path"""
    _load_data()
    
    total = 0
    for i in range(len(path) - 1):
        from_st = path[i]
        to_st = path[i + 1]
        
        for neighbor, dist, line in _graph.get(from_st, []):
            if neighbor == to_st:
                total += dist
                break
    
    return total

# ============================================================
# MAIN CONNECTIVITY RESOLVER
# ============================================================

def resolve_connectivity(from_station: str, to_station: str) -> ConnectivityResult:
    """
    Main entry point for resolving rail connectivity.
    
    Strategy:
    1. Direct connectivity (same line/corridor)
    2. Hub-based routing (max 2 hubs)
    3. Local catchment (nearby stations)
    """
    _load_data()
    
    # Normalize inputs
    origin_code = _normalize_station_code(from_station)
    dest_code = _normalize_station_code(to_station)
    
    if not origin_code:
        return ConnectivityResult(
            route_type=RouteType.NOT_FOUND,
            path=[],
            confidence=Confidence.LOW,
            note=f"Origin station not found: {from_station}"
        )
    
    if not dest_code:
        return ConnectivityResult(
            route_type=RouteType.NOT_FOUND,
            path=[],
            confidence=Confidence.LOW,
            note=f"Destination station not found: {to_station}"
        )
    
    if origin_code == dest_code:
        return ConnectivityResult(
            route_type=RouteType.DIRECT,
            path=[_build_path_node(origin_code, "ORIGIN")],
            confidence=Confidence.HIGH,
            note="Same station"
        )
    
    # Strategy 1: Direct connectivity
    direct_result = _check_direct_connectivity(origin_code, dest_code)
    if direct_result.route_type == RouteType.DIRECT:
        return direct_result
    
    # Strategy 2: Hub-based routing
    hub_result = _check_hub_routing(origin_code, dest_code)
    if hub_result.route_type == RouteType.HUB_BASED:
        return hub_result
    
    # Strategy 3: Local catchment
    catchment_result = _check_local_catchment(origin_code, dest_code)
    if catchment_result.route_type == RouteType.LOCAL_CATCHMENT:
        return catchment_result
    
    # Fallback: Estimate possible route
    return _create_estimated_route(origin_code, dest_code)

def _build_path_node(station_code: str, node_type: str) -> Dict:
    """Build a path node for the response"""
    _load_data()
    
    station = _stations.get(station_code)
    hub = _hubs.get(station_code)
    
    return {
        "station": station_code,
        "type": node_type,
        "station_name": station.station_name if station else station_code,
        "city": station.city if station else None,
        "zone": station.zone if station else None,
        "is_hub": hub is not None,
        "hub_type": hub.hub_type if hub else None
    }

def _check_direct_connectivity(origin: str, destination: str) -> ConnectivityResult:
    """Check for direct connectivity via BFS"""
    
    # Check if on same corridor first
    corridor = _is_on_same_corridor(origin, destination)
    if corridor:
        path = _bfs_find_path(origin, destination, max_depth=8)
        if path:
            distance = _calculate_path_distance(path)
            return ConnectivityResult(
                route_type=RouteType.DIRECT,
                path=[_build_path_node(s, "ORIGIN" if s == origin else "DESTINATION" if s == destination else "VIA") for s in path],
                confidence=Confidence.HIGH,
                note=f"Direct route via {corridor}. Trains run daily.",
                total_distance_km=distance,
                via_hubs=[],
                zone_changes=0
            )
    
    # Try BFS for direct path
    path = _bfs_find_path(origin, destination, max_depth=4)
    if path:
        distance = _calculate_path_distance(path)
        return ConnectivityResult(
            route_type=RouteType.DIRECT,
            path=[_build_path_node(s, "ORIGIN" if s == origin else "DESTINATION" if s == destination else "VIA") for s in path],
            confidence=Confidence.HIGH,
            note="Direct rail route available. Multiple trains operate on this line.",
            total_distance_km=distance,
            via_hubs=[],
            zone_changes=0
        )
    
    return ConnectivityResult(
        route_type=RouteType.NOT_FOUND,
        path=[],
        confidence=Confidence.LOW,
        note="No direct route found"
    )

def _check_hub_routing(origin: str, destination: str) -> ConnectivityResult:
    """Check for hub-based routing (max 2 hubs)"""
    
    # Find nearest hubs to origin and destination
    origin_hub = _find_nearest_hub(origin)
    dest_hub = _find_nearest_hub(destination)
    
    if not origin_hub or not dest_hub:
        return ConnectivityResult(
            route_type=RouteType.NOT_FOUND,
            path=[],
            confidence=Confidence.LOW,
            note="Could not find suitable hubs"
        )
    
    # Case 1: Same hub
    if origin_hub == dest_hub:
        path = [origin, origin_hub, destination] if origin != origin_hub else [origin, destination]
        return ConnectivityResult(
            route_type=RouteType.HUB_BASED,
            path=[_build_path_node(s, "ORIGIN" if s == origin else "DESTINATION" if s == destination else "HUB") for s in path],
            confidence=Confidence.HIGH,
            note=f"Both stations connect through {_hubs[origin_hub].hub_name}.",
            via_hubs=[origin_hub],
            zone_changes=0
        )
    
    # Case 2: Try routing via one hub (with longer max_depth for long routes)
    for hub in [origin_hub, dest_hub]:
        origin_to_hub = _bfs_find_path(origin, hub, max_depth=8)
        hub_to_dest = _bfs_find_path(hub, destination, max_depth=8)
        
        if origin_to_hub and hub_to_dest:
            full_path = origin_to_hub + hub_to_dest[1:]  # Avoid duplicate hub
            distance = _calculate_path_distance(full_path)
            
            hub_info = _hubs[hub]
            return ConnectivityResult(
                route_type=RouteType.HUB_BASED,
                path=[_build_path_node(s, "ORIGIN" if s == origin else "DESTINATION" if s == destination else "HUB" if s == hub else "VIA") for s in full_path],
                confidence=Confidence.HIGH,
                note=f"Most trains travel via {hub_info.hub_name}. Change of trains may be required.",
                total_distance_km=distance,
                via_hubs=[hub],
                zone_changes=1 if _stations[origin].zone != _stations[destination].zone else 0
            )
    
    # Case 3: Try routing via two hubs
    hub_to_hub = _bfs_find_path(origin_hub, dest_hub, max_depth=5)
    if hub_to_hub:
        origin_to_hub = _bfs_find_path(origin, origin_hub, max_depth=3)
        hub_to_dest = _bfs_find_path(dest_hub, destination, max_depth=3)
        
        if origin_to_hub and hub_to_dest:
            # Build full path avoiding duplicates
            full_path = origin_to_hub.copy()
            for s in hub_to_hub[1:]:
                if s not in full_path:
                    full_path.append(s)
            for s in hub_to_dest[1:]:
                if s not in full_path:
                    full_path.append(s)
            
            distance = _calculate_path_distance(full_path)
            
            return ConnectivityResult(
                route_type=RouteType.HUB_BASED,
                path=[_build_path_node(s, 
                    "ORIGIN" if s == origin else 
                    "DESTINATION" if s == destination else 
                    "HUB" if s in [origin_hub, dest_hub] else "VIA"
                ) for s in full_path],
                confidence=Confidence.MEDIUM,
                note=f"Travel via {_hubs[origin_hub].hub_name} and {_hubs[dest_hub].hub_name}. Multiple train changes likely.",
                total_distance_km=distance,
                via_hubs=[origin_hub, dest_hub],
                zone_changes=2
            )
    
    return ConnectivityResult(
        route_type=RouteType.NOT_FOUND,
        path=[],
        confidence=Confidence.LOW,
        note="No hub-based route found"
    )

def _check_local_catchment(origin: str, destination: str) -> ConnectivityResult:
    """Check nearby stations for connectivity"""
    
    # Try nearby origin stations
    nearby_origins = _get_nearby_stations(origin, radius_km=50)
    for nearby in nearby_origins[:3]:  # Check top 3
        result = _check_direct_connectivity(nearby, destination)
        if result.route_type == RouteType.DIRECT:
            # Prepend origin to path
            result.path.insert(0, _build_path_node(origin, "ORIGIN"))
            result.route_type = RouteType.LOCAL_CATCHMENT
            result.note = f"Travel to nearby station {_stations[nearby].station_name} ({_stations[nearby].city}) for connectivity. " + result.note
            return result
    
    # Try nearby destination stations
    nearby_dests = _get_nearby_stations(destination, radius_km=50)
    for nearby in nearby_dests[:3]:
        result = _check_direct_connectivity(origin, nearby)
        if result.route_type == RouteType.DIRECT:
            # Append destination to path
            result.path.append(_build_path_node(destination, "DESTINATION"))
            result.route_type = RouteType.LOCAL_CATCHMENT
            result.note += f" Then travel to {_stations[destination].station_name} ({_stations[destination].city})."
            return result
    
    return ConnectivityResult(
        route_type=RouteType.NOT_FOUND,
        path=[],
        confidence=Confidence.LOW,
        note="No local catchment options found"
    )

def _create_estimated_route(origin: str, destination: str) -> ConnectivityResult:
    """Create estimated route when no graph path exists"""
    
    origin_hub = _find_nearest_hub(origin)
    dest_hub = _find_nearest_hub(destination)
    
    path = []
    path.append(_build_path_node(origin, "ORIGIN"))
    
    if origin_hub and origin_hub != origin:
        path.append(_build_path_node(origin_hub, "HUB"))
    
    if dest_hub and dest_hub != destination and dest_hub != origin_hub:
        path.append(_build_path_node(dest_hub, "HUB"))
    
    path.append(_build_path_node(destination, "DESTINATION"))
    
    # Estimate distance
    if origin in _stations and destination in _stations:
        dist = _haversine_distance(
            _stations[origin].latitude, _stations[origin].longitude,
            _stations[destination].latitude, _stations[destination].longitude
        )
        rail_dist = int(dist * 1.3)  # Rail distance is typically 30% more than direct
    else:
        rail_dist = None
    
    hubs = []
    if origin_hub and origin_hub != origin:
        hubs.append(origin_hub)
    if dest_hub and dest_hub != destination and dest_hub != origin_hub:
        hubs.append(dest_hub)
    
    if hubs:
        hub_names = [_hubs[h].hub_name for h in hubs if h in _hubs]
        note = f"Possible route via {' and '.join(hub_names)}. Check booking partners for exact trains."
    else:
        note = "No common rail route found. Try nearby stations or major junctions."
    
    return ConnectivityResult(
        route_type=RouteType.HUB_BASED if hubs else RouteType.NOT_FOUND,
        path=path,
        confidence=Confidence.LOW,
        note=note,
        total_distance_km=rail_dist,
        via_hubs=hubs,
        zone_changes=len(hubs)
    )

# ============================================================
# PUBLIC API FUNCTIONS
# ============================================================

def get_station_info(station_code: str) -> Optional[Dict]:
    """Get station information"""
    _load_data()
    
    code = _normalize_station_code(station_code)
    if not code or code not in _stations:
        return None
    
    station = _stations[code]
    hub = _hubs.get(code)
    
    return {
        "station_code": code,
        "station_name": station.station_name,
        "city": station.city,
        "district": station.district,
        "state": station.state,
        "zone": station.zone,
        "station_type": station.station_type,
        "is_hub": hub is not None,
        "hub_type": hub.hub_type if hub else None,
        "aliases": station.aliases
    }

def get_all_hubs() -> List[Dict]:
    """Get all railway hubs"""
    _load_data()
    
    return [
        {
            "hub_code": h.hub_code,
            "hub_name": h.hub_name,
            "hub_type": h.hub_type,
            "city": h.city,
            "state": h.state,
            "zone": h.zone,
            "importance_score": h.importance_score,
            "is_zonal_hq": h.is_zonal_hq,
            "is_capital": h.is_capital
        }
        for h in _hubs.values()
    ]

def search_stations(query: str, limit: int = 10) -> List[Dict]:
    """Search stations by name, code, or city"""
    _load_data()
    
    query_lower = query.lower().strip()
    results = []
    
    for code, station in _stations.items():
        score = 0
        
        # Exact code match
        if query_lower == code.lower():
            score = 100
        # Code starts with
        elif code.lower().startswith(query_lower):
            score = 80
        # City exact match
        elif query_lower == station.city.lower():
            score = 75
        # City starts with
        elif station.city.lower().startswith(query_lower):
            score = 70
        # Station name contains
        elif query_lower in station.station_name.lower():
            score = 60
        # Alias match
        elif any(query_lower in alias.lower() for alias in station.aliases):
            score = 50
        
        if score > 0:
            # Boost for hubs and major stations
            if code in _hubs:
                score += 20
            if station.station_type == "MAJOR":
                score += 10
            elif station.station_type == "JUNCTION":
                score += 5
            
            results.append({
                "station_code": code,
                "station_name": station.station_name,
                "city": station.city,
                "state": station.state,
                "zone": station.zone,
                "station_type": station.station_type,
                "is_hub": code in _hubs,
                "score": score
            })
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results[:limit]

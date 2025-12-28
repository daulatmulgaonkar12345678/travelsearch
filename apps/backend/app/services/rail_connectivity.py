"""Rail Connectivity Resolver Service v2.0

Production-grade Indian Railway connectivity system with:
- City-first search (like redBus)
- Multi-station metro support
- Alias-based intelligent search
- Hub-based routing for connections
- Booking partner deep links

Does NOT depend on live IRCTC APIs - uses static graph.
"""

import json
import logging
import os
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass, field
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
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class SearchResultType(str, Enum):
    CITY = "city"
    STATION = "station"

@dataclass
class Station:
    station_id: str
    station_name: str
    city: str
    state: str
    zone: str
    is_major: bool
    trains_passing: int = 0

@dataclass
class City:
    city_id: str
    city_name: str
    state: str
    station_codes: List[str]
    primary_station: str
    is_metro: bool
    population_rank: int = 100

@dataclass
class SearchResult:
    result_type: SearchResultType
    display_name: str
    subtitle: str
    station_codes: List[str]  # For city: all stations, For station: single code
    city_id: Optional[str] = None
    station_code: Optional[str] = None
    is_metro: bool = False
    score: int = 0

@dataclass
class ConnectivityResult:
    route_type: RouteType
    path: List[Dict]
    confidence: Confidence
    note: str
    total_distance_km: Optional[int] = None
    via_hubs: List[str] = field(default_factory=list)
    zone_changes: int = 0
    from_stations: List[str] = field(default_factory=list)
    to_stations: List[str] = field(default_factory=list)

# ============================================================
# GLOBAL DATA STORES
# ============================================================

_stations: Dict[str, Station] = {}
_cities: Dict[str, City] = {}
_aliases: Dict[str, Dict] = {}  # alias -> {resolves_to_station, resolves_to_city, city}
_hubs: Dict[str, Dict] = {}
_graph: Dict[str, List[Tuple[str, int, str]]] = {}
_corridors: List[Dict] = []
_station_to_city: Dict[str, str] = {}  # station_code -> city_id
_loaded = False

# ============================================================
# DATA LOADING
# ============================================================

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
    global _stations, _cities, _aliases, _hubs, _graph, _corridors, _station_to_city, _loaded
    
    if _loaded:
        return
    
    try:
        # Load stations
        with open(_get_data_path("stations.json"), "r") as f:
            data = json.load(f)
            for s in data.get("stations", []):
                station = Station(
                    station_id=s["station_id"],
                    station_name=s["station_name"],
                    city=s["city"],
                    state=s["state"],
                    zone=s.get("zone", ""),
                    is_major=s.get("is_major", False),
                    trains_passing=s.get("trains_passing", 0)
                )
                _stations[station.station_id] = station
        
        logger.info(f"✅ Loaded {len(_stations)} stations")
        
        # Load cities
        with open(_get_data_path("cities.json"), "r") as f:
            data = json.load(f)
            for c in data.get("cities", []):
                city = City(
                    city_id=c["city_id"],
                    city_name=c["city_name"],
                    state=c["state"],
                    station_codes=c["station_codes"],
                    primary_station=c["primary_station"],
                    is_metro=c.get("is_metro", False),
                    population_rank=c.get("population_rank", 100)
                )
                _cities[city.city_id] = city
                
                # Build station to city mapping
                for station_code in city.station_codes:
                    _station_to_city[station_code] = city.city_id
        
        logger.info(f"✅ Loaded {len(_cities)} cities")
        
        # Load aliases
        with open(_get_data_path("station_aliases.json"), "r") as f:
            data = json.load(f)
            for a in data.get("station_aliases", []):
                alias_key = a["alias"].lower()
                _aliases[alias_key] = {
                    "resolves_to_station": a.get("resolves_to_station"),
                    "resolves_to_city": a.get("resolves_to_city"),
                    "city": a.get("city")
                }
        
        logger.info(f"✅ Loaded {len(_aliases)} aliases")
        
        # Load hubs
        try:
            with open(_get_data_path("rail_hubs.json"), "r") as f:
                data = json.load(f)
                for h in data.get("hubs", []):
                    _hubs[h["hub_code"]] = h
            logger.info(f"✅ Loaded {len(_hubs)} hubs")
        except Exception:
            logger.warning("⚠️ rail_hubs.json not found, skipping")
        
        # Load edges and build graph
        try:
            with open(_get_data_path("rail_edges.json"), "r") as f:
                data = json.load(f)
                _corridors.extend(data.get("corridors", []))
                
                for e in data.get("edges", []):
                    from_st = e["from"]
                    to_st = e["to"]
                    dist = e["distance_km"]
                    line = e["line"]
                    
                    if from_st not in _graph:
                        _graph[from_st] = []
                    if to_st not in _graph:
                        _graph[to_st] = []
                    
                    _graph[from_st].append((to_st, dist, line))
                    _graph[to_st].append((from_st, dist, line))
            
            logger.info(f"✅ Loaded {len(_corridors)} corridors, graph has {len(_graph)} nodes")
        except Exception:
            logger.warning("⚠️ rail_edges.json not found, skipping")
        
        _loaded = True
        
    except Exception as e:
        logger.error(f"❌ Failed to load railway data: {e}")
        raise

# ============================================================
# SEARCH FUNCTIONS (CITY-FIRST)
# ============================================================

def search_stations_cities(query: str, limit: int = 10) -> List[SearchResult]:
    """
    Search for cities and stations with city-first results.
    
    When user types "Pune" -> return City result with all stations
    When user types "Shivaji Nagar" -> return specific station
    """
    _load_data()
    
    query_lower = query.lower().strip()
    results: List[SearchResult] = []
    seen_cities = set()
    seen_stations = set()
    
    # 1. Check aliases first (handles old names, spellings)
    if query_lower in _aliases:
        alias_info = _aliases[query_lower]
        
        if alias_info.get("resolves_to_city"):
            city_id = alias_info["resolves_to_city"]
            if city_id in _cities:
                city = _cities[city_id]
                results.append(SearchResult(
                    result_type=SearchResultType.CITY,
                    display_name=city.city_name,
                    subtitle=f"{city.state} • {len(city.station_codes)} stations",
                    station_codes=city.station_codes,
                    city_id=city.city_id,
                    is_metro=city.is_metro,
                    score=200 - city.population_rank
                ))
                seen_cities.add(city_id)
        
        elif alias_info.get("resolves_to_station"):
            station_code = alias_info["resolves_to_station"]
            if station_code in _stations:
                station = _stations[station_code]
                results.append(SearchResult(
                    result_type=SearchResultType.STATION,
                    display_name=f"{station.station_name} ({station_code})",
                    subtitle=f"{station.city}, {station.state}",
                    station_codes=[station_code],
                    station_code=station_code,
                    score=150
                ))
                seen_stations.add(station_code)
    
    # 2. Search cities by name (exact and prefix match)
    for city_id, city in _cities.items():
        if city_id in seen_cities:
            continue
        
        score = 0
        city_name_lower = city.city_name.lower()
        
        if query_lower == city_name_lower:
            score = 200 - city.population_rank  # Exact match
        elif city_name_lower.startswith(query_lower):
            score = 150 - city.population_rank  # Prefix match
        elif query_lower in city_name_lower:
            score = 100 - city.population_rank  # Contains
        
        if score > 0:
            results.append(SearchResult(
                result_type=SearchResultType.CITY,
                display_name=city.city_name,
                subtitle=f"{city.state} • {len(city.station_codes)} station{'s' if len(city.station_codes) > 1 else ''}",
                station_codes=city.station_codes,
                city_id=city.city_id,
                is_metro=city.is_metro,
                score=score
            ))
            seen_cities.add(city_id)
    
    # 3. Search stations by code and name
    for station_code, station in _stations.items():
        if station_code in seen_stations:
            continue
        
        # Skip if already covered by city
        city_id = _station_to_city.get(station_code)
        if city_id in seen_cities:
            continue
        
        score = 0
        station_name_lower = station.station_name.lower()
        code_lower = station_code.lower()
        
        if query_lower == code_lower:
            score = 180  # Exact code match
        elif code_lower.startswith(query_lower):
            score = 140  # Code prefix
        elif station_name_lower.startswith(query_lower):
            score = 120  # Name prefix
        elif query_lower in station_name_lower:
            score = 80  # Name contains
        
        # Boost major stations
        if station.is_major:
            score += 10
        
        if score > 0:
            results.append(SearchResult(
                result_type=SearchResultType.STATION,
                display_name=f"{station.station_name} ({station_code})",
                subtitle=f"{station.city}, {station.state}",
                station_codes=[station_code],
                station_code=station_code,
                score=score
            ))
            seen_stations.add(station_code)
    
    # Sort by score descending
    results.sort(key=lambda x: x.score, reverse=True)
    
    return results[:limit]

def resolve_to_station_codes(input_str: str) -> Tuple[str, List[str]]:
    """
    Resolve a user input to station code(s).
    
    Returns: (input_type, station_codes)
    - For city input: ("city", [all station codes])
    - For station input: ("station", [single code])
    """
    _load_data()
    
    input_lower = input_str.lower().strip()
    input_upper = input_str.upper().strip()
    
    # 1. Check if it's a direct station code
    if input_upper in _stations:
        return ("station", [input_upper])
    
    # 2. Check aliases
    if input_lower in _aliases:
        alias_info = _aliases[input_lower]
        
        if alias_info.get("resolves_to_city"):
            city_id = alias_info["resolves_to_city"]
            if city_id in _cities:
                return ("city", _cities[city_id].station_codes)
        
        if alias_info.get("resolves_to_station"):
            station_code = alias_info["resolves_to_station"]
            if station_code in _stations:
                return ("station", [station_code])
    
    # 3. Check city names
    for city_id, city in _cities.items():
        if input_lower == city.city_name.lower() or input_lower == city_id:
            return ("city", city.station_codes)
    
    # 4. Check station names
    for station_code, station in _stations.items():
        if input_lower == station.station_name.lower():
            return ("station", [station_code])
    
    # 5. Fallback - try partial match on city
    for city_id, city in _cities.items():
        if input_lower in city.city_name.lower():
            return ("city", city.station_codes)
    
    return ("unknown", [])

# ============================================================
# CONNECTIVITY RESOLVER
# ============================================================

def _bfs_find_path(start: str, end: str, max_depth: int = 10) -> Optional[List[str]]:
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

def _find_nearest_hub(station_code: str) -> Optional[str]:
    """Find nearest hub to a station"""
    _load_data()
    
    if station_code in _hubs:
        return station_code
    
    # BFS to find nearest hub
    queue = deque([(station_code, 0)])
    visited = {station_code}
    
    while queue:
        current, dist = queue.popleft()
        
        if current in _hubs:
            return current
        
        if dist > 5:  # Max 5 hops to find hub
            continue
        
        for neighbor, _, _ in _graph.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, dist + 1))
    
    # Fallback: return station's city primary if it's a hub
    city_id = _station_to_city.get(station_code)
    if city_id and city_id in _cities:
        primary = _cities[city_id].primary_station
        if primary in _hubs:
            return primary
    
    return None

def resolve_connectivity(from_input: str, to_input: str) -> ConnectivityResult:
    """
    Resolve connectivity between two inputs (city or station).
    
    Handles:
    - City → City: Expands to all station pairs
    - Station → City: Single origin, multiple destinations
    - Station → Station: Direct lookup
    """
    _load_data()
    
    # Resolve inputs to station codes
    from_type, from_stations = resolve_to_station_codes(from_input)
    to_type, to_stations = resolve_to_station_codes(to_input)
    
    if not from_stations:
        return ConnectivityResult(
            route_type=RouteType.NOT_FOUND,
            path=[],
            confidence=Confidence.LOW,
            note=f"Origin not found: {from_input}",
            from_stations=[],
            to_stations=[]
        )
    
    if not to_stations:
        return ConnectivityResult(
            route_type=RouteType.NOT_FOUND,
            path=[],
            confidence=Confidence.LOW,
            note=f"Destination not found: {to_input}",
            from_stations=from_stations,
            to_stations=[]
        )
    
    # Try to find best route among all station pairs
    best_result = None
    best_path_length = float('inf')
    
    for origin in from_stations:
        for dest in to_stations:
            if origin == dest:
                continue
            
            result = _find_single_route(origin, dest)
            
            if result.route_type != RouteType.NOT_FOUND:
                path_len = len(result.path)
                
                # Prefer DIRECT over HUB_BASED
                if result.route_type == RouteType.DIRECT and best_result and best_result.route_type != RouteType.DIRECT:
                    best_result = result
                    best_path_length = path_len
                elif path_len < best_path_length:
                    best_result = result
                    best_path_length = path_len
    
    if best_result:
        best_result.from_stations = from_stations
        best_result.to_stations = to_stations
        
        # Add context to note
        if from_type == "city" or to_type == "city":
            if len(from_stations) > 1 or len(to_stations) > 1:
                best_result.note += " Multiple station options available."
        
        return best_result
    
    # No route found - create estimated
    return _create_estimated_route(from_stations, to_stations, from_input, to_input)

def _get_location_display_name(input_str: str, loc_type: str, station_codes: List[str]) -> str:
    """Get display name for a location"""
    if loc_type == "city":
        input_lower = input_str.lower()
        for city_id, city in _cities.items():
            if input_lower == city.city_name.lower() or input_lower == city_id:
                return city.city_name
    
    if station_codes and station_codes[0] in _stations:
        return _stations[station_codes[0]].station_name
    
    return input_str

def _find_single_route(origin: str, destination: str) -> ConnectivityResult:
    """Find route between two specific stations"""
    
    # Direct path
    path = _bfs_find_path(origin, destination, max_depth=8)
    if path:
        return ConnectivityResult(
            route_type=RouteType.DIRECT,
            path=[_build_path_node(s, "ORIGIN" if s == origin else "DESTINATION" if s == destination else "VIA") for s in path],
            confidence=Confidence.HIGH,
            note="Direct trains available on this route.",
            via_hubs=[]
        )
    
    # Hub-based routing
    origin_hub = _find_nearest_hub(origin)
    dest_hub = _find_nearest_hub(destination)
    
    if origin_hub and dest_hub:
        # Try via origin hub
        to_hub = _bfs_find_path(origin, origin_hub, max_depth=6)
        from_hub = _bfs_find_path(origin_hub, destination, max_depth=10)
        
        if to_hub and from_hub:
            full_path = to_hub + from_hub[1:]
            hub_name = _hubs.get(origin_hub, {}).get("hub_name", origin_hub)
            return ConnectivityResult(
                route_type=RouteType.HUB_BASED,
                path=[_build_path_node(s, "ORIGIN" if s == origin else "DESTINATION" if s == destination else "HUB" if s == origin_hub else "VIA") for s in full_path],
                confidence=Confidence.HIGH,
                note=f"Most trains travel via {hub_name}. Change of trains may be required.",
                via_hubs=[origin_hub]
            )
        
        # Try via destination hub
        to_hub = _bfs_find_path(origin, dest_hub, max_depth=10)
        from_hub = _bfs_find_path(dest_hub, destination, max_depth=6)
        
        if to_hub and from_hub:
            full_path = to_hub + from_hub[1:]
            hub_name = _hubs.get(dest_hub, {}).get("hub_name", dest_hub)
            return ConnectivityResult(
                route_type=RouteType.HUB_BASED,
                path=[_build_path_node(s, "ORIGIN" if s == origin else "DESTINATION" if s == destination else "HUB" if s == dest_hub else "VIA") for s in full_path],
                confidence=Confidence.HIGH,
                note=f"Most trains travel via {hub_name}. Change of trains may be required.",
                via_hubs=[dest_hub]
            )
    
    return ConnectivityResult(
        route_type=RouteType.NOT_FOUND,
        path=[],
        confidence=Confidence.LOW,
        note="No direct route found in graph."
    )

def _build_path_node(station_code: str, node_type: str) -> Dict:
    """Build a path node for response"""
    station = _stations.get(station_code)
    
    return {
        "station": station_code,
        "type": node_type,
        "station_name": station.station_name if station else station_code,
        "city": station.city if station else None,
        "zone": station.zone if station else None,
        "is_hub": station_code in _hubs
    }

def _create_estimated_route(from_stations: List[str], to_stations: List[str], from_input: str, to_input: str) -> ConnectivityResult:
    """Create estimated route when no graph path exists"""
    
    origin = from_stations[0] if from_stations else None
    destination = to_stations[0] if to_stations else None
    
    path = []
    if origin:
        path.append(_build_path_node(origin, "ORIGIN"))
    
    origin_hub = _find_nearest_hub(origin) if origin else None
    dest_hub = _find_nearest_hub(destination) if destination else None
    
    via_hubs = []
    if origin_hub and origin_hub != origin:
        path.append(_build_path_node(origin_hub, "HUB"))
        via_hubs.append(origin_hub)
    
    if dest_hub and dest_hub != destination and dest_hub != origin_hub:
        path.append(_build_path_node(dest_hub, "HUB"))
        via_hubs.append(dest_hub)
    
    if destination:
        path.append(_build_path_node(destination, "DESTINATION"))
    
    note = "Trains likely available. Check booking partners for schedules."
    if via_hubs:
        hub_names = [_hubs.get(h, {}).get("hub_name", h) for h in via_hubs]
        note = f"Possible route via {' and '.join(hub_names)}. Check booking partners for exact trains."
    
    return ConnectivityResult(
        route_type=RouteType.HUB_BASED if via_hubs else RouteType.NOT_FOUND,
        path=path,
        confidence=Confidence.LOW,
        note=note,
        via_hubs=via_hubs,
        from_stations=from_stations,
        to_stations=to_stations
    )

# ============================================================
# BOOKING PARTNER DEEP LINKS
# ============================================================

BOOKING_PARTNERS = [
    {
        "name": "IRCTC",
        "priority": 1,
        "url_template": "https://www.irctc.co.in/nget/train-search",
        "is_official": True,
        "description": "Official Indian Railways booking"
    },
    {
        "name": "RailYatri",
        "priority": 2,
        "url_template": "https://www.railyatri.in/trains-between-stations?fromStation={from_code}&toStation={to_code}&journeyDate={date}",
        "is_official": False,
        "description": "Seat availability & predictions"
    },
    {
        "name": "ConfirmTkt",
        "priority": 3,
        "url_template": "https://www.confirmtkt.com/train-between-stations/{from_code}/{to_code}",
        "is_official": False,
        "description": "Confirmation predictions"
    },
    {
        "name": "Paytm",
        "priority": 4,
        "url_template": "https://tickets.paytm.com/railways",
        "is_official": False,
        "description": "Easy booking with cashback"
    }
]

def generate_booking_links(from_station: str, to_station: str, date: Optional[str] = None) -> List[Dict]:
    """Generate booking partner deep links"""
    links = []
    
    for partner in BOOKING_PARTNERS:
        url = partner["url_template"]
        
        if "{from_code}" in url:
            url = url.replace("{from_code}", from_station)
        if "{to_code}" in url:
            url = url.replace("{to_code}", to_station)
        if "{date}" in url and date:
            url = url.replace("{date}", date)
        elif "{date}" in url:
            url = url.split("?")[0]  # Remove date param if not provided
        
        links.append({
            "name": partner["name"],
            "url": url,
            "priority": partner["priority"],
            "is_official": partner["is_official"],
            "description": partner["description"]
        })
    
    return links

# ============================================================
# PUBLIC API FUNCTIONS
# ============================================================

def get_station_info(station_code: str) -> Optional[Dict]:
    """Get station information"""
    _load_data()
    
    # Try direct lookup
    if station_code.upper() in _stations:
        station = _stations[station_code.upper()]
        city_id = _station_to_city.get(station_code.upper())
        city = _cities.get(city_id) if city_id else None
        
        return {
            "station_code": station_code.upper(),
            "station_name": station.station_name,
            "city": station.city,
            "state": station.state,
            "zone": station.zone,
            "is_major": station.is_major,
            "trains_passing": station.trains_passing,
            "is_hub": station_code.upper() in _hubs,
            "city_has_multiple_stations": len(city.station_codes) > 1 if city else False,
            "other_stations_in_city": [s for s in city.station_codes if s != station_code.upper()] if city else []
        }
    
    return None

def get_city_info(city_id: str) -> Optional[Dict]:
    """Get city information with all stations"""
    _load_data()
    
    city_key = city_id.lower()
    if city_key in _cities:
        city = _cities[city_key]
        
        stations_info = []
        for code in city.station_codes:
            if code in _stations:
                s = _stations[code]
                stations_info.append({
                    "station_code": code,
                    "station_name": s.station_name,
                    "is_major": s.is_major,
                    "trains_passing": s.trains_passing,
                    "is_primary": code == city.primary_station
                })
        
        # Sort: primary first, then by trains_passing
        stations_info.sort(key=lambda x: (not x["is_primary"], -x["trains_passing"]))
        
        return {
            "city_id": city.city_id,
            "city_name": city.city_name,
            "state": city.state,
            "is_metro": city.is_metro,
            "primary_station": city.primary_station,
            "station_count": len(city.station_codes),
            "stations": stations_info
        }
    
    return None

def get_all_cities() -> List[Dict]:
    """Get all cities sorted by population rank"""
    _load_data()
    
    cities_list = []
    for city in _cities.values():
        cities_list.append({
            "city_id": city.city_id,
            "city_name": city.city_name,
            "state": city.state,
            "is_metro": city.is_metro,
            "station_count": len(city.station_codes),
            "primary_station": city.primary_station,
            "population_rank": city.population_rank
        })
    
    cities_list.sort(key=lambda x: x["population_rank"])
    return cities_list

def get_all_hubs() -> List[Dict]:
    """Get all railway hubs"""
    _load_data()
    
    return [
        {
            "hub_code": code,
            "hub_name": h.get("hub_name", code),
            "hub_type": h.get("hub_type"),
            "city": h.get("city"),
            "state": h.get("state"),
            "zone": h.get("zone"),
            "importance_score": h.get("importance_score", 0)
        }
        for code, h in _hubs.items()
    ]

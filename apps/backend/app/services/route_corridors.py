"""
MSRTC Route Corridors & Intermediate Stops Service
===================================================

Provides "Likely Stops on Route" feature for MSRTC bus routes.

IMPORTANT DISCLAIMER:
- These are INDICATIVE stops based on geographic corridors
- NOT official MSRTC route schedules
- Actual routes may vary
- For precise information, check MSRTC official website

Logic:
1. Define major highway corridors across Maharashtra
2. Map each corridor to ordered list of districts (city_ids)
3. For a route (from → to), find applicable corridor
4. Return major stops (is_search_surface=true) along that corridor
5. Order stops geographically from origin to destination

Corridors Defined:
- Mumbai-Pune Expressway
- Pune-Satara-Kolhapur (NH48)
- Mumbai-Nashik (NH3)
- Nashik-Aurangabad
- Pune-Aurangabad
- Mumbai-Konkan Coast (NH66)
- Nagpur-Amravati-Akola (NH6)
- Pune-Solapur (NH65)
- And more...
"""

from typing import List, Dict, Optional, Tuple
import logging

from app.data.places import (
    get_all_stops,
    get_all_cities,
    get_city_by_id,
    get_stops_by_district,
)

logger = logging.getLogger(__name__)


# ============================================================
# GEOGRAPHIC COORDINATES (Approximate centroids for ordering)
# ============================================================
# city_id -> (latitude, longitude)
# Used for geographic ordering within corridors

CITY_COORDINATES: Dict[int, Tuple[float, float]] = {
    # Konkan Division
    1: (18.9750, 72.8258),   # Mumbai
    2: (19.0760, 72.8777),   # Mumbai Suburban
    3: (19.2183, 72.9781),   # Thane
    4: (19.6967, 72.7699),   # Palghar
    5: (18.5158, 73.1305),   # Raigad (Alibag)
    6: (16.9902, 73.3120),   # Ratnagiri
    7: (16.0167, 73.4667),   # Sindhudurg
    
    # Pune Division
    8: (18.5204, 73.8567),   # Pune
    9: (17.6868, 74.0183),   # Satara
    10: (16.8524, 74.5815),  # Sangli
    11: (16.7050, 74.2433),  # Kolhapur
    12: (17.6599, 75.9064),  # Solapur
    
    # Nashik Division
    13: (19.9975, 73.7898),  # Nashik
    14: (19.0948, 74.7480),  # Ahmednagar
    15: (20.9042, 74.7749),  # Dhule
    16: (21.0077, 75.5626),  # Jalgaon
    17: (21.3680, 74.2394),  # Nandurbar
    
    # Aurangabad Division
    18: (19.8762, 75.3433),  # Aurangabad
    19: (19.8347, 75.8816),  # Jalna
    20: (18.9891, 75.7601),  # Beed
    21: (18.4088, 76.5604),  # Latur
    22: (18.1788, 76.0430),  # Osmanabad
    23: (19.1383, 77.3210),  # Nanded
    24: (19.2704, 76.7603),  # Parbhani
    25: (19.7173, 77.1500),  # Hingoli
    
    # Nagpur Division
    26: (21.1458, 79.0882),  # Nagpur
    27: (20.7453, 78.6022),  # Wardha
    28: (21.1167, 79.6500),  # Bhandara
    29: (21.4500, 80.2000),  # Gondia
    30: (19.9500, 79.3000),  # Chandrapur
    31: (20.1000, 80.0000),  # Gadchiroli
    
    # Amravati Division
    32: (20.9320, 77.7523),  # Amravati
    33: (20.7059, 77.0049),  # Akola
    34: (20.1167, 77.1333),  # Washim
    35: (20.5292, 76.1842),  # Buldhana
    36: (20.3899, 78.1307),  # Yavatmal
}


# ============================================================
# HIGHWAY CORRIDORS - Ordered district sequences
# ============================================================
# Each corridor is an ordered list of city_ids representing
# the geographic sequence of districts along that highway

CORRIDORS = {
    # Mumbai-Pune Expressway (most frequent route)
    "MUMBAI_PUNE": {
        "name": "Mumbai-Pune Expressway",
        "highway": "NH48/Expressway",
        "districts": [1, 2, 3, 5, 8],  # Mumbai → Thane → Raigad → Pune
        "major_stops": ["Panvel", "Lonavala", "Khandala"],
    },
    
    # Pune-Satara-Kolhapur (NH48 South)
    "PUNE_KOLHAPUR": {
        "name": "Pune-Kolhapur Highway",
        "highway": "NH48",
        "districts": [8, 9, 10, 11],  # Pune → Satara → Sangli → Kolhapur
        "major_stops": ["Shirwal", "Satara", "Karad", "Sangli"],
    },
    
    # Mumbai-Nashik (NH3)
    "MUMBAI_NASHIK": {
        "name": "Mumbai-Nashik Highway",
        "highway": "NH3",
        "districts": [1, 3, 4, 13],  # Mumbai → Thane → Palghar → Nashik
        "major_stops": ["Thane", "Kasara", "Igatpuri"],
    },
    
    # Nashik-Aurangabad
    "NASHIK_AURANGABAD": {
        "name": "Nashik-Aurangabad Highway",
        "highway": "NH52",
        "districts": [13, 14, 18],  # Nashik → Ahmednagar → Aurangabad
        "major_stops": ["Shirdi", "Ahmednagar"],
    },
    
    # Pune-Aurangabad
    "PUNE_AURANGABAD": {
        "name": "Pune-Aurangabad Highway",
        "highway": "NH60",
        "districts": [8, 14, 18],  # Pune → Ahmednagar → Aurangabad
        "major_stops": ["Shirur", "Ahmednagar"],
    },
    
    # Mumbai-Konkan Coast (NH66)
    "MUMBAI_KONKAN": {
        "name": "Mumbai-Konkan Coast Highway",
        "highway": "NH66",
        "districts": [1, 5, 6, 7],  # Mumbai → Raigad → Ratnagiri → Sindhudurg
        "major_stops": ["Panvel", "Alibag", "Mahad", "Chiplun", "Ratnagiri"],
    },
    
    # Pune-Solapur (NH65)
    "PUNE_SOLAPUR": {
        "name": "Pune-Solapur Highway",
        "highway": "NH65",
        "districts": [8, 12],  # Pune → Solapur
        "major_stops": ["Indapur", "Pandharpur"],
    },
    
    # Solapur-Latur-Nanded
    "SOLAPUR_NANDED": {
        "name": "Solapur-Latur-Nanded",
        "highway": "NH52",
        "districts": [12, 22, 21, 23],  # Solapur → Osmanabad → Latur → Nanded
        "major_stops": ["Tuljapur", "Latur"],
    },
    
    # Nagpur-Amravati-Akola (NH6)
    "NAGPUR_AKOLA": {
        "name": "Nagpur-Akola Highway",
        "highway": "NH6",
        "districts": [26, 27, 32, 33],  # Nagpur → Wardha → Amravati → Akola
        "major_stops": ["Wardha", "Amravati"],
    },
    
    # Aurangabad-Jalna-Nanded
    "AURANGABAD_NANDED": {
        "name": "Aurangabad-Nanded Highway",
        "highway": "NH52",
        "districts": [18, 19, 24, 23],  # Aurangabad → Jalna → Parbhani → Nanded
        "major_stops": ["Jalna", "Parbhani"],
    },
    
    # Mumbai-Nagpur (via Nashik-Aurangabad)
    "MUMBAI_NAGPUR": {
        "name": "Mumbai-Nagpur Highway",
        "highway": "NH3/NH6",
        "districts": [1, 3, 13, 14, 18, 19, 24, 26],
        "major_stops": ["Nashik", "Aurangabad", "Jalna", "Parbhani"],
    },
    
    # Kolhapur-Sangli-Satara-Pune
    "KOLHAPUR_PUNE": {
        "name": "Kolhapur-Pune Highway",
        "highway": "NH48",
        "districts": [11, 10, 9, 8],  # Kolhapur → Sangli → Satara → Pune
        "major_stops": ["Sangli", "Karad", "Satara"],
    },
    
    # Nashik-Dhule-Nandurbar
    "NASHIK_NANDURBAR": {
        "name": "Nashik-Dhule Highway",
        "highway": "NH3",
        "districts": [13, 15, 17],  # Nashik → Dhule → Nandurbar
        "major_stops": ["Malegaon", "Dhule"],
    },
    
    # Jalgaon-Buldhana-Akola
    "JALGAON_AKOLA": {
        "name": "Jalgaon-Akola Highway",
        "highway": "NH6",
        "districts": [16, 35, 33],  # Jalgaon → Buldhana → Akola
        "major_stops": ["Buldhana"],
    },
    
    # Nagpur-Chandrapur
    "NAGPUR_CHANDRAPUR": {
        "name": "Nagpur-Chandrapur Highway",
        "highway": "NH30",
        "districts": [26, 30],  # Nagpur → Chandrapur
        "major_stops": ["Bhadravati"],
    },
    
    # Pune-Nashik (via Ahmednagar)
    "PUNE_NASHIK": {
        "name": "Pune-Nashik Highway",
        "highway": "NH60",
        "districts": [8, 14, 13],  # Pune → Ahmednagar → Nashik
        "major_stops": ["Shirur", "Sangamner", "Shirdi"],
    },
    
    # Mumbai-Shirdi (via Nashik)
    "MUMBAI_SHIRDI": {
        "name": "Mumbai-Shirdi Highway",
        "highway": "NH3",
        "districts": [1, 3, 13, 14],  # Mumbai → Thane → Nashik → Ahmednagar(Shirdi)
        "major_stops": ["Thane", "Nashik", "Shirdi"],
    },
}


def get_distance(city_id_1: int, city_id_2: int) -> float:
    """
    Calculate approximate distance between two cities using coordinates.
    Returns distance in degrees (not km, but sufficient for ordering).
    """
    if city_id_1 not in CITY_COORDINATES or city_id_2 not in CITY_COORDINATES:
        return float('inf')
    
    lat1, lon1 = CITY_COORDINATES[city_id_1]
    lat2, lon2 = CITY_COORDINATES[city_id_2]
    
    # Simple Euclidean distance (sufficient for ordering)
    return ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5


def find_corridor(from_city_id: int, to_city_id: int) -> Optional[Dict]:
    """
    Find the best matching corridor for a route.
    
    Returns corridor info if found, None otherwise.
    """
    best_corridor = None
    best_score = 0
    
    for corridor_id, corridor in CORRIDORS.items():
        districts = corridor["districts"]
        
        # Check if both cities are in this corridor
        if from_city_id in districts and to_city_id in districts:
            # Score based on directness (fewer districts = better)
            from_idx = districts.index(from_city_id)
            to_idx = districts.index(to_city_id)
            
            # Only consider if from comes before to (or can reverse)
            segment_len = abs(to_idx - from_idx) + 1
            
            # Prefer corridors where the route is a larger portion
            # (i.e., more direct routes)
            score = segment_len / len(districts)
            
            if score > best_score:
                best_score = score
                best_corridor = {
                    "corridor_id": corridor_id,
                    "corridor": corridor,
                    "from_idx": from_idx,
                    "to_idx": to_idx,
                    "reversed": from_idx > to_idx,
                }
    
    return best_corridor


def get_intermediate_districts(
    from_city_id: int,
    to_city_id: int,
) -> List[int]:
    """
    Get ordered list of intermediate districts between origin and destination.
    
    Returns list of city_ids (districts) in geographic order.
    """
    corridor_info = find_corridor(from_city_id, to_city_id)
    
    if corridor_info:
        districts = corridor_info["corridor"]["districts"]
        from_idx = corridor_info["from_idx"]
        to_idx = corridor_info["to_idx"]
        
        # Extract segment
        if from_idx <= to_idx:
            segment = districts[from_idx:to_idx + 1]
        else:
            segment = districts[to_idx:from_idx + 1][::-1]
        
        return segment
    
    # Fallback: Direct route (no known corridor)
    # Just return origin and destination
    return [from_city_id, to_city_id]


def get_likely_stops_on_route(
    from_city_id: int,
    to_city_id: int,
    max_stops: int = 10,
) -> Dict:
    """
    Get likely intermediate stops for a route.
    
    IMPORTANT: These are INDICATIVE stops, not official MSRTC schedules.
    
    Args:
        from_city_id: Origin district ID
        to_city_id: Destination district ID
        max_stops: Maximum number of stops to return
    
    Returns:
        Dict with:
        - stops: List of stop info dicts
        - corridor: Corridor name if found
        - disclaimer: Legal disclaimer text
    """
    # Get corridor info
    corridor_info = find_corridor(from_city_id, to_city_id)
    
    # Get intermediate districts
    districts = get_intermediate_districts(from_city_id, to_city_id)
    
    # Collect major stops from each district
    all_stops = []
    seen_cities = set()
    
    for district_id in districts:
        # Skip origin and destination districts (user already knows those)
        if district_id == from_city_id or district_id == to_city_id:
            continue
        
        # Get city info
        city = get_city_by_id(district_id)
        if not city:
            continue
        
        # Get major stops (search surface only) from this district
        district_stops = get_stops_by_district(district_id)
        major_stops = [
            s for s in district_stops 
            if s.get("is_search_surface", False) and s.get("stop_role") in ["ORIGIN", "TERMINAL"]
        ]
        
        # Take top 2 stops per district
        for stop in major_stops[:2]:
            if city["name_en"] not in seen_cities:
                all_stops.append({
                    "stop_id": stop["stop_id"],
                    "stop_name": stop["name_local"],
                    "stop_name_en": stop.get("normalized_key", "").replace("-", " ").title(),
                    "city": city["name_en"],
                    "city_local": city["name_local"],
                    "district_id": district_id,
                    "is_major": True,
                })
                seen_cities.add(city["name_en"])
                break  # One stop per city is enough
    
    # Order by geographic position along corridor
    if corridor_info:
        corridor_districts = corridor_info["corridor"]["districts"]
        
        def get_order(stop):
            try:
                return corridor_districts.index(stop["district_id"])
            except ValueError:
                return 999
        
        # Sort by corridor order
        if corridor_info["reversed"]:
            all_stops.sort(key=get_order, reverse=True)
        else:
            all_stops.sort(key=get_order)
    
    # Limit results
    stops = all_stops[:max_stops]
    
    # Build response
    from_city = get_city_by_id(from_city_id)
    to_city = get_city_by_id(to_city_id)
    
    return {
        "from_city": from_city["name_en"] if from_city else f"City {from_city_id}",
        "to_city": to_city["name_en"] if to_city else f"City {to_city_id}",
        "corridor_name": corridor_info["corridor"]["name"] if corridor_info else None,
        "highway": corridor_info["corridor"]["highway"] if corridor_info else None,
        "stops": stops,
        "stop_count": len(stops),
        "disclaimer": (
            "These are indicative stops based on common MSRTC routes. "
            "Actual bus routes may vary. Please verify with MSRTC official "
            "timetable at msrtc.maharashtra.gov.in for accurate information."
        ),
        "source": "corridor" if corridor_info else "direct",
    }


def get_route_summary(from_city_id: int, to_city_id: int) -> Dict:
    """
    Get a summary of a route including likely stops.
    
    Returns minimal info suitable for display in search results.
    """
    result = get_likely_stops_on_route(from_city_id, to_city_id, max_stops=5)
    
    # Extract just stop names for compact display
    stop_names = [s["city"] for s in result["stops"]]
    
    return {
        "via": stop_names,
        "via_text": " → ".join(stop_names) if stop_names else "Direct",
        "corridor": result["corridor_name"],
        "highway": result["highway"],
        "stop_count": result["stop_count"],
    }


# ============================================================
# CITY NAME TO ID MAPPING (for API convenience)
# ============================================================

def get_city_id_by_name(name: str) -> Optional[int]:
    """Get city_id from city name (English or normalized)."""
    name_lower = name.lower().strip()
    
    for city in get_all_cities():
        if (city["name_en"].lower() == name_lower or 
            city["normalized_key"] == name_lower or
            city["name_local"] == name):
            return city["city_id"]
    
    return None


def get_likely_stops_by_city_names(
    from_city: str,
    to_city: str,
    max_stops: int = 10,
) -> Dict:
    """
    Get likely stops using city names instead of IDs.
    
    Convenience wrapper for API usage.
    """
    from_id = get_city_id_by_name(from_city)
    to_id = get_city_id_by_name(to_city)
    
    if not from_id:
        return {"error": f"Unknown origin city: {from_city}"}
    if not to_id:
        return {"error": f"Unknown destination city: {to_city}"}
    
    return get_likely_stops_on_route(from_id, to_id, max_stops)

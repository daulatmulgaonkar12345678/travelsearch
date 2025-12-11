"""
Hub Airport Configurations

Defines major hub airports by region for connecting flight composition.
Used when direct flights are not available.
"""

from typing import Dict, List, Set

# Major hubs by region
REGIONAL_HUBS: Dict[str, List[str]] = {
    "IN": ["DEL", "BOM", "BLR"],  # India
    "EU": ["LHR", "AMS", "FRA", "CDG", "MAD", "FCO"],  # Europe
    "US": ["JFK", "ORD", "ATL", "LAX", "DFW", "DEN"],  # United States
    "ME": ["DXB", "DOH", "AUH"],  # Middle East
    "SG": ["SIN"],  # Singapore
    "CN": ["PEK", "PVG", "CAN"],  # China
    "JP": ["NRT", "HND"],  # Japan
    "AU": ["SYD", "MEL"],  # Australia
    "CA": ["YYZ", "YVR"],  # Canada
}

# Preferred hub for small airports (origin -> preferred hub)
PREFERRED_HUBS: Dict[str, str] = {
    "PNQ": "BOM",  # Pune -> Mumbai
    "GOI": "BOM",  # Goa -> Mumbai
    "COK": "BLR",  # Kochi -> Bangalore
    "HYD": "DEL",  # Hyderabad -> Delhi
    "MAA": "BLR",  # Chennai -> Bangalore
    "CCU": "DEL",  # Kolkata -> Delhi
    "AMD": "DEL",  # Ahmedabad -> Delhi
    "JAI": "DEL",  # Jaipur -> Delhi
}

# Airport to region mapping
AIRPORT_REGIONS: Dict[str, str] = {
    # India
    "DEL": "IN", "BOM": "IN", "BLR": "IN", "PNQ": "IN", "HYD": "IN",
    "MAA": "IN", "CCU": "IN", "GOI": "IN", "COK": "IN", "AMD": "IN",
    # US
    "JFK": "US", "LAX": "US", "ORD": "US", "ATL": "US", "BOS": "US",
    "DFW": "US", "DEN": "US", "SFO": "US", "SEA": "US", "MIA": "US",
    # Europe
    "LHR": "EU", "AMS": "EU", "FRA": "EU", "CDG": "EU", "MAD": "EU",
    "FCO": "EU", "MUC": "EU", "ZRH": "EU", "VIE": "EU", "IST": "EU",
    # Middle East
    "DXB": "ME", "DOH": "ME", "AUH": "ME",
    # Asia
    "SIN": "SG", "HKG": "SG", "KUL": "SG",
    "PEK": "CN", "PVG": "CN", "CAN": "CN",
    "NRT": "JP", "HND": "JP",
    # Australia
    "SYD": "AU", "MEL": "AU",
    # Canada
    "YYZ": "CA", "YVR": "CA",
}

def get_region(iata: str) -> str:
    """Get region for an airport IATA code."""
    return AIRPORT_REGIONS.get(iata, "OTHER")

def get_regional_hubs(region: str) -> List[str]:
    """Get list of hubs for a region."""
    return REGIONAL_HUBS.get(region, [])

def get_preferred_hub(origin: str) -> str:
    """Get preferred hub for an origin airport."""
    return PREFERRED_HUBS.get(origin, "")

def get_candidate_hubs(origin: str, destination: str, max_hubs: int = 3) -> List[str]:
    """
    Get candidate hub airports for connecting flights.
    
    Strategy:
    1. Check if origin has a preferred hub
    2. Get regional hubs for origin region
    3. Get regional hubs for destination region
    4. Combine and deduplicate
    """
    candidates: Set[str] = set()
    
    # Preferred hub for origin
    preferred = get_preferred_hub(origin)
    if preferred:
        candidates.add(preferred)
    
    # Regional hubs
    origin_region = get_region(origin)
    dest_region = get_region(destination)
    
    if origin_region != "OTHER":
        candidates.update(get_regional_hubs(origin_region))
    
    if dest_region != "OTHER" and dest_region != origin_region:
        candidates.update(get_regional_hubs(dest_region))
    
    # Don't use origin or destination as hubs
    candidates.discard(origin)
    candidates.discard(destination)
    
    # Return up to max_hubs
    return list(candidates)[:max_hubs]

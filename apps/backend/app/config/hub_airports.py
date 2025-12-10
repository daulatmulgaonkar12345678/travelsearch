"""
Regional Hub Airports Configuration

Major hub airports by region for intelligent fallback routing.
Used when direct routes return zero results.
"""

from typing import Dict, List

# Major regional hubs by continent/region
REGIONAL_HUBS: Dict[str, List[str]] = {
    # India
    "IN": ["BOM", "DEL", "BLR", "HYD", "MAA", "CCU"],
    
    # Europe
    "EU": ["LHR", "CDG", "AMS", "FRA", "MAD", "FCO", "MUC", "ZRH"],
    
    # Middle East
    "ME": ["DXB", "DOH", "AUH", "JED", "RUH", "KWI"],
    
    # Southeast Asia
    "SEA": ["SIN", "BKK", "KUL", "CGK", "MNL", "HAN"],
    
    # East Asia
    "EA": ["NRT", "HND", "ICN", "PVG", "PEK", "HKG", "TPE"],
    
    # North America
    "NA": ["JFK", "LAX", "ORD", "ATL", "DFW", "SFO", "MIA", "IAH"],
    
    # Oceania
    "OC": ["SYD", "MEL", "BNE", "AKL", "PER"],
    
    # Africa
    "AF": ["JNB", "CPT", "CAI", "NBO", "ADD", "LOS"],
    
    # South America
    "SA": ["GRU", "EZE", "GIG", "SCL", "BOG", "LIM"],
}

# Country to region mapping
COUNTRY_TO_REGION: Dict[str, str] = {
    "IN": "IN",
    "US": "NA",
    "GB": "EU",
    "FR": "EU",
    "DE": "EU",
    "NL": "EU",
    "AE": "ME",
    "QA": "ME",
    "SA": "ME",
    "SG": "SEA",
    "TH": "SEA",
    "MY": "SEA",
    "JP": "EA",
    "KR": "EA",
    "CN": "EA",
    "AU": "OC",
    "NZ": "OC",
    "ZA": "AF",
    "EG": "AF",
    "BR": "SA",
    "AR": "SA",
    # Add more as needed
}

def get_regional_hubs(country_code: str, exclude: List[str] = None) -> List[str]:
    """
    Get regional hub airports for a country.
    
    Args:
        country_code: ISO 2-letter country code
        exclude: List of airport IATAs to exclude (e.g., origin itself)
    
    Returns:
        List of hub airport IATA codes
    """
    exclude = exclude or []
    region = COUNTRY_TO_REGION.get(country_code)
    
    if not region:
        # If country not mapped, return empty (no fallback hubs)
        return []
    
    hubs = REGIONAL_HUBS.get(region, [])
    
    # Filter out excluded airports
    return [hub for hub in hubs if hub not in exclude]


def get_top_hubs(country_code: str, limit: int = 3, exclude: List[str] = None) -> List[str]:
    """
    Get top N hub airports for a country.
    
    Args:
        country_code: ISO 2-letter country code
        limit: Maximum number of hubs to return
        exclude: List of airport IATAs to exclude
    
    Returns:
        List of top hub airport IATA codes (limited)
    """
    hubs = get_regional_hubs(country_code, exclude)
    return hubs[:limit]

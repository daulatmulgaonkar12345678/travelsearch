"""
Airport Validator Service

Single source of truth for airport validation.
Validates IATA codes against the canonical airport database.

Used by:
- Search orchestrator
- Autocomplete
- SEO route generation
- API request validation
"""

import json
import logging
from pathlib import Path
from typing import Dict, Set, Optional, List

logger = logging.getLogger(__name__)

# Canonical airport database path
AIRPORTS_PATH = Path("/app/data/airports-full.json")

# In-memory cache
_airports_by_iata: Dict[str, Dict] = {}
_valid_iata_codes: Set[str] = set()
_airports_loaded = False


def _load_airports():
    """Load airports from canonical database."""
    global _airports_by_iata, _valid_iata_codes, _airports_loaded
    
    if _airports_loaded:
        return
    
    try:
        with open(AIRPORTS_PATH, 'r', encoding='utf-8') as f:
            airports = json.load(f)
        
        for airport in airports:
            iata = airport.get('iata', '').upper()
            if iata and len(iata) == 3:
                _airports_by_iata[iata] = airport
                _valid_iata_codes.add(iata)
        
        _airports_loaded = True
        logger.info(f"✅ Airport validator loaded {len(_valid_iata_codes)} valid IATA codes")
    
    except Exception as e:
        logger.error(f"❌ Failed to load airports: {e}")
        _airports_loaded = True  # Mark as loaded to avoid repeated failures


# Load on module import
_load_airports()


def is_valid_airport(iata_code: str) -> bool:
    """
    Check if an IATA code is valid (exists in our database).
    
    Args:
        iata_code: 3-letter IATA airport code
    
    Returns:
        True if valid, False otherwise
    """
    if not iata_code:
        return False
    
    _load_airports()
    return iata_code.upper() in _valid_iata_codes


def get_airport(iata_code: str) -> Optional[Dict]:
    """
    Get airport details by IATA code.
    
    Returns:
        Airport dict or None if not found
    """
    if not iata_code:
        return None
    
    _load_airports()
    return _airports_by_iata.get(iata_code.upper())


def get_airport_name(iata_code: str) -> str:
    """Get airport name by IATA code."""
    airport = get_airport(iata_code)
    if airport:
        return airport.get('name', iata_code)
    return iata_code


def get_airport_city(iata_code: str) -> str:
    """Get city name by IATA code."""
    airport = get_airport(iata_code)
    if airport:
        return airport.get('city', iata_code)
    return iata_code


def is_indian_airport(iata_code: str) -> bool:
    """Check if airport is in India."""
    airport = get_airport(iata_code)
    if airport:
        country = airport.get('iso_country', airport.get('country', ''))
        return country.upper() in ('IN', 'INDIA')
    return False


def is_apac_airport(iata_code: str) -> bool:
    """Check if airport is in Asia-Pacific region."""
    airport = get_airport(iata_code)
    if not airport:
        return False
    
    country = airport.get('iso_country', airport.get('country', '')).upper()
    
    # APAC country codes
    apac_countries = {
        'IN', 'LK', 'NP', 'BD', 'PK',  # South Asia
        'TH', 'SG', 'MY', 'ID', 'VN', 'PH', 'MM', 'KH', 'LA',  # Southeast Asia
        'JP', 'KR', 'CN', 'HK', 'TW', 'MO',  # East Asia
        'AU', 'NZ', 'FJ', 'PG',  # Oceania
    }
    
    return country in apac_countries


def get_all_indian_airports() -> List[Dict]:
    """Get all Indian airports."""
    _load_airports()
    return [
        airport for airport in _airports_by_iata.values()
        if airport.get('iso_country', '').upper() == 'IN'
    ]


def get_all_apac_airports() -> List[Dict]:
    """Get all APAC airports."""
    _load_airports()
    
    apac_countries = {
        'IN', 'LK', 'NP', 'BD', 'PK',
        'TH', 'SG', 'MY', 'ID', 'VN', 'PH', 'MM', 'KH', 'LA',
        'JP', 'KR', 'CN', 'HK', 'TW', 'MO',
        'AU', 'NZ', 'FJ', 'PG',
    }
    
    return [
        airport for airport in _airports_by_iata.values()
        if airport.get('iso_country', '').upper() in apac_countries
    ]


def validate_route(origin: str, destination: str) -> tuple[bool, Optional[str]]:
    """
    Validate a flight route.
    
    Returns:
        (is_valid, error_message)
    """
    if not origin:
        return False, "Origin airport is required"
    
    if not destination:
        return False, "Destination airport is required"
    
    origin = origin.upper()
    destination = destination.upper()
    
    if origin == destination:
        return False, "Origin and destination must be different"
    
    if not is_valid_airport(origin):
        return False, f"Invalid origin airport: {origin}"
    
    if not is_valid_airport(destination):
        return False, f"Invalid destination airport: {destination}"
    
    return True, None


def get_stats() -> Dict:
    """Get airport database statistics."""
    _load_airports()
    
    india_count = len([
        a for a in _airports_by_iata.values() 
        if a.get('iso_country', '').upper() == 'IN'
    ])
    
    return {
        "total_airports": len(_valid_iata_codes),
        "india_airports": india_count,
        "loaded": _airports_loaded
    }

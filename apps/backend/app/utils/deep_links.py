"""Bus Deep Link Generator - Proper URL Generation for Booking Partners
========================================================================

PROBLEM SOLVED:
- Deep links with undefined, city IDs, or internal IDs break partner pages
- Partners like redBus, Paytm, AbhiBus only accept normalized city slugs

RULES:
1. Use SLUG-ONLY URLs (no city IDs, no query params)
2. Normalize city names to slugs (lowercase, hyphenated)
3. Remove suffixes like "bus stand", "bus station", "msrtc", "depot"
4. Resolve city aliases (e.g., "Chhatrapati Sambhaji Nagar" -> "aurangabad")
5. Fail-safe: return partner homepage if slug generation fails

CORRECT FORMAT:
- redBus:   https://www.redbus.in/bus-tickets/pune-to-kolhapur
- Paytm:    https://tickets.paytm.com/bus/pune-to-kolhapur
- AbhiBus:  https://www.abhibus.com/bus-tickets/pune-to-kolhapur
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================
# CITY ALIAS MAP - Canonical Name Resolution
# ============================================================

CITY_ALIASES = {
    # Official name changes
    "chhatrapati sambhaji nagar": "aurangabad",
    "chhatrapati-sambhaji-nagar": "aurangabad",
    "csn": "aurangabad",
    "sambhaji nagar": "aurangabad",
    "sambhajinagar": "aurangabad",
    
    # Historical names
    "bombay": "mumbai",
    "poona": "pune",
    "baroda": "vadodara",
    "calcutta": "kolkata",
    "madras": "chennai",
    "bangalore": "bengaluru",
    "mysore": "mysuru",
    
    # Common variations for Maharashtra cities
    "mumbai central": "mumbai",
    "mumbai cst": "mumbai",
    "dadar": "mumbai",
    "thane west": "thane",
    "thane east": "thane",
    "navi-mumbai": "navi-mumbai",
    "new mumbai": "navi-mumbai",
    
    # Pune variations
    "pune swargate": "pune",
    "pune shivajinagar": "pune",
    "pune station": "pune",
    "pimpri": "pune",
    "pimpri chinchwad": "pune",
    "pimpri-chinchwad": "pune",
    "pcmc": "pune",
    
    # District HQ variations
    "kolhapur cbs": "kolhapur",
    "kolhapur mahalaxmi": "kolhapur",
    "sangli miraj": "sangli",
    "miraj": "sangli",
    "ichalkaranji": "kolhapur",
    
    # Common misspellings
    "nasik": "nashik",
    "nagpore": "nagpur",
    "sholapur": "solapur",
    "ratanagiri": "ratnagiri",
    
    # Tourist destinations - use main city
    "ajanta caves": "aurangabad",
    "ajanta": "aurangabad",
    "ellora caves": "aurangabad",
    "ellora": "aurangabad",
    "shirdi": "shirdi",  # Keep as is - popular destination
    "mahabaleshwar": "mahabaleshwar",  # Keep as is
    "lonavala": "lonavala",  # Keep as is
    "panchgani": "panchgani",  # Keep as is
    "matheran": "neral",  # Use nearest station
    "ganpatipule": "ratnagiri",
    "trimbakeshwar": "nashik",
    "bhimashankar": "pune",
    
    # Alibaug variations
    "alibag": "alibaug",
    "alibagh": "alibaug",
}

# ============================================================
# SUFFIXES TO REMOVE
# ============================================================

SUFFIXES_TO_REMOVE = [
    "bus stand",
    "bus station",
    "bus depot",
    "bus terminal",
    "st stand",
    "st depot",
    "msrtc",
    "msrtc depot",
    "cbs",  # Central Bus Station
    "depot",
    "terminal",
    "junction",
    "railway station",
    "rly station",
    "station",
    "(msrtc)",
    "(st)",
]


# ============================================================
# BOOKING PARTNER CONFIGURATIONS
# ============================================================

class BookingPartner:
    """Booking partner configuration."""
    
    REDBUS = {
        "name": "redBus",
        "slug": "redbus",
        "priority": 1,
        "url_template": "https://www.redbus.in/bus-tickets/{from_slug}-to-{to_slug}",
        "homepage": "https://www.redbus.in",
        "description": "India's largest bus booking platform",
        "is_official": False,
    }
    
    MSRTC_OFFICIAL = {
        "name": "MSRTC Official",
        "slug": "msrtc",
        "priority": 2,
        "url_template": "https://public.msrtcors.com/ticket/",
        "homepage": "https://public.msrtcors.com/ticket/",
        "description": "Official MSRTC Online Reservation",
        "is_official": True,
    }
    
    ABHIBUS = {
        "name": "AbhiBus",
        "slug": "abhibus",
        "priority": 3,
        "url_template": "https://www.abhibus.com/bus-tickets/{from_slug}-to-{to_slug}",
        "homepage": "https://www.abhibus.com",
        "description": "Wide operator coverage",
        "is_official": False,
    }
    
    PAYTM = {
        "name": "Paytm Bus",
        "slug": "paytm",
        "priority": 4,
        "url_template": "https://tickets.paytm.com/bus/{from_slug}-to-{to_slug}",
        "homepage": "https://tickets.paytm.com/bus",
        "description": "Cashback & easy booking",
        "is_official": False,
    }
    
    @classmethod
    def all_partners(cls) -> List[Dict]:
        """Get all booking partners in priority order."""
        return [
            cls.REDBUS,
            cls.MSRTC_OFFICIAL,
            cls.ABHIBUS,
            cls.PAYTM,
        ]


# ============================================================
# SLUG NORMALIZATION
# ============================================================

def normalize_city_slug(city_name: str) -> Optional[str]:
    """
    Normalize a city name to a URL-safe slug.
    
    RULES:
    1. Convert to lowercase
    2. Remove suffixes like "bus stand", "depot", etc.
    3. Remove special characters (keep only alphanumeric and spaces)
    4. Replace spaces with hyphens
    5. Resolve aliases to canonical names
    
    Args:
        city_name: Raw city name from search
    
    Returns:
        Normalized slug or None if invalid
    
    Examples:
        "Pune Swargate" -> "pune"
        "Kolhapur Bus Stand" -> "kolhapur"
        "Chhatrapati Sambhaji Nagar" -> "aurangabad"
        "Mumbai Central" -> "mumbai"
    """
    if not city_name:
        return None
    
    # Step 1: Lowercase
    slug = city_name.lower().strip()
    
    # Step 2: Remove suffixes (case insensitive)
    for suffix in SUFFIXES_TO_REMOVE:
        # Remove suffix if it appears at the end
        if slug.endswith(suffix):
            slug = slug[:-len(suffix)].strip()
        # Also check with leading space
        slug = re.sub(rf'\s+{re.escape(suffix)}\s*$', '', slug, flags=re.IGNORECASE)
    
    # Step 3: Remove parenthetical content
    slug = re.sub(r'\([^)]*\)', '', slug).strip()
    
    # Step 4: Remove special characters (keep only alphanumeric and spaces)
    slug = re.sub(r'[^a-z0-9\s]', '', slug)
    
    # Step 5: Normalize whitespace
    slug = re.sub(r'\s+', ' ', slug).strip()
    
    # Step 6: Check alias map BEFORE converting to hyphens
    if slug in CITY_ALIASES:
        slug = CITY_ALIASES[slug]
    
    # Step 7: Replace spaces with hyphens
    slug = slug.replace(' ', '-')
    
    # Step 8: Check alias map AFTER converting to hyphens (for hyphenated aliases)
    if slug in CITY_ALIASES:
        slug = CITY_ALIASES[slug]
    
    # Step 9: Remove any trailing/leading hyphens
    slug = slug.strip('-')
    
    # Step 10: Collapse multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Validate: must have at least 2 characters
    if len(slug) < 2:
        return None
    
    return slug


# ============================================================
# DEEP LINK GENERATION
# ============================================================

def build_bus_deep_link(
    partner: Dict,
    from_city: str,
    to_city: str,
) -> str:
    """
    Build a deep link for a booking partner.
    
    RULES:
    - Use SLUG-ONLY URLs
    - NO city IDs, NO query params (except homepage)
    - Falls back to partner homepage on any error
    
    Args:
        partner: Partner configuration dict
        from_city: Origin city name
        to_city: Destination city name
    
    Returns:
        Valid deep link URL
    """
    # Normalize slugs
    from_slug = normalize_city_slug(from_city)
    to_slug = normalize_city_slug(to_city)
    
    # FAIL-SAFE: If slugs are invalid, return homepage
    if not from_slug or not to_slug:
        logger.warning(f"Invalid slugs for deep link: from='{from_city}'->{from_slug}, to='{to_city}'->{to_slug}")
        return partner.get("homepage", partner.get("url_template", ""))
    
    # FAIL-SAFE: If from == to (shouldn't happen, but guard)
    if from_slug == to_slug:
        logger.warning(f"Same origin and destination: {from_slug}")
        return partner.get("homepage", partner.get("url_template", ""))
    
    # MSRTC Official doesn't support deep linking to specific routes
    if partner.get("is_official"):
        return partner.get("homepage", partner.get("url_template", ""))
    
    # Build URL using template
    url_template = partner.get("url_template", "")
    
    try:
        url = url_template.format(
            from_slug=from_slug,
            to_slug=to_slug,
            origin=from_slug,  # Legacy support
            destination=to_slug,  # Legacy support
        )
        return url
    except Exception as e:
        logger.error(f"Error building deep link: {e}")
        return partner.get("homepage", url_template)


def generate_booking_partners(
    from_city: str,
    to_city: str,
) -> List[Dict]:
    """
    Generate booking partner links for a route.
    
    This is the main function to use when creating bus offers.
    
    Args:
        from_city: Origin city name
        to_city: Destination city name
    
    Returns:
        List of booking partner dicts with valid URLs
    """
    booking_partners = []
    
    for partner in BookingPartner.all_partners():
        url = build_bus_deep_link(partner, from_city, to_city)
        
        booking_partners.append({
            "name": partner["name"],
            "url": url,
            "priority": partner["priority"],
            "is_official": partner.get("is_official", False),
            "description": partner["description"],
        })
    
    return booking_partners


# ============================================================
# VALIDATION & TESTING
# ============================================================

def validate_deep_link(url: str) -> bool:
    """
    Validate that a deep link is properly formatted.
    
    CHECKS:
    - No 'undefined' in URL
    - No city IDs in URL
    - No empty segments
    """
    if not url:
        return False
    
    # Check for common issues
    invalid_patterns = [
        'undefined',
        'null',
        'NaN',
        'cityId=',
        'fromCityId=',
        'toCityId=',
        'srcId=',
        'destId=',
        '-to-$',  # Missing destination
        '^https?://[^/]+/bus-tickets/-',  # Missing origin
    ]
    
    for pattern in invalid_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return False
    
    return True


# ============================================================
# TEST CASES
# ============================================================

if __name__ == "__main__":
    # Test slug normalization
    test_cases = [
        ("Pune Swargate", "pune"),
        ("Kolhapur Bus Stand", "kolhapur"),
        ("Chhatrapati Sambhaji Nagar", "aurangabad"),
        ("Mumbai Central", "mumbai"),
        ("Satara", "satara"),
        ("Karad", "karad"),
        ("Ratnagiri Bus Station", "ratnagiri"),
        ("Nashik CBS", "nashik"),
        ("Ajanta Caves", "aurangabad"),
        ("", None),
    ]
    
    print("=== Slug Normalization Tests ===")
    for input_city, expected in test_cases:
        result = normalize_city_slug(input_city)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_city}' -> '{result}' (expected: '{expected}')")
    
    print("\n=== Deep Link Generation Tests ===")
    routes = [
        ("Pune Swargate", "Kolhapur Bus Stand"),
        ("Mumbai Central", "Nashik CBS"),
        ("Satara", "Karad"),
        ("Chhatrapati Sambhaji Nagar", "Mumbai"),
    ]
    
    for from_city, to_city in routes:
        print(f"\n{from_city} → {to_city}:")
        partners = generate_booking_partners(from_city, to_city)
        for p in partners:
            valid = "✅" if validate_deep_link(p["url"]) else "❌"
            print(f"  {valid} {p['name']}: {p['url']}")

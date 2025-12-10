#!/usr/bin/env python3
"""
Airport Dataset Builder

Downloads, merges, and deduplicates airport data from OurAirports and OpenFlights.
Generates a production-ready airports-full.json with aliases for fuzzy search.

Data Sources:
- OurAirports: https://ourairports.com/data/ (Primary - more metadata)
- OpenFlights: https://github.com/jpatokal/openflights (Secondary - fill gaps)

Output: /app/data/airports-full.json
"""

import json
import csv
import urllib.request
import unicodedata
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, asdict
import sys
from pathlib import Path

# Data source URLs
OURAIRPORTS_AIRPORTS_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
OPENFLIGHTS_AIRPORTS_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"

# Output path
OUTPUT_PATH = Path("/app/data/airports-full.json")

# Indian airports to explicitly verify
REQUIRED_INDIAN_AIRPORTS = {
    "SAG": "Shirdi",
    "KLH": "Kolhapur", 
    "RTC": "Ratnagiri",
    "IXC": "Chandigarh",
    "PNQ": "Pune",
}


@dataclass
class Airport:
    """Normalized airport data structure"""
    iata: str
    icao: Optional[str]
    name: str
    city: str
    country: str
    iso_country: str
    lat: float
    lon: float
    timezone: Optional[str]
    type: str  # large_airport, medium_airport, small_airport
    aliases: List[str]
    
    def to_dict(self):
        """Convert to dictionary, excluding None values"""
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}


def normalize_string(s: str) -> str:
    """Normalize string to NFC and lowercase for indexing"""
    if not s:
        return ""
    # NFC normalization
    normalized = unicodedata.normalize('NFC', s)
    return normalized.lower().strip()


def generate_aliases(airport_data: Dict) -> List[str]:
    """Generate search aliases for an airport"""
    aliases = []
    
    # Add normalized forms
    if airport_data.get('city'):
        aliases.append(normalize_string(airport_data['city']))
    
    if airport_data.get('name'):
        name = normalize_string(airport_data['name'])
        aliases.append(name)
        # Remove common suffixes for shorter forms
        for suffix in [' airport', ' international airport', ' intl', ' regional']:
            if name.endswith(suffix):
                aliases.append(name.replace(suffix, '').strip())
    
    if airport_data.get('iata'):
        aliases.append(normalize_string(airport_data['iata']))
    
    if airport_data.get('icao'):
        aliases.append(normalize_string(airport_data['icao']))
    
    # Deduplicate while preserving order
    seen = set()
    unique_aliases = []
    for alias in aliases:
        if alias and alias not in seen:
            seen.add(alias)
            unique_aliases.append(alias)
    
    return unique_aliases


def download_ourairports() -> List[Dict]:
    """Download and parse OurAirports dataset"""
    print("📥 Downloading OurAirports data...")
    
    try:
        with urllib.request.urlopen(OURAIRPORTS_AIRPORTS_URL) as response:
            content = response.read().decode('utf-8')
        
        reader = csv.DictReader(content.splitlines())
        airports = list(reader)
        
        print(f"✅ Downloaded {len(airports)} airports from OurAirports")
        return airports
    
    except Exception as e:
        print(f"❌ Failed to download OurAirports: {e}")
        return []


def download_openflights() -> List[Dict]:
    """Download and parse OpenFlights dataset"""
    print("📥 Downloading OpenFlights data...")
    
    try:
        with urllib.request.urlopen(OPENFLIGHTS_AIRPORTS_URL) as response:
            content = response.read().decode('utf-8')
        
        # OpenFlights uses custom format (not standard CSV with headers)
        # Fields: ID, Name, City, Country, IATA, ICAO, Lat, Lon, Alt, TZ offset, DST, Timezone, Type, Source
        airports = []
        for line in content.splitlines():
            if not line.strip():
                continue
            
            parts = line.split(',')
            if len(parts) < 14:
                continue
            
            # Clean quotes
            parts = [p.strip('"') for p in parts]
            
            airport = {
                'name': parts[1],
                'city': parts[2],
                'country': parts[3],
                'iata_code': parts[4] if parts[4] != '\\N' else '',
                'icao_code': parts[5] if parts[5] != '\\N' else '',
                'latitude_deg': parts[6],
                'longitude_deg': parts[7],
                'timezone': parts[11] if parts[11] != '\\N' else '',
                'type': 'airport',
            }
            airports.append(airport)
        
        print(f"✅ Downloaded {len(airports)} airports from OpenFlights")
        return airports
    
    except Exception as e:
        print(f"❌ Failed to download OpenFlights: {e}")
        return []


def filter_active_airports(airports: List[Dict], source: str) -> List[Dict]:
    """Filter to keep only active, relevant airports"""
    filtered = []
    
    for airport in airports:
        # Skip if no name
        if not airport.get('name'):
            continue
        
        # Get airport type
        airport_type = airport.get('type', '').lower()
        
        # Skip helipads, closed, and non-relevant
        if source == 'ourairports':
            if airport_type in ['heliport', 'closed', 'seaplane_base', 'balloonport']:
                continue
            if airport.get('scheduled_service', 'no').lower() != 'yes':
                # Allow if it has IATA (likely important)
                if not airport.get('iata_code'):
                    continue
        
        filtered.append(airport)
    
    print(f"✅ Filtered to {len(filtered)} active airports ({source})")
    return filtered


def merge_and_deduplicate(ourairports: List[Dict], openflights: List[Dict]) -> Dict[str, Airport]:
    """Merge datasets and deduplicate by IATA code"""
    print("🔄 Merging and deduplicating...")
    
    airports_by_iata: Dict[str, Airport] = {}
    
    # Process OurAirports first (primary source)
    for raw in ourairports:
        iata = raw.get('iata_code', '').strip().upper()
        if not iata or len(iata) != 3:
            continue
        
        try:
            airport = Airport(
                iata=iata,
                icao=raw.get('ident', '').strip().upper() or None,
                name=raw.get('name', '').strip(),
                city=raw.get('municipality', '').strip() or raw.get('name', '').strip(),
                country=raw.get('iso_country', '').strip(),
                iso_country=raw.get('iso_country', '').strip(),
                lat=float(raw.get('latitude_deg', 0)),
                lon=float(raw.get('longitude_deg', 0)),
                timezone=raw.get('timezone', '') or None,
                type=raw.get('type', 'airport'),
                aliases=[]
            )
            
            # Generate aliases
            airport.aliases = generate_aliases({
                'iata': airport.iata,
                'icao': airport.icao,
                'name': airport.name,
                'city': airport.city
            })
            
            airports_by_iata[iata] = airport
        
        except (ValueError, KeyError) as e:
            continue
    
    # Supplement with OpenFlights data (fill gaps)
    for raw in openflights:
        iata = raw.get('iata_code', '').strip().upper()
        if not iata or len(iata) != 3:
            continue
        
        # Skip if already have from OurAirports
        if iata in airports_by_iata:
            continue
        
        try:
            # Get country code (OpenFlights doesn't have ISO country directly)
            country = raw.get('country', '').strip()
            iso_country = country[:2].upper() if country else 'XX'
            
            airport = Airport(
                iata=iata,
                icao=raw.get('icao_code', '').strip().upper() or None,
                name=raw.get('name', '').strip(),
                city=raw.get('city', '').strip(),
                country=country,
                iso_country=iso_country,
                lat=float(raw.get('latitude_deg', 0)),
                lon=float(raw.get('longitude_deg', 0)),
                timezone=raw.get('timezone', '') or None,
                type='airport',
                aliases=[]
            )
            
            # Generate aliases
            airport.aliases = generate_aliases({
                'iata': airport.iata,
                'icao': airport.icao,
                'name': airport.name,
                'city': airport.city
            })
            
            airports_by_iata[iata] = airport
        
        except (ValueError, KeyError):
            continue
    
    print(f"✅ Merged to {len(airports_by_iata)} unique airports")
    return airports_by_iata


def verify_required_airports(airports: Dict[str, Airport]) -> bool:
    """Verify that required Indian airports are present"""
    print("\n🔍 Verifying required Indian airports...")
    
    all_found = True
    for iata, expected_city in REQUIRED_INDIAN_AIRPORTS.items():
        if iata in airports:
            airport = airports[iata]
            print(f"✅ {iata}: {airport.name} ({airport.city})")
        else:
            print(f"❌ {iata}: MISSING - {expected_city}")
            all_found = False
    
    return all_found


def save_airports(airports: Dict[str, Airport], output_path: Path):
    """Save airports to JSON file (minified)"""
    print(f"\n💾 Saving to {output_path}...")
    
    # Convert to list of dicts
    airports_list = [airport.to_dict() for airport in airports.values()]
    
    # Sort by IATA for consistency
    airports_list.sort(key=lambda x: x['iata'])
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save minified JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(airports_list, f, ensure_ascii=False, separators=(',', ':'))
    
    # Get file size
    size_mb = output_path.stat().st_size / (1024 * 1024)
    
    print(f"✅ Saved {len(airports_list)} airports")
    print(f"📊 File size: {size_mb:.2f} MB")


def main():
    """Main build process"""
    print("🚀 Building airport dataset...\n")
    
    # Download data
    ourairports_raw = download_ourairports()
    openflights_raw = download_openflights()
    
    if not ourairports_raw and not openflights_raw:
        print("❌ Failed to download any data sources!")
        sys.exit(1)
    
    # Filter active airports
    ourairports_filtered = filter_active_airports(ourairports_raw, 'ourairports')
    openflights_filtered = filter_active_airports(openflights_raw, 'openflights')
    
    # Merge and deduplicate
    airports = merge_and_deduplicate(ourairports_filtered, openflights_filtered)
    
    # Verify required airports
    if not verify_required_airports(airports):
        print("\n⚠️  Warning: Some required airports are missing!")
        print("Continuing anyway...")
    
    # Save to file
    save_airports(airports, OUTPUT_PATH)
    
    print("\n✅ Airport dataset build complete!")
    print(f"📁 Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

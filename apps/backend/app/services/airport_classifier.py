"""
Airport Classification Service

Identifies international airports and hubs from the airport dataset.
Used for intelligent fallback routing.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional

logger = logging.getLogger(__name__)


class AirportClassifier:
    """
    Classifies airports as international, hub, or regional based on:
    - Curated hub list
    - Airport type/size
    - Name patterns
    """
    
    def __init__(self, airport_data: Dict, hub_config_path: str = "/app/data/hub-airports.json"):
        """
        Initialize airport classifier.
        
        Args:
            airport_data: Dictionary of all airports (IATA -> airport info)
            hub_config_path: Path to hub airports JSON config
        """
        self.airport_data = airport_data
        self.hub_airports = self._load_hub_config(hub_config_path)
        self.international_cache: Dict[str, bool] = {}
    
    def _load_hub_config(self, config_path: str) -> Dict[str, List[str]]:
        """Load hub airports configuration."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            total_hubs = sum(len(hubs) for hubs in config.values())
            logger.info(f"✅ Loaded {total_hubs} hub airports across {len(config)} countries")
            return config
        except Exception as e:
            logger.error(f"❌ Failed to load hub config: {e}")
            return {}
    
    def is_hub_airport(self, iata: str) -> bool:
        """
        Check if airport is a major hub.
        
        Args:
            iata: Airport IATA code
        
        Returns:
            True if airport is in the hub list
        """
        if not iata:
            return False
        
        # Check all countries for this IATA
        for country, hubs in self.hub_airports.items():
            if iata.upper() in hubs:
                return True
        
        return False
    
    def is_international_airport(self, iata: str) -> bool:
        """
        Check if airport handles international flights.
        
        Heuristics:
        1. Is a hub (hubs are always international)
        2. Airport type is "large_airport" or "medium_airport"
        3. Name contains "International"
        
        Args:
            iata: Airport IATA code
        
        Returns:
            True if airport is classified as international
        """
        if not iata:
            return False
        
        # Check cache
        if iata in self.international_cache:
            return self.international_cache[iata]
        
        # Hub airports are always international
        if self.is_hub_airport(iata):
            self.international_cache[iata] = True
            return True
        
        # Check airport data
        airport = self.airport_data.get(iata.upper())
        if not airport:
            self.international_cache[iata] = False
            return False
        
        # Check type
        airport_type = airport.get('type', '').lower()
        if airport_type in ['large_airport', 'medium_airport']:
            self.international_cache[iata] = True
            return True
        
        # Check name
        name = airport.get('name', '').lower()
        if 'international' in name:
            self.international_cache[iata] = True
            return True
        
        # Default to regional/domestic
        self.international_cache[iata] = False
        return False
    
    def get_hub_airports(self, country_code: str, exclude: Optional[List[str]] = None) -> List[str]:
        """
        Get hub airports for a country.
        
        Args:
            country_code: ISO 2-letter country code
            exclude: List of IATA codes to exclude
        
        Returns:
            List of hub airport IATA codes
        """
        exclude = exclude or []
        hubs = self.hub_airports.get(country_code.upper(), [])
        return [hub for hub in hubs if hub not in exclude]
    
    def get_international_airports(self, country_code: str, limit: int = 10, exclude: Optional[List[str]] = None) -> List[str]:
        """
        Get international airports for a country.
        
        Priority order:
        1. Hub airports
        2. Large airports
        3. Medium airports with "International" in name
        
        Args:
            country_code: ISO 2-letter country code
            limit: Maximum number of airports to return
            exclude: List of IATA codes to exclude
        
        Returns:
            List of international airport IATA codes
        """
        exclude = exclude or []
        result = []
        
        # First, add all hubs for this country
        hubs = self.get_hub_airports(country_code, exclude)
        result.extend(hubs)
        
        # Then, scan airport data for other international airports in this country
        for iata, airport in self.airport_data.items():
            if iata in exclude or iata in result:
                continue
            
            if airport.get('country') == country_code.upper():
                if self.is_international_airport(iata):
                    result.append(iata)
            
            if len(result) >= limit:
                break
        
        return result[:limit]
    
    def get_airport_country(self, iata: str) -> Optional[str]:
        """
        Get country code for an airport.
        
        Args:
            iata: Airport IATA code
        
        Returns:
            ISO 2-letter country code or None
        """
        airport = self.airport_data.get(iata.upper())
        if airport:
            return airport.get('country')
        return None
    
    def classify_route_type(self, origin: str, destination: str) -> Dict:
        """
        Classify a route and determine fallback strategy.
        
        Returns:
            Dictionary with classification info:
            {
                "is_international_route": bool,
                "origin_country": str,
                "destination_country": str,
                "origin_is_international": bool,
                "destination_is_international": bool,
                "origin_is_hub": bool,
                "destination_is_hub": bool,
                "suggested_strategy": str  # "direct", "origin_hub", "dest_hub", "both_hub", "nearby"
            }
        """
        origin_country = self.get_airport_country(origin)
        dest_country = self.get_airport_country(destination)
        
        origin_is_intl = self.is_international_airport(origin)
        dest_is_intl = self.is_international_airport(destination)
        
        origin_is_hub = self.is_hub_airport(origin)
        dest_is_hub = self.is_hub_airport(destination)
        
        is_international_route = (origin_country != dest_country)
        
        # Determine suggested strategy
        strategy = "direct"
        if is_international_route:
            if not origin_is_intl and not dest_is_intl:
                strategy = "both_hub"
            elif not origin_is_intl:
                strategy = "origin_hub"
            elif not dest_is_intl:
                strategy = "dest_hub"
        else:
            # Domestic route
            if not origin_is_hub and not dest_is_hub:
                strategy = "nearby"
        
        return {
            "is_international_route": is_international_route,
            "origin_country": origin_country,
            "destination_country": dest_country,
            "origin_is_international": origin_is_intl,
            "destination_is_international": dest_is_intl,
            "origin_is_hub": origin_is_hub,
            "destination_is_hub": dest_is_hub,
            "suggested_strategy": strategy
        }

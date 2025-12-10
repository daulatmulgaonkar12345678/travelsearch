"""
Universal Flight Search Fallback Orchestrator

Handles zero-result scenarios by intelligently expanding origin airports
to include nearby airports and regional hubs.

Key Features:
- Deterministic (no AI/fabrication)
- Production-safe (respects rate limits, caching)
- Universal (works globally)
- Route validation (distance-based stop requirements)
"""

import logging
import httpx
from typing import List, Set, Optional, Dict
from app.models.flight import FlightOffer, FlightSearchRequest
from app.config.hub_airports import get_top_hubs
from app.services.flight_validator import haversine_distance

logger = logging.getLogger(__name__)

# Fallback metrics
fallback_metrics = {
    "total_fallback_searches": 0,
    "successful_fallbacks": 0,
    "failed_fallbacks": 0,
}


class FallbackOrchestrator:
    """
    Orchestrates intelligent fallback searches when primary search returns zero results.
    """
    
    def __init__(self, airport_data: Dict):
        """
        Initialize fallback orchestrator.
        
        Args:
            airport_data: Dictionary of airport data (IATA -> {lat, lon, country, etc})
        """
        self.airport_data = airport_data
    
    async def get_nearby_airports(
        self, 
        iata: str, 
        radius_km: float = 250.0,
        limit: int = 3
    ) -> List[str]:
        """
        Fetch nearby airports using internal API endpoint.
        
        Args:
            iata: Airport IATA code
            radius_km: Search radius in kilometers
            limit: Maximum number of nearby airports
        
        Returns:
            List of nearby airport IATA codes
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://localhost:8001/api/airports/{iata}/nearby",
                    params={"radius_km": radius_km, "limit": limit},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    nearby = [item['airport']['iata'] for item in data.get('results', [])]
                    logger.info(f"[Fallback] Found {len(nearby)} nearby airports for {iata}: {nearby}")
                    return nearby
                else:
                    logger.warning(f"[Fallback] Failed to fetch nearby for {iata}: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"[Fallback] Error fetching nearby airports for {iata}: {e}")
            return []
    
    def get_airport_country(self, iata: str) -> Optional[str]:
        """
        Get country code for an airport.
        
        Args:
            iata: Airport IATA code
        
        Returns:
            ISO 2-letter country code or None
        """
        airport = self.airport_data.get(iata)
        if airport:
            return airport.get('country')
        return None
    
    def calculate_route_distance(self, origin: str, destination: str) -> Optional[float]:
        """
        Calculate great-circle distance between two airports.
        
        Args:
            origin: Origin airport IATA
            destination: Destination airport IATA
        
        Returns:
            Distance in kilometers or None if coordinates unavailable
        """
        origin_data = self.airport_data.get(origin)
        dest_data = self.airport_data.get(destination)
        
        if not origin_data or not dest_data:
            return None
        
        origin_lat = origin_data.get('lat')
        origin_lon = origin_data.get('lon')
        dest_lat = dest_data.get('lat')
        dest_lon = dest_data.get('lon')
        
        if None in (origin_lat, origin_lon, dest_lat, dest_lon):
            return None
        
        return haversine_distance(
            float(origin_lat), float(origin_lon),
            float(dest_lat), float(dest_lon)
        )
    
    def requires_stop(self, origin: str, destination: str) -> bool:
        """
        Determine if route likely requires at least 1 stop based on distance.
        
        Args:
            origin: Origin airport IATA
            destination: Destination airport IATA
        
        Returns:
            True if route distance > 3500 km (typically requires connection)
        """
        distance = self.calculate_route_distance(origin, destination)
        
        if distance is None:
            # Unknown distance, be conservative
            return False
        
        # Routes > 3500 km typically require connections
        return distance > 3500
    
    async def build_expanded_origin_list(
        self,
        original_origin: str,
        limit_nearby: int = 3,
        limit_hubs: int = 3
    ) -> List[str]:
        """
        Build expanded list of origin airports for fallback search.
        
        Includes:
        1. Original origin
        2. Nearby airports (within 250 km)
        3. Regional hub airports
        
        Args:
            original_origin: Original origin IATA
            limit_nearby: Max nearby airports to include
            limit_hubs: Max regional hubs to include
        
        Returns:
            Ordered list of origin IATA codes (original first, then nearby, then hubs)
        """
        expanded_origins: List[str] = [original_origin]
        seen: Set[str] = {original_origin}
        
        # 1. Add nearby airports
        nearby = await self.get_nearby_airports(original_origin, radius_km=250.0, limit=limit_nearby)
        for airport in nearby:
            if airport not in seen:
                expanded_origins.append(airport)
                seen.add(airport)
        
        # 2. Add regional hubs
        origin_country = self.get_airport_country(original_origin)
        if origin_country:
            hubs = get_top_hubs(origin_country, limit=limit_hubs, exclude=list(seen))
            for hub in hubs:
                if hub not in seen:
                    expanded_origins.append(hub)
                    seen.add(hub)
        
        logger.info(
            f"[Fallback] Expanded origins for {original_origin}: "
            f"{expanded_origins} (nearby: {len(nearby)}, hubs: {len(hubs) if origin_country else 0})"
        )
        
        return expanded_origins
    
    def log_fallback_activation(
        self,
        original_origin: str,
        destination: str,
        expanded_origins: List[str],
        route_distance: Optional[float],
        requires_stop: bool
    ):
        """
        Log fallback activation with route metadata.
        
        Args:
            original_origin: Original origin IATA
            destination: Destination IATA
            expanded_origins: List of expanded origin IATAs
            route_distance: Route distance in km
            requires_stop: Whether route requires stops
        """
        fallback_metrics["total_fallback_searches"] += 1
        
        logger.info(
            f"[Fallback] ACTIVATED for {original_origin} → {destination} | "
            f"Distance: {route_distance:.0f if route_distance else 'N/A'} km | "
            f"Requires stop: {requires_stop} | "
            f"Expanded origins: {expanded_origins} ({len(expanded_origins)} total)"
        )
    
    async def execute_fallback_search(
        self,
        original_request: FlightSearchRequest,
        search_function,
        **search_kwargs
    ) -> tuple[List[FlightOffer], Dict]:
        """
        Execute fallback search with expanded origins.
        
        Args:
            original_request: Original flight search request that returned 0 results
            search_function: Function to call for search (e.g., aggregator.search_flights)
            **search_kwargs: Additional kwargs to pass to search function
        
        Returns:
            Tuple of (offers, fallback_metadata)
        """
        original_origin = original_request.origin
        destination = original_request.destination
        
        # Build expanded origin list
        expanded_origins = await self.build_expanded_origin_list(
            original_origin,
            limit_nearby=3,
            limit_hubs=3
        )
        
        # Calculate route distance and stop requirement
        route_distance = self.calculate_route_distance(original_origin, destination)
        requires_stop = self.requires_stop(original_origin, destination)
        
        # Log fallback activation
        self.log_fallback_activation(
            original_origin,
            destination,
            expanded_origins,
            route_distance,
            requires_stop
        )
        
        # Prepare fallback metadata
        fallback_metadata = {
            "fallback_activated": True,
            "original_origin": original_origin,
            "expanded_origins": expanded_origins,
            "route_distance_km": route_distance,
            "requires_stop": requires_stop,
            "used_origins": []
        }
        
        # Try each expanded origin (skip original since we already tried it)
        all_offers = []
        
        for alt_origin in expanded_origins[1:]:  # Skip original (index 0)
            try:
                logger.info(f"[Fallback] Trying origin: {alt_origin} → {destination}")
                
                # Create modified request
                fallback_request = original_request.model_copy(deep=True)
                fallback_request.origin = alt_origin
                
                # If route requires stops, adjust search
                if requires_stop and fallback_request.direct_only:
                    logger.info(f"[Fallback] Route > 3500km, allowing connections")
                    fallback_request.direct_only = False
                
                # Execute search
                offers = await search_function(fallback_request, **search_kwargs)
                
                if offers and len(offers) > 0:
                    logger.info(f"[Fallback] SUCCESS: {alt_origin} → {destination} returned {len(offers)} offers")
                    
                    # Tag offers with fallback metadata
                    for offer in offers:
                        offer.nearby_origin = True
                        offer.source_airport = alt_origin
                    
                    all_offers.extend(offers)
                    fallback_metadata["used_origins"].append(alt_origin)
                    
                    # Don't break - collect offers from all expanded origins
                else:
                    logger.info(f"[Fallback] No results from {alt_origin} → {destination}")
            
            except Exception as e:
                logger.error(f"[Fallback] Error searching {alt_origin} → {destination}: {e}")
                continue
        
        if all_offers:
            fallback_metrics["successful_fallbacks"] += 1
            logger.info(
                f"[Fallback] COMPLETED: Found {len(all_offers)} offers from "
                f"{fallback_metadata['used_origins']}"
            )
        else:
            fallback_metrics["failed_fallbacks"] += 1
            logger.warning(f"[Fallback] FAILED: No results found for any expanded origin")
        
        return all_offers, fallback_metadata


def get_fallback_metrics() -> Dict:
    """Get fallback metrics for monitoring."""
    return fallback_metrics.copy()

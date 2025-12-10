"""
Global Fallback Orchestrator with International Airport Priority

Implements multi-stage fallback strategy:
1. Primary (exact route)
2. International/Hub expansion (priority for cross-border)
3. Nearby airports
4. Hub-only safety net
"""

import logging
import asyncio
import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from app.models.flight import FlightOffer, FlightSearchRequest
from app.services.airport_classifier import AirportClassifier

logger = logging.getLogger(__name__)

# Fallback metrics
global_fallback_metrics = {
    "total_searches": 0,
    "primary_success": 0,
    "fallback_success": 0,
    "total_failure": 0,
}


class GlobalFallbackOrchestrator:
    """
    Orchestrates intelligent multi-stage fallback searches.
    Prioritizes international airports and hubs for cross-border routes.
    """
    
    def __init__(self, airport_data: Dict, classifier: AirportClassifier):
        """
        Initialize global fallback orchestrator.
        
        Args:
            airport_data: Dictionary of all airports
            classifier: Airport classification service
        """
        self.airport_data = airport_data
        self.classifier = classifier
    
    async def execute_global_fallback(
        self,
        original_request: FlightSearchRequest,
        primary_results: List[FlightOffer],
        search_function,
        nearby_function,
        max_fallback_offers: int = 20
    ) -> Dict:
        """
        Execute global fallback strategy when primary search returns 0 or few results.
        
        Args:
            original_request: Original search request
            primary_results: Results from primary search
            search_function: Function to execute flight search
            nearby_function: Function to get nearby airports
            max_fallback_offers: Stop when we have this many offers
        
        Returns:
            Structured fallback response
        """
        search_id = str(uuid.uuid4())[:8]
        global_fallback_metrics["total_searches"] += 1
        
        origin = original_request.origin
        destination = original_request.destination
        
        # Classify route
        route_info = self.classifier.classify_route_type(origin, destination)
        
        logger.info(
            f"[fallback] search_id={search_id} origin={origin} dest={destination} "
            f"route_type={'international' if route_info['is_international_route'] else 'domestic'} "
            f"strategy={route_info['suggested_strategy']}"
        )
        
        # Initialize response structure
        response = {
            "primary_results": primary_results,
            "fallback_results": {
                "origin_international": [],
                "dest_international": [],
                "both_international": [],
                "dest_nearby": [],
                "origin_nearby": [],
                "both_nearby": [],
                "hub": []
            },
            "search_metadata": {
                "search_id": search_id,
                "origin": origin,
                "destination": destination,
                "departure_date": original_request.departure_date,
                "trip_type": original_request.trip_type,
                "adults": original_request.adults,
                "cabin_class": original_request.cabin_class,
                "route_classification": route_info,
                "fallback_stages_tried": ["primary"],
                "has_any_results": len(primary_results) > 0
            }
        }
        
        # If primary has results, we're done
        if len(primary_results) > 0:
            global_fallback_metrics["primary_success"] += 1
            logger.info(f"[fallback] search_id={search_id} primary={len(primary_results)} STOP (primary success)")
            return response
        
        # Execute fallback stages
        total_fallback_offers = 0
        
        # Stage A: International & Hub Expansion
        if route_info['is_international_route']:
            logger.info(f"[fallback] search_id={search_id} STAGE A: International/Hub expansion")
            
            # A1: Origin International (if origin is not international)
            if not route_info['origin_is_international']:
                stage_offers = await self._stage_origin_international(
                    original_request, search_function, route_info
                )
                response["fallback_results"]["origin_international"] = stage_offers
                response["search_metadata"]["fallback_stages_tried"].append("origin_international")
                total_fallback_offers += len(stage_offers)
                logger.info(f"[fallback] search_id={search_id} origin_international={len(stage_offers)}")
                
                if total_fallback_offers >= max_fallback_offers:
                    return self._finalize_response(response, search_id, total_fallback_offers)
            
            # A2: Destination International (if dest is not international)
            if not route_info['destination_is_international']:
                stage_offers = await self._stage_dest_international(
                    original_request, search_function, route_info
                )
                response["fallback_results"]["dest_international"] = stage_offers
                response["search_metadata"]["fallback_stages_tried"].append("dest_international")
                total_fallback_offers += len(stage_offers)
                logger.info(f"[fallback] search_id={search_id} dest_international={len(stage_offers)}")
                
                if total_fallback_offers >= max_fallback_offers:
                    return self._finalize_response(response, search_id, total_fallback_offers)
            
            # A3: Both International (if neither is international)
            if not route_info['origin_is_international'] and not route_info['destination_is_international']:
                stage_offers = await self._stage_both_international(
                    original_request, search_function, route_info
                )
                response["fallback_results"]["both_international"] = stage_offers
                response["search_metadata"]["fallback_stages_tried"].append("both_international")
                total_fallback_offers += len(stage_offers)
                logger.info(f"[fallback] search_id={search_id} both_international={len(stage_offers)}")
                
                if total_fallback_offers >= max_fallback_offers:
                    return self._finalize_response(response, search_id, total_fallback_offers)
        
        # Stage B: Nearby Airports
        logger.info(f"[fallback] search_id={search_id} STAGE B: Nearby airports")
        
        # B1: Destination Nearby
        stage_offers = await self._stage_dest_nearby(
            original_request, search_function, nearby_function
        )
        response["fallback_results"]["dest_nearby"] = stage_offers
        response["search_metadata"]["fallback_stages_tried"].append("dest_nearby")
        total_fallback_offers += len(stage_offers)
        logger.info(f"[fallback] search_id={search_id} dest_nearby={len(stage_offers)}")
        
        if total_fallback_offers >= max_fallback_offers:
            return self._finalize_response(response, search_id, total_fallback_offers)
        
        # B2: Origin Nearby
        stage_offers = await self._stage_origin_nearby(
            original_request, search_function, nearby_function
        )
        response["fallback_results"]["origin_nearby"] = stage_offers
        response["search_metadata"]["fallback_stages_tried"].append("origin_nearby")
        total_fallback_offers += len(stage_offers)
        logger.info(f"[fallback] search_id={search_id} origin_nearby={len(stage_offers)}")
        
        if total_fallback_offers >= max_fallback_offers:
            return self._finalize_response(response, search_id, total_fallback_offers)
        
        # B3: Both Nearby (limited)
        stage_offers = await self._stage_both_nearby(
            original_request, search_function, nearby_function
        )
        response["fallback_results"]["both_nearby"] = stage_offers
        response["search_metadata"]["fallback_stages_tried"].append("both_nearby")
        total_fallback_offers += len(stage_offers)
        logger.info(f"[fallback] search_id={search_id} both_nearby={len(stage_offers)}")
        
        if total_fallback_offers >= max_fallback_offers:
            return self._finalize_response(response, search_id, total_fallback_offers)
        
        # Stage C: Hub-Only Safety Net
        logger.info(f"[fallback] search_id={search_id} STAGE C: Hub safety net")
        stage_offers = await self._stage_hub_only(
            original_request, search_function, route_info
        )
        response["fallback_results"]["hub"] = stage_offers
        response["search_metadata"]["fallback_stages_tried"].append("hub")
        total_fallback_offers += len(stage_offers)
        logger.info(f"[fallback] search_id={search_id} hub={len(stage_offers)}")
        
        return self._finalize_response(response, search_id, total_fallback_offers)
    
    def _finalize_response(self, response: Dict, search_id: str, total_offers: int) -> Dict:
        """Finalize response and update metrics."""
        response["search_metadata"]["has_any_results"] = total_offers > 0
        
        if total_offers > 0:
            global_fallback_metrics["fallback_success"] += 1
        else:
            global_fallback_metrics["total_failure"] += 1
        
        # Log summary
        stage_counts = {k: len(v) for k, v in response["fallback_results"].items()}
        logger.info(
            f"[fallback] search_id={search_id} COMPLETE "
            f"primary={len(response['primary_results'])} "
            + " ".join(f"{k}={v}" for k, v in stage_counts.items()) +
            f" has_results={response['search_metadata']['has_any_results']}"
        )
        
        return response
    
    async def _stage_origin_international(
        self, request: FlightSearchRequest, search_fn, route_info: Dict
    ) -> List[FlightOffer]:
        """Stage A1: Search from origin country's international airports to exact destination."""
        offers = []
        origin_country = route_info['origin_country']
        
        # Get hubs first, then other international airports
        hubs = self.classifier.get_hub_airports(origin_country, exclude=[request.origin])
        intl_airports = self.classifier.get_international_airports(origin_country, limit=5, exclude=[request.origin] + hubs)
        
        # Try top 3 hubs + top 2 international
        candidates = hubs[:3] + intl_airports[:2]
        
        for alt_origin in candidates:
            try:
                modified_request = request.model_copy(deep=True)
                modified_request.origin = alt_origin
                
                results = await search_fn(modified_request)
                
                for offer in results:
                    offer.origin_type = "hub" if self.classifier.is_hub_airport(alt_origin) else "international"
                    offer.destination_type = "exact"
                    offer.fallback_stage = "origin_international"
                    offer.nearby_origin = True
                    offer.source_airport = alt_origin
                
                offers.extend(results)
            except Exception as e:
                logger.error(f"[fallback] origin_international {alt_origin} failed: {e}")
        
        return offers
    
    async def _stage_dest_international(
        self, request: FlightSearchRequest, search_fn, route_info: Dict
    ) -> List[FlightOffer]:
        """Stage A2: Search from exact origin to destination country's international airports."""
        offers = []
        dest_country = route_info['destination_country']
        
        hubs = self.classifier.get_hub_airports(dest_country, exclude=[request.destination])
        intl_airports = self.classifier.get_international_airports(dest_country, limit=5, exclude=[request.destination] + hubs)
        
        candidates = hubs[:3] + intl_airports[:2]
        
        for alt_dest in candidates:
            try:
                modified_request = request.model_copy(deep=True)
                modified_request.destination = alt_dest
                
                results = await search_fn(modified_request)
                
                for offer in results:
                    offer.origin_type = "exact"
                    offer.destination_type = "hub" if self.classifier.is_hub_airport(alt_dest) else "international"
                    offer.fallback_stage = "dest_international"
                    offer.nearby_destination = True
                
                offers.extend(results)
            except Exception as e:
                logger.error(f"[fallback] dest_international {alt_dest} failed: {e}")
        
        return offers
    
    async def _stage_both_international(
        self, request: FlightSearchRequest, search_fn, route_info: Dict
    ) -> List[FlightOffer]:
        """Stage A3: Search between international airports on both sides."""
        offers = []
        origin_country = route_info['origin_country']
        dest_country = route_info['destination_country']
        
        origin_hubs = self.classifier.get_hub_airports(origin_country, exclude=[request.origin])[:2]
        dest_hubs = self.classifier.get_hub_airports(dest_country, exclude=[request.destination])[:2]
        
        for alt_origin in origin_hubs:
            for alt_dest in dest_hubs:
                try:
                    modified_request = request.model_copy(deep=True)
                    modified_request.origin = alt_origin
                    modified_request.destination = alt_dest
                    
                    results = await search_fn(modified_request)
                    
                    for offer in results:
                        offer.origin_type = "hub"
                        offer.destination_type = "hub"
                        offer.fallback_stage = "both_international"
                        offer.nearby_origin = True
                        offer.nearby_destination = True
                        offer.source_airport = alt_origin
                    
                    offers.extend(results)
                except Exception as e:
                    logger.error(f"[fallback] both_international {alt_origin}→{alt_dest} failed: {e}")
        
        return offers
    
    async def _stage_dest_nearby(
        self, request: FlightSearchRequest, search_fn, nearby_fn
    ) -> List[FlightOffer]:
        """Stage B1: Search to nearby destinations."""
        offers = []
        
        try:
            nearby_dests = await nearby_fn(request.destination, radius_km=250, limit=5)
            
            for nearby_iata in nearby_dests:
                modified_request = request.model_copy(deep=True)
                modified_request.destination = nearby_iata
                
                results = await search_fn(modified_request)
                
                for offer in results:
                    offer.origin_type = "exact"
                    offer.destination_type = "nearby"
                    offer.fallback_stage = "dest_nearby"
                    offer.nearby_destination = True
                
                offers.extend(results)
        except Exception as e:
            logger.error(f"[fallback] dest_nearby failed: {e}")
        
        return offers
    
    async def _stage_origin_nearby(
        self, request: FlightSearchRequest, search_fn, nearby_fn
    ) -> List[FlightOffer]:
        """Stage B2: Search from nearby origins."""
        offers = []
        
        try:
            nearby_origins = await nearby_fn(request.origin, radius_km=250, limit=5)
            
            for nearby_iata in nearby_origins:
                modified_request = request.model_copy(deep=True)
                modified_request.origin = nearby_iata
                
                results = await search_fn(modified_request)
                
                for offer in results:
                    offer.origin_type = "nearby"
                    offer.destination_type = "exact"
                    offer.fallback_stage = "origin_nearby"
                    offer.nearby_origin = True
                    offer.source_airport = nearby_iata
                
                offers.extend(results)
        except Exception as e:
            logger.error(f"[fallback] origin_nearby failed: {e}")
        
        return offers
    
    async def _stage_both_nearby(
        self, request: FlightSearchRequest, search_fn, nearby_fn
    ) -> List[FlightOffer]:
        """Stage B3: Search between nearby origins and destinations (limited)."""
        offers = []
        
        try:
            nearby_origins = await nearby_fn(request.origin, radius_km=150, limit=3)
            nearby_dests = await nearby_fn(request.destination, radius_km=150, limit=3)
            
            # Limit combinations
            for alt_origin in nearby_origins[:2]:
                for alt_dest in nearby_dests[:2]:
                    modified_request = request.model_copy(deep=True)
                    modified_request.origin = alt_origin
                    modified_request.destination = alt_dest
                    
                    results = await search_fn(modified_request)
                    
                    for offer in results:
                        offer.origin_type = "nearby"
                        offer.destination_type = "nearby"
                        offer.fallback_stage = "both_nearby"
                        offer.nearby_origin = True
                        offer.nearby_destination = True
                        offer.source_airport = alt_origin
                    
                    offers.extend(results)
        except Exception as e:
            logger.error(f"[fallback] both_nearby failed: {e}")
        
        return offers
    
    async def _stage_hub_only(
        self, request: FlightSearchRequest, search_fn, route_info: Dict
    ) -> List[FlightOffer]:
        """Stage C: Hub-only safety net."""
        offers = []
        origin_country = route_info['origin_country']
        dest_country = route_info['destination_country']
        
        origin_hubs = self.classifier.get_hub_airports(origin_country)[:2]
        dest_hubs = self.classifier.get_hub_airports(dest_country)[:2]
        
        for alt_origin in origin_hubs:
            for alt_dest in dest_hubs:
                try:
                    modified_request = request.model_copy(deep=True)
                    modified_request.origin = alt_origin
                    modified_request.destination = alt_dest
                    
                    results = await search_fn(modified_request)
                    
                    for offer in results:
                        offer.origin_type = "hub"
                        offer.destination_type = "hub"
                        offer.fallback_stage = "hub"
                        offer.nearby_origin = True
                        offer.nearby_destination = True
                        offer.source_airport = alt_origin
                    
                    offers.extend(results)
                except Exception as e:
                    logger.error(f"[fallback] hub {alt_origin}→{alt_dest} failed: {e}")
        
        return offers


def get_global_fallback_metrics() -> Dict:
    """Get global fallback metrics."""
    return global_fallback_metrics.copy()

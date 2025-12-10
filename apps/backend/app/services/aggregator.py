from typing import List
import asyncio
import httpx
import json
from pathlib import Path
from app.models.flight import FlightOffer, FlightSearchRequest
from app.models.hotel import HotelOffer, HotelSearchRequest
from app.services.adapters.amadeus_flights import AmadeusFlightsAdapter
from app.services.adapters.amadeus_hotels import AmadeusHotelsAdapter
from app.services.adapters.duffel_flights import DuffelFlightsAdapter
from app.services.ranking import RankingEngine
from app.services.cache import CacheService
from app.services.flight_validator import validate_flight_offers
from app.services.fallback_orchestrator import FallbackOrchestrator
from app.config import settings, is_mock_mode
import logging

logger = logging.getLogger(__name__)

class SearchAggregator:
    """Aggregates search results from multiple providers"""
    
    def __init__(self):
        # Initialize new real adapters
        self.amadeus_flights = AmadeusFlightsAdapter()
        self.duffel_flights = DuffelFlightsAdapter()
        self.amadeus_hotels = AmadeusHotelsAdapter()
        
        # Provider selection from config
        self.flight_provider = settings.flight_provider
        self.hotel_provider = settings.hotel_provider
        
        self.ranking = RankingEngine()
        self.cache = CacheService()
        
        # Load airport data for validation
        self.airport_data = self._load_airport_data()
        
        logger.info(f"SearchAggregator initialized with flight={self.flight_provider}, hotel={self.hotel_provider}")
    
    def _load_airport_data(self):
        """Load airport dataset for duration validation"""
        try:
            airports_path = Path("/app/data/airports-full.json")
            with open(airports_path, 'r', encoding='utf-8') as f:
                airports_list = json.load(f)
            
            # Build IATA lookup dictionary
            airport_dict = {
                airport['iata']: airport
                for airport in airports_list
                if 'iata' in airport
            }
            
            logger.info(f"✅ Loaded {len(airport_dict)} airports for validation")
            return airport_dict
        except Exception as e:
            logger.error(f"❌ Failed to load airport data for validation: {e}")
            return {}
    
    async def _get_nearby_airports(self, iata: str, radius_km: float = 250.0) -> List[str]:
        """Get nearby airport IATA codes for a given airport"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://localhost:8001/api/airports/{iata}/nearby",
                    params={"radius_km": radius_km, "limit": 5},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    nearby_iatas = [item['airport']['iata'] for item in data.get('results', [])]
                    logger.info(f"Found {len(nearby_iatas)} nearby airports for {iata}: {nearby_iatas}")
                    return nearby_iatas
                else:
                    logger.warning(f"Failed to fetch nearby airports for {iata}: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching nearby airports for {iata}: {e}")
            return []
    
    async def search_flights(self, request: FlightSearchRequest) -> List[FlightOffer]:
        """Search flights from configured providers and aggregate"""
        # Build cache key including nearby flags
        nearby_suffix = ""
        if request.include_nearby_origin or request.include_nearby_destination:
            nearby_suffix = f":nearby_o{request.include_nearby_origin}_d{request.include_nearby_destination}"
        cache_key = f"flights:{request.origin}:{request.destination}:{request.departure_date}:{request.cabin_class}{nearby_suffix}"
        
        # Check cache first
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for {cache_key}")
            return cached
        
        # Handle nearby airports if enabled
        origin_airports = [request.origin] if request.origin else []
        destination_airports = [request.destination] if request.destination else []
        
        if request.include_nearby_origin and request.origin:
            logger.info(f"Fetching nearby airports for origin: {request.origin}")
            nearby_origins = await self._get_nearby_airports(request.origin, request.nearby_radius_km)
            origin_airports.extend(nearby_origins)
            logger.info(f"Total origin airports: {origin_airports}")
        
        if request.include_nearby_destination and request.destination:
            logger.info(f"Fetching nearby airports for destination: {request.destination}")
            nearby_destinations = await self._get_nearby_airports(request.destination, request.nearby_radius_km)
            destination_airports.extend(nearby_destinations)
            logger.info(f"Total destination airports: {destination_airports}")
        
        # Create search tasks for all combinations
        tasks = []
        original_origin = request.origin
        original_destination = request.destination
        
        for origin_code in origin_airports:
            for dest_code in destination_airports:
                # Create a modified request for this combination
                modified_request = request.model_copy(deep=True)
                modified_request.origin = origin_code
                modified_request.destination = dest_code
                
                # Add search tasks based on provider configuration
                if self.flight_provider == "amadeus":
                    tasks.append((origin_code, dest_code, self.amadeus_flights.search_flights(modified_request)))
                elif self.flight_provider == "duffel":
                    tasks.append((origin_code, dest_code, self.duffel_flights.search_flights(modified_request)))
                elif self.flight_provider == "amadeus+duffel":
                    tasks.append((origin_code, dest_code, self.amadeus_flights.search_flights(modified_request)))
                    tasks.append((origin_code, dest_code, self.duffel_flights.search_flights(modified_request)))
                else:
                    logger.warning(f"Unknown flight provider: {self.flight_provider}, defaulting to Amadeus")
                    tasks.append((origin_code, dest_code, self.amadeus_flights.search_flights(modified_request)))
        
        # Query providers in parallel
        logger.info(f"Searching flights: {len(tasks)} route combinations via {self.flight_provider}")
        
        # Extract just the coroutines for asyncio.gather
        search_coroutines = [task[2] for task in tasks]
        results = await asyncio.gather(*search_coroutines, return_exceptions=True)
        
        # Flatten results, handle errors, and tag with nearby metadata
        all_offers = []
        for idx, result in enumerate(results):
            if isinstance(result, list):
                origin_code, dest_code = tasks[idx][0], tasks[idx][1]
                
                # Tag offers with nearby airport metadata
                for offer in result:
                    offer.nearby_origin = (origin_code != original_origin)
                    offer.nearby_destination = (dest_code != original_destination)
                    if offer.nearby_origin:
                        offer.source_airport = origin_code
                    
                all_offers.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Provider error: {result}")
        
        # Validate flight data quality and recompute durations
        validated_offers = validate_flight_offers(all_offers, self.airport_data)
        logger.info(f"✅ Validated {len(validated_offers)} offers (dropped {len(all_offers) - len(validated_offers)} invalid)")
        
        # Remove duplicates (same route, carrier, time)
        unique_offers = self._deduplicate_flights(validated_offers)
        
        # Rank results
        ranked_offers = self.ranking.rank_flights(unique_offers)
        
        # Cache for 15 minutes
        await self.cache.set(cache_key, ranked_offers, ttl=settings.cache_ttl)
        
        logger.info(f"Returning {len(ranked_offers)} flight offers")
        return ranked_offers
    
    async def search_hotels(self, request: HotelSearchRequest) -> List[HotelOffer]:
        """Search hotels from configured provider"""
        cache_key = f"hotels:{request.city}:{request.check_in}:{request.check_out}:{len(request.rooms)}"
        
        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for {cache_key}")
            return cached
        
        # Query hotel provider (currently only Amadeus)
        logger.info(f"Searching hotels in: {request.city} via {self.hotel_provider}")
        
        if self.hotel_provider == "amadeus":
            offers = await self.amadeus_hotels.search_hotels(request)
        else:
            logger.warning(f"Unknown hotel provider: {self.hotel_provider}, defaulting to Amadeus")
            offers = await self.amadeus_hotels.search_hotels(request)
        
        # Rank results
        ranked_offers = self.ranking.rank_hotels(offers)
        
        # Cache
        await self.cache.set(cache_key, ranked_offers, ttl=settings.cache_ttl)
        
        logger.info(f"Returning {len(ranked_offers)} hotel offers")
        return ranked_offers
    
    def _deduplicate_flights(self, offers: List[FlightOffer]) -> List[FlightOffer]:
        """Remove duplicate flight offers"""
        seen = set()
        unique = []
        
        for offer in offers:
            # Create key from first segment (main flight)
            if offer.segments:
                seg = offer.segments[0]
                key = f"{seg.carrier_code}:{seg.flight_number}:{seg.departure_time}"
                if key not in seen:
                    seen.add(key)
                    unique.append(offer)
        
        return unique

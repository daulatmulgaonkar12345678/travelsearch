from typing import List
import asyncio
from app.models.flight import FlightOffer, FlightSearchRequest
from app.models.hotel import HotelOffer, HotelSearchRequest
from app.services.adapters.amadeus_flights import AmadeusFlightsAdapter
from app.services.adapters.amadeus_hotels import AmadeusHotelsAdapter
from app.services.adapters.duffel_flights import DuffelFlightsAdapter
from app.services.ranking import RankingEngine
from app.services.cache import CacheService
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
        
        logger.info(f"SearchAggregator initialized with flight={self.flight_provider}, hotel={self.hotel_provider}")
    
    async def search_flights(self, request: FlightSearchRequest) -> List[FlightOffer]:
        """Search flights from all providers and aggregate"""
        cache_key = f"flights:{request.origin}:{request.destination}:{request.departure_date}"
        
        # Check cache first
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for {cache_key}")
            return cached
        
        # Query all providers in parallel
        logger.info(f"Searching flights: {request.origin} -> {request.destination}")
        results = await asyncio.gather(
            self.amadeus.search_flights(request),
            self.lcc.search_flights(request),
            return_exceptions=True
        )
        
        # Flatten results and handle errors
        all_offers = []
        for result in results:
            if isinstance(result, list):
                all_offers.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Provider error: {result}")
        
        # Remove duplicates (same route, carrier, time)
        unique_offers = self._deduplicate_flights(all_offers)
        
        # Rank results
        ranked_offers = self.ranking.rank_flights(unique_offers)
        
        # Cache for 15 minutes
        await self.cache.set(cache_key, ranked_offers, ttl=settings.cache_ttl)
        
        return ranked_offers
    
    async def search_hotels(self, request: HotelSearchRequest) -> List[HotelOffer]:
        """Search hotels from all providers and aggregate"""
        cache_key = f"hotels:{request.city}:{request.check_in}:{request.check_out}"
        
        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for {cache_key}")
            return cached
        
        # Query hotel providers
        logger.info(f"Searching hotels in: {request.city}")
        offers = await self.hotels.search_hotels(request)
        
        # Rank results
        ranked_offers = self.ranking.rank_hotels(offers)
        
        # Cache
        await self.cache.set(cache_key, ranked_offers, ttl=settings.cache_ttl)
        
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

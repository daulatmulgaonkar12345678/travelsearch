"""
Hub Composition Engine

Composes multi-leg connecting flights when direct routes are not available.
Example: PNQ → BOM → BOS (Pune to Mumbai to Boston via hub)
"""

import logging
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

from app.models.flight import FlightOffer, FlightSegment, FlightSearchRequest
from app.hubs.hub_config import get_candidate_hubs

logger = logging.getLogger(__name__)

class HubComposer:
    """
    Composes connecting flights via hub airports.
    
    Strategy:
    1. Identify candidate hubs between origin and destination
    2. Search for: origin → hub AND hub → destination
    3. If both legs have flights, compose them into a single itinerary
    4. Calculate total journey time and price
    """
    
    def __init__(self, flight_search_func):
        """
        Args:
            flight_search_func: Async function to search flights
                               Signature: async (origin, dest, date, request) -> List[FlightOffer]
        """
        self.search_flights = flight_search_func
    
    async def compose_via_hubs(
        self,
        request: FlightSearchRequest,
        max_hubs: int = 3
    ) -> List[FlightOffer]:
        """
        Attempt to compose connecting flights via hub airports.
        
        Args:
            request: Original flight search request
            max_hubs: Maximum number of hubs to try
            
        Returns:
            List of composed multi-leg flight offers
        """
        logger.info(f"🔄 Hub composition: {request.origin} → ? → {request.destination}")
        
        # Get candidate hubs
        candidate_hubs = get_candidate_hubs(
            request.origin,
            request.destination,
            max_hubs=max_hubs
        )
        
        if not candidate_hubs:
            logger.info(f"No candidate hubs found for {request.origin} → {request.destination}")
            return []
        
        logger.info(f"📍 Trying hubs: {candidate_hubs}")
        
        composed_offers = []
        
        for hub in candidate_hubs:
            try:
                # Search both legs
                leg1_offers, leg2_offers = await self._search_both_legs(
                    request,
                    hub
                )
                
                if not leg1_offers or not leg2_offers:
                    logger.info(f"❌ {hub}: Missing leg (leg1={len(leg1_offers)}, leg2={len(leg2_offers)})")
                    continue
                
                # Compose compatible combinations
                compositions = self._compose_compatible_flights(
                    leg1_offers,
                    leg2_offers,
                    hub,
                    request.origin,
                    request.destination
                )
                
                if compositions:
                    logger.info(f"✅ {hub}: Composed {len(compositions)} connecting flights")
                    composed_offers.extend(compositions)
                
            except Exception as e:
                logger.error(f"Error composing via hub {hub}: {e}")
                continue
        
        # Sort by total price
        composed_offers.sort(key=lambda x: x.price)
        
        logger.info(f"🎯 Hub composition found {len(composed_offers)} total options")
        return composed_offers[:10]  # Return top 10
    
    async def _search_both_legs(
        self,
        request: FlightSearchRequest,
        hub: str
    ) -> Tuple[List[FlightOffer], List[FlightOffer]]:
        """
        Search both legs of a connecting flight in parallel.
        
        Returns:
            (leg1_offers, leg2_offers)
        """
        import asyncio
        
        # Leg 1: origin → hub (same date)
        leg1_request = FlightSearchRequest(
            trip_type="oneway",
            origin=request.origin,
            destination=hub,
            departure_date=request.departure_date,
            adults=request.adults,
            children=request.children,
            infants=request.infants,
            cabin_class=request.cabin_class,
            direct_only=False
        )
        
        # Leg 2: hub → destination (same date or +1 day for layover)
        leg2_request = FlightSearchRequest(
            trip_type="oneway",
            origin=hub,
            destination=request.destination,
            departure_date=request.departure_date,
            adults=request.adults,
            children=request.children,
            infants=request.infants,
            cabin_class=request.cabin_class,
            direct_only=False
        )
        
        # Search both in parallel
        leg1_offers, leg2_offers = await asyncio.gather(
            self.search_flights(leg1_request),
            self.search_flights(leg2_request),
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(leg1_offers, Exception):
            logger.error(f"Leg 1 error: {leg1_offers}")
            leg1_offers = []
        if isinstance(leg2_offers, Exception):
            logger.error(f"Leg 2 error: {leg2_offers}")
            leg2_offers = []
        
        return leg1_offers, leg2_offers
    
    def _compose_compatible_flights(
        self,
        leg1_offers: List[FlightOffer],
        leg2_offers: List[FlightOffer],
        hub: str,
        origin: str,
        destination: str,
        min_connection_minutes: int = 90,
        max_connection_minutes: int = 480
    ) -> List[FlightOffer]:
        """
        Combine compatible flights from both legs.
        
        Rules:
        - Leg 2 departure must be after leg 1 arrival
        - Connection time must be between min and max
        - Total duration should be reasonable
        """
        composed = []
        
        for leg1 in leg1_offers[:5]:  # Top 5 from leg 1
            leg1_arrival = self._parse_datetime(leg1.segments[-1].arrival_time)
            if not leg1_arrival:
                continue
            
            for leg2 in leg2_offers[:5]:  # Top 5 from leg 2
                leg2_departure = self._parse_datetime(leg2.segments[0].departure_time)
                if not leg2_departure:
                    continue
                
                # Check connection time
                connection_minutes = (leg2_departure - leg1_arrival).total_seconds() / 60
                
                if connection_minutes < min_connection_minutes:
                    continue  # Too short
                if connection_minutes > max_connection_minutes:
                    continue  # Too long
                
                # Create composed offer
                composed_offer = self._create_composed_offer(
                    leg1, leg2, hub, origin, destination, connection_minutes
                )
                composed.append(composed_offer)
        
        return composed
    
    def _create_composed_offer(
        self,
        leg1: FlightOffer,
        leg2: FlightOffer,
        hub: str,
        origin: str,
        destination: str,
        connection_minutes: float
    ) -> FlightOffer:
        """Create a single FlightOffer from two legs."""
        
        # Combine segments
        all_segments = leg1.segments + leg2.segments
        
        # Calculate totals
        total_price = leg1.price + leg2.price
        total_duration = leg1.total_duration_minutes + leg2.total_duration_minutes + int(connection_minutes)
        total_stops = leg1.stops + leg2.stops + 1  # +1 for hub connection
        
        # Create composed offer
        composed = FlightOffer(
            offer_id=f"HUB-{leg1.offer_id}-{leg2.offer_id}",
            provider="hub_composed",
            price=total_price,
            currency=leg1.currency,
            segments=all_segments,
            total_duration_minutes=total_duration,
            stops=total_stops,
            cabin_class=leg1.cabin_class,
            refundable=leg1.refundable and leg2.refundable,
            baggage_allowance=min(leg1.baggage_allowance or 0, leg2.baggage_allowance or 0) if leg1.baggage_allowance and leg2.baggage_allowance else None,
            booking_url=None,  # Needs separate bookings
            # Metadata
            nearby_origin=False,
            nearby_destination=False,
            source_airport=origin,
            composed_via_hub=hub,
            connection_time_minutes=int(connection_minutes),
            requires_separate_bookings=True
        )
        
        return composed
    
    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Parse ISO datetime string."""
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            return None

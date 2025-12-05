from typing import List
from app.models.flight import FlightOffer
from app.models.hotel import HotelOffer

class RankingEngine:
    """Ranks search results using composite scoring"""
    
    # Weights for flight ranking
    FLIGHT_WEIGHTS = {
        "price": 0.6,
        "duration": 0.25,
        "stops": 0.15
    }
    
    def rank_flights(self, offers: List[FlightOffer]) -> List[FlightOffer]:
        """Rank flights by composite score"""
        if not offers:
            return offers
        
        # Calculate scores
        for offer in offers:
            offer.rating = self._calculate_flight_score(offer, offers)
        
        # Sort by rating descending
        return sorted(offers, key=lambda x: x.rating or 0, reverse=True)
    
    def _calculate_flight_score(self, offer: FlightOffer, all_offers: List[FlightOffer]) -> float:
        """Calculate composite score for a flight (0-100)"""
        # Normalize price (lower is better)
        prices = [o.price for o in all_offers]
        min_price = min(prices)
        max_price = max(prices)
        price_score = 100 - ((offer.price - min_price) / (max_price - min_price + 1) * 100) if max_price > min_price else 100
        
        # Normalize duration (shorter is better)
        durations = [o.total_duration_minutes for o in all_offers]
        min_duration = min(durations)
        max_duration = max(durations)
        duration_score = 100 - ((offer.total_duration_minutes - min_duration) / (max_duration - min_duration + 1) * 100) if max_duration > min_duration else 100
        
        # Stops score (fewer is better)
        stops_score = 100 - (offer.stops * 30)  # -30 points per stop
        stops_score = max(stops_score, 0)
        
        # Composite score
        score = (
            price_score * self.FLIGHT_WEIGHTS["price"] +
            duration_score * self.FLIGHT_WEIGHTS["duration"] +
            stops_score * self.FLIGHT_WEIGHTS["stops"]
        )
        
        return round(score, 1)
    
    def rank_hotels(self, offers: List[HotelOffer]) -> List[HotelOffer]:
        """Rank hotels by rating and price"""
        if not offers:
            return offers
        
        # Sort by rating (desc), then price (asc)
        return sorted(
            offers,
            key=lambda x: (-(x.rating or 0), x.total_price)
        )

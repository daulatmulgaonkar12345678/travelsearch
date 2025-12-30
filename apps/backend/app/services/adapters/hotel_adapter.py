from typing import List
from datetime import datetime
from app.models.hotel import HotelOffer, HotelSearchRequest
from app.models.flight import FlightOffer, FlightSearchRequest
from app.utils.travelpayouts_deeplinks import (
    generate_hotel_specific_deep_link,
    generate_hotel_specific_booking_partners
)
from .base import ProviderAdapter

class HotelAdapter(ProviderAdapter):
    """Multi-provider hotel adapter (Trip.com, Agoda, Booking.com)"""
    
    def __init__(self, trip_key: str = None, agoda_key: str = None, mock_mode: bool = True):
        super().__init__("hotel_aggregator", mock_mode)
        self.trip_key = trip_key
        self.agoda_key = agoda_key
    
    async def search_flights(self, request: FlightSearchRequest) -> List[FlightOffer]:
        """Flights not supported by this adapter"""
        return []
    
    async def search_hotels(self, request: HotelSearchRequest) -> List[HotelOffer]:
        """Search hotels from multiple providers"""
        if self.mock_mode:
            return self._mock_hotel_search(request)
        else:
            # Real hotel API integrations go here
            return self._mock_hotel_search(request)
    
    def _mock_hotel_search(self, request: HotelSearchRequest) -> List[HotelOffer]:
        """Generate realistic mock hotel data from multiple providers"""
        check_in = datetime.fromisoformat(request.check_in)
        check_out = datetime.fromisoformat(request.check_out)
        nights = (check_out - check_in).days
        
        offers = []
        
        # Define mock hotels with unique names
        mock_hotels = [
            {
                "hotel_name": "Grand Plaza Hotel",
                "provider": "trip.com",
                "address": f"123 Main Street, {request.city}",
                "rating": 4.5,
                "review_score": 8.7,
                "review_count": 1243,
                "price_per_night": 4500.0,
                "amenities": ["Free WiFi", "Pool", "Gym", "Restaurant", "Bar"],
                "room_type": "Deluxe King Room",
                "cancellation_policy": "Free cancellation until 24h before check-in",
            },
            {
                "hotel_name": "City View Inn",
                "provider": "agoda",
                "address": f"456 Park Avenue, {request.city}",
                "rating": 3.5,
                "review_score": 7.8,
                "review_count": 856,
                "price_per_night": 2800.0,
                "amenities": ["Free WiFi", "Breakfast", "24h Reception"],
                "room_type": "Standard Double Room",
                "cancellation_policy": "Non-refundable",
            },
            {
                "hotel_name": "Luxury Suites & Spa",
                "provider": "booking.com",
                "address": f"789 Elite Boulevard, {request.city}",
                "rating": 5.0,
                "review_score": 9.3,
                "review_count": 2104,
                "price_per_night": 8900.0,
                "amenities": ["Free WiFi", "Pool", "Spa", "Gym", "Fine Dining", "Concierge", "Valet"],
                "room_type": "Executive Suite",
                "cancellation_policy": "Free cancellation until 48h before check-in",
            },
        ]
        
        for idx, hotel in enumerate(mock_hotels):
            hotel_name = hotel["hotel_name"]
            
            # CRITICAL: Generate HOTEL-SPECIFIC deep link for each hotel
            # This ensures each hotel card has a UNIQUE booking URL
            deep_link_result = generate_hotel_specific_deep_link(
                hotel_name=hotel_name,
                city=request.city,
                check_in=request.check_in,
                check_out=request.check_out,
                adults=request.adults or 2,
                rooms=request.rooms or 1,
                hotel_id=f"MOCK-{idx+1}",
                provider=hotel["provider"]
            )
            
            # Generate hotel-specific booking partners
            booking_partners = generate_hotel_specific_booking_partners(
                hotel_name=hotel_name,
                city=request.city,
                check_in=request.check_in,
                check_out=request.check_out,
                adults=request.adults or 2,
                rooms=request.rooms or 1,
                hotel_id=f"MOCK-{idx+1}",
                provider=hotel["provider"]
            )
            
            offers.append(HotelOffer(
                offer_id=f"{hotel['provider'].upper()}-{request.city}-{idx+1:03d}",
                provider=hotel["provider"],
                hotel_name=hotel_name,
                address=hotel["address"],
                city=request.city,
                rating=hotel["rating"],
                review_score=hotel["review_score"],
                review_count=hotel["review_count"],
                price_per_night=hotel["price_per_night"],
                total_price=hotel["price_per_night"] * nights,
                currency="INR",
                amenities=hotel["amenities"],
                room_type=hotel["room_type"],
                cancellation_policy=hotel["cancellation_policy"],
                images=[
                    f"https://via.placeholder.com/400x300?text={hotel_name.replace(' ', '+')}"
                ],
                deep_link=deep_link_result["url"],  # HOTEL-SPECIFIC URL
                booking_partners=booking_partners  # HOTEL-SPECIFIC partners
            ))
        
        # Filter by min_rating if specified
        if request.min_rating:
            offers = [o for o in offers if o.rating and o.rating >= request.min_rating]
        
        # Filter by max_price if specified
        if request.max_price:
            offers = [o for o in offers if o.total_price <= request.max_price]
        
        return offers

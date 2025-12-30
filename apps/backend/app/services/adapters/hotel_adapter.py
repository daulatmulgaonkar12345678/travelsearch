from typing import List
from datetime import datetime
from app.models.hotel import HotelOffer, HotelSearchRequest
from app.models.flight import FlightOffer, FlightSearchRequest
from app.utils.travelpayouts_deeplinks import generate_hotel_deep_link, generate_hotel_booking_partners
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
        
        # Generate proper Travelpayouts deep link
        deep_link_result = generate_hotel_deep_link(
            city=request.city,
            check_in=request.check_in,
            check_out=request.check_out,
            adults=request.adults or 2,
            rooms=request.rooms or 1
        )
        travelpayouts_url = deep_link_result["url"]
        
        # Generate booking partners for this hotel search
        booking_partners = generate_hotel_booking_partners(
            city=request.city,
            check_in=request.check_in,
            check_out=request.check_out,
            adults=request.adults or 2,
            rooms=request.rooms or 1
        )
        
        offers = []
        
        # Trip.com offer
        offers.append(HotelOffer(
            offer_id=f"TRIP-{request.city}-001",
            provider="trip.com",
            hotel_name="Grand Plaza Hotel",
            address=f"123 Main Street, {request.city}",
            city=request.city,
            rating=4.5,
            review_score=8.7,
            review_count=1243,
            price_per_night=4500.0,
            total_price=4500.0 * nights,
            currency="INR",
            amenities=["Free WiFi", "Pool", "Gym", "Restaurant", "Bar"],
            room_type="Deluxe King Room",
            cancellation_policy="Free cancellation until 24h before check-in",
            images=[
                "https://via.placeholder.com/400x300?text=Hotel+Room+1",
                "https://via.placeholder.com/400x300?text=Hotel+Pool"
            ],
            deep_link=travelpayouts_url,  # Use Travelpayouts redirect
            booking_partners=booking_partners
        ))
        
        # Agoda offer - cheaper option
        offers.append(HotelOffer(
            offer_id=f"AGODA-{request.city}-001",
            provider="agoda",
            hotel_name="City View Inn",
            address=f"456 Park Avenue, {request.city}",
            city=request.city,
            rating=3.5,
            review_score=7.8,
            review_count=856,
            price_per_night=2800.0,
            total_price=2800.0 * nights,
            currency="INR",
            amenities=["Free WiFi", "Breakfast", "24h Reception"],
            room_type="Standard Double Room",
            cancellation_policy="Non-refundable",
            images=[
                "https://via.placeholder.com/400x300?text=City+View+Room"
            ],
            deep_link=travelpayouts_url,  # Use Travelpayouts redirect
            booking_partners=booking_partners
        ))
        
        # Booking.com offer - luxury option
        offers.append(HotelOffer(
            offer_id=f"BOOKING-{request.city}-001",
            provider="booking.com",
            hotel_name="Luxury Suites & Spa",
            address=f"789 Elite Boulevard, {request.city}",
            city=request.city,
            rating=5.0,
            review_score=9.3,
            review_count=2104,
            price_per_night=8900.0,
            total_price=8900.0 * nights,
            currency="INR",
            amenities=["Free WiFi", "Pool", "Spa", "Gym", "Fine Dining", "Concierge", "Valet"],
            room_type="Executive Suite",
            cancellation_policy="Free cancellation until 48h before check-in",
            images=[
                "https://via.placeholder.com/400x300?text=Luxury+Suite",
                "https://via.placeholder.com/400x300?text=Hotel+Spa",
                "https://via.placeholder.com/400x300?text=Restaurant"
            ],
            deep_link=travelpayouts_url,  # Use Travelpayouts redirect
            booking_partners=booking_partners
        ))
        
        # Filter by min_rating if specified
        if request.min_rating:
            offers = [o for o in offers if o.rating and o.rating >= request.min_rating]
        
        # Filter by max_price if specified
        if request.max_price:
            offers = [o for o in offers if o.total_price <= request.max_price]
        
        return offers

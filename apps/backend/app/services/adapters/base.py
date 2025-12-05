from abc import ABC, abstractmethod
from typing import List
from app.models.flight import FlightOffer, FlightSearchRequest
from app.models.hotel import HotelOffer, HotelSearchRequest

class ProviderAdapter(ABC):
    """Base interface for all provider adapters"""
    
    def __init__(self, provider_name: str, mock_mode: bool = True):
        self.provider_name = provider_name
        self.mock_mode = mock_mode
    
    @abstractmethod
    async def search_flights(self, request: FlightSearchRequest) -> List[FlightOffer]:
        """Search flights and return normalized offers"""
        pass
    
    @abstractmethod
    async def search_hotels(self, request: HotelSearchRequest) -> List[HotelOffer]:
        """Search hotels and return normalized offers"""
        pass
    
    def normalize_price(self, price: float, currency: str = "INR") -> float:
        """Normalize price to INR"""
        # Currency conversion rates (mock)
        rates = {
            "USD": 83.0,
            "EUR": 90.0,
            "GBP": 105.0,
            "INR": 1.0,
        }
        return price * rates.get(currency, 1.0)

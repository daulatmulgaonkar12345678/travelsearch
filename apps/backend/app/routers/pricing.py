"""
Pricing API for flexible date searches
Returns minimum prices per date without filters
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory cache for date prices
# Key: "origin:destination:date:adults:cabin"
# Value: {"price": float, "expires_at": datetime}
DATE_PRICE_CACHE: Dict[str, Dict] = {}
CACHE_TTL_SECONDS = 900  # 15 minutes

class DatePriceRequest(BaseModel):
    origin: str
    destination: str
    dates: List[str]  # List of dates in YYYY-MM-DD format
    adults: int = 1
    children: int = 0
    infants: int = 0
    cabin_class: str = "economy"
    trip_type: str = "oneway"

class DatePriceResponse(BaseModel):
    date: str
    min_price: Optional[float]
    currency: str = "INR"
    cached: bool = False

def get_cache_key(origin: str, destination: str, date: str, adults: int, cabin: str) -> str:
    """Generate cache key for a specific date search"""
    return f"{origin}:{destination}:{date}:{adults}:{cabin}"

def get_cached_price(cache_key: str) -> Optional[float]:
    """Get price from cache if not expired"""
    if cache_key in DATE_PRICE_CACHE:
        cached_data = DATE_PRICE_CACHE[cache_key]
        if datetime.utcnow() < cached_data["expires_at"]:
            logger.info(f"Cache hit for {cache_key}")
            return cached_data["price"]
        else:
            # Expired, remove it
            del DATE_PRICE_CACHE[cache_key]
    return None

def set_cached_price(cache_key: str, price: Optional[float]):
    """Store price in cache with TTL"""
    DATE_PRICE_CACHE[cache_key] = {
        "price": price,
        "expires_at": datetime.utcnow() + timedelta(seconds=CACHE_TTL_SECONDS)
    }

@router.post("/pricing/date-range", response_model=List[DatePriceResponse])
async def get_date_range_prices(request: DatePriceRequest):
    """
    Get minimum prices for multiple dates
    
    This endpoint fetches the baseline minimum price for each date
    without applying UI filters (stops, airlines, departure time, etc.)
    
    Used by the flexible date strip to show real per-day pricing
    """
    try:
        from app.services.adapters.amadeus_flights import AmadeusFlightsAdapter
        from app.models.flight import FlightSearchRequest
        
        amadeus = AmadeusFlightsAdapter()
        results = []
        
        logger.info(f"Fetching prices for {len(request.dates)} dates: {request.origin} -> {request.destination}")
        
        for date_str in request.dates:
            cache_key = get_cache_key(
                request.origin, 
                request.destination, 
                date_str, 
                request.adults, 
                request.cabin_class
            )
            
            # Check cache first
            cached_price = get_cached_price(cache_key)
            if cached_price is not None:
                results.append(DatePriceResponse(
                    date=date_str,
                    min_price=cached_price,
                    currency="INR",
                    cached=True
                ))
                continue
            
            # Fetch from Amadeus
            try:
                search_request = FlightSearchRequest(
                    trip_type=request.trip_type,
                    origin=request.origin,
                    destination=request.destination,
                    departure_date=date_str,
                    return_date=None,
                    adults=request.adults,
                    children=None,
                    infants=request.infants,
                    cabin_class=request.cabin_class,
                    direct_only=False,
                    max_price=None,
                    max_duration_minutes=None,
                    refundable_only=False,
                    include_red_eye=True,
                    green_only=False
                )
                
                offers = await amadeus.search_flights(search_request)
                
                if offers and len(offers) > 0:
                    # Find minimum price
                    min_price = min(offer.price for offer in offers)
                    
                    # Cache it
                    set_cached_price(cache_key, min_price)
                    
                    results.append(DatePriceResponse(
                        date=date_str,
                        min_price=min_price,
                        currency="INR",
                        cached=False
                    ))
                    logger.info(f"Date {date_str}: min price = {min_price}")
                else:
                    # No flights for this date
                    set_cached_price(cache_key, None)
                    results.append(DatePriceResponse(
                        date=date_str,
                        min_price=None,
                        currency="INR",
                        cached=False
                    ))
                    logger.info(f"Date {date_str}: no flights")
                    
            except Exception as e:
                logger.error(f"Error fetching price for {date_str}: {str(e)}")
                # Return None for this date but continue
                results.append(DatePriceResponse(
                    date=date_str,
                    min_price=None,
                    currency="INR",
                    cached=False
                ))
        
        return results
        
    except Exception as e:
        logger.error(f"Date range pricing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pricing/cache-stats")
async def get_cache_stats():
    """Get cache statistics (for debugging)"""
    active_entries = sum(
        1 for data in DATE_PRICE_CACHE.values() 
        if datetime.utcnow() < data["expires_at"]
    )
    
    return {
        "total_entries": len(DATE_PRICE_CACHE),
        "active_entries": active_entries,
        "cache_ttl_seconds": CACHE_TTL_SECONDS
    }

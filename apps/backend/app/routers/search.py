from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models.flight import FlightSearchRequest, FlightSearchResponse, FlightOffer
from app.models.hotel import HotelSearchRequest, HotelSearchResponse, HotelOffer
from app.services.aggregator import SearchAggregator
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
aggregator = SearchAggregator()

@router.get("/search/flights", response_model=FlightSearchResponse)
async def search_flights(
    # Trip type
    trip_type: str = Query("roundtrip", description="Trip type: oneway, roundtrip, multicity"),
    
    # Basic route (for oneway/roundtrip)
    origin: Optional[str] = Query(None, description="Origin airport IATA code"),
    destination: Optional[str] = Query(None, description="Destination airport IATA code"),
    departure_date: Optional[str] = Query(None, description="Departure date (YYYY-MM-DD)"),
    return_date: Optional[str] = Query(None, description="Return date (YYYY-MM-DD)"),
    
    # Passengers
    adults: int = Query(1, ge=1, le=9),
    infants: int = Query(0, ge=0, le=9),
    
    # Cabin class
    cabin_class: str = Query("economy"),
    
    # Filters
    direct_only: bool = Query(False),
    max_price: Optional[float] = Query(None),
    max_duration_minutes: Optional[int] = Query(None),
    refundable_only: bool = Query(False),
    include_red_eye: bool = Query(True),
    green_only: bool = Query(False),
):
    """Search flights from multiple providers (GET endpoint for simple queries)"""
    try:
        # Parse children ages from query params (child_0_age, child_1_age, etc.)
        from fastapi import Request
        # For simplicity in GET, we'll accept a children count
        # Real implementation would parse dynamic params
        
        request = FlightSearchRequest(
            trip_type=trip_type,
            origin=origin.upper() if origin else None,
            destination=destination.upper() if destination else None,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            children=None,  # Will be parsed from query params in real implementation
            infants=infants,
            cabin_class=cabin_class,
            direct_only=direct_only,
            max_price=max_price,
            max_duration_minutes=max_duration_minutes,
            refundable_only=refundable_only,
            include_red_eye=include_red_eye,
            green_only=green_only,
        )
        
        logger.info(f"Flight search request: {request.trip_type} {request.origin} -> {request.destination}")
        
        offers = await aggregator.search_flights(request)
        
        return FlightSearchResponse(
            offers=offers,
            search_id=str(uuid.uuid4()),
            cached=False,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Flight search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/flights", response_model=FlightSearchResponse)
async def search_flights_post(request: FlightSearchRequest):
    """Search flights (POST method)"""
    try:
        logger.info(f"Flight search request: {request.origin} -> {request.destination}")
        offers = await aggregator.search_flights(request)
        
        return FlightSearchResponse(
            offers=offers,
            search_id=str(uuid.uuid4()),
            cached=False,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Flight search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/hotels", response_model=HotelSearchResponse)
async def search_hotels(
    city: str = Query(..., description="City name"),
    check_in: str = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: str = Query(..., description="Check-out date (YYYY-MM-DD)"),
    
    # Filters
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    max_rating: Optional[float] = Query(None, ge=0, le=5),
    min_review_score: Optional[float] = Query(None, ge=0, le=10),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    
    # Policies
    free_cancellation: bool = Query(False),
    pay_at_hotel: bool = Query(False),
    ac_required: bool = Query(False),
    
    # Location
    max_distance_km: Optional[float] = Query(None),
):
    """Search hotels from multiple providers (GET endpoint for simple queries)"""
    try:
        # Validate dates
        from datetime import date, timedelta
        today = date.today()
        check_in_date = date.fromisoformat(check_in)
        check_out_date = date.fromisoformat(check_out)
        
        if check_in_date < today + timedelta(days=1):
            raise HTTPException(status_code=400, detail="Check-in must be at least tomorrow")
        
        if check_out_date <= check_in_date:
            raise HTTPException(status_code=400, detail="Check-out must be after check-in")
        
        # For GET endpoint, we'll use a simple structure
        # Real implementation would parse room configurations from query params
        request = HotelSearchRequest(
            city=city,
            check_in=check_in,
            check_out=check_out,
            rooms=[{"adults": 2, "children": []}],  # Default single room
            min_rating=min_rating,
            max_rating=max_rating,
            min_review_score=min_review_score,
            min_price=min_price,
            max_price=max_price,
            free_cancellation=free_cancellation,
            pay_at_hotel=pay_at_hotel,
            ac_required=ac_required,
            max_distance_km=max_distance_km,
        )
        
        logger.info(f"Hotel search request: {request.city}")
        
        offers = await aggregator.search_hotels(request)
        
        return HotelSearchResponse(
            offers=offers,
            search_id=str(uuid.uuid4()),
            cached=False,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Hotel search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/hotels", response_model=HotelSearchResponse)
async def search_hotels_post(request: HotelSearchRequest):
    """Search hotels (POST method)"""
    try:
        logger.info(f"Hotel search request: {request.city}")
        offers = await aggregator.search_hotels(request)
        
        return HotelSearchResponse(
            offers=offers,
            search_id=str(uuid.uuid4()),
            cached=False,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Hotel search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

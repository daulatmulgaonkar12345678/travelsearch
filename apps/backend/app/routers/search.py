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
    origin: str = Query(..., description="Origin airport IATA code"),
    destination: str = Query(..., description="Destination airport IATA code"),
    departure_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    return_date: Optional[str] = Query(None, description="Return date (YYYY-MM-DD)"),
    adults: int = Query(1, ge=1, le=9),
    children: int = Query(0, ge=0, le=9),
    infants: int = Query(0, ge=0, le=9),
    cabin_class: str = Query("economy"),
    direct_only: bool = Query(False),
):
    """Search flights from multiple providers"""
    try:
        request = FlightSearchRequest(
            origin=origin.upper(),
            destination=destination.upper(),
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            children=children,
            infants=infants,
            cabin_class=cabin_class,
            direct_only=direct_only
        )
        
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
    adults: int = Query(1, ge=1),
    children: int = Query(0, ge=0),
    rooms: int = Query(1, ge=1),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    max_price: Optional[float] = Query(None, ge=0),
):
    """Search hotels from multiple providers"""
    try:
        request = HotelSearchRequest(
            city=city,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            children=children,
            rooms=rooms,
            min_rating=min_rating,
            max_price=max_price
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

from fastapi import APIRouter, HTTPException, Query, Request, Header
from typing import List, Optional, Dict, Any
from app.models.flight import FlightSearchRequest, FlightSearchResponse, FlightOffer
from app.models.hotel import HotelSearchRequest, HotelSearchResponse, HotelOffer
from app.services.aggregator import SearchAggregator
from app.services.airport_validator import validate_route, is_valid_airport
from app.core.config import settings
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
aggregator = SearchAggregator()


@router.get("/search/flights")
async def search_flights(
    request: Request,
    # Search intent header - REQUIRED for real searches
    x_search_intent: Optional[str] = Header(None, alias="x-search-intent"),
    
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
    
    # Filters (CLIENT-SIDE ONLY - these NEVER trigger API calls)
    # ⚠️ WARNING: Filters are intentionally client-side to prevent API cost leakage
    direct_only: bool = Query(False),
    max_price: Optional[float] = Query(None),
    max_duration_minutes: Optional[int] = Query(None),
    refundable_only: bool = Query(False),
    include_red_eye: bool = Query(True),
    green_only: bool = Query(False),
    
    # Nearby airports
    include_nearby_origin: bool = Query(False),
    include_nearby_destination: bool = Query(False),
    nearby_radius_km: float = Query(250.0),
) -> Dict[str, Any]:
    """
    Search flights with cost-controlled Amadeus integration.
    
    COST CONTROL RULES:
    1. Only explicit "Search Flights" clicks trigger real API calls
    2. Must include header: x-search-intent = "real" for real searches
    3. Daily cap: 70 searches (configurable) for Amadeus fallback
    4. Results cached for 10-15 minutes
    5. Per-IP rate limit: 5/minute
    
    PROVIDER PRIORITY:
    1. Aviasales (PRIMARY) - Real-time pricing with affiliate deeplinks
    2. Amadeus (FALLBACK) - Cost-controlled with daily caps
    
    ⚠️ FILTERS ARE CLIENT-SIDE ONLY:
    Filters and sorting operate on already-fetched results.
    They NEVER trigger additional API calls.
    """
    try:
        # Build request object
        search_request = FlightSearchRequest(
            trip_type=trip_type,
            origin=origin.upper() if origin else None,
            destination=destination.upper() if destination else None,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            children=None,
            infants=infants,
            cabin_class=cabin_class,
            direct_only=direct_only,
            max_price=max_price,
            max_duration_minutes=max_duration_minutes,
            refundable_only=refundable_only,
            include_red_eye=include_red_eye,
            green_only=green_only,
            include_nearby_origin=include_nearby_origin,
            include_nearby_destination=include_nearby_destination,
            nearby_radius_km=nearby_radius_km,
        )
        
        # Validate route
        if not search_request.origin or not search_request.destination:
            return {
                "status": "completed",
                "outcome": "error",
                "message": "Origin and destination are required",
                "offers": [],
                "flights": []
            }
        
        # Get client IP for rate limiting
        client_ip = request.client.host if request.client else "unknown"
        
        # Build headers dict for search control
        headers = {
            "x-search-intent": x_search_intent or ""
        }
        
        logger.info(
            f"🔍 Flight search: {search_request.origin} → {search_request.destination} "
            f"on {search_request.departure_date} | Intent: {x_search_intent}"
        )
        
        # Step 1: Try Aviasales (PRIMARY) first
        from app.services.aviasales_orchestrator import aviasales_first_orchestrator
        aviasales_result = await aviasales_first_orchestrator.search(search_request)
        
        # If Aviasales returns results, use them
        if aviasales_result.get("outcome") == "results" and aviasales_result.get("offers"):
            logger.info(f"✅ Aviasales returned {len(aviasales_result.get('offers', []))} offers")
            aviasales_result["request_id"] = str(uuid.uuid4())
            aviasales_result["search_id"] = aviasales_result["request_id"]
            aviasales_result["timestamp"] = datetime.utcnow().isoformat()
            aviasales_result["source"] = "aviasales"
            aviasales_result["is_live"] = True
            return aviasales_result
        
        # Step 2: If Aviasales returns empty, try cost-controlled Amadeus (FALLBACK)
        logger.info("⚠️ Aviasales returned no results, trying Amadeus fallback")
        
        from app.services.amadeus_protected import search_flights_protected
        result = await search_flights_protected(
            request=search_request,
            headers=headers,
            client_ip=client_ip
        )
        
        # Add standard fields for compatibility
        result["request_id"] = str(uuid.uuid4())
        result["search_id"] = result["request_id"]
        result["timestamp"] = datetime.utcnow().isoformat()
        
        # Note: Filters should be applied CLIENT-SIDE on these results
        # This prevents additional API calls when user changes filters
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Flight search error: {e}", exc_info=True)
        return {
            "request_id": str(uuid.uuid4()),
            "status": "completed",
            "outcome": "error",
            "message": "Something went wrong. Please try again.",
            "flights": [],
            "offers": [],
            "source": "error"
        }

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
        # Log incoming request for debugging
        logger.info(f"=== HOTEL SEARCH REQUEST START ===")
        logger.info(f"Request city: {request.city}")
        logger.info(f"Request check_in: {request.check_in}")
        logger.info(f"Request check_out: {request.check_out}")
        logger.info(f"Request rooms: {request.rooms}")
        logger.info(f"Full request dict: {request.dict()}")
        
        # Validate dates
        from datetime import date, timedelta
        today = date.today()
        
        try:
            check_in_date = date.fromisoformat(request.check_in)
            check_out_date = date.fromisoformat(request.check_out)
            logger.info(f"Parsed dates - check_in: {check_in_date}, check_out: {check_out_date}")
        except ValueError as e:
            logger.error(f"Invalid date format: {e}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid date format. Use YYYY-MM-DD format. Error: {str(e)}"
            )
        
        if check_in_date < today:
            logger.warning(f"Check-in date {check_in_date} is in the past")
            # Allow it but warn - some users might be testing
        
        if check_out_date <= check_in_date:
            logger.error(f"Check-out date {check_out_date} is not after check-in date {check_in_date}")
            raise HTTPException(
                status_code=400, 
                detail="Check-out date must be after check-in date"
            )
        
        # Validate rooms
        if not request.rooms or len(request.rooms) == 0:
            logger.warning("No rooms specified, using default: 1 room, 2 adults")
            request.rooms = [{"adults": 2, "children": []}]
        
        # Validate each room structure
        for idx, room in enumerate(request.rooms):
            if not isinstance(room, dict):
                logger.error(f"Room {idx} is not a dict: {type(room)}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Room {idx} must be an object with 'adults' and 'children' fields"
                )
            if "adults" not in room:
                logger.error(f"Room {idx} missing 'adults' field")
                raise HTTPException(
                    status_code=400,
                    detail=f"Room {idx} must have an 'adults' field"
                )
            if not isinstance(room.get("adults"), int) or room["adults"] < 1:
                logger.error(f"Room {idx} has invalid adults count: {room.get('adults')}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Room {idx} must have at least 1 adult"
                )
        
        logger.info(f"Hotel search validated: {request.city}, {request.check_in} to {request.check_out}, {len(request.rooms)} room(s)")
        
        # Call aggregator
        offers = await aggregator.search_hotels(request)
        
        logger.info(f"Hotel search returned {len(offers)} offers")
        logger.info(f"=== HOTEL SEARCH REQUEST END ===")
        
        return HotelSearchResponse(
            offers=offers,
            search_id=str(uuid.uuid4()),
            cached=False,
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hotel search unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException, Query, Request, Header
from typing import Optional, Dict, Any
from app.models.flight import FlightSearchRequest, FlightSearchResponse
from app.models.hotel import HotelSearchRequest, HotelSearchResponse
from app.services.aggregator import SearchAggregator
from app.core.config import settings
import uuid
from datetime import datetime, date, timedelta
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter()
aggregator = SearchAggregator()

# ======================================================
# PROVIDER MODE (ENFORCED)
# ======================================================
FLIGHT_PROVIDER = os.getenv("FLIGHT_PROVIDER", "amadeus").lower()
HOTEL_PROVIDER = os.getenv("HOTEL_PROVIDER", "amadeus").lower()

if FLIGHT_PROVIDER != "amadeus":
    logger.error(f"❌ Invalid FLIGHT_PROVIDER={FLIGHT_PROVIDER}. Only 'amadeus' supported.")
    raise RuntimeError("Only Amadeus flight provider is supported.")

# ======================================================
# FLIGHT SEARCH (GET) — AMADEUS ONLY
# ======================================================
@router.get("/search/flights")
async def search_flights(
    request: Request,

    # REQUIRED header to trigger real API calls
    x_search_intent: Optional[str] = Header(None, alias="x-search-intent"),

    # Trip details
    trip_type: str = Query("roundtrip"),
    origin: Optional[str] = Query(None),
    destination: Optional[str] = Query(None),
    departure_date: Optional[str] = Query(None),
    return_date: Optional[str] = Query(None),

    # Passengers
    adults: int = Query(1, ge=1, le=9),
    infants: int = Query(0, ge=0, le=9),

    # Cabin
    cabin_class: str = Query("economy"),

    # Filters (CLIENT-SIDE ONLY — NEVER trigger API calls)
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
    AMADEUS-ONLY FLIGHT SEARCH (Cost Controlled)

    RULES:
    • Only Amadeus is used
    • Real API calls require header: x-search-intent=real
    • Daily cap enforced (via amadeus_protected)
    • Cache TTL ~15 minutes
    • Rate limit: 5 req/min/IP
    • Filters are CLIENT-SIDE ONLY
    """

    try:
        if not origin or not destination:
            return {
                "status": "completed",
                "outcome": "error",
                "message": "Origin and destination are required",
                "offers": [],
                "flights": []
            }

        search_request = FlightSearchRequest(
            trip_type=trip_type,
            origin=origin.upper(),
            destination=destination.upper(),
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

        client_ip = request.client.host if request.client else "unknown"

        headers = {
            "x-search-intent": x_search_intent or ""
        }

        logger.info(
            f"✈️ Amadeus search {search_request.origin} → {search_request.destination} "
            f"on {search_request.departure_date} | intent={x_search_intent}"
        )

        from app.services.amadeus_protected import search_flights_protected

        result = await search_flights_protected(
            request=search_request,
            headers=headers,
            client_ip=client_ip
        )

        result["request_id"] = str(uuid.uuid4())
        result["search_id"] = result["request_id"]
        result["timestamp"] = datetime.utcnow().isoformat()
        result["source"] = "amadeus"

        return result

    except Exception as e:
        logger.error(f"❌ Flight search error: {e}", exc_info=True)
        return {
            "request_id": str(uuid.uuid4()),
            "status": "completed",
            "outcome": "error",
            "message": "Live search temporarily unavailable. Please try again.",
            "flights": [],
            "offers": [],
            "source": "amadeus"
        }

# ======================================================
# FLIGHT SEARCH (POST) — DISABLED (SECURITY)
# ======================================================
@router.post("/search/flights", response_model=FlightSearchResponse)
async def search_flights_post(_: FlightSearchRequest):
    raise HTTPException(
        status_code=410,
        detail="POST flight search disabled. Use GET /search/flights"
    )

# ======================================================
# HOTEL SEARCH (GET) - Supports CITY, AREA, and HOTEL search types
# ======================================================
@router.get("/search/hotels", response_model=HotelSearchResponse)
async def search_hotels(
    city: str = Query(...),
    check_in: str = Query(...),
    check_out: str = Query(...),

    # Search type: CITY (default), AREA, or HOTEL
    search_type: Optional[str] = Query("CITY", description="Search type: CITY, AREA, or HOTEL"),
    
    # AREA search parameters
    area: Optional[str] = Query(None, description="Area/locality name for AREA search"),
    lat: Optional[float] = Query(None, description="Latitude for AREA geo-search"),
    lng: Optional[float] = Query(None, description="Longitude for AREA geo-search"),
    
    # HOTEL search parameters
    hotel_id: Optional[str] = Query(None, description="Hotel ID for direct HOTEL search"),
    hotel_name: Optional[str] = Query(None, description="Hotel name for HOTEL search"),

    min_rating: Optional[float] = Query(None, ge=0, le=5),
    max_rating: Optional[float] = Query(None, ge=0, le=5),
    min_review_score: Optional[float] = Query(None, ge=0, le=10),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),

    free_cancellation: bool = Query(False),
    pay_at_hotel: bool = Query(False),
    ac_required: bool = Query(False),
    max_distance_km: Optional[float] = Query(None),
):
    try:
        today = date.today()
        check_in_date = date.fromisoformat(check_in)
        check_out_date = date.fromisoformat(check_out)

        if check_in_date < today + timedelta(days=1):
            raise HTTPException(400, "Check-in must be at least tomorrow")

        if check_out_date <= check_in_date:
            raise HTTPException(400, "Check-out must be after check-in")

        # Log search type for debugging
        logger.info(f"[HOTEL_SEARCH] type={search_type} city={city} area={area} hotel_id={hotel_id}")
        
        # For AREA searches with geo coordinates, set max_distance_km to filter nearby hotels
        effective_max_distance = max_distance_km
        if search_type == "AREA" and lat is not None and lng is not None:
            # Default 5km radius for AREA searches
            effective_max_distance = max_distance_km or 5.0
            logger.info(f"[HOTEL_SEARCH] AREA search with geo: lat={lat}, lng={lng}, radius={effective_max_distance}km")

        request_obj = HotelSearchRequest(
            city=city,
            check_in=check_in,
            check_out=check_out,
            rooms=[{"adults": 2, "children": []}],
            min_rating=min_rating,
            max_rating=max_rating,
            min_review_score=min_review_score,
            min_price=min_price,
            max_price=max_price,
            free_cancellation=free_cancellation,
            pay_at_hotel=pay_at_hotel,
            ac_required=ac_required,
            max_distance_km=effective_max_distance,
            # Pass AREA/HOTEL specific params for backend filtering
            search_type=search_type,
            area=area,
            latitude=lat,
            longitude=lng,
            hotel_id=hotel_id,
            hotel_name=hotel_name,
        )

        offers = await aggregator.search_hotels(request_obj)

        return HotelSearchResponse(
            offers=offers,
            search_id=str(uuid.uuid4()),
            cached=False,
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Hotel search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ======================================================
# HOTEL SEARCH (POST)
# ======================================================
@router.post("/search/hotels", response_model=HotelSearchResponse)
async def search_hotels_post(request: HotelSearchRequest):
    try:
        offers = await aggregator.search_hotels(request)

        return HotelSearchResponse(
            offers=offers,
            search_id=str(uuid.uuid4()),
            cached=False,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Hotel search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

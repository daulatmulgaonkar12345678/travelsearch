"""MSRTC API Router

Provides endpoints for:
- MSRTC bus search (variant-level results)
- Stop/station listing
- Route information
- Database sync operations
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.db.mongodb import get_database as get_db
from app.scrapers.msrtc_service import (
    search_msrtc_buses,
    save_msrtc_stops_to_db,
    save_msrtc_routes_to_db,
    get_msrtc_stops_from_db,
    get_msrtc_routes_from_db,
    search_msrtc_stops,
)
from app.scrapers.msrtc_seed_data import (
    get_all_msrtc_stops,
    get_all_msrtc_routes,
    MSRTC_BUS_TYPES,
)
from app.models.transport import BusOffer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/msrtc", tags=["msrtc"])


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class MSRTCSearchRequest(BaseModel):
    """MSRTC Bus Search Request"""
    origin: str = Field(..., description="Origin city (Marathi/English/code)", min_length=2)
    destination: str = Field(..., description="Destination city (Marathi/English/code)", min_length=2)
    departure_date: str = Field(..., description="Departure date (YYYY-MM-DD)")


class MSRTCSearchResponse(BaseModel):
    """MSRTC Bus Search Response"""
    offers: List[BusOffer]
    search_id: str
    origin: str
    destination: str
    departure_date: str
    is_msrtc: bool = True
    message: Optional[str] = None


class MSRTCStop(BaseModel):
    """MSRTC Stop/Station"""
    value: str
    name_marathi: str
    name_english: str
    name_normalized: str
    stop_type: str
    district: Optional[str] = None
    station_name: Optional[str] = None
    station_name_english: Optional[str] = None


class MSRTCRoute(BaseModel):
    """MSRTC Route Info"""
    route_id: str
    origin_english: str
    origin_marathi: str
    destination_english: str
    destination_marathi: str
    distance_km: int
    base_fare: int
    avg_duration_minutes: int
    bus_types: List[str]
    frequency: str


class MSRTCBusType(BaseModel):
    """MSRTC Bus Type Info"""
    code: str
    name_marathi: str
    name_english: str
    is_ac: bool
    is_sleeper: bool
    fare_multiplier: float


class SyncResponse(BaseModel):
    """Database Sync Response"""
    success: bool
    stops_synced: int = 0
    routes_synced: int = 0
    message: str


# ============================================================
# SEARCH ENDPOINT
# ============================================================

@router.post("/search", response_model=MSRTCSearchResponse)
async def search_msrtc(
    request: MSRTCSearchRequest,
):
    """
    Search for MSRTC buses between two Maharashtra cities.
    
    Supports:
    - Marathi names (पुणे, मुंबई)
    - English names (Pune, Mumbai)
    - City codes (PUNE, MUMBAI)
    
    Returns variant-level results:
    - Each bus type (ST, Shivneri, Shivshahi) = separate card
    - Different prices and features per card
    """
    # Validate date
    try:
        dep_date = datetime.strptime(request.departure_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    # Check date range
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    max_date = today + timedelta(days=90)
    
    if dep_date < today:
        raise HTTPException(status_code=400, detail="Departure date cannot be in the past.")
    
    if dep_date > max_date:
        raise HTTPException(status_code=400, detail="Departure date cannot be more than 90 days in the future.")
    
    # Check same origin/destination
    if request.origin.lower().strip() == request.destination.lower().strip():
        raise HTTPException(status_code=400, detail="Origin and destination cannot be the same.")
    
    # Search MSRTC buses
    offers = search_msrtc_buses(
        origin=request.origin,
        destination=request.destination,
        departure_date=request.departure_date,
    )
    
    import uuid
    search_id = str(uuid.uuid4())
    
    if not offers:
        return MSRTCSearchResponse(
            offers=[],
            search_id=search_id,
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            message=f"No MSRTC routes found for {request.origin} → {request.destination}. This may be a non-MSRTC route or the cities are not yet in our Phase 1 coverage.",
        )
    
    return MSRTCSearchResponse(
        offers=offers,
        search_id=search_id,
        origin=request.origin,
        destination=request.destination,
        departure_date=request.departure_date,
        message=f"Found {len(offers)} MSRTC bus options",
    )


# ============================================================
# STOPS & ROUTES ENDPOINTS
# ============================================================

@router.get("/stops", response_model=List[MSRTCStop])
async def get_stops(
    query: Optional[str] = Query(None, description="Search query (Marathi/English)"),
    stop_type: Optional[str] = Query(None, description="Filter by type: major or minor"),
):
    """
    Get all MSRTC stops/stations.
    
    Optionally filter by:
    - query: Search in Marathi or English
    - stop_type: 'major' for district HQs, 'minor' for smaller stops
    """
    stops = get_all_msrtc_stops()
    
    # Filter by query if provided
    if query:
        query_lower = query.lower()
        stops = [
            s for s in stops
            if query_lower in s["name_english"].lower()
            or query_lower in s["name_normalized"]
            or query in s["name_marathi"]
        ]
    
    # Filter by stop type
    if stop_type:
        stops = [s for s in stops if s["stop_type"] == stop_type]
    
    return stops


@router.get("/routes", response_model=List[MSRTCRoute])
async def get_routes(
    phase: Optional[int] = Query(None, description="Route phase: 1 or 2"),
):
    """
    Get all MSRTC routes.
    
    Phase 1 routes: High-traffic corridors (Pune-Mumbai, Pune-Nashik, etc.)
    Phase 2 routes: District HQ connections
    """
    from app.scrapers.msrtc_seed_data import MSRTC_PHASE1_ROUTES, MSRTC_PHASE2_ROUTES
    
    if phase == 1:
        routes = MSRTC_PHASE1_ROUTES
    elif phase == 2:
        routes = MSRTC_PHASE2_ROUTES
    else:
        routes = get_all_msrtc_routes()
    
    return [
        MSRTCRoute(
            route_id=r.route_id,
            origin_english=r.origin_english,
            origin_marathi=r.origin_marathi,
            destination_english=r.destination_english,
            destination_marathi=r.destination_marathi,
            distance_km=r.distance_km,
            base_fare=r.base_fare,
            avg_duration_minutes=r.avg_duration_minutes,
            bus_types=r.bus_types,
            frequency=r.frequency,
        )
        for r in routes
    ]


@router.get("/bus-types", response_model=List[MSRTCBusType])
async def get_bus_types():
    """
    Get all MSRTC bus types with descriptions and fares.
    
    Types include:
    - ST (साधी): Ordinary non-AC
    - SEMI_LUX (निमलक्झरी): Semi-luxury
    - ASIAD (आशियाड): AC buses
    - SHIVNERI (शिवनेरी): Premium AC (Pune-Mumbai express)
    - SHIVSHAHI (शिवशाही): AC Sleeper
    - ASHWAMEDH (अश्वमेध): Multi-axle premium
    """
    return [
        MSRTCBusType(
            code=code,
            name_marathi=info["name_marathi"],
            name_english=info["name_english"],
            is_ac=info["is_ac"],
            is_sleeper=info["is_sleeper"],
            fare_multiplier=info["fare_multiplier"],
        )
        for code, info in MSRTC_BUS_TYPES.items()
    ]


# ============================================================
# DATABASE SYNC ENDPOINTS (Admin)
# ============================================================

@router.post("/sync", response_model=SyncResponse)
async def sync_msrtc_data():
    """
    Sync MSRTC seed data to MongoDB.
    
    This populates the database with:
    - All MSRTC stops (major + minor)
    - All MSRTC routes (Phase 1 + Phase 2)
    
    Safe to call multiple times - uses upsert.
    """
    try:
        db = await get_db()
        
        stops_count = await save_msrtc_stops_to_db(db)
        routes_count = await save_msrtc_routes_to_db(db)
        
        return SyncResponse(
            success=True,
            stops_synced=stops_count,
            routes_synced=routes_count,
            message=f"Successfully synced {stops_count} stops and {routes_count} routes to database.",
        )
    except Exception as e:
        logger.error(f"Failed to sync MSRTC data: {e}")
        return SyncResponse(
            success=False,
            message=f"Sync failed: {str(e)}",
        )


@router.get("/db/stops")
async def get_db_stops():
    """
    Get MSRTC stops from database (after sync).
    """
    try:
        db = await get_db()
        stops = await get_msrtc_stops_from_db(db)
        return {"count": len(stops), "stops": stops}
    except Exception as e:
        logger.error(f"Failed to get stops from DB: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db/routes")
async def get_db_routes():
    """
    Get MSRTC routes from database (after sync).
    """
    try:
        db = await get_db()
        routes = await get_msrtc_routes_from_db(db)
        return {"count": len(routes), "routes": routes}
    except Exception as e:
        logger.error(f"Failed to get routes from DB: {e}")
        raise HTTPException(status_code=500, detail=str(e))

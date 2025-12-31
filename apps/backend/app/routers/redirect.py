"""
Affiliate Redirect API - Industry-Proven Click Tracking (Redirect-First Model)

ARCHITECTURE: Redirect-First, Non-Blocking Click Tracking
Mirrors Skyscanner, Kayak, Trivago, and Booking Affiliate systems.

CORE PRINCIPLES:
1. Redirect immediately (< 50ms response time)
2. Log clicks asynchronously (BackgroundTasks)
3. Never block the redirect
4. Best-effort persistence only

EXECUTION FLOW:
1. User clicks a booking link
2. Backend returns HTTP 302 redirect immediately
3. Click event is sent to a background task
4. Database persistence failures are logged but ignored
5. User experience is never impacted

EXPLICIT NON-GOALS:
- No queues (Redis, RabbitMQ, Kafka)
- No blocking retries
- No transaction coupling
- No redirect delays
- No dependency on logging success

Endpoint: GET /api/redirect
"""

from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse
from typing import Optional
from datetime import datetime, timezone
from urllib.parse import unquote
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory buffer for click events (will also persist to DB)
click_buffer = []


class ClickEvent:
    """Structured click event for logging"""
    def __init__(
        self,
        service: str,
        vendor: str,
        target: str,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        city: Optional[str] = None,
        hotel_name: Optional[str] = None,
        price: Optional[float] = None,
        session_id: Optional[str] = None,
        # Search intent (for analytics)
        search_type: Optional[str] = None,  # CITY, AREA, HOTEL
        area: Optional[str] = None,
    ):
        self.event = "affiliate_click"
        self.service = service
        self.vendor = vendor
        self.target = target
        self.origin = origin
        self.destination = destination
        self.city = city
        self.hotel_name = hotel_name
        self.price = price
        self.session_id = session_id
        self.search_type = search_type
        self.area = area
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values"""
        data = {
            "event": self.event,
            "service": self.service,
            "vendor": self.vendor,
            "timestamp": self.timestamp,
        }
        if self.origin:
            data["origin"] = self.origin
        if self.destination:
            data["destination"] = self.destination
        if self.city:
            data["city"] = self.city
        if self.hotel_name:
            data["hotel_name"] = self.hotel_name
        if self.price is not None:
            data["price"] = self.price
        if self.session_id:
            data["session_id"] = self.session_id
        # Include search intent for analytics
        if self.search_type:
            data["search_type"] = self.search_type
        if self.area:
            data["area"] = self.area
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string for logging"""
        return json.dumps(self.to_dict())


async def log_click_event(event: ClickEvent, db=None):
    """
    Non-blocking click event logging (best-effort).
    
    INDUSTRY STANDARD (Skyscanner/Kayak/Trivago pattern):
    - Log to console for immediate visibility
    - Buffer in memory for quick access
    - Persist to DB asynchronously
    - NEVER propagate errors to caller
    
    This function runs in a background task and must:
    1. Complete quickly (< 100ms)
    2. Never throw exceptions to caller
    3. Gracefully handle all failure scenarios
    """
    try:
        # 1. Structured JSON logging (immediate, always succeeds)
        logger.info(f"CLICK_EVENT: {event.to_json()}")
        
        # 2. Add to in-memory buffer (for /redirect/health and quick access)
        click_buffer.append(event.to_dict())
        
        # Keep buffer size manageable (last 1000 events)
        while len(click_buffer) > 1000:
            click_buffer.pop(0)
        
        # 3. Persist to database (best-effort, non-blocking)
        await persist_click_to_db(event)
            
    except Exception as e:
        # CRITICAL: Never let logging failures affect anything
        # This is expected behavior - log and move on
        logger.warning(f"Click logging error (non-blocking, ignored): {e}")


async def persist_click_to_db(event: ClickEvent):
    """
    Persist click event to MongoDB (non-blocking, best-effort).
    
    INDUSTRY STANDARD: This is a background task that should:
    - Never block the redirect
    - Silently fail if DB is unavailable
    - Log errors for monitoring but not propagate
    """
    try:
        from app.db.mongodb import get_database
        
        # CRITICAL: Await the async database getter
        db = await get_database()
        
        # Include search intent fields for analytics
        click_doc = {
            "service": event.service,
            "vendor": event.vendor,
            "origin": event.origin,
            "destination": event.destination,
            "city": event.city,
            "hotel_name": event.hotel_name,
            "price": event.price,
            "session_id": event.session_id,
            "target_url": event.target,
            # Search intent for analytics
            "search_type": event.search_type,
            "area": event.area,
            "created_at": datetime.now(timezone.utc),
        }
        
        # Remove None values to keep documents clean
        click_doc = {k: v for k, v in click_doc.items() if v is not None}
        
        await db.click_events.insert_one(click_doc)
        logger.debug(f"Click event persisted to DB: {event.service}/{event.vendor}")
        
    except Exception as e:
        # Best-effort logging: Never propagate errors to main request
        # This is expected behavior when DB is temporarily unavailable
        logger.warning(f"Click persistence failed (non-blocking): {e}")


@router.get("/redirect")
async def redirect_to_vendor(
    background_tasks: BackgroundTasks,
    # Required
    target: str = Query(..., description="URL-encoded vendor booking URL"),
    service: str = Query(..., description="Service type: flight|hotel|bus|train"),
    vendor: str = Query(..., description="Vendor name: makemytrip|booking|agoda|irctc|redbus|etc"),
    # Optional - Flight/Bus/Train
    origin: Optional[str] = Query(None, description="Origin code/city"),
    destination: Optional[str] = Query(None, description="Destination code/city"),
    # Optional - Hotel
    city: Optional[str] = Query(None, description="Hotel city"),
    hotel_name: Optional[str] = Query(None, description="Hotel name"),
    # Optional - Search Intent (for analytics)
    search_type: Optional[str] = Query(None, description="Search type: CITY|AREA|HOTEL"),
    area: Optional[str] = Query(None, description="Area name for AREA searches"),
    # Optional - Common
    date: Optional[str] = Query(None, description="Travel date"),
    check_in: Optional[str] = Query(None, description="Hotel check-in date"),
    check_out: Optional[str] = Query(None, description="Hotel check-out date"),
    price: Optional[float] = Query(None, description="Price shown to user"),
    session_id: Optional[str] = Query(None, description="Anonymous session ID"),
):
    """
    REDIRECT-FIRST Affiliate Click Handler (Industry Standard Pattern)
    
    Mirrors how Skyscanner, Kayak, Trivago, and Booking Affiliate systems operate.
    
    FLOW (Target: < 50ms response time):
    1. Validate target URL (sync, ~1ms)
    2. Create click event object (sync, ~1ms)
    3. Schedule background logging task (non-blocking, ~0ms)
    4. Return HTTP 302 redirect IMMEDIATELY
    
    GUARANTEES:
    - User redirect is NEVER blocked by logging
    - Redirect works even if database is unavailable
    - Click logging is best-effort (analytics, not revenue)
    - No retries, no queues, no blocking waits
    
    Response: HTTP 302 Redirect (immediate)
    """
    # Decode the target URL
    decoded_target = unquote(target)
    
    # Basic URL validation
    if not decoded_target.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="Invalid target URL")
    
    # Validate service type
    valid_services = ['flight', 'hotel', 'bus', 'train', 'flights', 'hotels', 'buses', 'trains']
    if service.lower() not in valid_services:
        raise HTTPException(status_code=400, detail=f"Invalid service: {service}")
    
    # Normalize service name (flights -> flight, buses -> bus, etc.)
    service_normalized = service.lower()
    if service_normalized.endswith('s') and service_normalized not in ['bus']:
        if service_normalized == 'buses':
            service_normalized = 'bus'  # Special case: buses -> bus
        else:
            service_normalized = service_normalized[:-1]  # Remove trailing 's' for other plural forms
    
    # Create click event
    click_event = ClickEvent(
        service=service_normalized,
        vendor=vendor.lower(),
        target=decoded_target,
        origin=origin,
        destination=destination,
        city=city,
        hotel_name=hotel_name,
        price=price,
        session_id=session_id,
        # Search intent for analytics
        search_type=search_type,
        area=area,
    )
    
    # Log click event in background (non-blocking)
    background_tasks.add_task(log_click_event, click_event)
    
    # Immediate HTTP 302 redirect
    return RedirectResponse(url=decoded_target, status_code=302)


@router.get("/redirect/health")
async def redirect_health():
    """Health check for redirect endpoint"""
    return {
        "status": "healthy",
        "buffer_size": len(click_buffer),
        "last_click": click_buffer[-1] if click_buffer else None,
    }

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime
from app.models.click import ClickLog
from app.db.mongodb import get_clicks_collection
from app.middleware.bot_detection import BotDetectionService
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class RedirectRequest(BaseModel):
    provider: str
    offer_id: str
    route: str
    price: float
    deep_link: str
    device_fingerprint: Optional[str] = None

@router.post("/redirect")
async def create_redirect(redirect_req: RedirectRequest, request: Request):
    """Create click log and return redirect info"""
    try:
        # Generate unique click ID
        click_id = str(uuid.uuid4())
        
        # Get request metadata
        user_agent = request.headers.get("user-agent", "")
        client_ip = request.client.host
        accept_headers = request.headers.get("accept", "")
        
        # Generate device fingerprint
        device_fingerprint = redirect_req.device_fingerprint or BotDetectionService.generate_fingerprint(
            user_agent, accept_headers, client_ip
        )
        
        # Calculate fraud score
        fraud_score = BotDetectionService.calculate_fraud_score(
            user_agent, client_ip, {}
        )
        
        # Create click log
        click_log = ClickLog(
            click_id=click_id,
            route=redirect_req.route,
            provider=redirect_req.provider,
            offer_id=redirect_req.offer_id,
            price=redirect_req.price,
            device_fingerprint_hash=ClickLog.hash_fingerprint(device_fingerprint),
            ip_masked=ClickLog.mask_ip(client_ip),
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
            fraud_flag=fraud_score > 50,
            fraud_reason="High fraud score" if fraud_score > 50 else None,
            conversion_status="pending"
        )
        
        # Save to database
        clicks_collection = get_clicks_collection()
        await clicks_collection.insert_one(click_log.dict())
        
        logger.info(f"Click logged: {click_id} - {redirect_req.provider} - {redirect_req.route}")
        
        # Return click info (frontend will handle actual redirect after interstitial)
        return {
            "click_id": click_id,
            "redirect_url": redirect_req.deep_link,
            "fraud_score": fraud_score,
            "requires_captcha": BotDetectionService.should_challenge(fraud_score)
        }
    
    except Exception as e:
        logger.error(f"Redirect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/go/{click_id}")
async def redirect_to_provider(click_id: str):
    """Direct redirect using click_id (alternative method)"""
    try:
        # Lookup click in database
        clicks_collection = get_clicks_collection()
        click = await clicks_collection.find_one({"click_id": click_id})
        
        if not click:
            raise HTTPException(status_code=404, detail="Click ID not found")
        
        # Extract deep link from original click log
        # In production, store deep_link in click log
        deep_link = f"https://mock-provider.com/book?click_id={click_id}"
        
        # Redirect
        return RedirectResponse(url=deep_link, status_code=302)
    
    except Exception as e:
        logger.error(f"Redirect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/conversion")
async def conversion_webhook(click_id: str, status: str, booking_id: Optional[str] = None):
    """Webhook endpoint for provider to confirm booking"""
    try:
        clicks_collection = get_clicks_collection()
        
        # Update click status
        result = await clicks_collection.update_one(
            {"click_id": click_id},
            {
                "$set": {
                    "conversion_status": status,
                    "booking_id": booking_id,
                    "conversion_time": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Click ID not found")
        
        logger.info(f"Conversion updated: {click_id} - {status}")
        
        return {"status": "success", "click_id": click_id}
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/redirect/aviasales")
async def redirect_to_aviasales(
    request: Request,
    origin: str = Query(..., description="Origin airport IATA code"),
    destination: str = Query(..., description="Destination airport IATA code"),
    depart_date: str = Query(..., description="Departure date YYYY-MM-DD", alias="depart"),
    return_date: Optional[str] = Query(None, description="Return date YYYY-MM-DD", alias="return"),
    adults: int = Query(1, description="Number of adults")
):
    """
    Redirect to Travelpayouts/Aviasales affiliate link.
    
    This endpoint:
    1. Builds the affiliate URL with proper marker
    2. Logs the click for tracking
    3. Redirects user to partner site (302)
    
    TODO: Expand deep-link building with proper Travelpayouts documentation
    """
    try:
        # Generate click ID for tracking
        click_id = str(uuid.uuid4())
        
        # Get base URL and marker from config
        base_url = settings.travelpayouts_aviasales_base_url
        marker = settings.travelpayouts_marker
        
        # Check if configured
        if base_url == "REPLACE_ME" or marker == "REPLACE_ME":
            logger.warning("Aviasales affiliate not configured")
            raise HTTPException(
                status_code=503, 
                detail="Affiliate redirect not configured"
            )
        
        # Build affiliate URL
        # Travelpayouts URL structure (basic):
        # https://aviasales.tpx.lt/{marker}?origin={origin}&destination={dest}&depart_date={date}
        affiliate_url = f"{base_url}?origin_iata={origin}&destination_iata={destination}"
        affiliate_url += f"&depart_date={depart_date}"
        
        if return_date:
            affiliate_url += f"&return_date={return_date}"
        
        if adults > 1:
            affiliate_url += f"&adults={adults}"
        
        # Add marker for commission tracking
        affiliate_url += f"&marker={marker}"
        
        # Log the click
        user_agent = request.headers.get("user-agent", "")
        client_ip = request.client.host
        
        click_log = ClickLog(
            click_id=click_id,
            route=f"{origin}-{destination}",
            provider="aviasales",
            offer_id=f"{origin}-{destination}-{depart_date}",
            price=0.0,  # Price not known at redirect time
            device_fingerprint_hash=ClickLog.hash_fingerprint(user_agent + client_ip),
            ip_masked=ClickLog.mask_ip(client_ip),
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
            fraud_flag=False,
            fraud_reason=None,
            conversion_status="pending"
        )
        
        # Save to database (async)
        try:
            clicks_collection = get_clicks_collection()
            await clicks_collection.insert_one(click_log.dict())
            logger.info(f"Aviasales click logged: {click_id} - {origin} to {destination}")
        except Exception as db_error:
            # Log but don't fail the redirect
            logger.error(f"Failed to log click: {db_error}")
        
        # Redirect to partner
        logger.info(f"Redirecting to Aviasales: {affiliate_url}")
        return RedirectResponse(url=affiliate_url, status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Aviasales redirect error: {str(e)}")
        raise HTTPException(status_code=500, detail="Redirect failed")


"""
Track Price Router
==================
Endpoints for managing price tracking and alerts.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timezone

from app.services.track_price import track_price_service
from app.db.mongodb import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


class ManualCheckRequest(BaseModel):
    """Request to manually check a specific saved search."""
    search_id: str
    email: EmailStr


@router.post("/track-price/check-all")
async def trigger_price_check(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Trigger a background job to check all saved searches for price drops.
    
    This endpoint should be called:
    - By a scheduled cron job (daily)
    - Or manually by admin for testing
    
    Returns immediately while job runs in background.
    """
    background_tasks.add_task(track_price_service.check_all_saved_searches)
    
    return {
        "status": "started",
        "message": "Price check job started in background",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post("/track-price/check-single")
async def check_single_search(request: ManualCheckRequest) -> Dict[str, Any]:
    """
    Manually check a single saved search for price changes.
    Useful for testing or user-triggered refresh.
    """
    try:
        db = get_db()
        
        # Get the saved search
        search = await db.saved_searches.find_one(
            {"id": request.search_id, "email": request.email.lower()},
            {"_id": 0}
        )
        
        if not search:
            raise HTTPException(status_code=404, detail="Saved search not found")
        
        search_params = search.get("search", {})
        
        # Fetch current price
        price_data = await track_price_service.fetch_current_price(
            origin=search_params.get("origin"),
            destination=search_params.get("destination"),
            departure_date=search_params.get("departure_date"),
            adults=search_params.get("adults", 1),
            cabin_class=search_params.get("cabin_class", "economy")
        )
        
        if not price_data:
            return {
                "status": "no_data",
                "message": "Could not fetch current prices for this route",
                "search_id": request.search_id
            }
        
        current_price = price_data["price"]
        current_currency = price_data["currency"]
        last_price = search.get("last_checked_price") or search.get("last_known_price")
        
        # Check for price drop
        price_changed = False
        price_drop = 0
        drop_percent = 0
        
        if last_price:
            should_alert, price_drop, drop_percent = track_price_service.should_send_alert(
                last_price, current_price, current_currency
            )
            price_changed = current_price != last_price
        
        # Update saved search
        await track_price_service.update_saved_search(
            request.search_id, current_price, current_currency
        )
        
        return {
            "status": "checked",
            "search_id": request.search_id,
            "route": f"{search_params.get('origin')} → {search_params.get('destination')}",
            "previous_price": last_price,
            "current_price": current_price,
            "currency": current_currency,
            "price_changed": price_changed,
            "price_drop": price_drop if price_drop > 0 else None,
            "drop_percent": f"{drop_percent:.1f}%" if drop_percent > 0 else None,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TrackPrice] Error checking single search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/track-price/status")
async def get_tracking_status() -> Dict[str, Any]:
    """
    Get overall tracking status and statistics.
    """
    try:
        db = get_db()
        
        # Count active saved searches
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        total_active = await db.saved_searches.count_documents({
            "is_active": True,
            "search.departure_date": {"$gte": today}
        })
        
        total_all = await db.saved_searches.count_documents({"is_active": True})
        
        # Get recent alerts sent
        recent_alerts = await db.saved_searches.find(
            {"last_notified_at": {"$ne": None}},
            {"_id": 0, "email": 1, "search": 1, "last_notified_at": 1, "notification_count": 1}
        ).sort("last_notified_at", -1).limit(5).to_list(5)
        
        return {
            "status": "ok",
            "active_searches_future": total_active,
            "active_searches_total": total_all,
            "price_drop_threshold_percent": 5.0,
            "min_price_drop_amount": 500,
            "recent_alerts": [
                {
                    "route": f"{a['search']['origin']} → {a['search']['destination']}",
                    "notified_at": a.get("last_notified_at"),
                    "total_notifications": a.get("notification_count", 0)
                }
                for a in recent_alerts
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"[TrackPrice] Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

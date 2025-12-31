
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime, timezone
from app.db.mongodb import get_db

router = APIRouter()

class ReconcilePayload(BaseModel):
    click_id: str
    booking_ref: str
    provider: str = None
    payout: float = 0.0
    booked_at: str = None

@router.post('/webhooks/reconcile')
async def reconcile(payload: ReconcilePayload, request: Request):
    """Receive affiliate booking confirmation webhook"""
    db = get_db()
    record = {
        "click_id": payload.click_id,
        "booking_ref": payload.booking_ref,
        "provider": payload.provider,
        "payout": payload.payout,
        "booked_at": payload.booked_at or datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.reconciliations.insert_one(record)
    # Return a clean dict without MongoDB's _id
    return {
        "detail": "received",
        "click_id": record["click_id"],
        "booking_ref": record["booking_ref"],
        "status": record["status"]
    }

@router.get('/admin/reconciliations')
async def get_reconciliations():
    """List pending reconciliations for admin review"""
    db = get_db()
    cursor = db.reconciliations.find({"status":"pending"}, {"_id": 0}).sort("created_at",-1).limit(100)
    rows = await cursor.to_list(100)
    return rows


@router.get('/admin/click-logs')
async def get_click_logs_simple(
    limit: int = 100,
    service: str = None,
    vendor: str = None,
):
    """
    Get booking click logs for admin reconciliation dashboard.
    Simple version without JWT auth (matching reconciliations endpoint pattern).
    
    Returns latest click events sorted by newest first.
    """
    from app.routers.redirect import click_buffer
    
    db = get_db()
    
    try:
        # Build query
        query = {}
        
        if service:
            query["service"] = service.lower().rstrip('s')  # Normalize: flights -> flight
        
        if vendor:
            query["vendor"] = vendor.lower()
        
        # Fetch from database
        logs = await db.click_events.find(
            query,
            {"_id": 0}  # Exclude MongoDB _id
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        total = await db.click_events.count_documents(query)
        
        # If no DB logs, fall back to in-memory buffer
        if not logs and click_buffer:
            logs = sorted(click_buffer, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]
            total = len(click_buffer)
        
        return {
            "count": len(logs),
            "total": total,
            "logs": logs
        }
        
    except Exception as e:
        # Fallback to in-memory buffer
        filtered = click_buffer
        if service:
            filtered = [c for c in filtered if c.get('service') == service.lower().rstrip('s')]
        if vendor:
            filtered = [c for c in filtered if c.get('vendor') == vendor.lower()]
        
        sorted_logs = sorted(filtered, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]
        
        return {
            "count": len(sorted_logs),
            "total": len(filtered),
            "logs": sorted_logs,
            "source": "memory_buffer"
        }

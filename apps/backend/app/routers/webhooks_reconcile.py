
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
    return {"detail": "received", "record": record}

@router.get('/admin/reconciliations')
async def get_reconciliations():
    """List pending reconciliations for admin review"""
    db = get_db()
    cursor = db.reconciliations.find({"status":"pending"}, {"_id": 0}).sort("created_at",-1).limit(100)
    rows = await cursor.to_list(100)
    return rows

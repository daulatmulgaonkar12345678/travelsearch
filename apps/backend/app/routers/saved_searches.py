"""
Saved Searches Router
=====================
Handles explicit user-saved searches for price alerts.

This is SEPARATE from Recent Searches (frontend localStorage).
Saved searches are stored in the database and used for:
- Price tracking
- Email notifications when prices change
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timezone
import logging
import uuid

from app.db.mongodb import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


class SearchParams(BaseModel):
    """Flight search parameters"""
    origin: str = Field(..., min_length=3, max_length=3)
    destination: str = Field(..., min_length=3, max_length=3)
    departure_date: str
    return_date: Optional[str] = None
    adults: int = Field(default=1, ge=1, le=9)
    cabin_class: str = Field(default="economy")
    trip_type: str = Field(default="oneway")


class SavedSearchCreate(BaseModel):
    """Request body for saving a search"""
    email: EmailStr
    search: SearchParams
    last_known_price: Optional[float] = None
    last_known_currency: str = Field(default="INR")


class SavedSearchResponse(BaseModel):
    """Response after saving a search"""
    id: str
    message: str
    created_at: str


@router.post("/saved-searches", response_model=SavedSearchResponse)
async def save_search(request: Request, body: SavedSearchCreate):
    """
    Save a flight search for price alerts.
    
    This endpoint:
    1. Stores the search in MongoDB
    2. Associates it with an email for notifications
    3. Records the last known price for comparison
    
    Returns a confirmation with the saved search ID.
    """
    try:
        db = get_db()
        
        # Create unique ID for the saved search
        search_id = str(uuid.uuid4())
        
        # Build the document
        saved_search = {
            "id": search_id,
            "email": body.email.lower(),
            "search": {
                "origin": body.search.origin.upper(),
                "destination": body.search.destination.upper(),
                "departure_date": body.search.departure_date,
                "return_date": body.search.return_date,
                "adults": body.search.adults,
                "cabin_class": body.search.cabin_class,
                "trip_type": body.search.trip_type,
            },
            "last_known_price": body.last_known_price,
            "last_known_currency": body.last_known_currency,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True,
            "notification_count": 0,
            "last_notified_at": None,
        }
        
        # Check for duplicate (same email + same route + same date)
        existing = await db.saved_searches.find_one({
            "email": body.email.lower(),
            "search.origin": body.search.origin.upper(),
            "search.destination": body.search.destination.upper(),
            "search.departure_date": body.search.departure_date,
            "is_active": True
        }, {"_id": 0})
        
        if existing:
            # Update existing instead of creating duplicate
            await db.saved_searches.update_one(
                {"id": existing["id"]},
                {
                    "$set": {
                        "last_known_price": body.last_known_price,
                        "last_known_currency": body.last_known_currency,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                }
            )
            
            logger.info(f"Updated existing saved search {existing['id']} for {body.email}")
            
            return SavedSearchResponse(
                id=existing["id"],
                message="Search updated. We'll notify you if prices change.",
                created_at=existing["created_at"]
            )
        
        # Insert new saved search
        await db.saved_searches.insert_one(saved_search)
        
        logger.info(f"Created saved search {search_id} for {body.email}")
        
        return SavedSearchResponse(
            id=search_id,
            message="Search saved. We'll notify you if prices change.",
            created_at=saved_search["created_at"]
        )
        
    except Exception as e:
        logger.error(f"Failed to save search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save search")


@router.get("/saved-searches")
async def get_saved_searches(email: str):
    """
    Get all saved searches for an email.
    """
    try:
        db = await get_db()
        
        searches = await db.saved_searches.find(
            {"email": email.lower(), "is_active": True},
            {"_id": 0}
        ).to_list(100)
        
        return {
            "searches": searches,
            "count": len(searches)
        }
        
    except Exception as e:
        logger.error(f"Failed to get saved searches: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get saved searches")


@router.delete("/saved-searches/{search_id}")
async def delete_saved_search(search_id: str, email: str):
    """
    Deactivate a saved search (soft delete).
    """
    try:
        db = await get_db()
        
        result = await db.saved_searches.update_one(
            {"id": search_id, "email": email.lower()},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Saved search not found")
        
        logger.info(f"Deactivated saved search {search_id}")
        
        return {"message": "Search removed", "id": search_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete saved search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete saved search")

"""
Global Quota Store (MongoDB-Backed)

Provides distributed per-minute quota tracking using MongoDB.
Ensures all instances respect the same global rate limit.

Collection: supplier_quota
Document structure:
{
  "_id": "amadeus:1702896234",  # supplier:bucket_timestamp
  "supplier": "amadeus",
  "bucket_start_ts": 1702896234,  # Unix timestamp / 60
  "allowed": 100,
  "used": 25,
  "created_at": ISODate(...)
}
"""

import time
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

def current_minute_bucket() -> int:
    """Get current minute bucket (Unix timestamp / 60)."""
    return int(time.time() // 60)

class GlobalQuotaStore:
    """
    MongoDB-backed global quota tracker.
    
    Uses atomic updates to ensure distributed correctness.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["supplier_quota"]
        logger.info("GlobalQuotaStore initialized with MongoDB")
    
    async def ensure_indexes(self):
        """Create indexes for efficient queries."""
        try:
            await self.collection.create_index(
                [("supplier", 1), ("bucket_start_ts", 1)],
                unique=True,
                background=True
            )
            await self.collection.create_index(
                "bucket_start_ts",
                expireAfterSeconds=3600,  # Auto-delete old buckets after 1 hour
                background=True
            )
            logger.info("Global quota indexes created")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    async def try_increment(self, supplier: str, allowed_per_minute: int) -> bool:
        """
        Try to increment usage atomically.
        
        Args:
            supplier: Supplier identifier
            allowed_per_minute: Max requests allowed per minute
            
        Returns:
            True if increment succeeded (quota available), False if exhausted
        """
        bucket = current_minute_bucket()
        doc_id = f"{supplier}:{bucket}"
        
        try:
            # Upsert with $inc - atomic increment
            result = await self.collection.update_one(
                {
                    "_id": doc_id,
                    "used": {"$lt": allowed_per_minute}  # Only update if under quota
                },
                {
                    "$inc": {"used": 1},
                    "$setOnInsert": {
                        "supplier": supplier,
                        "bucket_start_ts": bucket,
                        "allowed": allowed_per_minute,
                        "created_at": time.time()
                    }
                },
                upsert=True
            )
            
            # If matched and modified, quota was available
            if result.matched_count > 0 or result.upserted_id:
                return True
            
            # No match means quota exhausted
            return False
            
        except Exception as e:
            logger.exception(f"MongoDB error in try_increment: {e}")
            # Fail open - allow request if DB is down
            return True
    
    async def get_status(self, supplier: str) -> Optional[dict]:
        """
        Get current quota status for a supplier.
        
        Returns:
            Dictionary with allowed, used, remaining, or None if not found
        """
        bucket = current_minute_bucket()
        doc_id = f"{supplier}:{bucket}"
        
        try:
            doc = await self.collection.find_one({"_id": doc_id})
            
            if doc:
                return {
                    "supplier": supplier,
                    "bucket_start_ts": bucket,
                    "allowed": doc.get("allowed", 0),
                    "used": doc.get("used", 0),
                    "remaining": doc.get("allowed", 0) - doc.get("used", 0)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting quota status: {e}")
            return None
    
    async def reset_quota(self, supplier: str):
        """Reset quota for current minute (testing/admin use)."""
        bucket = current_minute_bucket()
        doc_id = f"{supplier}:{bucket}"
        
        try:
            await self.collection.update_one(
                {"_id": doc_id},
                {"$set": {"used": 0}}
            )
            logger.info(f"Reset quota for {supplier} in bucket {bucket}")
        except Exception as e:
            logger.error(f"Error resetting quota: {e}")

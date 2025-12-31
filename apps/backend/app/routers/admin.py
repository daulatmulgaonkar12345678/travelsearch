from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
from app.routers.auth import get_current_user
from app.models.user import User
from app.db.mongodb import get_admin_audit_collection, get_clicks_collection, get_users_collection
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class AuditLog(BaseModel):
    id: str
    user_id: str
    user_email: str
    action: str
    resource: str
    details: dict
    ip_address: str
    timestamp: datetime

def require_admin_role(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin role"""
    admin_roles = ["superadmin", "ops", "seo", "content"]
    if current_user.role not in admin_roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def require_superadmin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require superadmin role"""
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return current_user

async def log_admin_action(user: User, action: str, resource: str, details: dict, ip: str):
    """Log admin action to audit collection"""
    audit_log = AuditLog(
        id=str(uuid.uuid4()),
        user_id=user.id,
        user_email=user.email,
        action=action,
        resource=resource,
        details=details,
        ip_address=ip,
        timestamp=datetime.utcnow()
    )
    
    audit_collection = get_admin_audit_collection()
    await audit_collection.insert_one(audit_log.dict())
    logger.info(f"Admin action logged: {action} on {resource} by {user.email}")

@router.get("/admin/dashboard")
async def get_dashboard(admin: User = Depends(require_admin_role)):
    """Get admin dashboard stats"""
    clicks_collection = get_clicks_collection()
    users_collection = get_users_collection()
    
    # Get stats
    total_clicks = await clicks_collection.count_documents({})
    fraud_clicks = await clicks_collection.count_documents({"fraud_flag": True})
    total_users = await users_collection.count_documents({})
    
    # Recent clicks
    recent_clicks = await clicks_collection.find({}).sort("timestamp", -1).limit(10).to_list(10)
    
    return {
        "stats": {
            "total_clicks": total_clicks,
            "fraud_clicks": fraud_clicks,
            "total_users": total_users,
            "fraud_rate": round(fraud_clicks / total_clicks * 100, 2) if total_clicks > 0 else 0
        },
        "recent_clicks": recent_clicks
    }

@router.get("/admin/clicks")
async def get_clicks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    fraud_only: bool = Query(False),
    admin: User = Depends(require_admin_role)
):
    """Get click logs with pagination"""
    clicks_collection = get_clicks_collection()
    
    query = {"fraud_flag": True} if fraud_only else {}
    
    clicks = await clicks_collection.find(query).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    total = await clicks_collection.count_documents(query)
    
    return {
        "clicks": clicks,
        "total": total,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit
    }

@router.get("/admin/users")
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    admin: User = Depends(require_superadmin)
):
    """Get all users (superadmin only)"""
    users_collection = get_users_collection()
    
    users = await users_collection.find({}, {"password_hash": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await users_collection.count_documents({})
    
    return {
        "users": users,
        "total": total,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit
    }

@router.patch("/admin/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    admin: User = Depends(require_superadmin)
):
    """Update user role (superadmin only)"""
    valid_roles = ["user", "ops", "seo", "content", "superadmin"]
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    users_collection = get_users_collection()
    result = await users_collection.update_one(
        {"id": user_id},
        {"$set": {"role": role}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log action
    await log_admin_action(
        admin,
        "UPDATE_ROLE",
        f"user:{user_id}",
        {"new_role": role},
        "0.0.0.0"
    )
    
    return {"status": "success", "user_id": user_id, "role": role}

@router.get("/admin/audit-logs")
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    admin: User = Depends(require_admin_role)
):
    """Get audit logs"""
    audit_collection = get_admin_audit_collection()
    
    logs = await audit_collection.find({}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    total = await audit_collection.count_documents({})
    
    return {
        "logs": logs,
        "total": total,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit
    }


# ============================================
# Booking Click Logs API
# ============================================

@router.get("/admin/click-logs")
async def get_click_logs(
    limit: int = Query(100, ge=1, le=500, description="Number of logs to return"),
    service: Optional[str] = Query(None, description="Filter by service: flight|hotel|bus|train"),
    vendor: Optional[str] = Query(None, description="Filter by vendor name"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    admin: User = Depends(require_admin_role)
):
    """
    Get booking click logs for reconciliation.
    
    Returns latest click events with optional filtering.
    Sorted by newest first.
    """
    from app.db.mongodb import get_database
    from app.routers.redirect import click_buffer
    
    try:
        db = get_database()
        
        # Build query
        query = {}
        
        if service:
            query["service"] = service.lower().rstrip('s')  # Normalize: flights -> flight
        
        if vendor:
            query["vendor"] = vendor.lower()
        
        if date_from or date_to:
            query["created_at"] = {}
            if date_from:
                query["created_at"]["$gte"] = datetime.fromisoformat(date_from)
            if date_to:
                # Include the entire end date
                query["created_at"]["$lte"] = datetime.fromisoformat(date_to + "T23:59:59")
        
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
        logger.error(f"Error fetching click logs: {e}")
        
        # Fallback to in-memory buffer
        from app.routers.redirect import click_buffer
        
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


@router.get("/admin/click-stats")
async def get_click_stats(
    days: int = Query(7, ge=1, le=30, description="Number of days for stats"),
    admin: User = Depends(require_admin_role)
):
    """
    Get aggregated click statistics.
    
    Returns counts by service and vendor for the specified period.
    """
    from app.db.mongodb import get_database
    from datetime import timedelta
    
    try:
        db = get_database()
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Aggregate by service
        service_pipeline = [
            {"$match": {"created_at": {"$gte": start_date}}},
            {"$group": {"_id": "$service", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        service_stats = await db.click_events.aggregate(service_pipeline).to_list(10)
        
        # Aggregate by vendor
        vendor_pipeline = [
            {"$match": {"created_at": {"$gte": start_date}}},
            {"$group": {"_id": "$vendor", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        vendor_stats = await db.click_events.aggregate(vendor_pipeline).to_list(20)
        
        # Total clicks
        total = await db.click_events.count_documents({"created_at": {"$gte": start_date}})
        
        return {
            "period_days": days,
            "total_clicks": total,
            "by_service": {s["_id"]: s["count"] for s in service_stats if s["_id"]},
            "by_vendor": {v["_id"]: v["count"] for v in vendor_stats if v["_id"]}
        }
        
    except Exception as e:
        logger.error(f"Error fetching click stats: {e}")
        return {
            "period_days": days,
            "total_clicks": 0,
            "by_service": {},
            "by_vendor": {},
            "error": "Stats temporarily unavailable"
        }


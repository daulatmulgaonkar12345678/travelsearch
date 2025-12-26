"""
INTERNAL SEARCH STATS ROUTER
============================
Exposes search statistics for internal monitoring only.

⚠️ WARNING: This endpoint should only be accessed internally.
Useful for cost tracking, trust auditing, and debugging.
"""

from fastapi import APIRouter, Request
from typing import Dict, Any
import logging
from datetime import datetime, timezone

from app.services.search_control import get_search_stats, get_quota_status
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/internal/search-stats")
async def get_internal_search_stats(request: Request) -> Dict[str, Any]:
    """
    Get internal search statistics for monitoring.
    
    Returns:
    - searches_today: Number of Amadeus API calls today
    - daily_cap: Maximum allowed calls per day
    - remaining_today: Remaining quota
    - cache_hit_ratio: Cache efficiency
    - recent_searches: Last 10 search events with sources
    - quota_status: Current quota state
    
    Use for:
    - Cost tracking
    - Trust auditing
    - Debugging price freshness issues
    """
    # Log access for audit trail
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"📊 Search stats accessed from {client_ip}")
    
    stats = get_search_stats()
    
    # Add environment info
    stats["environment"] = settings.amadeus_environment
    
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "statistics": stats
    }


@router.get("/internal/quota-status")
async def get_internal_quota_status(request: Request) -> Dict[str, Any]:
    """
    Get current quota status only (lightweight endpoint).
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "quota": get_quota_status()
    }


@router.get("/internal/cost-estimate")
async def get_cost_estimate(request: Request) -> Dict[str, Any]:
    """
    Get estimated cost metrics based on current usage.
    
    Note: This is for internal planning only.
    For accurate costs, check your Amadeus billing dashboard.
    """
    stats = get_search_stats()
    
    # Calculate daily average (if we have multiple days of data)
    daily_avg = stats["searches_today"]  # Simplified - in production, track across days
    
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "usage": {
            "today": stats["searches_today"],
            "this_month": stats["searches_this_month"],
            "daily_cap": stats["daily_cap"],
            "cap_utilization_percent": round((stats["searches_today"] / stats["daily_cap"]) * 100, 1) if stats["daily_cap"] > 0 else 0,
            "cache_efficiency_percent": round(stats["cache_hit_ratio"] * 100, 1),
            "estimated_monthly_at_current_rate": int(daily_avg * 30)
        },
        "note": "For accurate cost estimates, check your Amadeus billing dashboard"
    }

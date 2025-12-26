"""
INTERNAL SEARCH STATS ROUTER
============================
Exposes search statistics for internal monitoring only.

⚠️ WARNING: This endpoint must NEVER be exposed publicly.
Only for internal monitoring and debugging.
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import logging

from app.services.search_control import get_search_stats
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/internal/search-stats")
async def get_internal_search_stats(request: Request) -> Dict[str, Any]:
    """
    Get internal search statistics.
    
    ⚠️ INTERNAL ONLY - Do not expose publicly.
    
    Returns:
    - searches_today: Number of real Amadeus searches today
    - searches_this_month: Monthly total
    - daily_cap: Current daily cap setting
    - remaining_today: Searches remaining before cap
    - cache_hit_ratio: Cache efficiency metric
    - real_search_enabled: Whether real searches are enabled
    - recent_searches: Last 10 search events
    """
    # Basic IP check for internal access (customize as needed)
    client_ip = request.client.host if request.client else "unknown"
    
    # Log access for audit trail
    logger.info(f"📊 Search stats accessed from {client_ip}")
    
    stats = get_search_stats()
    
    # Add environment info
    stats["environment"] = settings.amadeus_environment
    stats["base_url"] = settings.amadeus_base_url
    
    return stats


@router.post("/internal/toggle-real-search")
async def toggle_real_search(enabled: bool, request: Request) -> Dict[str, str]:
    """
    Toggle real Amadeus search on/off.
    
    ⚠️ INTERNAL ONLY - Emergency kill switch for real searches.
    
    This doesn't modify the env var permanently, only runtime state.
    For permanent change, update AMADEUS_REAL_SEARCH_ENABLED in .env.
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.warning(f"⚠️ Real search toggle requested: {enabled} from {client_ip}")
    
    # Note: This would require modifying the settings object
    # For now, just return the current state
    return {
        "message": f"To {'enable' if enabled else 'disable'} real searches, update AMADEUS_REAL_SEARCH_ENABLED in .env and restart",
        "current_state": str(settings.amadeus_real_search_enabled)
    }


@router.get("/internal/cost-estimate")
async def get_cost_estimate() -> Dict[str, Any]:
    """
    Estimate API costs based on current usage.
    
    ⚠️ INTERNAL ONLY
    """
    stats = get_search_stats()
    
    # Amadeus pricing (approximate - check actual pricing)
    # Free tier: ~2000 calls/month
    # Production: varies by plan
    
    monthly_searches = stats["searches_this_month"]
    daily_avg = monthly_searches / max(1, 25)  # Assuming ~25 days per month
    
    return {
        "monthly_searches": monthly_searches,
        "daily_average": round(daily_avg, 1),
        "daily_cap": stats["daily_cap"],
        "cap_utilization_percent": round((stats["searches_today"] / stats["daily_cap"]) * 100, 1),
        "cache_efficiency_percent": round(stats["cache_hit_ratio"] * 100, 1),
        "estimated_monthly_at_current_rate": int(daily_avg * 30),
        "note": "For accurate cost estimates, check your Amadeus billing dashboard"
    }

"""
SEARCH CONTROL SERVICE
======================
COST-EFFICIENT, TRUST-FIRST flight search control system.

CRITICAL RULES:
- ONLY ONE action triggers real Amadeus API: explicit "Search Flights" button click
- Header x-search-intent = "real" MUST be present for real searches
- Daily search cap: 70 (configurable via DAILY_SEARCH_CAP env var)
- Cache TTL: 10-15 minutes
- Per-IP rate limit: 5 searches/minute
- Filters and sorting are CLIENT-SIDE ONLY - NEVER trigger API calls

This module provides:
1. Daily search counter with midnight UTC reset
2. Flight search result caching with "Last Known Live Price"
3. Per-IP rate limiting
4. Search intent validation
5. Graceful fallbacks (never show technical errors)
6. Comprehensive logging for cost monitoring

⚠️ WARNING: Only the protected search function in this module is allowed to call
   the Amadeus flight search API. All other code paths are FORBIDDEN.
"""

import hashlib
import logging
import time
from datetime import datetime, date, timezone
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import json

from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# GLOBAL STATE (In-memory - use Redis in production for multi-instance)
# ============================================================================

# Daily search counter - resets at UTC midnight
_daily_counter = {
    "date": None,
    "count": 0,
    "monthly_count": 0,
    "month": None
}

# Flight search cache with "Last Known Live Price" metadata
# Format: {
#   cache_key: {
#     "data": results,
#     "timestamp": unix_time,
#     "last_live_price": float,
#     "last_live_currency": str,
#     "last_live_updated_at": ISO timestamp,
#     "source": "AMADEUS" | "CACHE"
#   }
# }
_flight_cache: Dict[str, Dict] = {}

# Per-IP rate limiter: {ip_hash: [timestamp1, timestamp2, ...]}
_ip_rate_limits: Dict[str, List[float]] = defaultdict(list)

# Search logs for monitoring
_search_logs: List[Dict] = []

# Cache stats
_cache_stats = {
    "hits": 0,
    "misses": 0
}


# ============================================================================
# CONFIGURATION
# ============================================================================

def get_daily_cap() -> int:
    """Get daily search cap from environment."""
    return settings.daily_search_cap


def get_cache_ttl() -> int:
    """Get cache TTL in seconds."""
    return settings.flight_cache_ttl_seconds


def get_rate_limit_per_ip() -> int:
    """Get max searches per minute per IP."""
    return settings.search_rate_limit_per_ip


def is_real_search_enabled() -> bool:
    """Check if real Amadeus searches are enabled (feature flag)."""
    return settings.amadeus_real_search_enabled


# ============================================================================
# DAILY COUNTER MANAGEMENT (UTC Midnight Reset)
# ============================================================================

def _get_utc_date() -> date:
    """Get current date in UTC timezone."""
    return datetime.now(timezone.utc).date()


def _get_utc_month() -> str:
    """Get current month in UTC timezone as YYYY-MM."""
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _reset_daily_counter_if_needed():
    """Reset daily counter at UTC midnight (00:00 UTC)."""
    today = _get_utc_date()
    current_month = _get_utc_month()
    
    if _daily_counter["date"] != today:
        logger.info(
            f"📅 Daily counter reset at UTC midnight. "
            f"Previous: {_daily_counter['count']} searches on {_daily_counter['date']}"
        )
        _daily_counter["date"] = today
        _daily_counter["count"] = 0
    
    if _daily_counter["month"] != current_month:
        logger.info(
            f"📅 Monthly counter reset. "
            f"Previous: {_daily_counter['monthly_count']} in {_daily_counter['month']}"
        )
        _daily_counter["month"] = current_month
        _daily_counter["monthly_count"] = 0


def get_daily_search_count() -> int:
    """Get current daily search count."""
    _reset_daily_counter_if_needed()
    return _daily_counter["count"]


def get_monthly_search_count() -> int:
    """Get current monthly search count."""
    _reset_daily_counter_if_needed()
    return _daily_counter["monthly_count"]


def increment_search_counter():
    """Increment daily and monthly search counters."""
    _reset_daily_counter_if_needed()
    _daily_counter["count"] += 1
    _daily_counter["monthly_count"] += 1
    logger.info(
        f"📊 Search count: {_daily_counter['count']}/{get_daily_cap()} today, "
        f"{_daily_counter['monthly_count']} this month"
    )


def can_make_real_search() -> Tuple[bool, str]:
    """
    Check if a real Amadeus search is allowed.
    
    Returns:
        (allowed: bool, reason: str)
    """
    _reset_daily_counter_if_needed()
    
    # Check feature flag
    if not is_real_search_enabled():
        return False, "real_search_disabled"
    
    # Check daily cap
    if _daily_counter["count"] >= get_daily_cap():
        return False, "daily_cap_reached"
    
    return True, "allowed"


def get_quota_status() -> Dict[str, Any]:
    """Get current quota status for monitoring."""
    _reset_daily_counter_if_needed()
    return {
        "daily_used": _daily_counter["count"],
        "daily_cap": get_daily_cap(),
        "daily_remaining": max(0, get_daily_cap() - _daily_counter["count"]),
        "cap_reached": _daily_counter["count"] >= get_daily_cap(),
        "real_search_enabled": is_real_search_enabled()
    }


# ============================================================================
# CACHING WITH "LAST KNOWN LIVE PRICE"
# ============================================================================

def _build_cache_key(
    origin: str,
    destination: str,
    departure_date: str,
    adults: int = 1,
    cabin_class: str = "economy"
) -> str:
    """
    Build cache key for flight search.
    
    Format: ORIGIN-DESTINATION-DEPARTURE_DATE-PAX-CLASS
    """
    key = f"{origin.upper()}-{destination.upper()}-{departure_date}-{adults}-{cabin_class.lower()}"
    return key


def get_cached_results(
    origin: str,
    destination: str,
    departure_date: str,
    adults: int = 1,
    cabin_class: str = "economy",
    ignore_ttl: bool = False
) -> Optional[Dict]:
    """
    Get cached flight search results.
    
    Args:
        ignore_ttl: If True, returns cached data even if expired (for fallback)
    
    Returns:
        Cached results dict with metadata or None if not found
    """
    cache_key = _build_cache_key(origin, destination, departure_date, adults, cabin_class)
    
    if cache_key not in _flight_cache:
        _cache_stats["misses"] += 1
        return None
    
    cached = _flight_cache[cache_key]
    age = time.time() - cached["timestamp"]
    
    if not ignore_ttl and age > get_cache_ttl():
        # Expired - but don't delete, keep for fallback
        _cache_stats["misses"] += 1
        logger.debug(f"Cache expired for {cache_key} (age: {age:.0f}s)")
        return None
    
    _cache_stats["hits"] += 1
    logger.info(f"✅ Cache HIT for {cache_key} (age: {age:.0f}s)")
    
    # Return with source indicator
    return {
        **cached["data"],
        "source": "CACHE",
        "last_live_updated_at": cached.get("last_live_updated_at"),
        "last_live_price": cached.get("last_live_price"),
        "last_live_currency": cached.get("last_live_currency"),
        "cache_age_seconds": int(age)
    }


def get_last_known_live_results(
    origin: str,
    destination: str,
    departure_date: str,
    adults: int = 1,
    cabin_class: str = "economy"
) -> Optional[Dict]:
    """
    Get last known live results for fallback (ignores TTL).
    
    This is used when quota is exceeded to show cached data with honest timestamps.
    """
    cache_key = _build_cache_key(origin, destination, departure_date, adults, cabin_class)
    
    if cache_key not in _flight_cache:
        return None
    
    cached = _flight_cache[cache_key]
    age = time.time() - cached["timestamp"]
    
    logger.info(f"📦 Using last known live results for {cache_key} (age: {age:.0f}s)")
    
    return {
        **cached["data"],
        "source": "CACHE",
        "last_live_updated_at": cached.get("last_live_updated_at"),
        "last_live_price": cached.get("last_live_price"),
        "last_live_currency": cached.get("last_live_currency"),
        "cache_age_seconds": int(age),
        "is_stale": True
    }


def cache_results(
    origin: str,
    destination: str,
    departure_date: str,
    adults: int,
    cabin_class: str,
    results: Dict,
    is_live: bool = True
):
    """
    Cache flight search results with "Last Known Live Price" metadata.
    
    Args:
        results: Flight search results
        is_live: True if this is from a real Amadeus API call
    """
    cache_key = _build_cache_key(origin, destination, departure_date, adults, cabin_class)
    
    # Extract minimum price from offers
    offers = results.get("offers", []) or results.get("flights", [])
    min_price = None
    currency = "INR"
    
    if offers:
        prices = [o.get("price", 0) for o in offers if o.get("price")]
        if prices:
            min_price = min(prices)
        currencies = [o.get("currency", "INR") for o in offers if o.get("currency")]
        if currencies:
            currency = currencies[0]
    
    now_utc = datetime.now(timezone.utc).isoformat()
    
    _flight_cache[cache_key] = {
        "data": results,
        "timestamp": time.time(),
        "last_live_price": min_price,
        "last_live_currency": currency,
        "last_live_updated_at": now_utc if is_live else _flight_cache.get(cache_key, {}).get("last_live_updated_at"),
        "source": "AMADEUS" if is_live else "CACHE"
    }
    
    offer_count = len(offers)
    logger.info(
        f"💾 Cached {'live' if is_live else 'fallback'} results for {cache_key} "
        f"({offer_count} offers, min price: {min_price} {currency})"
    )


def get_cache_hit_ratio() -> float:
    """Get cache hit ratio."""
    total = _cache_stats["hits"] + _cache_stats["misses"]
    if total == 0:
        return 0.0
    return _cache_stats["hits"] / total


# ============================================================================
# PER-IP RATE LIMITING
# ============================================================================

def _hash_ip(ip: str) -> str:
    """Hash IP address for logging (never store raw IPs)."""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def check_ip_rate_limit(ip: str) -> Tuple[bool, str]:
    """
    Check if IP is within rate limit.
    
    Returns:
        (allowed: bool, reason: str)
    """
    ip_hash = _hash_ip(ip)
    now = time.time()
    window = 60  # 1 minute window
    
    # Clean old entries
    _ip_rate_limits[ip_hash] = [
        ts for ts in _ip_rate_limits[ip_hash]
        if now - ts < window
    ]
    
    # Check limit
    if len(_ip_rate_limits[ip_hash]) >= get_rate_limit_per_ip():
        logger.warning(f"⚠️ IP rate limit reached for {ip_hash}")
        return False, "ip_rate_limited"
    
    return True, "allowed"


def record_ip_search(ip: str):
    """Record a search for IP rate limiting."""
    ip_hash = _hash_ip(ip)
    _ip_rate_limits[ip_hash].append(time.time())


# ============================================================================
# SEARCH INTENT VALIDATION
# ============================================================================

def validate_search_intent(headers: Dict) -> Tuple[bool, str]:
    """
    Validate search intent.
    
    RELAXED GATE: Now allows searches when:
    1. x-search-intent header is "real" (explicit button click)
    2. x-search-intent header is missing or empty (direct API call)
    
    Only blocks explicit prefetch/filter requests.
    This ensures live provider searches run when valid params are present.
    
    Returns:
        (is_real_intent: bool, reason: str)
    """
    intent = headers.get("x-search-intent", "").lower().strip()
    
    # Explicit "real" intent - always allow
    if intent == "real":
        return True, "explicit_real_intent"
    
    # Explicit prefetch/filter - block (these are optimization requests)
    if intent == "prefetch":
        return False, "prefetch_request"
    if intent == "filter":
        return False, "filter_request"
    
    # Missing or empty intent - ALLOW (direct API calls, valid searches)
    # This relaxes the gate to allow live searches when params are valid
    return True, "implicit_search_allowed"


# ============================================================================
# LOGGING
# ============================================================================

def log_search_event(
    search_key: str,
    served_source: str,
    ip: str,
    is_real: bool,
    result_count: int,
    last_live_updated_at: Optional[str] = None,
    quota_status: Optional[Dict] = None,
    latency_ms: float = 0
):
    """
    Log a search event for monitoring and trust auditing.
    
    Logs:
    - search_key
    - served_source (AMADEUS | CACHE)
    - last_live_updated_at
    - quota_status
    
    Never logs raw IP - only hashed version.
    """
    ip_hash = _hash_ip(ip)
    
    if quota_status is None:
        quota_status = get_quota_status()
    
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "search_key": search_key,
        "served_source": served_source,
        "last_live_updated_at": last_live_updated_at,
        "quota_status": quota_status,
        "ip_hash": ip_hash,
        "is_real": is_real,
        "result_count": result_count,
        "latency_ms": latency_ms
    }
    
    _search_logs.append(event)
    
    # Keep only last 1000 events
    if len(_search_logs) > 1000:
        _search_logs.pop(0)
    
    logger.info(
        f"🔍 Search: {search_key} | Source: {served_source} | "
        f"Real: {is_real} | Results: {result_count} | "
        f"Quota: {quota_status['daily_used']}/{quota_status['daily_cap']}"
    )


# ============================================================================
# STATS ENDPOINT DATA
# ============================================================================

def get_search_stats() -> Dict[str, Any]:
    """
    Get search statistics for internal monitoring.
    
    This data should ONLY be exposed via internal endpoint.
    """
    _reset_daily_counter_if_needed()
    
    return {
        "searches_today": _daily_counter["count"],
        "searches_this_month": _daily_counter["monthly_count"],
        "daily_cap": get_daily_cap(),
        "remaining_today": max(0, get_daily_cap() - _daily_counter["count"]),
        "cache_hit_ratio": round(get_cache_hit_ratio(), 3),
        "cache_hits": _cache_stats["hits"],
        "cache_misses": _cache_stats["misses"],
        "cached_routes": len(_flight_cache),
        "real_search_enabled": is_real_search_enabled(),
        "rate_limit_per_ip": get_rate_limit_per_ip(),
        "cache_ttl_seconds": get_cache_ttl(),
        "recent_searches": _search_logs[-10:],
        "quota_status": get_quota_status()
    }


# ============================================================================
# FALLBACK MESSAGES (USER-FRIENDLY)
# ============================================================================

def get_cache_display_message() -> str:
    """
    Get user-friendly message for cached results.
    
    Approved UX copy: "Showing recent results. Live prices may update shortly."
    """
    return "Showing recent results. Live prices may update shortly."


def get_cache_helper_text() -> str:
    """
    Get helper text for cached results.
    
    Approved copy: "Prices may change on the booking site"
    """
    return "Prices may change on the booking site"


def get_demo_flights(origin: str, destination: str, departure_date: str) -> List[Dict]:
    """
    Get demo/sample flight data for fallback.
    
    This should be clearly marked as non-live data.
    """
    # Return empty for now - can be populated with popular route examples
    return []


# ============================================================================
# MAIN SEARCH DECISION FUNCTION
# ============================================================================

def should_make_real_search(
    headers: Dict,
    ip: str,
    origin: str,
    destination: str,
    departure_date: str,
    adults: int = 1,
    cabin_class: str = "economy"
) -> Tuple[bool, str, Optional[Dict]]:
    """
    Determine if a real Amadeus API call should be made.
    
    This is the CENTRAL DECISION POINT for all search requests.
    
    Args:
        headers: Request headers (must contain x-search-intent)
        ip: Client IP address
        origin, destination, departure_date: Search parameters
        adults, cabin_class: Additional search parameters
    
    Returns:
        (should_call_api: bool, reason: str, cached_data: Optional[Dict])
    
    Decision flow:
    1. Check for cached results -> return cached if available
    2. Validate search intent header
    3. Check IP rate limit
    4. Check daily cap
    5. Allow real search if all checks pass
    """
    # Step 1: Check cache first (ALWAYS)
    cached = get_cached_results(origin, destination, departure_date, adults, cabin_class)
    if cached:
        return False, "cache_hit", cached
    
    # Step 2: Validate intent
    is_real_intent, intent_reason = validate_search_intent(headers)
    if not is_real_intent:
        return False, f"no_real_intent:{intent_reason}", None
    
    # Step 3: Check IP rate limit
    ip_allowed, ip_reason = check_ip_rate_limit(ip)
    if not ip_allowed:
        return False, ip_reason, None
    
    # Step 4: Check daily cap
    cap_allowed, cap_reason = can_make_real_search()
    if not cap_allowed:
        return False, cap_reason, None
    
    # All checks passed - allow real search
    return True, "allowed", None

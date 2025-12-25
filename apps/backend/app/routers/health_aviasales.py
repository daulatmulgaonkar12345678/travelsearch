"""
Aviasales / Travelpayouts Health Check Router

Provides health check endpoints for Aviasales integration:
- Check if API token is configured
- Test API connectivity
- Get provider status
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import os
import httpx
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health/aviasales")
async def check_aviasales_health() -> Dict[str, Any]:
    """
    Check Aviasales/Travelpayouts integration health.
    
    Checks:
    1. API token configured
    2. API connectivity
    3. Response validity
    """
    result = {
        "provider": "aviasales",
        "status": "unknown",
        "checks": {}
    }
    
    # Check 1: API token configured
    api_token = os.environ.get("TRAVELPAYOUTS_API_TOKEN") or getattr(settings, "travelpayouts_api_token", None)
    
    if not api_token:
        result["status"] = "unconfigured"
        result["checks"]["token"] = {
            "status": "missing",
            "message": "TRAVELPAYOUTS_API_TOKEN not set in environment"
        }
        result["message"] = "Aviasales is not configured. Set TRAVELPAYOUTS_API_TOKEN to enable."
        return result
    
    result["checks"]["token"] = {
        "status": "configured",
        "message": f"Token configured (starts with {api_token[:6]}...)"
    }
    
    # Check 2: API connectivity
    try:
        # Test with a simple price check
        test_url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
        params = {
            "origin": "DEL",
            "destination": "BOM",
            "departure_at": "2025-02-15",
            "currency": "INR",
            "limit": 1,
            "token": api_token
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(test_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            result["checks"]["connectivity"] = {
                "status": "ok",
                "response_code": 200,
                "data_received": len(data.get("data", [])) > 0
            }
            result["status"] = "healthy"
            result["message"] = "Aviasales integration is working"
        elif response.status_code == 401:
            result["checks"]["connectivity"] = {
                "status": "auth_failed",
                "response_code": 401,
                "message": "Invalid API token"
            }
            result["status"] = "auth_error"
            result["message"] = "Aviasales API token is invalid"
        else:
            result["checks"]["connectivity"] = {
                "status": "error",
                "response_code": response.status_code,
                "message": response.text[:200]
            }
            result["status"] = "api_error"
            result["message"] = f"Aviasales API returned {response.status_code}"
    
    except httpx.TimeoutException:
        result["checks"]["connectivity"] = {
            "status": "timeout",
            "message": "API request timed out"
        }
        result["status"] = "timeout"
        result["message"] = "Aviasales API is not responding"
    
    except Exception as e:
        result["checks"]["connectivity"] = {
            "status": "error",
            "message": str(e)
        }
        result["status"] = "error"
        result["message"] = f"Failed to connect to Aviasales: {e}"
    
    return result


@router.get("/health/providers")
async def get_provider_status() -> Dict[str, Any]:
    """
    Get status of all flight search providers.
    """
    providers = {
        "primary": None,
        "fallback": [],
        "providers": {}
    }
    
    # Check Aviasales (PRIMARY)
    aviasales_token = os.environ.get("TRAVELPAYOUTS_API_TOKEN") or getattr(settings, "travelpayouts_api_token", None)
    aviasales_enabled = bool(aviasales_token)
    
    providers["providers"]["aviasales"] = {
        "enabled": aviasales_enabled,
        "role": "primary" if aviasales_enabled else "disabled",
        "status": "configured" if aviasales_enabled else "unconfigured"
    }
    
    if aviasales_enabled:
        providers["primary"] = "aviasales"
    
    # Check Amadeus (FALLBACK)
    amadeus_key = getattr(settings, "amadeus_api_key", None)
    amadeus_enabled = bool(amadeus_key)
    
    providers["providers"]["amadeus"] = {
        "enabled": amadeus_enabled,
        "role": "fallback" if aviasales_enabled else "primary",
        "status": "configured" if amadeus_enabled else "unconfigured"
    }
    
    if amadeus_enabled:
        if not aviasales_enabled:
            providers["primary"] = "amadeus"
        else:
            providers["fallback"].append("amadeus")
    
    # Check FlightAPI (FINAL FALLBACK)
    flightapi_key = getattr(settings, "flightapi_key", None)
    flightapi_enabled = getattr(settings, "flightapi_enabled", False) and bool(flightapi_key)
    
    providers["providers"]["flightapi"] = {
        "enabled": flightapi_enabled,
        "role": "fallback",
        "status": "configured" if flightapi_enabled else "disabled"
    }
    
    if flightapi_enabled:
        providers["fallback"].append("flightapi")
    
    # Summary
    providers["summary"] = {
        "primary_provider": providers["primary"] or "none",
        "fallback_count": len(providers["fallback"]),
        "total_configured": sum(1 for p in providers["providers"].values() if p["enabled"])
    }
    
    return providers


@router.get("/health/airports")
async def get_airport_stats() -> Dict[str, Any]:
    """
    Get airport database statistics.
    """
    try:
        from app.services.airport_validator import get_stats, get_all_indian_airports
        
        stats = get_stats()
        india_airports = get_all_indian_airports()
        
        # Sample some Indian airports
        sample = india_airports[:10] if india_airports else []
        sample_list = [
            {"iata": a.get("iata"), "city": a.get("city"), "name": a.get("name")}
            for a in sample
        ]
        
        return {
            "status": "ok",
            "stats": stats,
            "india_sample": sample_list
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

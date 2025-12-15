"""
Amadeus Health Check Endpoint

Provides a dedicated endpoint to test Amadeus authentication.
Returns full debug information about credential loading and token fetching.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from datetime import datetime
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)

@router.get("/amadeus")
async def health_check_amadeus() -> Dict[str, Any]:
    """
    Test Amadeus API authentication and return full debug info.
    
    This endpoint:
    1. Shows what credentials are loaded from .env
    2. Attempts to fetch an access token
    3. Returns success/failure with full logs
    """
    logger.info("Starting Amadeus health check...")
    
    # Step 1: Check what credentials are loaded
    credentials_loaded = {
        "api_key_set": bool(settings.amadeus_api_key),
        "api_key_preview": f"{settings.amadeus_api_key[:8]}...{settings.amadeus_api_key[-4:]}" if settings.amadeus_api_key else "NOT SET",
        "api_secret_set": bool(settings.amadeus_api_secret),
        "api_secret_preview": f"{settings.amadeus_api_secret[:4]}...{settings.amadeus_api_secret[-4:]}" if settings.amadeus_api_secret else "NOT SET",
        "base_url": settings.amadeus_base_url,
        "environment": settings.amadeus_environment
    }
    
    logger.info(f"Credentials check: {credentials_loaded}")
    
    # Step 2: Attempt to fetch token
    try:
        from app.services.adapters.amadeus_flights_v2 import AmadeusFlightsAdapterV2
        
        adapter = AmadeusFlightsAdapterV2()
        logger.info("Adapter initialized, fetching token...")
        
        token = await adapter.get_access_token()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "credentials": credentials_loaded,
            "token_obtained": True,
            "token_preview": f"{token[:10]}...{token[-6:]}",
            "message": "Amadeus authentication successful"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "credentials": credentials_loaded,
            "token_obtained": False,
            "error": str(e),
            "message": "Amadeus authentication failed",
            "troubleshooting": {
                "check_env_file": "/app/apps/backend/.env",
                "verify_credentials": "Ensure AMADEUS_API_KEY and AMADEUS_API_SECRET are correct",
                "restart_backend": "Run: sudo supervisorctl restart backend",
                "clear_cache": "Run: find /app/apps/backend -type d -name __pycache__ -exec rm -rf {} +"
            }
        }

"""Service Status Health Check Endpoints

Provides dedicated health check endpoints for each service.
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

router = APIRouter(prefix="/api", tags=["health"])
logger = logging.getLogger(__name__)

@router.get("/flights/status")
async def flights_status() -> Dict[str, Any]:
    """
    Check if flights service is available.
    Returns 200 if available, 503 if not.
    """
    try:
        # Check if flight providers are accessible
        from app.services.aggregator import SearchAggregator
        aggregator = SearchAggregator()
        
        # Basic validation
        if aggregator.amadeus_flights:
            return {
                "status": "available",
                "service": "flights",
                "message": "Flights service is operational"
            }
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "unavailable",
                    "service": "flights",
                    "message": "Flights service temporarily unavailable"
                }
            )
    except Exception as e:
        logger.error(f"Flights status check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unavailable",
                "service": "flights",
                "message": "Flights service temporarily unavailable"
            }
        )

@router.get("/hotels/status")
async def hotels_status() -> Dict[str, Any]:
    """
    Check if hotels service is available.
    Returns 200 if available, 503 if not.
    """
    try:
        # Check if hotel providers are accessible
        from app.services.aggregator import SearchAggregator
        aggregator = SearchAggregator()
        
        # Basic validation
        if aggregator.amadeus_hotels:
            return {
                "status": "available",
                "service": "hotels",
                "message": "Hotels service is operational"
            }
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "unavailable",
                    "service": "hotels",
                    "message": "Hotels service temporarily unavailable"
                }
            )
    except Exception as e:
        logger.error(f"Hotels status check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unavailable",
                "service": "hotels",
                "message": "Hotels service temporarily unavailable"
            }
        )

@router.get("/status")
async def backend_status() -> Dict[str, Any]:
    """
    Overall backend health check.
    """
    return {
        "status": "available",
        "service": "backend",
        "message": "Backend service is operational"
    }

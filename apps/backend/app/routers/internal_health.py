"""
Internal Health Endpoints

Provides health status for:
- Rate limiter (per supplier)
- Circuit breaker (per supplier)
- Redis connection
- Metrics

Routes:
- GET /internal/health/rate/:supplier
- GET /internal/health/circuit/:supplier
- GET /internal/health/redis
- GET /internal/metrics
"""

from fastapi import APIRouter, HTTPException
from typing import Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["internal-health"])

@router.get("/health/rate/{supplier}")
async def get_rate_limiter_status(supplier: str) -> Dict:
    """
    Get rate limiter status for a supplier.
    
    Returns token bucket state: remaining tokens, capacity, refill rate.
    """
    try:
        from app.services.protected_orchestrator import protected_orchestrator
        
        status = await protected_orchestrator.rate_limiter.get_status(supplier)
        
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        
        return {
            "supplier": supplier,
            "status": "ok",
            **status
        }
    
    except Exception as e:
        logger.error(f"Error getting rate limiter status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/circuit/{supplier}")
async def get_circuit_breaker_status(supplier: str) -> Dict:
    """
    Get circuit breaker status for a supplier.
    
    Returns state: CLOSED/OPEN/HALF_OPEN, failures, retry_after.
    """
    try:
        from app.services.protected_orchestrator import protected_orchestrator
        
        status = await protected_orchestrator.circuit_breaker.get_status(supplier)
        
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        
        return {
            "supplier": supplier,
            "status": "ok",
            **status
        }
    
    except Exception as e:
        logger.error(f"Error getting circuit breaker status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/redis")
async def get_redis_health() -> Dict:
    """
    Check Redis connection health.
    """
    try:
        from app.services.redis_client import redis_client
        
        is_healthy = await redis_client.health_check()
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "connected": is_healthy
        }
    
    except Exception as e:
        logger.error(f"Redis health check error: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }

@router.get("/metrics")
async def get_metrics() -> Dict:
    """
    Get aggregated metrics for monitoring.
    
    Includes:
    - Orchestrator metrics
    - Rate limiter metrics
    - Circuit breaker metrics
    """
    try:
        from app.services.protected_orchestrator import protected_orchestrator
        
        metrics = protected_orchestrator.get_metrics()
        
        return {
            "status": "ok",
            "metrics": metrics
        }
    
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check() -> Dict:
    """
    Overall system health check.
    """
    try:
        from app.services.redis_client import redis_client
        from app.services.protected_orchestrator import protected_orchestrator
        
        redis_healthy = await redis_client.health_check()
        
        # Check circuit breakers
        circuit_status = {}
        for supplier in ["amadeus", "flightapi"]:
            status = await protected_orchestrator.circuit_breaker.get_status(supplier)
            circuit_status[supplier] = status.get("state", "unknown")
        
        return {
            "status": "healthy" if redis_healthy else "degraded",
            "redis": "connected" if redis_healthy else "disconnected",
            "circuits": circuit_status,
            "timestamp": __import__('time').time()
        }
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

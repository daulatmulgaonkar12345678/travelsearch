"""
Hybrid Protection System Health Endpoints

Provides monitoring and diagnostics for the hybrid supplier protection system.

Routes:
- GET /internal/hybrid/health/rate/:supplier - Local bucket status
- GET /internal/hybrid/health/quota/:supplier - Global quota status
- GET /internal/hybrid/health/circuit/:supplier - Circuit breaker status
- GET /internal/hybrid/status/:supplier - Complete status
- GET /internal/hybrid/metrics - System metrics
- POST /internal/hybrid/reset/:supplier - Reset protection (admin)
"""

from fastapi import APIRouter, HTTPException
from typing import Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/hybrid", tags=["hybrid-protection"])

@router.get("/health/rate/{supplier}")
async def get_rate_limiter_status(supplier: str) -> Dict:
    """
    Get local rate limiter (token bucket) status.
    
    Returns current tokens, capacity, and refill rate.
    """
    try:
        from app.services.supplier_protection_controller import get_controller
        
        controller = await get_controller()
        
        if supplier not in controller.local_buckets:
            raise HTTPException(status_code=404, detail=f"Supplier {supplier} not found")
        
        bucket = controller.local_buckets[supplier]
        
        return {
            "supplier": supplier,
            "type": "local_token_bucket",
            **bucket.peek()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rate limiter status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/quota/{supplier}")
async def get_quota_status(supplier: str) -> Dict:
    """
    Get global quota status (per-minute).
    
    Returns allowed, used, and remaining requests for current minute.
    """
    try:
        from app.services.supplier_protection_controller import get_controller
        
        controller = await get_controller()
        
        if not controller.global_quota:
            return {
                "supplier": supplier,
                "status": "unavailable",
                "message": "Global quota store not initialized"
            }
        
        status = await controller.global_quota.get_status(supplier)
        
        if not status:
            return {
                "supplier": supplier,
                "status": "no_data",
                "message": "No quota data for current minute"
            }
        
        return {
            "type": "global_quota",
            **status
        }
    
    except Exception as e:
        logger.error(f"Error getting quota status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/circuit/{supplier}")
async def get_circuit_status(supplier: str) -> Dict:
    """
    Get circuit breaker status.
    
    Returns state (CLOSED/OPEN/HALF_OPEN), failures, and retry timing.
    """
    try:
        from app.services.supplier_protection_controller import get_controller
        
        controller = await get_controller()
        
        if not controller.circuit_breaker:
            return {
                "supplier": supplier,
                "status": "unavailable",
                "message": "Circuit breaker not initialized"
            }
        
        status = await controller.circuit_breaker.get_status(supplier)
        
        return {
            "type": "circuit_breaker",
            **status
        }
    
    except Exception as e:
        logger.error(f"Error getting circuit status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{supplier}")
async def get_complete_status(supplier: str) -> Dict:
    """
    Get complete protection status for a supplier.
    
    Combines rate limiter, quota, and circuit breaker status.
    """
    try:
        from app.services.supplier_protection_controller import get_supplier_status
        
        status = await get_supplier_status(supplier)
        
        return status
    
    except Exception as e:
        logger.error(f"Error getting complete status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_system_metrics() -> Dict:
    """
    Get system-wide protection metrics.
    
    Returns request counts, block rates, and error counts.
    """
    try:
        from app.services.supplier_protection_controller import get_metrics
        
        metrics = await get_metrics()
        
        return {
            "status": "ok",
            "metrics": metrics
        }
    
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset/{supplier}")
async def reset_protection(supplier: str) -> Dict:
    """
    Reset protection for a supplier (admin/testing use).
    
    Resets:
    - Circuit breaker state
    - Global quota (current minute)
    - Failure counters
    
    Note: Local token bucket refills naturally.
    """
    try:
        from app.services.supplier_protection_controller import get_controller
        
        controller = await get_controller()
        
        # Reset circuit breaker
        if controller.circuit_breaker:
            await controller.circuit_breaker.reset(supplier)
        
        # Reset global quota
        if controller.global_quota:
            await controller.global_quota.reset_quota(supplier)
        
        logger.info(f"✅ Reset protection for {supplier}")
        
        return {
            "supplier": supplier,
            "status": "reset",
            "message": "Protection reset successfully"
        }
    
    except Exception as e:
        logger.error(f"Error resetting protection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def overall_health() -> Dict:
    """
    Get overall hybrid protection system health.
    """
    try:
        from app.services.supplier_protection_controller import get_controller
        
        controller = await get_controller()
        
        return {
            "status": "healthy" if controller.initialized else "degraded",
            "initialized": controller.initialized,
            "global_quota": "available" if controller.global_quota else "unavailable",
            "circuit_breaker": "available" if controller.circuit_breaker else "unavailable",
            "local_buckets": len(controller.local_buckets)
        }
    
    except Exception as e:
        logger.error(f"Error checking health: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

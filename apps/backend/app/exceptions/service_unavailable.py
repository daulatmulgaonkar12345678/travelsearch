"""Service Unavailability Exception Handler

Handles service unavailability gracefully with structured 503 responses.
Production-ready exception handling for microservices architecture.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ServiceUnavailableException(Exception):
    """Exception raised when a service is temporarily unavailable"""
    
    def __init__(
        self,
        service: str = "backend",
        message: Optional[str] = None,
        details: Optional[str] = None
    ):
        self.service = service
        self.message = message or f"{service.capitalize()} service temporarily unavailable"
        self.details = details
        super().__init__(self.message)

async def service_unavailable_exception_handler(
    request: Request,
    exc: ServiceUnavailableException
) -> JSONResponse:
    """
    Global exception handler for service unavailability.
    Returns structured 503 response.
    """
    logger.error(
        f"Service unavailable: {exc.service} - {exc.message}",
        extra={"service": exc.service, "path": request.url.path}
    )
    
    response_data = {
        "status": "unavailable",
        "service": exc.service,
        "message": exc.message
    }
    
    if exc.details:
        response_data["details"] = exc.details
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=response_data
    )

async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Catch-all exception handler for unexpected errors.
    Prevents service crashes and returns 503.
    """
    logger.exception(
        f"Unexpected error in {request.url.path}: {str(exc)}",
        exc_info=exc
    )
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "unavailable",
            "service": "backend",
            "message": "Service temporarily unavailable. Please try again later."
        }
    )

"""
Protected Amadeus Adapter (Hybrid Protection)

Wraps Amadeus API calls with hybrid supplier protection:
- Local token bucket (RPS limiting)
- Global quota (per-minute limiting)
- Circuit breaker (failure tracking)

Usage:
    adapter = ProtectedAmadeusAdapter()
    offers = await adapter.search_flights_protected(request)
"""

import logging
import httpx
from typing import List
from app.models.flight import FlightOffer, FlightSearchRequest
from app.services.adapters.amadeus_flights import AmadeusFlightsAdapter
from app.services.supplier_protection_controller import (
    allow_request,
    on_supplier_success,
    on_supplier_failure
)

logger = logging.getLogger(__name__)

class ProtectedAmadeusAdapter(AmadeusFlightsAdapter):
    """
    Amadeus adapter with integrated hybrid protection.
    
    Extends base adapter to add protection before/after API calls.
    """
    
    async def search_flights_protected(self, request: FlightSearchRequest) -> List[FlightOffer]:
        """
        Search flights with protection.
        
        Returns:
            List of FlightOffer objects (empty list on any error)
        """
        supplier = "amadeus"
        
        # Step 1: Check if request is allowed
        allowed, reason, metadata = await allow_request(supplier, queue_timeout=0.3)
        
        if not allowed:
            logger.warning(
                f"🛡️  Amadeus blocked: {reason} | metadata: {metadata}"
            )
            # Return empty - caller should try fallback
            return []
        
        # Step 2: Make API call with error handling
        try:
            # Call parent class method (original Amadeus logic)
            offers = await self.search_flights(request)
            
            # Step 3: Record success
            if offers and len(offers) > 0:
                await on_supplier_success(supplier)
                logger.info(f"✅ Amadeus protected call: {len(offers)} offers")
            
            return offers
        
        except httpx.HTTPStatusError as e:
            # Step 4: Record failure for specific HTTP errors
            status_code = str(e.response.status_code)
            
            if status_code in ["429", "401", "500", "502", "503", "504"]:
                await on_supplier_failure(supplier, status_code)
                logger.error(f"❌ Amadeus protected call failed: {status_code}")
            
            return []
        
        except Exception as e:
            # Step 5: Record generic failure
            error_str = str(e)
            
            # Try to extract error code
            if "429" in error_str:
                await on_supplier_failure(supplier, "429")
            elif "401" in error_str:
                await on_supplier_failure(supplier, "401")
            else:
                await on_supplier_failure(supplier, "500")
            
            logger.error(f"❌ Amadeus protected call exception: {e}")
            return []

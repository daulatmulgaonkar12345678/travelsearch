"""
Aviasales-First Flight Search Orchestrator

PRIORITY ORDER:
1. Aviasales (Travelpayouts Data API) - PRIMARY
2. Amadeus - FALLBACK
3. Cached results - LAST FALLBACK

This orchestrator implements the industry-standard approach:
- Aviasales provides real-time pricing with affiliate deeplinks
- Amadeus is used only when Aviasales fails or returns empty
- Results include real deeplinks (not manually generated)

Feature Flag: SUPPLIER_PROTECTION=true (uses this orchestrator)
"""

import asyncio
import logging
import time
import uuid
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from app.models.flight import FlightOffer, FlightSearchRequest
from app.core.config import settings

logger = logging.getLogger(__name__)


class AviasalesFirstOrchestrator:
    """
    Aviasales-first orchestrator with Amadeus fallback.
    
    Priority:
    1. Aviasales (PRIMARY) - Real pricing data with deeplinks
    2. Amadeus (FALLBACK) - When Aviasales fails
    3. FlightAPI (FINAL FALLBACK) - Emergency backup
    """
    
    def __init__(self):
        self.metrics = {
            "total_searches": 0,
            "aviasales_success": 0,
            "aviasales_empty": 0,
            "amadeus_fallback_used": 0,
            "flightapi_fallback_used": 0,
            "all_failed": 0
        }
        
        # Check if Aviasales is configured
        self.aviasales_enabled = bool(
            os.environ.get("TRAVELPAYOUTS_API_TOKEN") or 
            getattr(settings, "travelpayouts_api_token", None)
        )
        
        if self.aviasales_enabled:
            logger.info("✅ AviasalesFirstOrchestrator: Aviasales is PRIMARY provider")
        else:
            logger.warning("⚠️  AviasalesFirstOrchestrator: Aviasales not configured, using Amadeus as primary")
    
    async def search(
        self,
        request: FlightSearchRequest,
        request_id: Optional[str] = None
    ) -> Dict:
        """
        Execute flight search with Aviasales-first priority.
        
        Flow:
        1. Try Aviasales (PRIMARY)
        2. If Aviasales returns >= 1 result -> return immediately
        3. If Aviasales fails/empty -> try Amadeus (FALLBACK)
        4. If Amadeus fails/empty -> try FlightAPI (FINAL)
        5. Return results or no_results
        """
        if not request_id:
            request_id = str(uuid.uuid4())
        
        self.metrics["total_searches"] += 1
        search_logs = []
        start_time = time.time()
        
        logger.info(
            f"🔍 [{request_id}] Aviasales-first search: "
            f"{request.origin} → {request.destination} on {request.departure_date}"
        )
        
        # Validate airport codes
        if not self._validate_airports(request.origin, request.destination):
            return self._build_error_response(
                request_id, 
                "Invalid airport code. Please select from the autocomplete list.",
                search_logs,
                time.time() - start_time
            )
        
        # Step 1: Try Aviasales (PRIMARY)
        if self.aviasales_enabled:
            aviasales_offers, aviasales_logs = await self._try_aviasales(request, request_id)
            search_logs.extend(aviasales_logs)
            
            if aviasales_offers and len(aviasales_offers) > 0:
                # SUCCESS - Aviasales returned results
                self.metrics["aviasales_success"] += 1
                elapsed = time.time() - start_time
                
                logger.info(
                    f"✅ [{request_id}] Aviasales SUCCESS: {len(aviasales_offers)} offers in {elapsed:.2f}s"
                )
                
                return self._build_success_response(
                    request_id,
                    aviasales_offers,
                    "aviasales",
                    search_logs,
                    elapsed
                )
            else:
                self.metrics["aviasales_empty"] += 1
                logger.warning(f"⚠️  [{request_id}] Aviasales returned empty - trying Amadeus fallback")
        
        # Step 2: Try Amadeus (FALLBACK)
        amadeus_offers, amadeus_logs = await self._try_amadeus(request, request_id)
        search_logs.extend(amadeus_logs)
        
        if amadeus_offers and len(amadeus_offers) > 0:
            self.metrics["amadeus_fallback_used"] += 1
            elapsed = time.time() - start_time
            
            logger.info(
                f"✅ [{request_id}] Amadeus FALLBACK SUCCESS: {len(amadeus_offers)} offers in {elapsed:.2f}s"
            )
            
            return self._build_success_response(
                request_id,
                amadeus_offers,
                "amadeus",
                search_logs,
                elapsed
            )
        
        # Step 3: Try FlightAPI (FINAL FALLBACK)
        flightapi_offers, flightapi_logs = await self._try_flightapi(request, request_id)
        search_logs.extend(flightapi_logs)
        
        if flightapi_offers and len(flightapi_offers) > 0:
            self.metrics["flightapi_fallback_used"] += 1
            elapsed = time.time() - start_time
            
            logger.info(
                f"✅ [{request_id}] FlightAPI FINAL FALLBACK SUCCESS: {len(flightapi_offers)} offers"
            )
            
            return self._build_success_response(
                request_id,
                flightapi_offers,
                "flightapi",
                search_logs,
                elapsed
            )
        
        # All providers failed
        self.metrics["all_failed"] += 1
        elapsed = time.time() - start_time
        
        logger.error(f"❌ [{request_id}] All providers failed ({elapsed:.2f}s)")
        
        return {
            "request_id": request_id,
            "status": "completed",
            "outcome": "no_results",
            "message": "No flights found. Try different dates or check back later.",
            "flights": [],
            "offers": [],
            "supplier": "none",
            "logs": search_logs,
            "elapsed_seconds": elapsed,
            "retry_hint": "Flight availability varies. Consider checking nearby dates or airports."
        }
    
    async def _try_aviasales(
        self,
        request: FlightSearchRequest,
        request_id: str
    ) -> Tuple[List[FlightOffer], List[Dict]]:
        """Try Aviasales/Travelpayouts Data API."""
        logs = []
        
        try:
            from app.services.adapters.aviasales_adapter import AviasalesAdapter
            
            # Check if token is available
            if not AviasalesAdapter.is_available():
                logs.append({
                    "step": "aviasales",
                    "status": "disabled",
                    "reason": "TRAVELPAYOUTS_API_TOKEN not configured"
                })
                return [], logs
            
            adapter = AviasalesAdapter()
            
            start = time.time()
            timeout_ms = getattr(settings, "travelpayouts_timeout_ms", 10000)
            
            offers = await asyncio.wait_for(
                adapter.search_flights(request),
                timeout=timeout_ms / 1000
            )
            
            latency_ms = (time.time() - start) * 1000
            
            if offers and len(offers) > 0:
                logs.append({
                    "step": "aviasales",
                    "status": "success",
                    "results": len(offers),
                    "latency_ms": round(latency_ms, 2),
                    "provider": "travelpayouts_data_api"
                })
                return offers, logs
            else:
                logs.append({
                    "step": "aviasales",
                    "status": "empty",
                    "results": 0,
                    "latency_ms": round(latency_ms, 2)
                })
                return [], logs
        
        except asyncio.TimeoutError:
            logs.append({
                "step": "aviasales",
                "status": "timeout",
                "error": "Request timeout"
            })
            logger.warning(f"[{request_id}] Aviasales timeout")
            return [], logs
        
        except Exception as e:
            logs.append({
                "step": "aviasales",
                "status": "error",
                "error": str(e)
            })
            logger.error(f"[{request_id}] Aviasales error: {e}")
            return [], logs
    
    async def _try_amadeus(
        self,
        request: FlightSearchRequest,
        request_id: str
    ) -> Tuple[List[FlightOffer], List[Dict]]:
        """Try Amadeus as fallback."""
        logs = []
        
        try:
            from app.services.adapters.amadeus_flights import AmadeusFlightsAdapter
            
            adapter = AmadeusFlightsAdapter()
            
            start = time.time()
            timeout_ms = getattr(settings, "amadeus_timeout_ms", 2500)
            
            offers = await asyncio.wait_for(
                adapter.search_flights(request),
                timeout=timeout_ms / 1000
            )
            
            latency_ms = (time.time() - start) * 1000
            
            if offers and len(offers) > 0:
                logs.append({
                    "step": "amadeus",
                    "status": "success",
                    "results": len(offers),
                    "latency_ms": round(latency_ms, 2)
                })
                return offers, logs
            else:
                logs.append({
                    "step": "amadeus",
                    "status": "empty",
                    "results": 0,
                    "latency_ms": round(latency_ms, 2)
                })
                return [], logs
        
        except asyncio.TimeoutError:
            logs.append({
                "step": "amadeus",
                "status": "timeout"
            })
            return [], logs
        
        except Exception as e:
            logs.append({
                "step": "amadeus",
                "status": "error",
                "error": str(e)
            })
            logger.error(f"[{request_id}] Amadeus error: {e}")
            return [], logs
    
    async def _try_flightapi(
        self,
        request: FlightSearchRequest,
        request_id: str
    ) -> Tuple[List[FlightOffer], List[Dict]]:
        """Try FlightAPI as final fallback."""
        logs = []
        
        try:
            if not getattr(settings, "flightapi_enabled", False):
                logs.append({
                    "step": "flightapi",
                    "status": "disabled"
                })
                return [], logs
            
            from app.services.adapters.flightapi_adapter import FlightAPIAdapter
            
            adapter = FlightAPIAdapter()
            
            start = time.time()
            timeout_ms = getattr(settings, "flightapi_timeout_ms", 3000)
            
            offers = await asyncio.wait_for(
                adapter.search_flights(request),
                timeout=timeout_ms / 1000
            )
            
            latency_ms = (time.time() - start) * 1000
            
            if offers and len(offers) > 0:
                logs.append({
                    "step": "flightapi",
                    "status": "success",
                    "results": len(offers),
                    "latency_ms": round(latency_ms, 2)
                })
                return offers, logs
            else:
                logs.append({
                    "step": "flightapi",
                    "status": "empty",
                    "results": 0
                })
                return [], logs
        
        except asyncio.TimeoutError:
            logs.append({
                "step": "flightapi",
                "status": "timeout"
            })
            return [], logs
        
        except Exception as e:
            logs.append({
                "step": "flightapi",
                "status": "error",
                "error": str(e)
            })
            return [], logs
    
    def _validate_airports(self, origin: str, destination: str) -> bool:
        """
        Validate airport codes are in our canonical list.
        Returns True if valid, False otherwise.
        """
        if not origin or not destination:
            return False
        
        # Load airport validator
        try:
            from app.services.airport_validator import is_valid_airport
            return is_valid_airport(origin) and is_valid_airport(destination)
        except ImportError:
            # If validator not available, accept any 3-letter code
            return len(origin) == 3 and len(destination) == 3 and origin.isalpha() and destination.isalpha()
    
    def _build_success_response(
        self,
        request_id: str,
        offers: List[FlightOffer],
        supplier: str,
        logs: List[Dict],
        elapsed: float
    ) -> Dict:
        """Build successful response."""
        return {
            "request_id": request_id,
            "status": "completed",
            "outcome": "results",
            "flights": [self._serialize_offer(o) for o in offers],
            "offers": [self._serialize_offer(o) for o in offers],
            "supplier": supplier,
            "logs": logs,
            "elapsed_seconds": elapsed,
            "count": len(offers)
        }
    
    def _build_error_response(
        self,
        request_id: str,
        message: str,
        logs: List[Dict],
        elapsed: float
    ) -> Dict:
        """Build error response."""
        return {
            "request_id": request_id,
            "status": "completed",
            "outcome": "error",
            "message": message,
            "flights": [],
            "offers": [],
            "supplier": "none",
            "logs": logs,
            "elapsed_seconds": elapsed
        }
    
    def _serialize_offer(self, offer: FlightOffer) -> Dict:
        """Convert FlightOffer to dict."""
        return offer.dict()
    
    def get_metrics(self) -> Dict:
        """Get orchestrator metrics."""
        return self.metrics


# Global instance
aviasales_first_orchestrator = AviasalesFirstOrchestrator()

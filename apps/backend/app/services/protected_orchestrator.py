"""
Protected Flight Search Orchestrator (Pattern 1 - Safe/Cost-Conscious)

Implements comprehensive supplier protection with:
1. Redis-based rate limiter (token bucket)
2. Redis-based circuit breaker
3. Same-day search policy (IST timezone)
4. Primary + Fallback supplier logic
5. Background enrichment
6. Hub composition as final fallback

Supplier Priority:
- Primary: Amadeus (with protections)
- Fallback: FlightAPI (when Amadeus fails/circuit open)
- Final: Hub composition (connecting flights)

Feature Flag: SUPPLIER_PROTECTION=true
"""

import asyncio
import logging
import time
import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

from app.models.flight import FlightOffer, FlightSearchRequest
from app.services.redis_client import redis_client
from app.services.redis_rate_limiter import RedisRateLimiter, RateLimitConfig
from app.services.redis_circuit_breaker import RedisCircuitBreaker
from app.services.same_day_validator import SameDayValidator
from app.services.hub_composer import HubComposer
from app.config import settings

logger = logging.getLogger(__name__)

class ProtectedOrchestrator:
    """
    Pattern 1: Safe/Cost-Conscious orchestrator.
    
    Always prefer Amadeus, but protect it aggressively.
    Use FlightAPI as synchronous fallback.
    Apply same-day policy.
    """
    
    def __init__(self):
        self.rate_limiter = RedisRateLimiter(redis_client)
        self.circuit_breaker = RedisCircuitBreaker(redis_client)
        self.hub_composer = None  # Initialized later
        self.background_window_ms = 800
        
        # Metrics
        self.metrics = {
            "total_searches": 0,
            "amadeus_success": 0,
            "amadeus_fallback": 0,
            "flightapi_used": 0,
            "hub_composition_used": 0,
            "same_day_shifted": 0
        }
    
    async def initialize(self):
        """Initialize Redis-based components."""
        try:
            # Connect to Redis
            await redis_client.connect()
            
            # Load Lua scripts
            await self.rate_limiter.initialize()
            
            # Configure rate limiter for Amadeus
            amadeus_rps = getattr(settings, 'amadeus_rps', 3)
            amadeus_rpm = getattr(settings, 'amadeus_rpm', 100)
            amadeus_burst = getattr(settings, 'amadeus_burst', 5)
            
            self.rate_limiter.configure(RateLimitConfig(
                supplier_id="amadeus",
                requests_per_second=amadeus_rps,
                requests_per_minute=amadeus_rpm,
                burst_capacity=amadeus_burst,
                queue_timeout_ms=2000
            ))
            
            # Configure circuit breaker for Amadeus
            amadeus_failures = getattr(settings, 'amadeus_circuit_failures', 3)
            amadeus_cooldown = getattr(settings, 'amadeus_circuit_cooldown_seconds', 300)
            
            self.circuit_breaker.configure(
                supplier_id="amadeus",
                failure_threshold=amadeus_failures,
                cooldown_seconds=amadeus_cooldown
            )
            
            # Configure FlightAPI (no rate limit for now)
            self.circuit_breaker.configure(
                supplier_id="flightapi",
                failure_threshold=5,
                cooldown_seconds=180
            )
            
            # Initialize hub composer
            self.hub_composer = HubComposer(self._search_single_supplier)
            
            logger.info("✅ ProtectedOrchestrator initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize ProtectedOrchestrator: {e}")
            raise
    
    async def search(
        self,
        request: FlightSearchRequest,
        request_id: Optional[str] = None
    ) -> Dict:
        """
        Execute protected flight search with fallbacks.
        
        Flow:
        1. Validate same-day policy
        2. Check Amadeus circuit breaker
        3. Try Amadeus (with rate limiter)
        4. If Amadeus fails/empty -> FlightAPI (sync)
        5. If FlightAPI fails/empty -> Hub composition
        6. Return results or no_results
        """
        if not request_id:
            request_id = str(uuid.uuid4())
        
        self.metrics["total_searches"] += 1
        search_logs = []
        start_time = time.time()
        
        logger.info(
            f"🔍 [{request_id}] Protected search: "
            f"{request.origin} → {request.destination} on {request.departure_date}"
        )
        
        # Step 1: Apply same-day policy
        request_dict = request.dict()
        request_dict, same_day_meta = SameDayValidator.apply_to_request(request_dict)
        
        if same_day_meta.get("same_day_shifted"):
            self.metrics["same_day_shifted"] += 1
            search_logs.append({
                "step": "same_day_policy",
                "action": "shifted",
                "original_date": request.departure_date,
                "suggested_date": request_dict["departure_date"],
                "reason": same_day_meta.get("reason")
            })
            # Update request
            request = FlightSearchRequest(**request_dict)
        
        # Step 2: Try Amadeus (primary)
        amadeus_offers, amadeus_logs = await self._try_amadeus(request, request_id)
        search_logs.extend(amadeus_logs)
        
        if amadeus_offers:
            # Amadeus success - return immediately
            self.metrics["amadeus_success"] += 1
            elapsed = time.time() - start_time
            
            # Launch FlightAPI in background (non-blocking)
            asyncio.create_task(self._background_enrich(request, request_id, amadeus_offers))
            
            logger.info(
                f"✅ [{request_id}] Amadeus SUCCESS: {len(amadeus_offers)} offers in {elapsed:.2f}s"
            )
            
            return {
                "request_id": request_id,
                "status": "completed",
                "outcome": "results",
                "flights": [self._serialize_offer(o) for o in amadeus_offers],
                "supplier": "amadeus",
                "same_day_metadata": same_day_meta,
                "logs": search_logs,
                "elapsed_seconds": elapsed
            }
        
        # Step 3: Amadeus failed/empty - try FlightAPI (fallback)
        self.metrics["amadeus_fallback"] += 1
        logger.warning(f"⚠️  [{request_id}] Amadeus empty/failed - using FlightAPI fallback")
        
        flightapi_offers, flightapi_logs = await self._try_flightapi(request, request_id)
        search_logs.extend(flightapi_logs)
        
        if flightapi_offers:
            self.metrics["flightapi_used"] += 1
            elapsed = time.time() - start_time
            logger.info(
                f"✅ [{request_id}] FlightAPI SUCCESS: {len(flightapi_offers)} offers in {elapsed:.2f}s"
            )
            
            return {
                "request_id": request_id,
                "status": "completed",
                "outcome": "results",
                "flights": [self._serialize_offer(o) for o in flightapi_offers],
                "supplier": "flightapi",
                "same_day_metadata": same_day_meta,
                "logs": search_logs,
                "elapsed_seconds": elapsed
            }
        
        # Step 4: Both suppliers failed - try hub composition
        logger.warning(f"🔄 [{request_id}] All suppliers failed - trying hub composition")
        
        hub_offers, hub_logs = await self._try_hub_composition(request, request_id)
        search_logs.extend(hub_logs)
        
        if hub_offers:
            self.metrics["hub_composition_used"] += 1
            elapsed = time.time() - start_time
            logger.info(
                f"✅ [{request_id}] HUB COMPOSITION SUCCESS: {len(hub_offers)} offers in {elapsed:.2f}s"
            )
            
            return {
                "request_id": request_id,
                "status": "completed",
                "outcome": "results",
                "flights": [self._serialize_offer(o) for o in hub_offers],
                "supplier": "hub_composition",
                "same_day_metadata": same_day_meta,
                "logs": search_logs,
                "elapsed_seconds": elapsed
            }
        
        # Step 5: All fallbacks exhausted - no results
        elapsed = time.time() - start_time
        logger.error(f"❌ [{request_id}] NO RESULTS after all fallbacks ({elapsed:.2f}s)")
        
        # Get supplier warnings
        warnings = await self._get_supplier_warnings()
        
        return {
            "request_id": request_id,
            "status": "completed",
            "outcome": "no_results",
            "message": "No flights found after checking all suppliers and alternatives",
            "flights": [],
            "warnings": warnings,
            "same_day_metadata": same_day_meta,
            "logs": search_logs,
            "elapsed_seconds": elapsed
        }
    
    async def _try_amadeus(
        self,
        request: FlightSearchRequest,
        request_id: str
    ) -> Tuple[List[FlightOffer], List[Dict]]:
        """Try Amadeus with rate limiter and circuit breaker."""
        logs = []
        
        try:
            # Check circuit breaker
            available, circuit_meta = await self.circuit_breaker.is_available("amadeus")
            
            if not available:
                logs.append({
                    "step": "amadeus",
                    "status": "circuit_open",
                    "circuit_metadata": circuit_meta
                })
                logger.warning(f"🚫 [{request_id}] Amadeus circuit OPEN - skipping")
                return [], logs
            
            # Check rate limiter
            allowed, rate_meta = await self.rate_limiter.acquire("amadeus")
            
            if not allowed:
                logs.append({
                    "step": "amadeus",
                    "status": "rate_limited",
                    "rate_metadata": rate_meta
                })
                logger.warning(f"⏸️  [{request_id}] Amadeus rate limited")
                # Don't record as failure - just skip
                return [], logs
            
            # Import adapter
            from app.services.adapters.amadeus_flights import AmadeusFlightsAdapter
            adapter = AmadeusFlightsAdapter()
            
            # Make request with timeout
            timeout_ms = getattr(settings, 'amadeus_timeout_ms', 2500)
            start = time.time()
            
            offers = await asyncio.wait_for(
                adapter.search_flights(request),
                timeout=timeout_ms / 1000
            )
            
            latency_ms = (time.time() - start) * 1000
            
            if offers and len(offers) > 0:
                # Success
                await self.circuit_breaker.record_success("amadeus")
                logs.append({
                    "step": "amadeus",
                    "status": "success",
                    "results": len(offers),
                    "latency_ms": round(latency_ms, 2)
                })
                return offers, logs
            else:
                # Empty result (not a failure)
                logs.append({
                    "step": "amadeus",
                    "status": "empty",
                    "results": 0,
                    "latency_ms": round(latency_ms, 2)
                })
                return [], logs
        
        except asyncio.TimeoutError:
            await self.circuit_breaker.record_failure("amadeus", "timeout")
            logs.append({
                "step": "amadeus",
                "status": "timeout",
                "error": "Request timeout"
            })
            return [], logs
        
        except Exception as e:
            error_str = str(e)
            
            # Detect error type
            if "429" in error_str:
                await self.circuit_breaker.record_failure("amadeus", "429")
            elif "401" in error_str:
                await self.circuit_breaker.record_failure("amadeus", "401")
            else:
                await self.circuit_breaker.record_failure("amadeus", "5xx")
            
            logs.append({
                "step": "amadeus",
                "status": "error",
                "error": error_str
            })
            logger.error(f"Amadeus error: {e}")
            return [], logs
    
    async def _try_flightapi(
        self,
        request: FlightSearchRequest,
        request_id: str
    ) -> Tuple[List[FlightOffer], List[Dict]]:
        """Try FlightAPI as fallback."""
        logs = []
        
        try:
            # Check if enabled
            if not getattr(settings, 'flightapi_enabled', False):
                logs.append({
                    "step": "flightapi",
                    "status": "disabled"
                })
                return [], logs
            
            # Check circuit breaker
            available, circuit_meta = await self.circuit_breaker.is_available("flightapi")
            
            if not available:
                logs.append({
                    "step": "flightapi",
                    "status": "circuit_open",
                    "circuit_metadata": circuit_meta
                })
                return [], logs
            
            # Import adapter
            from app.services.adapters.flightapi_adapter import FlightAPIAdapter
            adapter = FlightAPIAdapter()
            
            # Make request
            timeout_ms = getattr(settings, 'flightapi_timeout_ms', 3000)
            start = time.time()
            
            offers = await asyncio.wait_for(
                adapter.search_flights(request),
                timeout=timeout_ms / 1000
            )
            
            latency_ms = (time.time() - start) * 1000
            
            if offers and len(offers) > 0:
                await self.circuit_breaker.record_success("flightapi")
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
            await self.circuit_breaker.record_failure("flightapi", "timeout")
            logs.append({
                "step": "flightapi",
                "status": "timeout"
            })
            return [], logs
        
        except Exception as e:
            await self.circuit_breaker.record_failure("flightapi", "5xx")
            logs.append({
                "step": "flightapi",
                "status": "error",
                "error": str(e)
            })
            logger.error(f"FlightAPI error: {e}")
            return [], logs
    
    async def _try_hub_composition(
        self,
        request: FlightSearchRequest,
        request_id: str
    ) -> Tuple[List[FlightOffer], List[Dict]]:
        """Try hub composition as final fallback."""
        logs = []
        
        if not self.hub_composer:
            return [], logs
        
        try:
            start = time.time()
            offers = await self.hub_composer.compose_via_hubs(request, max_hubs=2)
            latency_ms = (time.time() - start) * 1000
            
            logs.append({
                "step": "hub_composition",
                "status": "success" if offers else "empty",
                "results": len(offers) if offers else 0,
                "latency_ms": round(latency_ms, 2)
            })
            
            return offers or [], logs
        
        except Exception as e:
            logs.append({
                "step": "hub_composition",
                "status": "error",
                "error": str(e)
            })
            logger.error(f"Hub composition error: {e}")
            return [], logs
    
    async def _background_enrich(
        self,
        request: FlightSearchRequest,
        request_id: str,
        primary_offers: List[FlightOffer]
    ):
        """Launch FlightAPI in background to enrich results (non-blocking)."""
        try:
            logger.info(f"🔄 [{request_id}] Background enrichment: FlightAPI")
            
            flightapi_offers, _ = await self._try_flightapi(request, request_id)
            
            if flightapi_offers:
                # Deduplicate and merge
                merged = self._deduplicate_offers(primary_offers, flightapi_offers)
                
                logger.info(
                    f"✅ [{request_id}] Background enrichment: +{len(merged) - len(primary_offers)} offers"
                )
                
                # Store in cache for potential UI refresh
                # TODO: Implement cache storage and WebSocket push
        
        except Exception as e:
            logger.error(f"Background enrichment error: {e}")
    
    def _deduplicate_offers(
        self,
        primary: List[FlightOffer],
        secondary: List[FlightOffer]
    ) -> List[FlightOffer]:
        """Deduplicate offers using deterministic key."""
        seen_keys = set()
        merged = []
        
        for offer in primary + secondary:
            # Generate deterministic key
            key_parts = []
            for seg in offer.segments:
                key_parts.append(f"{seg.departure_airport}-{seg.arrival_airport}")
                key_parts.append(seg.carrier_code or "")
                key_parts.append(str(seg.departure_time)[:16])  # Minute precision
            
            key = "|".join(key_parts)
            
            if key not in seen_keys:
                seen_keys.add(key)
                merged.append(offer)
        
        return merged
    
    async def _search_single_supplier(
        self,
        request: FlightSearchRequest
    ) -> List[FlightOffer]:
        """Helper for hub composer."""
        offers, _ = await self._try_amadeus(request, "hub-internal")
        return offers
    
    async def _get_supplier_warnings(self) -> List[Dict]:
        """Get warnings for degraded suppliers."""
        warnings = []
        
        for supplier_id in ["amadeus", "flightapi"]:
            status = await self.circuit_breaker.get_status(supplier_id)
            
            if status.get("state") == "OPEN":
                warnings.append({
                    "supplier": supplier_id,
                    "status": "degraded",
                    "reason": status.get("last_error", "unknown"),
                    "retry_after_seconds": status.get("retry_after_seconds", 0),
                    "message": f"{supplier_id.title()} is temporarily unavailable. Using alternate providers."
                })
        
        return warnings
    
    def _serialize_offer(self, offer: FlightOffer) -> Dict:
        """Convert FlightOffer to dict."""
        return offer.dict()
    
    def get_metrics(self) -> Dict:
        """Get orchestrator metrics."""
        return {
            **self.metrics,
            "rate_limiter": self.rate_limiter.get_metrics(),
            "circuit_breaker": self.circuit_breaker.get_metrics()
        }

# Global instance
protected_orchestrator = ProtectedOrchestrator()

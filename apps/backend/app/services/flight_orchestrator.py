"""
Flight Search Orchestrator

Implements comprehensive search strategy with fallbacks:
1. Primary supplier search (parallel)
2. Date window fallback
3. Nearby airports fallback
4. Hub composition fallback

Never returns "no results" until ALL fallbacks are exhausted.
"""

import asyncio
import logging
import time
import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

from app.models.flight import FlightOffer, FlightSearchRequest
from app.services.aggregator import SearchAggregator
from app.services.hub_composer import HubComposer
from app.services.circuit_breaker import circuit_breaker
from app.config import settings

logger = logging.getLogger(__name__)

class FlightOrchestrator:
    """
    Orchestrates flight search with comprehensive fallback strategy.
    
    Ensures:
    - Immediate status response
    - All fallbacks attempted before "no results"
    - Hub composition for long-haul routes
    - Circuit breaker for unhealthy suppliers
    """
    
    def __init__(self):
        self.aggregator = SearchAggregator()
        self.hub_composer = HubComposer(self._search_via_aggregator)
        self.max_total_calls = 25  # Budget limit
        self.call_count = 0
        
    async def search(
        self,
        request: FlightSearchRequest,
        request_id: Optional[str] = None
    ) -> Dict:
        """
        Execute comprehensive flight search with fallbacks.
        
        Returns:
        {
            "request_id": "...",
            "status": "completed",
            "outcome": "results" | "no_results" | "invalid_input",
            "flights": [...],
            "suggestions": [...],
            "logs": [...]
        }
        """
        if not request_id:
            request_id = str(uuid.uuid4())
        
        self.call_count = 0
        search_logs = []
        start_time = time.time()
        
        logger.info(f"🔍 [{request_id}] Search started: {request.origin} → {request.destination}")
        
        # Step 1: Validate inputs
        validation_error = self._validate_request(request)
        if validation_error:
            logger.warning(f"❌ [{request_id}] Validation failed: {validation_error}")
            return {
                "request_id": request_id,
                "status": "completed",
                "outcome": "invalid_input",
                "message": validation_error,
                "flights": [],
                "suggestions": [],
                "logs": []
            }
        
        # Step 2: Primary supplier search
        logger.info(f"📡 [{request_id}] PRIMARY SEARCH")
        primary_offers, primary_logs = await self._primary_search(request)
        search_logs.extend(primary_logs)
        
        if primary_offers:
            elapsed = time.time() - start_time
            logger.info(f"✅ [{request_id}] PRIMARY SUCCESS: {len(primary_offers)} flights in {elapsed:.2f}s")
            return {
                "request_id": request_id,
                "status": "completed",
                "outcome": "results",
                "flights": [self._serialize_offer(o) for o in primary_offers],
                "suggestions": [],
                "warnings": self._get_supplier_warnings(),
                "logs": search_logs,
                "total_calls": self.call_count,
                "elapsed_seconds": elapsed
            }
        
        logger.info(f"⚠️ [{request_id}] No primary results - starting fallbacks...")
        
        # Step 3: DATE WINDOW FALLBACK
        logger.info(f"📅 [{request_id}] DATE WINDOW FALLBACK (±3 days)")
        date_offers, date_logs = await self._date_window_fallback(request)
        search_logs.extend(date_logs)
        
        if date_offers:
            elapsed = time.time() - start_time
            logger.info(f"✅ [{request_id}] DATE FALLBACK SUCCESS: {len(date_offers)} flights")
            return {
                "request_id": request_id,
                "status": "completed",
                "outcome": "results",
                "flights": [self._serialize_offer(o) for o in date_offers],
                "suggestions": self._build_suggestions("date"),
                "logs": search_logs,
                "total_calls": self.call_count,
                "elapsed_seconds": elapsed
            }
        
        # Step 4: NEARBY AIRPORTS FALLBACK
        logger.info(f"🗺️ [{request_id}] NEARBY AIRPORTS FALLBACK")
        nearby_offers, nearby_logs = await self._nearby_airports_fallback(request)
        search_logs.extend(nearby_logs)
        
        if nearby_offers:
            elapsed = time.time() - start_time
            logger.info(f"✅ [{request_id}] NEARBY FALLBACK SUCCESS: {len(nearby_offers)} flights")
            return {
                "request_id": request_id,
                "status": "completed",
                "outcome": "results",
                "flights": [self._serialize_offer(o) for o in nearby_offers],
                "suggestions": self._build_suggestions("nearby"),
                "logs": search_logs,
                "total_calls": self.call_count,
                "elapsed_seconds": elapsed
            }
        
        # Step 5: HUB COMPOSITION FALLBACK (THE KEY FIX!)
        logger.info(f"🔄 [{request_id}] HUB COMPOSITION FALLBACK")
        hub_offers, hub_logs = await self._hub_composition_fallback(request)
        search_logs.extend(hub_logs)
        
        if hub_offers:
            elapsed = time.time() - start_time
            logger.info(f"✅ [{request_id}] HUB COMPOSITION SUCCESS: {len(hub_offers)} connecting flights")
            return {
                "request_id": request_id,
                "status": "completed",
                "outcome": "results",
                "flights": [self._serialize_offer(o) for o in hub_offers],
                "suggestions": self._build_suggestions("hub"),
                "logs": search_logs,
                "total_calls": self.call_count,
                "elapsed_seconds": elapsed
            }
        
        # Step 6: ALL FALLBACKS EXHAUSTED - NO RESULTS
        elapsed = time.time() - start_time
        logger.warning(f"❌ [{request_id}] NO RESULTS after all fallbacks ({elapsed:.2f}s, {self.call_count} calls)")
        
        # Check for degraded suppliers
        warnings = self._get_supplier_warnings()
        
        return {
            "request_id": request_id,
            "status": "completed",
            "outcome": "no_results",
            "message": "No flights found after checking all alternatives",
            "flights": [],
            "suggestions": self._build_suggestions("all"),
            "logs": search_logs,
            "warnings": warnings,
            "total_calls": self.call_count,
            "elapsed_seconds": elapsed
        }
    
    def _validate_request(self, request: FlightSearchRequest) -> Optional[str]:
        """Validate request inputs. Returns error message or None."""
        if not request.origin or len(request.origin) != 3:
            return "Invalid origin airport code"
        
        if not request.destination or len(request.destination) != 3:
            return "Invalid destination airport code"
        
        if not request.departure_date:
            return "Departure date is required"
        
        try:
            dep_date = datetime.strptime(request.departure_date, "%Y-%m-%d")
            if dep_date.date() < datetime.now().date():
                return "Departure date must be in the future"
        except:
            return "Invalid date format (expected YYYY-MM-DD)"
        
        return None
    
    async def _primary_search(
        self,
        request: FlightSearchRequest
    ) -> Tuple[List[FlightOffer], List[Dict]]:
        """Execute primary search across all suppliers."""
        logs = []
        
        try:
            start = time.time()
            offers = await asyncio.wait_for(
                self.aggregator.search_flights(request),
                timeout=7.0  # 7 second timeout
            )
            latency = (time.time() - start) * 1000
            
            self.call_count += 1
            logs.append({
                "step": "primary",
                "supplier": "aggregated",
                "status": "success",
                "results": len(offers),
                "latency_ms": latency
            })
            
            return offers, logs
            
        except asyncio.TimeoutError:
            logs.append({
                "step": "primary",
                "supplier": "aggregated",
                "status": "timeout",
                "results": 0
            })
            return [], logs
        except Exception as e:
            logger.error(f"Primary search error: {e}")
            logs.append({
                "step": "primary",
                "supplier": "aggregated",
                "status": "error",
                "error": str(e)
            })
            return [], logs
    
    async def _date_window_fallback(
        self,
        request: FlightSearchRequest,
        window_days: int = 3
    ) -> Tuple[List[FlightOffer], List[Dict]]:
        """Try alternative dates ±N days."""
        if self.call_count >= self.max_total_calls:
            return [], []
        
        logs = []
        base_date = datetime.strptime(request.departure_date, "%Y-%m-%d")
        
        # Try ±1, ±2, ±3 days
        alt_dates = []
        for offset in [-3, -2, -1, 1, 2, 3]:
            alt_date = base_date + timedelta(days=offset)
            if alt_date.date() >= datetime.now().date():
                alt_dates.append(alt_date.strftime("%Y-%m-%d"))
        
        # Search alternative dates in parallel
        tasks = []
        for alt_date in alt_dates[:3]:  # Limit to 3 dates
            alt_request = request.copy(deep=True)
            alt_request.departure_date = alt_date
            tasks.append(self._search_via_aggregator(alt_request))
        
        if not tasks:
            return [], []
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        self.call_count += len(tasks)
        
        all_offers = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logs.append({
                    "step": "date_fallback",
                    "date": alt_dates[i],
                    "status": "error",
                    "error": str(result)
                })
            elif isinstance(result, list) and result:
                logs.append({
                    "step": "date_fallback",
                    "date": alt_dates[i],
                    "status": "success",
                    "results": len(result)
                })
                all_offers.extend(result)
            else:
                logs.append({
                    "step": "date_fallback",
                    "date": alt_dates[i],
                    "status": "no_results"
                })
        
        return all_offers[:10], logs
    
    async def _nearby_airports_fallback(
        self,
        request: FlightSearchRequest
    ) -> Tuple[List[FlightOffer], List[Dict]]:
        """Try nearby airports for origin and destination."""
        if self.call_count >= self.max_total_calls:
            return [], []
        
        # Use aggregator's nearby airport logic
        nearby_request = request.copy(deep=True)
        nearby_request.include_nearby_origin = True
        nearby_request.include_nearby_destination = True
        
        logs = []
        
        try:
            offers = await self.aggregator.search_flights(nearby_request)
            self.call_count += 1
            
            # Filter to only nearby results
            nearby_offers = [
                o for o in offers
                if o.nearby_origin or o.nearby_destination
            ]
            
            logs.append({
                "step": "nearby_airports",
                "status": "success",
                "results": len(nearby_offers)
            })
            
            return nearby_offers[:10], logs
            
        except Exception as e:
            logger.error(f"Nearby airports fallback error: {e}")
            logs.append({
                "step": "nearby_airports",
                "status": "error",
                "error": str(e)
            })
            return [], logs
    
    async def _hub_composition_fallback(
        self,
        request: FlightSearchRequest
    ) -> Tuple[List[FlightOffer], List[Dict]]:
        """Compose connecting flights via hub airports."""
        if self.call_count >= self.max_total_calls:
            return [], []
        
        logs = []
        
        try:
            start = time.time()
            offers = await self.hub_composer.compose_via_hubs(request, max_hubs=3)
            latency = (time.time() - start) * 1000
            
            self.call_count += 6  # Approximate (3 hubs × 2 legs)
            
            logs.append({
                "step": "hub_composition",
                "status": "success",
                "results": len(offers),
                "latency_ms": latency
            })
            
            return offers, logs
            
        except Exception as e:
            logger.error(f"Hub composition error: {e}")
            logs.append({
                "step": "hub_composition",
                "status": "error",
                "error": str(e)
            })
            return [], logs
    
    async def _search_via_aggregator(
        self,
        request: FlightSearchRequest
    ) -> List[FlightOffer]:
        """Helper to search via aggregator."""
        try:
            return await asyncio.wait_for(
                self.aggregator.search_flights(request),
                timeout=7.0
            )
        except asyncio.TimeoutError:
            logger.warning(f"Aggregator timeout for {request.origin} → {request.destination}")
            return []
        except Exception as e:
            logger.error(f"Aggregator error: {e}")
            return []
    
    def _build_suggestions(self, fallback_type: str) -> List[Dict]:
        """Build suggestions for no-results scenario."""
        suggestions = []
        
        if fallback_type in ["all", "date"]:
            suggestions.append({
                "type": "date",
                "description": "Try searching ±3 days from your preferred date",
                "example": "Flights may be available on nearby dates"
            })
        
        if fallback_type in ["all", "nearby"]:
            suggestions.append({
                "type": "nearby",
                "description": "Try nearby airports within 200km",
                "example": "Consider major airports like BOM, DEL, BLR"
            })
        
        if fallback_type in ["all", "hub"]:
            suggestions.append({
                "type": "hub",
                "description": "Try connecting via major hubs",
                "example": "Book separate flights via hubs like Mumbai (BOM) or Delhi (DEL)"
            })
        
        return suggestions
    
    def _serialize_offer(self, offer: FlightOffer) -> Dict:
        """Convert FlightOffer to dict for JSON response."""
        return offer.dict()
    
    def _get_supplier_warnings(self) -> List[Dict]:
        """Get warnings for degraded suppliers."""
        from app.services.circuit_breaker import circuit_breaker
        import time
        
        warnings = []
        stats = circuit_breaker.get_stats()
        
        for supplier_id, stat in stats.items():
            if stat.get("circuit_open"):
                # Calculate when circuit will close
                health = circuit_breaker.get_health(supplier_id)
                if health and health.circuit_open_until > time.time():
                    warnings.append({
                        "supplier": supplier_id,
                        "status": "degraded",
                        "reason": "429 - quota exceeded",
                        "opened_until": datetime.fromtimestamp(health.circuit_open_until).isoformat() + "Z",
                        "message": f"{supplier_id.title()} is temporarily rate-limited. Using alternate providers."
                    })
        
        return warnings

# Global orchestrator instance
orchestrator = FlightOrchestrator()

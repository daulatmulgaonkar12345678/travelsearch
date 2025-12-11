"""
Rate Limiter for Supplier APIs

Prevents account suspension from excessive API calls.
Implements sliding window algorithm with burst capacity.

Features:
- Per-second rate limiting (RPS)
- Per-minute rate limiting (RPM)
- Burst capacity
- Request queuing
- Circuit breaker integration
"""

import asyncio
import time
import logging
from typing import Optional, Dict, List, Tuple
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Rate limit configuration for a supplier."""
    supplier_id: str
    requests_per_second: int = 3
    requests_per_minute: int = 100
    burst_capacity: int = 5
    queue_timeout_seconds: float = 2.0

@dataclass
class RateLimitState:
    """Track rate limit state for a supplier."""
    supplier_id: str
    
    # Sliding windows
    requests_last_second: deque = field(default_factory=deque)
    requests_last_minute: deque = field(default_factory=deque)
    
    # Burst tracking
    burst_tokens: int = 0
    last_burst_refill: float = field(default_factory=time.time)
    
    # Statistics
    total_requests: int = 0
    blocked_requests: int = 0
    queued_requests: int = 0
    
    # Circuit breaker tracking
    recent_429s: deque = field(default_factory=deque)  # Timestamps of 429 errors

class RateLimiter:
    """
    Sliding window rate limiter with burst capacity and queuing.
    
    Prevents supplier account suspension by:
    1. Limiting requests per second (RPS)
    2. Limiting requests per minute (RPM)
    3. Allowing short bursts
    4. Queuing requests when near limit
    5. Tracking 429 errors for circuit breaker
    """
    
    def __init__(self):
        self.configs: Dict[str, RateLimitConfig] = {}
        self.states: Dict[str, RateLimitState] = {}
        self._lock = asyncio.Lock()
        
    def configure(self, config: RateLimitConfig):
        """Configure rate limits for a supplier."""
        self.configs[config.supplier_id] = config
        self.states[config.supplier_id] = RateLimitState(
            supplier_id=config.supplier_id,
            burst_tokens=config.burst_capacity
        )
        logger.info(
            f"⚙️  Rate limiter configured for {config.supplier_id}: "
            f"{config.requests_per_second} RPS, {config.requests_per_minute} RPM, "
            f"burst={config.burst_capacity}"
        )
    
    async def acquire(self, supplier_id: str) -> bool:
        """
        Acquire permission to make a request.
        
        Returns:
            True if request allowed, False if rejected
        """
        if supplier_id not in self.configs:
            # No rate limiting configured
            return True
        
        config = self.configs[supplier_id]
        state = self.states[supplier_id]
        
        async with self._lock:
            # Clean old timestamps
            self._cleanup_old_requests(state)
            
            # Check if we can proceed immediately
            if self._can_proceed(state, config):
                self._record_request(state)
                return True
            
            # Try burst capacity
            if self._use_burst_token(state, config):
                self._record_request(state)
                logger.debug(f"🔥 Burst token used for {supplier_id}")
                return True
            
            # Need to queue
            logger.warning(
                f"⏸️  Rate limit reached for {supplier_id}. "
                f"RPS: {len(state.requests_last_second)}/{config.requests_per_second}, "
                f"RPM: {len(state.requests_last_minute)}/{config.requests_per_minute}"
            )
            state.queued_requests += 1
            
        # Wait and retry
        wait_time = self._calculate_wait_time(state, config)
        
        if wait_time > config.queue_timeout_seconds:
            logger.error(
                f"❌ Rate limit exceeded for {supplier_id}. "
                f"Would need to wait {wait_time:.2f}s (timeout: {config.queue_timeout_seconds}s)"
            )
            state.blocked_requests += 1
            return False
        
        logger.info(f"⏳ Queuing request for {supplier_id}, waiting {wait_time:.2f}s...")
        await asyncio.sleep(wait_time)
        
        # Try again after waiting
        async with self._lock:
            if self._can_proceed(state, config):
                self._record_request(state)
                return True
            else:
                state.blocked_requests += 1
                return False
    
    def record_429(self, supplier_id: str):
        """Record a 429 error for circuit breaker tracking."""
        if supplier_id not in self.states:
            return
        
        state = self.states[supplier_id]
        now = time.time()
        state.recent_429s.append(now)
        
        # Keep only last minute
        while state.recent_429s and state.recent_429s[0] < now - 60:
            state.recent_429s.popleft()
        
        logger.warning(
            f"⚠️  429 error recorded for {supplier_id}. "
            f"Count in last minute: {len(state.recent_429s)}"
        )
    
    def get_429_count_last_minute(self, supplier_id: str) -> int:
        """Get count of 429 errors in the last minute."""
        if supplier_id not in self.states:
            return 0
        
        state = self.states[supplier_id]
        now = time.time()
        
        # Clean old 429s
        while state.recent_429s and state.recent_429s[0] < now - 60:
            state.recent_429s.popleft()
        
        return len(state.recent_429s)
    
    def _cleanup_old_requests(self, state: RateLimitState):
        """Remove timestamps older than tracking window."""
        now = time.time()
        
        # Clean requests older than 1 second
        while state.requests_last_second and state.requests_last_second[0] < now - 1.0:
            state.requests_last_second.popleft()
        
        # Clean requests older than 1 minute
        while state.requests_last_minute and state.requests_last_minute[0] < now - 60.0:
            state.requests_last_minute.popleft()
    
    def _can_proceed(self, state: RateLimitState, config: RateLimitConfig) -> bool:
        """Check if request can proceed without waiting."""
        rps_ok = len(state.requests_last_second) < config.requests_per_second
        rpm_ok = len(state.requests_last_minute) < config.requests_per_minute
        return rps_ok and rpm_ok
    
    def _use_burst_token(self, state: RateLimitState, config: RateLimitConfig) -> bool:
        """Try to use a burst token."""
        now = time.time()
        
        # Refill burst tokens (1 token per second)
        elapsed = now - state.last_burst_refill
        if elapsed >= 1.0:
            tokens_to_add = int(elapsed)
            state.burst_tokens = min(
                state.burst_tokens + tokens_to_add,
                config.burst_capacity
            )
            state.last_burst_refill = now
        
        # Use token if available
        if state.burst_tokens > 0:
            state.burst_tokens -= 1
            return True
        
        return False
    
    def _record_request(self, state: RateLimitState):
        """Record a request timestamp."""
        now = time.time()
        state.requests_last_second.append(now)
        state.requests_last_minute.append(now)
        state.total_requests += 1
    
    def _calculate_wait_time(self, state: RateLimitState, config: RateLimitConfig) -> float:
        """Calculate how long to wait before retry."""
        now = time.time()
        
        # Calculate when next second slot opens
        if state.requests_last_second:
            oldest_in_second = state.requests_last_second[0]
            wait_for_second = max(0, 1.0 - (now - oldest_in_second) + 0.05)  # 50ms buffer
        else:
            wait_for_second = 0
        
        # Calculate when next minute slot opens
        if len(state.requests_last_minute) >= config.requests_per_minute:
            oldest_in_minute = state.requests_last_minute[0]
            wait_for_minute = max(0, 60.0 - (now - oldest_in_minute) + 0.1)  # 100ms buffer
        else:
            wait_for_minute = 0
        
        return max(wait_for_second, wait_for_minute)
    
    def get_stats(self, supplier_id: str) -> Dict:
        """Get rate limiter statistics."""
        if supplier_id not in self.states:
            return {}
        
        state = self.states[supplier_id]
        config = self.configs[supplier_id]
        
        self._cleanup_old_requests(state)
        
        return {
            "total_requests": state.total_requests,
            "blocked_requests": state.blocked_requests,
            "queued_requests": state.queued_requests,
            "current_rps": len(state.requests_last_second),
            "current_rpm": len(state.requests_last_minute),
            "max_rps": config.requests_per_second,
            "max_rpm": config.requests_per_minute,
            "burst_tokens_available": state.burst_tokens,
            "recent_429s": len(state.recent_429s)
        }

# Global rate limiter instance
rate_limiter = RateLimiter()

# Configure Amadeus rate limits (from env or defaults)
from app.config import settings

amadeus_config = RateLimitConfig(
    supplier_id="amadeus",
    requests_per_second=getattr(settings, 'amadeus_rate_limit_rps', 3),
    requests_per_minute=getattr(settings, 'amadeus_rate_limit_rpm', 100),
    burst_capacity=5,
    queue_timeout_seconds=2.0
)

rate_limiter.configure(amadeus_config)

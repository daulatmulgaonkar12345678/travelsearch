"""
Local Token Bucket Rate Limiter (Per-Instance)

Implements in-memory token bucket for fast, local RPS/burst protection.
No external dependencies - pure Python with threading.

Features:
- Per-second rate limiting with burst capacity
- Thread-safe token refill
- Wait-and-consume with timeout
- Zero latency (no network calls)
"""

import time
import threading
import logging

logger = logging.getLogger(__name__)

class LocalTokenBucket:
    """
    Thread-safe token bucket for local rate limiting.
    
    Args:
        rate_per_sec: Tokens added per second (e.g., 3.0 for 3 RPS)
        burst: Maximum tokens (bucket capacity)
    """
    
    def __init__(self, rate_per_sec: float = 3.0, burst: float = 5.0):
        self.rate = float(rate_per_sec)
        self.burst = float(burst)
        self.tokens = float(burst)  # Start with full bucket
        self.last = time.time()
        self.lock = threading.Lock()
        
        logger.info(
            f"LocalTokenBucket initialized: rate={rate_per_sec}/s, burst={burst}"
        )
    
    def _refill(self):
        """Refill tokens based on elapsed time (called with lock held)."""
        now = time.time()
        elapsed = now - self.last
        # Add tokens proportional to time elapsed
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last = now
    
    def try_consume(self, tokens: float = 1.0) -> bool:
        """
        Try to consume tokens immediately (non-blocking).
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens available and consumed, False otherwise
        """
        with self.lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait_consume(self, tokens: float = 1.0, timeout: float = 0.3, poll: float = 0.02) -> bool:
        """
        Wait for tokens with timeout (blocking with polling).
        
        Args:
            tokens: Number of tokens to consume
            timeout: Maximum wait time in seconds
            poll: Polling interval in seconds
            
        Returns:
            True if tokens acquired within timeout, False otherwise
        """
        deadline = time.time() + timeout
        
        while time.time() < deadline:
            if self.try_consume(tokens):
                return True
            time.sleep(poll)
        
        return False
    
    def peek(self) -> dict:
        """
        Get current state without consuming tokens.
        
        Returns:
            Dictionary with current tokens, rate, and capacity
        """
        with self.lock:
            self._refill()
            return {
                "current_tokens": round(self.tokens, 2),
                "capacity": self.burst,
                "refill_rate_per_sec": self.rate
            }

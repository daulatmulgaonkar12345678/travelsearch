from typing import Optional
import hashlib
import re

class BotDetectionService:
    """Bot detection and device fingerprinting"""
    
    SUSPICIOUS_USER_AGENTS = [
        r"bot", r"crawler", r"spider", r"scraper",
        r"curl", r"wget", r"python-requests", r"go-http-client"
    ]
    
    @staticmethod
    def generate_fingerprint(user_agent: str, accept_headers: str, ip: str) -> str:
        """Generate device fingerprint from request headers"""
        fingerprint_str = f"{user_agent}|{accept_headers}|{ip}"
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()
    
    @staticmethod
    def is_suspicious_user_agent(user_agent: str) -> bool:
        """Check if user agent matches known bot patterns"""
        user_agent_lower = user_agent.lower()
        return any(
            re.search(pattern, user_agent_lower)
            for pattern in BotDetectionService.SUSPICIOUS_USER_AGENTS
        )
    
    @staticmethod
    def calculate_fraud_score(user_agent: str, ip: str, behavior_signals: dict) -> float:
        """Calculate fraud score 0-100 (higher = more suspicious)"""
        score = 0.0
        
        # Check user agent
        if BotDetectionService.is_suspicious_user_agent(user_agent):
            score += 40.0
        
        # Check IP patterns (mock)
        if ip.startswith("10.") or ip.startswith("172."):
            score += 5.0  # Private IP (less suspicious in dev)
        
        # Behavior signals
        if behavior_signals.get("rapid_clicks", 0) > 5:
            score += 20.0
        
        if behavior_signals.get("no_js", False):
            score += 15.0
        
        return min(score, 100.0)
    
    @staticmethod
    def should_challenge(fraud_score: float) -> bool:
        """Determine if CAPTCHA challenge is needed"""
        return fraud_score > 50.0

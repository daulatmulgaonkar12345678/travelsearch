from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import hashlib

class ClickLog(BaseModel):
    """Affiliate click tracking"""
    click_id: str
    route: str              # e.g., "BOM-PNQ"
    provider: str
    offer_id: str
    price: float
    device_fingerprint_hash: str
    ip_masked: str          # Last octet masked
    user_agent: str
    timestamp: datetime = datetime.utcnow
    fraud_flag: bool = False
    fraud_reason: Optional[str] = None
    conversion_status: str = "pending"  # pending, confirmed, cancelled
    
    @staticmethod
    def hash_fingerprint(fingerprint: str) -> str:
        """Hash device fingerprint for privacy"""
        return hashlib.sha256(fingerprint.encode()).hexdigest()
    
    @staticmethod
    def mask_ip(ip: str) -> str:
        """Mask last octet of IP for privacy"""
        parts = ip.split('.')
        if len(parts) == 4:
            parts[-1] = 'xxx'
        return '.'.join(parts)

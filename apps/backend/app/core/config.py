"""
CENTRALIZED CONFIGURATION HUB

This is the SINGLE SOURCE OF TRUTH for all API credentials and settings.
ALL services must import from here:
    from app.core.config import settings

NEVER:
- Load .env in multiple places
- Hardcode credentials
- Use fallback values
- Cache settings manually
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Single source of truth for all configuration"""
    
    # ===== AMADEUS API (Production - Cost Controlled) =====
    amadeus_api_key: str
    amadeus_api_secret: str
    amadeus_base_url: str = "https://api.amadeus.com"
    amadeus_environment: str = "production"
    
    # ===== AMADEUS COST CONTROL (CRITICAL) =====
    # Daily cap for real Amadeus flight searches
    daily_search_cap: int = 70
    # Cache TTL in seconds (10-15 min)
    flight_cache_ttl_seconds: int = 900
    # Per-IP rate limit for real searches
    search_rate_limit_per_ip: int = 5
    # Feature flag to instantly disable real searches
    amadeus_real_search_enabled: bool = True
    
    # Amadeus Rate Limiting & Circuit Breaker
    amadeus_rps: int = 3
    amadeus_rpm: int = 100
    amadeus_burst: int = 5
    amadeus_circuit_failures: int = 3
    amadeus_circuit_cooldown_seconds: int = 300
    amadeus_timeout_ms: int = 2500
    amadeus_rate_limit_rps: int = 3
    amadeus_rate_limit_rpm: int = 100
    
    # ===== AVIASALES / TRAVELPAYOUTS (PRIMARY Flight Provider) =====
    travelpayouts_api_token: Optional[str] = None
    travelpayouts_marker: str = "689331"
    travelpayouts_base_url: str = "https://api.travelpayouts.com"
    travelpayouts_timeout_ms: int = 10000
    aviasales_enabled: bool = True
    
    # Legacy Travelpayouts redirect URL (for backward compatibility)
    travelpayouts_aviasales_base_url: Optional[str] = None
    
    # ===== FLIGHTAPI.IO (Backup Flight Provider) =====
    flightapi_enabled: bool = True
    flightapi_key: Optional[str] = None
    flightapi_base: str = "https://api.flightapi.io"
    flightapi_timeout_ms: int = 3000
    
    # ===== DUFFEL (Secondary Flight Provider) =====
    duffel_test_token: Optional[str] = None
    duffel_environment: str = "test"
    duffel_enabled: bool = False
    
    # ===== OTHER PROVIDERS =====
    kiwi_enabled: bool = False
    kiwi_api_key: Optional[str] = None
    
    # ===== PROVIDER SELECTION =====
    flight_provider: str = "amadeus+duffel"
    hotel_provider: str = "amadeus"
    
    # ===== EMAIL & CAPTCHA =====
    sendgrid_api_key: Optional[str] = None
    recaptcha_site_key: Optional[str] = None
    recaptcha_secret: Optional[str] = None
    
    # ===== DATABASE & CACHE =====
    mongo_url: str = "mongodb://localhost:27017"
    db_name: str = "test_database"
    mongodb_uri: Optional[str] = None
    redis_url: Optional[str] = None
    
    # ===== AUTH & JWT =====
    jwt_secret: str = "your-secret-key-change-in-production"
    admin_totp_issuer: str = "MetasearchPlatform"
    
    # ===== MISC =====
    node_env: str = "development"
    cors_origins: str = "*"
    
    # ===== CACHE & RATE LIMITING =====
    cache_ttl: int = 900
    rate_limit_per_minute: int = 100
    rate_limit_queue_wait_ms: int = 2000
    background_merge_window_ms: int = 800
    
    # ===== SUPPLIER PROTECTION =====
    supplier_protection: bool = True
    
    # ===== ALERTING (Optional) =====
    mock_slack_webhook: Optional[str] = None
    mock_pagerduty_webhook: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file="/app/apps/backend/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

# ===== SINGLETON INSTANCE =====
# This is the ONLY instance that should be imported
settings = Settings()

# ===== STARTUP VALIDATION & LOGGING =====
def log_config_status():
    """Log configuration status on startup (mask sensitive data)"""
    logger.info("="*50)
    logger.info("CONFIGURATION STATUS")
    logger.info("="*50)
    
    # Aviasales/Travelpayouts (PRIMARY)
    if settings.travelpayouts_api_token:
        masked_token = f"{settings.travelpayouts_api_token[:6]}...{settings.travelpayouts_api_token[-4:]}"
        logger.info(f"✅ Travelpayouts API Token: {masked_token} (PRIMARY)")
        logger.info(f"✅ Travelpayouts Marker: {settings.travelpayouts_marker}")
    else:
        logger.warning("⚠️  Travelpayouts API Token: NOT SET (PRIMARY PROVIDER DISABLED)")
    
    # Amadeus (FALLBACK)
    if settings.amadeus_api_key:
        masked_key = f"{settings.amadeus_api_key[:6]}...{settings.amadeus_api_key[-4:]}"
        logger.info(f"✅ Amadeus API Key: {masked_key} (FALLBACK)")
        logger.info(f"✅ Amadeus Base URL: {settings.amadeus_base_url}")
        logger.info(f"✅ Amadeus Environment: {settings.amadeus_environment}")
    else:
        logger.error("❌ Amadeus API Key: NOT SET")
    
    if settings.amadeus_api_secret:
        masked_secret = f"{settings.amadeus_api_secret[:4]}...{settings.amadeus_api_secret[-4:]}"
        logger.info(f"✅ Amadeus API Secret: {masked_secret}")
    else:
        logger.error("❌ Amadeus API Secret: NOT SET")
    
    # FlightAPI
    if settings.flightapi_enabled and settings.flightapi_key:
        masked_key = f"{settings.flightapi_key[:6]}...{settings.flightapi_key[-4:]}"
        logger.info(f"✅ FlightAPI Key: {masked_key}")
    elif settings.flightapi_enabled:
        logger.warning("⚠️  FlightAPI enabled but key NOT SET")
    
    # Database
    logger.info(f"✅ MongoDB URL: {settings.mongo_url}")
    logger.info(f"✅ Database Name: {settings.db_name}")
    
    logger.info("="*50)

# Log config on module import
log_config_status()
